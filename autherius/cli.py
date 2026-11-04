"""Autherius terminal menu and search integrations."""

import os
import platform
import re
import subprocess
import sys
from pathlib import Path

from maigret.maigret import run as run_maigret
from . import __version__


VERSION = __version__
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPIDERFOOT_ROOT = PROJECT_ROOT / "integrations" / "spiderfoot"
BANNER = r"""  /$$$$$$  /$$   /$$ /$$$$$$$$ /$$   /$$ /$$$$$$$$ /$$$$$$$  /$$$$$$ /$$   /$$  /$$$$$$
 /$$__  $$| $$  | $$|__  $$__/| $$  | $$| $$_____/| $$__  $$|_  $$_/| $$  | $$ /$$__  $$
| $$  \ $$| $$  | $$   | $$   | $$  | $$| $$      | $$  \ $$  | $$  | $$  | $$| $$  \__/
| $$$$$$$$| $$  | $$   | $$   | $$$$$$$$| $$$$$   | $$$$$$$/  | $$  | $$  | $$|  $$$$$$
| $$__  $$| $$  | $$   | $$   | $$__  $$| $$__/   | $$__  $$  | $$  | $$  | $$ \____  $$
| $$  | $$| $$  | $$   | $$   | $$  | $$| $$      | $$  \ $$  | $$  | $$  | $$ /$$  \ $$
| $$  | $$|  $$$$$$/   | $$   | $$  | $$| $$$$$$$$| $$  | $$ /$$$$$$|  $$$$$$/|  $$$$$$/
|__/  |__/ \______/    |__/   |__/  |__/|________/|__/  |__/|______/ \______/  \______/"""


def _color(text: str, code: str) -> str:
    """Apply terminal color when output is interactive."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _clear_screen() -> None:
    """Clear the visible terminal before showing the application screen."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def _computer_info() -> str:
    """Return basic, non-identifying details about the current computer."""
    system = platform.system() or "Unknown OS"
    if system == "Darwin":
        system = "macOS"
        release = platform.mac_ver()[0] or platform.release()
    else:
        release = platform.release()
    architecture = platform.machine() or "Unknown"
    cpu_count = os.cpu_count() or "Unknown"
    return (
        f"[+] SYSTEM: {system} {release} | {architecture} | "
        f"{cpu_count} CPU CORES | PYTHON {platform.python_version()}"
    )


def _banner() -> str:
    """Return the ASCII logo left-aligned in the terminal."""
    return BANNER


def show_header() -> None:
    """Display the left-aligned logo and project information once at startup."""
    print(_color(_banner(), "1;32"))
    print()
    print(_color("AUTHERIUS  |  A COMPLETE OSINT TOOL", "1;97"))
    print()
    print(_color(f"[+] VERSION: v{VERSION}", "1;32"))
    print(_color("Telegram:@kanozawa", "97"))
    print(_color("EMAIL:kanozawadm@gmail.com", "97"))
    print(_color("GIT-HUB:Oleh-Koliadiuk/Autherius", "97"))
    print(_color(_computer_info(), "97"))


def show_menu() -> None:
    """Display the available search options."""
    print()
    print(_color("[INSERT AN OPTION]", "1;32"))
    print(_color("(1) SEARCH-BY-USERNAME", "1;97"))
    print(_color("(2) SEARCH-BY-PHONE", "1;97"))
    print(_color("(3) SEARCH-BY-FULL-NAME", "1;97"))
    print(_color("(4) SEARCH-BY-EMAIL", "1;97"))
    print()
    print(_color("(Q) QUIT", "1;32"))


def _prompt_target(label: str) -> str:
    """Read a search target and return an empty string when cancelled."""
    return input(_color(f"\n[?] Enter {label}: ", "1;32")).strip()


