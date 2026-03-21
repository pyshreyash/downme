from datetime import timedelta
import os, dotenv

from interfaces.auth import JWTAuthManager
dotenv.load_dotenv()
secret_key: str = os.environ["SECRET_KEY"]
algorithm: str = os.environ["ALGORITHM"]
session_timeout: timedelta = timedelta(minutes=int(os.environ["SESSION_TIMEOUT"]))

jwt_handler = JWTAuthManager(secret_key, algorithm, session_timeout)