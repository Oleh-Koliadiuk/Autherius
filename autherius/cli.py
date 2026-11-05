"""Autherius terminal menu and search integrations."""

import json
import os
import platform
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from maigret.maigret import run as run_maigret
from . import __version__


VERSION = __version__
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPIDERFOOT_ROOT = PROJECT_ROOT / "integrations" / "spiderfoot"
PHONE_SEARCH_MODULES = ("sfp_phone", "sfp_countryname", "sfp_callername")
FULL_NAME_SEARCH_MODULES = ("sfp_accounts",)
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


def _prompt_target(label: str) -> str | None:
    """Read a target, or return None when the user requests the menu."""
    print(_color("(B) BACK TO MENU", "1;32"))
    value = input(_color(f"[?] Enter {label}: ", "1;32")).strip()
    if value.lower() in {"b", "back"}:
        return None
    return value


def _search_username(username: str | None) -> None:
    """Run Maigret for an explicitly entered username."""
    if username is None:
        return
    if not username:
        print("Search cancelled.")
        return
    original_argv = sys.argv[:]
    try:
        report_username = username.replace("/", "_")
        report_dir = (
            _spiderfoot_data_root().parent
            / "MaigretReports"
            / f"{report_username}_{time.time_ns()}"
        )
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"report_{report_username}_simple.json"
        sys.argv = [
            original_argv[0],
            username,
            "--json",
            "simple",
            "--folderoutput",
            str(report_dir),
        ]
        try:
            run_maigret()
        except SystemExit as error:
            if error.code not in (None, 0):
                print(_color(f"Maigret exited with status {error.code}.", "1;32"))
        if report_path.is_file():
            _display_maigret_results(username, report_path)
            print(_color(f"Full JSON report saved to: {report_path}", "97"))
        else:
            print(_color("Maigret did not produce a structured results report.", "1;32"))
    finally:
        sys.argv = original_argv


def _display_maigret_results(username: str, report_path: Path) -> None:
    """Display every claimed Maigret account with its URL and extracted data."""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(_color(f"Could not read the Maigret report: {error}", "1;32"))
        return

    if not isinstance(report, dict) or not report:
        print(_color(f"\n[+] SCAN RESULTS FOR {username}", "1;32"))
        print(_color("No matching accounts were found.", "1;97"))
        return

    print(_color(f"\n[+] SCAN RESULTS FOR {username}", "1;32"))
    print(_color(f"Matching accounts: {len(report)}", "1;97"))
    for index, (site_name, result) in enumerate(report.items(), start=1):
        if not isinstance(result, dict):
            continue
        status = result.get("status", {})
        status_data = status if isinstance(status, dict) else {}
        site_data = result.get("site", {})
        site_url = (
            result.get("url_main")
            or (site_data.get("urlMain") if isinstance(site_data, dict) else None)
            or "Not provided"
        )
        profile_url = result.get("url_user") or status_data.get("url") or site_url
        account_name = result.get("username") or status_data.get("username") or username
        profile_data = status_data.get("ids", {})

        print(_color(f"\n[{index}] {site_name}", "1;32"))
        print(_color("Type: Account / profile", "1;97"))
        print(_color(f"Data: username = {account_name}", "1;97"))
        if isinstance(profile_data, dict) and profile_data:
            for data_type, value in profile_data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                print(_color(f"Data: {data_type} = {value}", "1;97"))
        print(_color(f"URL: {profile_url}", "97"))
        print(_color(f"Source: {site_name} ({site_url})", "97"))


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


