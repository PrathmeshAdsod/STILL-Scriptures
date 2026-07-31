from __future__ import annotations

import getpass
import json
import secrets
import shutil
import string
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ID = "still-scriptures"
ACCOUNT_EMAIL = "judges@demo.com"
REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
WEB_ENV_PATH = REPO_ROOT / "apps" / "web" / ".env.production.local"
HANDOFF_PATH = REPO_ROOT / "tmp" / "private-access.txt"


def password() -> str:
    chooser = secrets.SystemRandom()
    required = [
        chooser.choice(string.ascii_lowercase),
        chooser.choice(string.ascii_uppercase),
        chooser.choice(string.digits),
        chooser.choice("!@#$%&*_-"),
    ]
    remainder = [chooser.choice(string.ascii_letters + string.digits + "!@#$%&*_-.") for _ in range(24)]
    value = required + remainder
    chooser.shuffle(value)
    return "".join(value)


def ensure_access_code() -> str:
    if not ENV_PATH.exists():
        raise RuntimeError("The ignored root .env file is required.")
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith("ACCESS_COUPON_CODE=") and line.partition("=")[2].strip():
            return line.partition("=")[2].strip().strip('"').strip("'")
    code = f"STILL-{secrets.token_urlsafe(24)}"
    lines.append(f"ACCESS_COUPON_CODE={code}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return code


def config_value(path: Path, name: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.partition("=")[2].strip().strip('"').strip("'")
    raise RuntimeError(f"{path} is missing {name}.")


def identity_request(path: str, payload: dict[str, object], token: str, api_key: str) -> dict[str, object]:
    request = urllib.request.Request(
        f"https://identitytoolkit.googleapis.com/v1/projects/{PROJECT_ID}/{path}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-Goog-User-Project": PROJECT_ID},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def create_or_rotate_account(account_password: str) -> str:
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if not gcloud:
        raise RuntimeError("gcloud is required to create the private Firebase account.")
    token = subprocess.run(
        [gcloud, "auth", "print-access-token", "--project", PROJECT_ID],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    api_key = config_value(WEB_ENV_PATH, "VITE_FIREBASE_API_KEY")
    lookup = identity_request("accounts:lookup", {"email": [ACCOUNT_EMAIL]}, token, api_key)
    users = lookup.get("users", [])
    if isinstance(users, list) and users:
        local_id = str(users[0]["localId"])
        identity_request(
            "accounts:update",
            {"localId": local_id, "password": account_password, "emailVerified": True, "disableUser": False},
            token,
            api_key,
        )
        return local_id
    created = identity_request(
        "accounts",
        {"email": ACCOUNT_EMAIL, "password": account_password, "emailVerified": True, "disabled": False},
        token,
        api_key,
    )
    return str(created["localId"])


def restrict_file(path: Path) -> None:
    username = getpass.getuser()
    subprocess.run(
        ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:(F)", "SYSTEM:(F)"],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    access_code = ensure_access_code()
    account_password = password()
    uid = create_or_rotate_account(account_password)
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF_PATH.write_text(
        "STILL private access handoff\n"
        f"Generated: {datetime.now(UTC).isoformat()}\n"
        f"Firebase project: {PROJECT_ID}\n"
        f"Email: {ACCOUNT_EMAIL}\n"
        f"Password: {account_password}\n"
        f"Access code: {access_code}\n"
        f"Firebase uid: {uid}\n"
        "\nKeep this file private. Rotate the account password and access code after the event.\n",
        encoding="utf-8",
    )
    restrict_file(HANDOFF_PATH)
    print(f"Private account prepared. Credentials are stored at {HANDOFF_PATH}")


if __name__ == "__main__":
    main()
