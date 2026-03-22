import click, os
from pathlib import Path

from interfaces import APIClient, AuthManager, ConfigStore, DownloadManager, UploadManager

WORKERS = 8
DEFAULT_API = os.getenv("DOWNME_API_URL", "http://127.0.0.1:8000")
CONFIG_DIR = Path.home() / ".downme"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_DIR = CONFIG_DIR / "state"


# reuse your existing GameCLI but slightly modified
class GameCLI:
    def __init__(self):
        self.config_store = ConfigStore(CONFIG_DIR, CONFIG_FILE, STATE_DIR)
        self.api_client = APIClient(DEFAULT_API)
        self.auth_manager = AuthManager(self.config_store, self.api_client)
        self.download_manager = DownloadManager(self.api_client, self.auth_manager)
        self.upload_manager = UploadManager(self.auth_manager, self.api_client, self.config_store)

    def list_games(self):
        token = self.auth_manager.ensure_token()
        resp = self.api_client.request("GET", "/users/games", token=token)
        if resp.status_code == 401:
            raise RuntimeError("Invalid JWT. Delete ~/.downme/config.json and login again.")
        if resp.status_code != 200:
            raise RuntimeError(resp.text)

        games = resp.json()
        click.echo("Your Games:")
        for game in games:
            click.echo(f"- {game['name']} ({game['version']})")

# -------------- CLICK BEGINS -----------------

@click.group()
@click.pass_context
def cli(ctx):
    """downme CLI"""
    ctx.obj = GameCLI()


# Authentication operations

@cli.command()
@click.pass_obj
def login(app: GameCLI):
    app.auth_manager.login_user()

@cli.command()
@click.pass_obj
def register(app: GameCLI):
    app.auth_manager.register_user()


# User Operations

@cli.command(name="list")
@click.pass_obj
def list_games(app: GameCLI):
    app.list_games()


@cli.command()
@click.argument("game_name")
@click.pass_obj
def download(app: GameCLI, game_name):
    app.download_manager.download_game(game_name)


# Publisher Operations

@cli.command()
@click.argument("game_name")
@click.argument("version")
@click.argument("path", type=click.Path(exists=True))
@click.pass_obj
def upload(app: GameCLI, game_name, version, path):
    app.upload_manager.upload_game(game_name, version, path)


@cli.command()
@click.argument("game_name")
@click.argument("version")
@click.pass_obj
def commit(app: GameCLI, game_name, version):
    app.upload_manager.commit_upload(game_name, version)



def main():
    cli()


if __name__ == "__main__":
    main()