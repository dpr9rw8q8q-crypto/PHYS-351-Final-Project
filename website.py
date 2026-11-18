from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
import json
import shutil
import socket
import stat
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET

# Modifed with ChatGPT to add direct Pi SSH server running.
# Added support so tests can be done on a local computer when not on Pi.

HOST = "localhost"
PORT = 8000
ROOT = Path(__file__).resolve().parent
APP_ID = "tea-maker-kiosk"
OUTPUT = "SPI-1"
RESULTS = ROOT / "web-interface" / "results.txt"


def approve_results_access():
    """Remember this user's approval for the specific results file."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    approval = config_home / APP_ID / "results-access.txt"
    results_path = str(RESULTS.resolve())
    try:
        approved = approval.read_text(encoding="utf-8").strip() == results_path
    except (FileNotFoundError, UnicodeDecodeError):
        approved = False
    if not approved:
        try:
            answer = input(f"Allow saving orders to {RESULTS} on future runs? [y/N] ").strip().lower()
        except EOFError as error:
            raise RuntimeError("Run website.py in a terminal to approve saving orders.") from error
        if answer not in {"y", "yes"}:
            raise RuntimeError("Saving orders was declined.")
    # Check write access and create a missing file without changing existing orders.
    with RESULTS.open("ab"):
        pass
    if not approved:
        approval.parent.mkdir(parents=True, exist_ok=True)
        temporary = approval.with_suffix(".tmp")
        temporary.write_text(results_path + "\n", encoding="utf-8")
        temporary.replace(approval)


class OrderRequestHandler(SimpleHTTPRequestHandler):
    results_lock = threading.Lock()

    def do_POST(self):
        if self.path != "/api/orders":
            self.send_error(404)
            return
        expected_origin = f"http://{HOST}:{self.server.server_port}"
        if (self.headers.get("Origin") != expected_origin
                or self.headers.get("Host") != f"{HOST}:{self.server.server_port}"):
            self.send_error(403, "Orders must come from the local tea maker page.")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid order size.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Send orders as JSON.")
            order = json.loads(self.rfile.read(length))
            if not isinstance(order, dict) or set(order) != {"tea", "sugar_percent", "ice", "boba"}:
                raise ValueError("Invalid order fields.")
            if (order["tea"] not in ("classic_milk_tea", "matcha_milk_tea", "taro_milk_tea")
                    or type(order["sugar_percent"]) is not int
                    or order["sugar_percent"] not in (0, 50, 100)
                    or order["ice"] not in ("none", "light", "regular")
                    or type(order["boba"]) is not bool):
                raise ValueError("Invalid order selections.")
        except (ValueError, UnicodeDecodeError) as error:
            self.send_error(400, str(error))
            return
        try:
            # Serialize requests so simultaneous orders remain separate JSON lines.
            with self.results_lock, RESULTS.open("a+b") as results:
                results.seek(0, os.SEEK_END)
                needs_newline = False
                if results.tell():
                    results.seek(-1, os.SEEK_END)
                    needs_newline = results.read(1) != b"\n"
                line = ("\n" if needs_newline else "") + json.dumps(order) + "\n"
                results.write(line.encode("utf-8"))
                results.flush()
                os.fsync(results.fileno())
        except OSError as error:
            print(f"Could not save order to {RESULTS}: {error}", file=sys.stderr)
            self.send_error(500, "Could not write results.txt. Check the Pi terminal.")
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()


def desktop_environment():
    """Find this user's local Wayland desktop when started over Pi Connect."""
    env = os.environ.copy()
    runtime = Path(f"/run/user/{os.getuid()}")
    sockets = sorted(
        path for path in runtime.glob("wayland-*")
        if stat.S_ISSOCK(path.stat().st_mode)
    )
    if not sockets:
        raise RuntimeError("Log into the Pi desktop first, then run website.py as pi.")
    selected = None
    for path in sockets:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.connect(str(path))
            selected = path
            break
        except OSError:
            continue
    if selected is None:
        raise RuntimeError("Could not connect to the Pi's Wayland desktop.")
    env["XDG_RUNTIME_DIR"] = str(runtime)
    env["WAYLAND_DISPLAY"] = selected.name
    env["XDG_SESSION_TYPE"] = "wayland"
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={runtime}/bus"
    return env


def configure_touchscreen_window():
    """Add one labwc window rule, keeping touch calibration and other settings."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config = config_home / "labwc" / "rc.xml"
    config.parent.mkdir(parents=True, exist_ok=True)
    if config.exists():
        tree = ET.parse(config)
        backup = config.with_name("rc.xml.before-tea-maker")
        if not backup.exists():
            shutil.copy2(config, backup)
    else:
        tree = ET.ElementTree(ET.Element("labwc_config"))
    root = tree.getroot()
    if root.tag != "labwc_config":
        raise RuntimeError(f"Unexpected labwc configuration format in {config}")
    rules = root.find("windowRules")
    if rules is None:
        rules = ET.SubElement(root, "windowRules")
    for rule in list(rules):
        if rule.get("identifier") == APP_ID:
            rules.remove(rule)
    rule = ET.SubElement(rules, "windowRule", identifier=APP_ID)
    ET.SubElement(rule, "action", name="UnsetFullscreen")
    ET.SubElement(rule, "action", name="MoveToOutput", output=OUTPUT)
    ET.SubElement(rule, "action", name="SetFullscreen")
    temporary = config.with_name("rc.xml.tea-maker.tmp")
    tree.write(temporary, encoding="utf-8", xml_declaration=True)
    temporary.replace(config)
    subprocess.run(
        ["pkill", "-HUP", "-u", str(os.getuid()), "-x", "labwc"],
        check=True,
    )


def find_browser():
    """Prefer Chromium, then Google Chrome, including macOS app installations."""
    candidates = ["chromium", "chromium-browser"]
    if sys.platform == "darwin":
        candidates.extend([
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            str(Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium"),
        ])
    candidates.extend(["google-chrome", "google-chrome-stable", "chrome"])
    if sys.platform == "darwin":
        candidates.extend([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ])
    for candidate in candidates:
        browser = shutil.which(candidate)
        if browser:
            return browser
    raise RuntimeError("Install Chromium or Google Chrome to open the tea maker.")


def website_start():
    if not (ROOT / "web-interface" / "index.html").is_file():
        raise RuntimeError("Keep website.py next to the web-interface folder.")
    browser = find_browser()
    on_mac = sys.platform == "darwin"
    env = os.environ.copy() if on_mac else desktop_environment()
    handler = partial(OrderRequestHandler, directory=str(ROOT))
    with ThreadingHTTPServer((HOST, PORT), handler) as server:
        approve_results_access()
        if not on_mac:
            configure_touchscreen_window()
        profile = Path.home() / ".config" / APP_ID
        url = f"http://{HOST}:{PORT}/web-interface/index.html"
        command = [
            browser,
            f"--class={APP_ID}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--kiosk",
            url,
        ]
        if not on_mac:
            command.insert(1, "--ozone-platform=wayland")
        log_path = Path.home() / ".cache" / "tea-maker-browser.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log)
        screen = "the Mac display" if on_mac else OUTPUT
        print(f"Serving {url}\nOpening fullscreen on {screen}. Browser log: {log_path}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()






# Test

def main():
    try:
        website_start()
    except (OSError, RuntimeError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"Could not start tea maker: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