def _search_with_spiderfoot(target: str, modules: tuple[str, ...] | None = None) -> None:
    """Run SpiderFoot for a target, optionally limiting the scan to selected modules."""
    interpreter = _spiderfoot_python()
    script = SPIDERFOOT_ROOT / "sf.py"
    if not script.is_file() or interpreter is None:
        print(_color("SpiderFoot is not installed yet.", "1;32"))
        print("Run ./scripts/setup_spiderfoot.sh from the project directory first.")
        return

    if modules:
        if modules == PHONE_SEARCH_MODULES:
            print(_color("\n[+] Starting focused phone-number search...", "1;32"))
            progress_label = "Checking phone-number data"
        else:
            print(_color("\n[+] Starting full-name account search...", "1;32"))
            print("Account Finder derives username variants and checks public profile sites.")
            print("This can take several minutes; results will appear when checks finish.")
            progress_label = "Checking public account sites"
    else:
        print(_color("\n[+] Starting SpiderFoot passive search...", "1;32"))
        progress_label = "Checking passive data sources"
    command = [
        str(interpreter),
        str(script),
        "-s",
        target,
        "-max-threads",
        "1",
        "-o",
        "json",
    ]
    if modules:
        command.extend(["-m", ",".join(modules)])
    else:
        command.extend(["-u", "passive"])
    environment = os.environ.copy()
    try:
        data_root = _spiderfoot_data_root()
        data_root.mkdir(parents=True, exist_ok=True)
        cache_root = data_root / "cache"
        logs_root = data_root / "logs"
        cache_root.mkdir(parents=True, exist_ok=True)
        logs_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(_color(f"Cannot prepare SpiderFoot data directories: {error}", "1;32"))
        return

    # Keep SpiderFoot's database, cache, and logs in a known writable location.
    # Ignoring inherited SPIDERFOOT_* paths avoids stale or invalid shell settings.
    environment["SPIDERFOOT_DATA"] = str(data_root)
    environment["SPIDERFOOT_CACHE"] = str(cache_root)
    environment["SPIDERFOOT_LOGS"] = str(logs_root)
    try:
        process = _popen_with_file_limit(command, environment)
        progress_stop = threading.Event()
        progress_thread = threading.Thread(
            target=_show_search_progress,
            args=(progress_label, progress_stop),
            daemon=True,
        )
        progress_thread.start()
        try:
            stdout, stderr = process.communicate()
        except KeyboardInterrupt:
            print(_color("\n[+] Stopping the search and returning to the menu...", "1;32"))
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
            try:
                stdout, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                stdout, stderr = process.communicate()
            return
        finally:
            progress_stop.set()
            progress_thread.join()
            if sys.stdout.isatty():
                sys.stdout.write("\r\033[K")
                sys.stdout.flush()
    except OSError as error:
        print(_color(f"SpiderFoot could not start: {error}", "1;32"))
        return
    _display_spiderfoot_results(stdout, stderr, target, modules, process.returncode)


def _show_search_progress(label: str, stop_event: threading.Event) -> None:
    """Show a live elapsed-time indicator while SpiderFoot is running."""
    if not sys.stdout.isatty():
        return
    frames = "|/-\\"
    started = time.monotonic()
    tick = 0
    while not stop_event.wait(0.2):
        elapsed = int(time.monotonic() - started)
        frame = frames[tick % len(frames)]
        sys.stdout.write(f"\r{_color(f'[+] {label} {frame} {elapsed}s', '1;32')}")
        sys.stdout.flush()
        tick += 1


def _popen_with_file_limit(
    command: list[str], environment: dict[str, str]
) -> subprocess.Popen[str]:
    """Start SpiderFoot with a larger soft file limit when the OS allows it."""
    if os.name == "nt":
        return _popen_captured(command, environment)

    try:
        import resource
        old_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        soft_limit, hard_limit = old_limit
        target_limit = 8192 if hard_limit == resource.RLIM_INFINITY else min(8192, hard_limit)
        changed = soft_limit < target_limit
        if changed:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target_limit, hard_limit))
    except (ImportError, OSError, ValueError):
        return _popen_captured(command, environment)

    try:
        return _popen_captured(command, environment)
    finally:
        if changed:
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, old_limit)
            except (OSError, ValueError):
                pass


