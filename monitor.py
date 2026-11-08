#!/usr/bin/env python3
"""Sonic the HackHog — live terminal monitor.

Polls the VPS redirect server API and displays visitor hits
in a green-on-black hacker terminal with Rich.

Usage:
    python monitor.py                          # uses .env or env vars
    python monitor.py --url https://r.ferreirakorp.com --key YOUR_API_KEY
"""
import argparse, json, os, sys, time
from datetime import datetime

try:
    import requests as http_client
except ImportError:
    print("[!] Install requests: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    print("[!] Install rich: pip install rich")
    sys.exit(1)

# Force green terminal on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.system("color 0A")
    sys.stdout.write("\033[0;32m\033[40m")
    sys.stdout.flush()

hacker_theme = Theme({
    "default": "green on black",
    "info": "bright_green on black",
    "warning": "bright_green on black",
    "error": "bright_green on black",
})
console = Console(legacy_windows=False, force_terminal=True,
                  force_jupyter=False, theme=hacker_theme, style="green on black")

BANNER = r"""
[bold green]══════════════════════════════════════════════════════════════════════[/bold green]
[bold bright_cyan]⚡ SONIC THE HACKHOG - LIVE TERMINAL MODE ⚡[/bold bright_cyan]
[bold bright_cyan]Thread Ripper | The Widowmaker | Fantasma de Luanda[/bold bright_cyan]
[bold green]══════════════════════════════════════════════════════════════════════[/bold green]
[green]Server:     [*] ENCRYPTED[/green]
[green]Database:   [*] ENCRYPTED[/green]
[green]Protocol:   [*] SECURED[/green]
[bold green]══════════════════════════════════════════════════════════════════════[/bold green]
[bright_cyan]███████╗ █████╗ ███╗   ██╗████████╗ █████╗ ███████╗███╗   ███╗ █████╗[/bright_cyan]
[bright_cyan]██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔════╝████╗ ████║██╔══██╗[/bright_cyan]
[bright_cyan]█████╗  ███████║██╔██╗ ██║   ██║   ███████║███████╗██╔████╔██║███████║[/bright_cyan]
[bright_cyan]██╔══╝  ██╔══██║██║╚██╗██║   ██║   ██╔══██║╚════██║██║╚██╔╝██║██╔══██║[/bright_cyan]
[bright_cyan]██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║███████║██║ ╚═╝ ██║██║  ██║[/bright_cyan]
[bright_cyan]╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝[/bright_cyan]
[bright_cyan]      FANTASMA DE LUANDA - GHOST PROTOCOL ACTIVE[/bright_cyan]
[bold green]══════════════════════════════════════════════════════════════════════[/bold green]
"""

recent = []
MAX_ROWS = 25


def build_table():
    table = Table(
        title="[bold bright_green on black]INCOMING REQUESTS[/bold bright_green on black]",
        title_style="bold bright_green on black",
        style="bright_green on black",
        border_style="bright_green",
        show_header=True,
        header_style="bold bright_green on black",
        row_styles=["bright_green on black"],
    )
    table.add_column("TIME", style="bright_green on black", width=10)
    table.add_column("METHOD", style="bright_green on black", width=8)
    table.add_column("IP", style="bright_green on black", width=40)
    table.add_column("PATH", style="bright_green on black", width=20, overflow="fold")
    table.add_column("USER-AGENT", style="bright_green on black", width=40, overflow="ellipsis")
    table.add_column("LANG", style="bright_green on black", width=12, overflow="ellipsis")

    for v in recent[:MAX_ROWS]:
        ts = v.get("ts", "")
        time_str = ts.split("T")[1][:8] if "T" in ts else ts[:8]
        method = v.get("method", "GET")
        method_styled = {
            "GET": "[cyan]GET[/cyan]",
            "POST": "[magenta]POST[/magenta]",
            "HEAD": "[yellow]HEAD[/yellow]",
        }.get(method, method)

        table.add_row(
            Text(time_str, style="bright_green"),
            Text(method_styled),
            Text(v.get("ip", "?"), style="green"),
            Text(v.get("path", "/"), style="bright_green"),
            Text((v.get("ua", "") or "")[:40], style="green"),
            Text((v.get("lang", "") or "")[:12], style="green"),
        )
    return table


def poll_loop(server_url, api_key, interval=3):
    last_id = 0
    session = http_client.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"

    console.print(BANNER)
    console.print(f"[bold green]Polling [*] ENCRYPTED every {interval}s ...[/bold green]\n")

    while True:
        try:
            r = session.get(f"{server_url}/api/visits",
                            params={"since": last_id, "limit": 50}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                new_visits = data.get("visits", [])
                if new_visits:
                    for v in new_visits:
                        recent.insert(0, v)
                        vid = v.get("id", 0)
                        if vid > last_id:
                            last_id = vid

                        console.print(f"\n[bold bright_green]{'=' * 70}", style="green on black")
                        log = {
                            "event": "REDIRECT_VISITOR",
                            "timestamp": v.get("ts"),
                            "ip": v.get("ip"),
                            "method": v.get("method", "GET"),
                            "path": v.get("path"),
                            "user_agent": (v.get("ua") or "")[:80],
                            "language": v.get("lang"),
                            "redirect_target": "[*] ENCRYPTED",
                            "database": "[*] ENCRYPTED",
                            "system": "Sonic the HackHog - Thread Ripper Protocol",
                        }
                        console.print(f"[bright_green]{json.dumps(log, indent=2)}",
                                      style="green on black")
                        console.print(f"[bold bright_green]{'=' * 70}\n", style="green on black")

                    while len(recent) > MAX_ROWS:
                        recent.pop()
                    console.print(build_table())
            elif r.status_code == 401:
                console.print("[bold red]API key rejected. Check API_KEY.[/bold red]")
                break
        except http_client.ConnectionError:
            console.print(f"[yellow][{datetime.now().strftime('%H:%M:%S')}] Connection lost — retrying...[/yellow]")
        except Exception as e:
            console.print(f"[yellow][{datetime.now().strftime('%H:%M:%S')}] Error: {e}[/yellow]")

        time.sleep(interval)


def load_dotenv(path=".env"):
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    parser = argparse.ArgumentParser(description="Sonic the HackHog — Live Monitor")
    parser.add_argument("--url", default=os.environ.get("SERVER_URL", "https://r.ferreirakorp.com"),
                        help="Server URL (default: $SERVER_URL or https://r.ferreirakorp.com)")
    parser.add_argument("--key", default=os.environ.get("API_KEY", ""),
                        help="API key (default: $API_KEY)")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("POLL_INTERVAL", "3")),
                        help="Poll interval in seconds (default: 3)")
    args = parser.parse_args()

    if not args.key:
        console.print("[bold red]No API_KEY set. Use --key or set API_KEY in .env[/bold red]")
        sys.exit(1)

    poll_loop(args.url, args.key, args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold bright_cyan]Ghost Protocol deactivated. Fantasma out.[/bold bright_cyan]")
