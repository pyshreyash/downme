import sys
from .auth import signup, login
# from catalog import list_catalog

def main():
    if len(sys.argv) < 2:
        print("Commands: signup, login, list")
        return

    cmd = sys.argv[1]

    if cmd == "signup":
        signup()
    elif cmd == "login":
        login()
    # elif cmd == "list":
    #     list_catalog()
    else:
        print("Unknown command:", cmd)