def _popen_captured(command: list[str], environment: dict[str, str]) -> subprocess.Popen[str]:
    """Start SpiderFoot with output captured for a clean result summary."""
    return subprocess.Popen(
        command,
        cwd=SPIDERFOOT_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _display_spiderfoot_results(
    stdout: str,
    stderr: str,
    target: str,
    modules: tuple[str, ...] | None,
    return_code: int | None,
) -> None:
    """Print discovered SpiderFoot events and concise diagnostics."""
    try:
        events = json.loads(stdout)
    except json.JSONDecodeError:
        events = []
        parse_failed = bool(stdout.strip())
    else:
        parse_failed = not isinstance(events, list)
        if parse_failed:
            events = []

    findings: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    if isinstance(events, list):
        for event in events:
            if not isinstance(event, dict):
                continue
            event_type = str(event.get("type", "Finding"))
            data = _clean_spiderfoot_text(event.get("data", ""))
            module = str(event.get("module", "Unknown module"))
            related_to = _clean_spiderfoot_text(event.get("source", ""))
            if not data or module in {"SpiderFoot UI", "sfp__stor_stdout"}:
                continue
            if data.casefold() == target.casefold():
                continue
            key = (event_type, data, module)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "type": event_type,
                    "data": data,
                    "module": module,
                    "related_to": related_to,
                    "urls": _extract_spiderfoot_urls(data),
                }
            )

    print(_color("\n[+] SCAN RESULTS", "1;32"))
    print(_color(f"Target: {target}", "1;97"))
    if modules:
        print(_color(f"Modules: {', '.join(modules)}", "97"))
    else:
        print(_color("Modules: SpiderFoot passive set", "97"))
    if return_code:
        print(_color(f"SpiderFoot exited with status {return_code}.", "1;32"))

    if findings:
        print(_color(f"Findings: {len(findings)}", "1;32"))
        for index, finding in enumerate(findings, start=1):
            print(_color(f"\n[{index}] {finding['type']}", "1;32"))
            print(_color(f"What: {finding['data']}", "1;97"))
            urls = finding["urls"]
            if urls:
                print(_color("Where:", "1;32"))
                for url in urls:
                    print(_color(f"  {url}", "97"))
            else:
                print(_color("Where: The source did not provide a URL.", "97"))
            print(_color(f"Found by: {finding['module']}", "97"))
            related_to = finding["related_to"]
            if related_to:
                print(_color(f"Related to: {related_to}", "97"))
    else:
        print(_color("No related results were found.", "1;97"))

    diagnostics = _spiderfoot_diagnostics(stderr)
    if parse_failed:
        diagnostics.insert(0, "Could not parse SpiderFoot's JSON output; findings may be incomplete.")
    if diagnostics:
        print(_color("\n[!] SCAN DIAGNOSTICS", "1;32"))
        for diagnostic in diagnostics:
            print(_color(f"- {diagnostic}", "97"))


def _clean_spiderfoot_text(value: object) -> str:
    """Remove SpiderFoot URL wrapper tags while retaining their URLs."""
    return re.sub(r"</?SFURL>", "", str(value)).strip()


def _extract_spiderfoot_urls(value: str) -> list[str]:
    """Extract unique HTTP(S) locations from a SpiderFoot event value."""
    urls = re.findall(r"https?://[^\s<>\"']+", value)
    return list(dict.fromkeys(url.rstrip(".,);]}") for url in urls))


def _spiderfoot_diagnostics(stderr: str) -> list[str]:
    """Condense verbose SpiderFoot logs into actionable messages."""
    diagnostics: list[str] = []
    for line in stderr.splitlines():
        if "Too many open files" in line:
            message = "File descriptor limit was reached; some modules may have skipped results."
        elif "unable to open database file" in line:
            message = "SpiderFoot could not open its database or cache file."
        elif "did not set an API key and/or base URL" in line:
            message = "An optional API module was skipped because its key or endpoint is missing."
        elif "did not set an API key" in line or "did not set an API Username/Key" in line:
            module = re.search(r"module (sfp_[\w]+)", line)
            message = f"Optional API module {module.group(1)} was skipped because its key is missing." if module else "An optional API module was skipped because its key is missing."
        else:
            continue
        if message not in diagnostics:
            diagnostics.append(message)
        if len(diagnostics) == 8:
            break
    return diagnostics


def _spiderfoot_data_root() -> Path:
    """Return the per-user directory used for SpiderFoot databases and logs."""
    configured = os.environ.get("AUTHERIUS_SPIDERFOOT_HOME")
    if configured:
        return Path(configured).expanduser()

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Autherius" / "SpiderFoot"
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Autherius" / "SpiderFoot"
    return Path.home() / ".local" / "share" / "autherius" / "spiderfoot"


def _search_phone() -> None:
    """Validate an international phone number and pass it to SpiderFoot."""
    raw_phone = _prompt_target("phone number with country code, e.g. +380501234567")
    if raw_phone is None:
        return
    if not raw_phone:
        print("Search cancelled.")
        return
    phone = re.sub(r"[\s().-]", "", raw_phone)
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        print("Use international format: + followed by 8 to 15 digits.")
        return
    _search_with_spiderfoot(phone, PHONE_SEARCH_MODULES)


def _search_full_name() -> None:
    """Require a first and last name before starting a SpiderFoot scan."""
    name = _prompt_target("full name")
    if name is None:
        return
    if not name:
        print("Search cancelled.")
        return
    if len(name.split()) < 2 or '"' in name:
        print("Enter at least a first and last name without quotation marks.")
        return
    _search_with_spiderfoot(name, FULL_NAME_SEARCH_MODULES)


def _search_email() -> None:
    """Validate an email address and pass it to SpiderFoot."""
    email = _prompt_target("email address")
    if email is None:
        return
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
            try:
                action()
            except KeyboardInterrupt:
                print(_color("\n[+] Search interrupted; returning to the menu.", "1;32"))
    except (EOFError, KeyboardInterrupt):
        print("\nAutherius closed.")