def _search_username(username: str) -> None:
    """Run Maigret for an explicitly entered username."""
    if not username:
        print("Search cancelled.")
        return
    original_argv = sys.argv[:]
    try:
        sys.argv = [original_argv[0], username]
        run_maigret()
    finally:
        sys.argv = original_argv


def _spiderfoot_python() -> Path | None:
    """Find the isolated Python interpreter configured for SpiderFoot."""
    configured = os.environ.get("AUTHERIUS_SPIDERFOOT_PYTHON")
    if configured:
        candidate = Path(configured).expanduser()
        return candidate if candidate.is_file() else None

    candidates = [
        SPIDERFOOT_ROOT / ".venv" / "bin" / "python",
        SPIDERFOOT_ROOT / ".venv" / "Scripts" / "python.exe",
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _search_with_spiderfoot(target: str) -> None:
    """Run SpiderFoot's passive modules for an email, phone, or human name."""
    interpreter = _spiderfoot_python()
    script = SPIDERFOOT_ROOT / "sf.py"
    if not script.is_file() or interpreter is None:
        print(_color("SpiderFoot is not installed yet.", "1;32"))
        print("Run ./scripts/setup_spiderfoot.sh from the project directory first.")
        return

    print(_color("\n[+] Starting SpiderFoot passive search...", "1;32"))
    command = [
        str(interpreter),
        str(script),
        "-s",
        target,
        "-u",
        "passive",
        "-o",
        "json",
    ]
    data_root = Path.home() / ".autherius" / "spiderfoot"
    environment = os.environ.copy()
    environment.setdefault("SPIDERFOOT_DATA", str(data_root))
    environment.setdefault("SPIDERFOOT_CACHE", str(data_root / "cache"))
    environment.setdefault("SPIDERFOOT_LOGS", str(data_root / "logs"))
    try:
        completed = subprocess.run(
            command,
            cwd=SPIDERFOOT_ROOT,
            env=environment,
            check=False,
        )
    except OSError as error:
        print(_color(f"SpiderFoot could not start: {error}", "1;32"))
        return
    if completed.returncode:
        print(_color(f"SpiderFoot exited with status {completed.returncode}.", "1;32"))


def _search_phone() -> None:
    """Validate an international phone number and pass it to SpiderFoot."""
    raw_phone = _prompt_target("phone number with country code, e.g. +380501234567")
    if not raw_phone:
        print("Search cancelled.")
        return
    phone = re.sub(r"[\s().-]", "", raw_phone)
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        print("Use international format: + followed by 8 to 15 digits.")
        return
    _search_with_spiderfoot(phone)


def _search_full_name() -> None:
    """Require a first and last name before starting a SpiderFoot scan."""
    name = _prompt_target("full name")
    if not name:
        print("Search cancelled.")
        return
    if len(name.split()) < 2 or '"' in name:
        print("Enter at least a first and last name without quotation marks.")
        return
    _search_with_spiderfoot(name)


def _search_email() -> None:
    """Validate an email address and pass it to SpiderFoot."""
    email = _prompt_target("email address")
    if not email:
        print("Search cancelled.")
        return
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        print("Enter a valid email address.")
        return
    _search_with_spiderfoot(email)


def run() -> None:
    """Start the menu by default, or preserve explicit Maigret CLI arguments."""
    if len(sys.argv) > 1:
        _clear_screen()
        print(_color(_banner(), "1;32"))
        print()
        run_maigret()
        return

    actions = {
        "1": lambda: _search_username(_prompt_target("username")),
        "2": _search_phone,
        "3": _search_full_name,
        "4": _search_email,
    }
    try:
        _clear_screen()
        show_header()
        while True:
            show_menu()
            choice = input(_color("\n[AUTHERIUS] > ", "1;32")).strip()
            if choice.lower() == "q":
                print("Goodbye.")
                return
            action = actions.get(choice)
            if action is None:
                print("Select an option from 1 to 4, or Q to quit.")
                continue
            action()
    except (EOFError, KeyboardInterrupt):
        print("\nAutherius closed.")
