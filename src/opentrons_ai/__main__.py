"""Local bootstrap and server commands; no default password."""

import argparse
import getpass
import os
import secrets
from pathlib import Path

import uvicorn

from .app import PASSWORDS, ROOT
from .storage import Store, utc_now


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("create-admin")
    init.add_argument("--username", default="admin")
    init.add_argument("--generate", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8080, type=int)
    serve.add_argument("--cert")
    serve.add_argument("--key")
    args = parser.parse_args()
    if args.command == "create-admin":
        directory = Path(os.getenv("OT2_DATA_DIR", ROOT / ".local"))
        store = Store(directory)
        with store.connect() as db:
            if db.execute("SELECT 1 FROM users WHERE username=?", (args.username,)).fetchone():
                parser.error("Username already exists; it was not modified.")
        password = secrets.token_urlsafe(20) if args.generate else getpass.getpass("Password: ")
        if len(password) < 12:
            parser.error("Use at least 12 characters.")
        credential_file = directory / "bootstrap-admin.txt"
        if args.generate:
            descriptor = os.open(credential_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as output:
                output.write(f"Username: {args.username}\nPassword: {password}\n")
            credential_file.chmod(0o600)
        with store.connect() as db:
            db.execute(
                "INSERT INTO users VALUES (?, ?, 'admin', ?)",
                (
                    args.username,
                    PASSWORDS.hash(password),
                    utc_now(),
                ),
            )
        print(
            f"Admin created. Credentials: {credential_file}" if args.generate else "Admin created."
        )
    else:
        if args.host not in ("127.0.0.1", "localhost", "::1") and not (args.cert and args.key):
            parser.error("LAN binding requires --cert and --key (HTTPS).")
        os.environ["OT2_SECURE_COOKIE"] = "1" if args.cert else "0"
        uvicorn.run(
            "opentrons_ai.app:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            ssl_certfile=args.cert,
            ssl_keyfile=args.key,
            proxy_headers=False,
        )


if __name__ == "__main__":
    main()
