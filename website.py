from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
import shutil
import socket
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET


HOST = "localhost"
PORT = 8000
ROOT = Path(__file__).resolve().parent
APP_ID = "tea-maker-kiosk"
OUTPUT = "SPI-1"


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


def website_start():
    if not (ROOT / "web-interface" / "index.html").is_file():
        raise RuntimeError("Keep website.py next to the web-interface folder.")
    browser = shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        raise RuntimeError("Install Chromium with: sudo apt install chromium")
    env = desktop_environment()
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    with ThreadingHTTPServer((HOST, PORT), handler) as server:
        configure_touchscreen_window()
        profile = Path.home() / ".config" / APP_ID
        url = f"http://{HOST}:{PORT}/web-interface/index.html"
        command = [
            browser,
            "--ozone-platform=wayland",
            f"--class={APP_ID}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            f"--app={url}",
        ]
        log_path = Path.home() / ".cache" / "tea-maker-browser.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log)
        print(f"Serving {url}\nOpening fullscreen on {OUTPUT}. Browser log: {log_path}")
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





def main():
    try:
        website_start()
    except (OSError, RuntimeError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"Could not start tea maker: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()