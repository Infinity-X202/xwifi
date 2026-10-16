"""Terminal UI — Infinity X branding."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from xwifi import __version__

console = Console()

BANNER = r"""
 __  _____ _       _ _        __  __
 \ \/ /_ _| | __ _(_) |_ _   _\ \/ /
  \  / | || |/ _` | | __| | | |\  /
  /  \ | || | (_| | | |_| |_| |/  \
 /_/\_\___|_|\__, |_|\__|\__, /_/\_\
             |___/       |___/
"""

TAGLINE = "Created by Infinity X  •  Kali-ready  •  Menu 1·2·3 · 0 indietro"


def show_banner() -> None:
    console.print(
        Panel(
            f"[bold cyan]{BANNER.strip()}[/]\n\n[dim italic magenta]{TAGLINE}[/]",
            border_style="bright_blue",
            title="[bold white]xwifi[/]",
            subtitle=f"[dim]v{__version__}[/]",
        )
    )


def show_main_menu() -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold yellow", justify="right")
    table.add_column(style="white")
    table.add_row("1", "X Spoofing — blocca la rete (tranne te)")
    table.add_row("2", "Scansione rete / elenco host")
    table.add_row("3", "Info interfaccia")
    table.add_row("0", "Esci")
    console.print(
        Panel(table, title="[bold]Menu principale[/]", border_style="cyan")
    )


def show_back_hint() -> None:
    console.print("[dim]Premi [bold]0[/] o digita [bold]indietro[/] per tornare[/dim]\n")


def status_line(message: str) -> None:
    if message.startswith("[-]"):
        console.print(message, style="bold red")
    elif message.startswith("[+]"):
        console.print(message, style="bold green")
    elif message.startswith("[*]"):
        console.print(message, style="cyan")
    else:
        console.print(message)
