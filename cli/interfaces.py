import argparse
import concurrent.futures
import io
import json
import os
import re
import tarfile
import threading
import time
from pathlib import Path
from urllib.parse import quote
import requests


from azure.storage.blob import ContainerClient
from azure.core.exceptions import HttpResponseError



class ConfigStore:
    def __init__(self, config_dir: Path, config_file: Path, state_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_file
        self.state_dir = state_dir

    def ensure_dirs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        self.ensure_dirs()
        if not self.config_file.exists():
            return {}
        return json.loads(self.config_file.read_text(encoding="utf-8"))

    def save_config(self, data):
        self.ensure_dirs()
        self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
    
    def request(self, method, path, token=None, json_payload=None, data=None, headers=None):
        hdrs = dict(headers or {})
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        response = requests.request(method, url, json=json_payload, data=data, headers=hdrs, timeout=120)

        return response

class AuthManager:
    def __init__(self, config_store: ConfigStore, api_client: APIClient) -> None:
        self.api_client = api_client
        self.config_store = config_store
    
    def ensure_token(self):
        config = self.config_store.load_config()
        token = config.get("jwt")
        if token:
            return token
        raise RuntimeError("Not Authenticated. Please login or register; downme login or downme register.")
    
    def login_user(self):
        config = self.config_store.load_config()
        username = input("Username: ").rstrip()
        password = input("Password: ").rstrip()
        resp = self.api_client.request("POST", "/auth/login", 
                                       data={"username": username, "password": password})

        if resp.status_code != 200:
            raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")
        
        token = resp.json().get("access_token")
        config["jwt"] = token
        self.config_store.save_config(config)
        print("Login successful.")

        return token
    
    def register_user(self):
        config = self.config_store.load_config()
        username= input("Username: ").rstrip()
        password = input("Password: ").rstrip()
        resp = self.api_client.request("POST", "/auth/register", 
                                       json_payload={"username": username, "password": password})
        
        if resp.status_code != 200:
            raise RuntimeError(f"Registration failed: {resp.status_code} {resp.text}")
        
        token = resp.json().get("access_token")
        config["jwt"] = token
        self.config_store.save_config(config)
        print("Registration successful.")
    
        return token
    

class DownloadManager:
    def __init__(self, api_client: APIClient, auth_manager: AuthManager) -> None:
        self.api_client = api_client
        self.auth_manager = auth_manager
    
    def refresh_download_sas(self, game_name, token):
        resp = self.api_client.request(
            "POST",
            "/refresh-sas",
            token=token,
            json_payload={"game_name": game_name},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"SAS refresh failed: {resp.text}")
        return resp.json()["sas_token"]

    def get_download_payload(self, game_name, token):
        resp = self.api_client.request("GET", f"/users/download/{game_name}", token=token)
        if resp.status_code != 200:
            raise RuntimeError(resp.text)
        return resp.json()

    def download_game(self, game_name):
        token = self.auth_manager.ensure_token()
        payload = self.get_download_payload(game_name, token)

        blob_name = payload["blob_prefix"]
        blob_size = payload["blob_size"]
        sas_lock = threading.Lock()
        sas_token = payload["sas_token"]
        blob_base_url = payload["blob_base_url"].rstrip('/')

        out_dir = Path.cwd() / "downloads" / game_name
        out_dir.mkdir(parents=True, exist_ok=True)

        final_file = out_dir / f"{game_name}.zip"

        def fetch_blob() -> bytes:
            nonlocal sas_token

            for _ in range(5):
                try:
                    with sas_lock:
                        container_url = f"{blob_base_url}?{sas_token}"
                        container_client = ContainerClient.from_container_url(container_url)
                        blob_client = container_client.get_blob_client(blob_name)
                    
                    stream = blob_client.download_blob()
                    return stream.readall()

                except HttpResponseError as e:
                    #403 -> SAS expired need to refresh
                    if e.status_code == 403:
                        with sas_lock:
                            sas_token = self.refresh_download_sas(game_name, token)
                        continue
            
            raise RuntimeError(f"Failed downloading game: {game_name}")
        
        data = fetch_blob()

        if len(data) != blob_size:
            raise RuntimeError("Fatal Error: Game file corrupted")
        
        final_file.write_bytes(data)

        print(f"Game download completed !! -- {final_file}")

class UploadManager:
    def __init__(self, auth_manager: AuthManager, api_client: APIClient, config_store: ConfigStore):
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.config_store = config_store
    
    @staticmethod
    def to_binary_payload(path_str: str) -> bytes:
        p = Path(path_str)
        if p.is_file():
            return p.read_bytes()
        if p.is_dir():
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tf:
                for child in sorted(p.rglob("*")):
                    if child.is_file():
                        tf.add(child, arcname=str(child.relative_to(p)))
            return buf.getvalue()
        raise RuntimeError(f"Path not found: {path_str}")
    

    def upload_game(self, game_name, version, path):
        token = self.auth_manager.ensure_token()

        init_resp = self.api_client.request(
            "POST",
            "/publisher/upload/init",
            token=token,
            json_payload={"game_name": game_name, "version": version},
        )
        if init_resp.status_code not in (200, 201):
            raise RuntimeError(init_resp.text)

        init_payload = init_resp.json()
        sas_token = init_payload["sas_token"]
        base_url = init_payload["container_base_url"].rstrip("/")

        blob = self.to_binary_payload(path)
        blob_path = f"{game_name}/{version}/"

        state_file = self.config_store.state_dir / f"{game_name}_{version}_upload.json"
        self.config_store.ensure_dirs()

        state = {}
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))

        if state.get("complete") and state.get("blob_path") == blob_path:
            print(f"Upload already complete for {game_name} {version}. Run commit next.")
            return

        lock = threading.Lock()

        def do_upload():
            nonlocal sas_token

            retries = 5
            for attempt in range(retries):
                try:
                    with lock:
                        container_url = f"{base_url}?{sas_token}"
                        container_client = ContainerClient.from_container_url(container_url)
                        blob_client = container_client.get_blob_client(blob_path)

                    blob_client.upload_blob(
                        blob,
                        overwrite=True,
                        max_concurrency=4,   # optional parallelism
                    )

                    return

                except HttpResponseError as e:
                    if e.status_code == 403:
                        refresh = self.api_client.request(
                            "POST",
                            "/publisher/refresh-sas",
                            token=token,
                            json_payload={"game_name": game_name},
                        )
                        if refresh.status_code == 200:
                            with lock:
                                sas_token = refresh.json()["sas_token"]

                    time.sleep(min(2**attempt, 10))

            raise RuntimeError("Failed to upload game archive")

        do_upload()

        state_file.write_text(
            json.dumps({"complete": True, "blob_path": blob_path}, indent=2),
            encoding="utf-8",
        )

        print(f"Upload complete for {game_name} {version}. Run commit next.")

    def commit_upload(self, game_name, version):
        token = self.auth_manager.ensure_token()
        resp = self.api_client.request(
            "POST",
            "/publisher/upload/commit",
            token=token,
            json_payload={"game_name": game_name, "version": version},
        )
        if resp.status_code != 200:
            raise RuntimeError(resp.text)
        msg = resp.json().get("message", "Game uploaded Successfully!!")
        print(msg)







