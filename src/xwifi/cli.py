"""Interactive CLI entry point."""

from __future__ import annotations

import sys

from xwifi.deps import ensure_dependencies

ensure_dependencies()

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from scapy.all import get_if_hwaddr

from xwifi.core import (
    get_my_ip,
    list_arp_hosts,
    list_ipv4_interfaces,
    require_root,
    run_x_spoofing,
)
from xwifi.ui import console, show_back_hint, show_banner, show_main_menu, status_line

BACK = {"0", "indietro", "back", "b"}


def _pick_interface() -> str | None:
    ifaces = list_ipv4_interfaces()
    if not ifaces:
        console.print("[red]Nessuna interfaccia IPv4 trovata.[/]")
        return None
    table = Table(title="Interfacce", border_style="blue")
    table.add_column("#", style="yellow", justify="right")
    table.add_column("Nome", style="cyan")
    for i, name in enumerate(ifaces, 1):
        table.add_row(str(i), name)
    table.add_row("0", "Indietro")
    console.print(table)
    choice = Prompt.ask("Scegli interfaccia", default="1")
    if choice.strip().lower() in BACK:
        return None
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(ifaces):
            console.print("[red]Scelta non valida.[/]")
            return None
        return ifaces[idx]
    except ValueError:
        console.print("[red]Inserisci un numero.[/]")
        return None


def _pick_gateway(default: str | None = None) -> str | None:
    gw = Prompt.ask(
        "IP gateway (router)",
        default=default or "192.168.1.1",
    )
    if gw.strip().lower() in BACK:
        return None
    return gw.strip()


def menu_x_spoofing() -> None:
    if not require_root():
        console.print(
            "[bold red]X Spoofing richiede root.[/] "
            "Chiudi e rilancia: [cyan]sudo xwifi[/]"
        )
        Prompt.ask("\nInvio per continuare", default="")
        return
    show_back_hint()
    iface = _pick_interface()
    if not iface:
        return
    try:
        my_ip = get_my_ip(iface)
        guess_gw = ".".join(my_ip.split(".")[:3]) + ".1"
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        return
    gw = _pick_gateway(guess_gw)
    if not gw:
        return
    console.print(
        "\n[bold yellow]⚠[/] Usa solo su reti autorizzate. "
        "Ctrl+C ferma e ripristina ARP/iptables.\n"
    )
    Prompt.ask("Premi Invio per avviare X Spoofing", default="")
    try:
        run_x_spoofing(iface, gw, on_status=status_line)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
    except Exception as e:
        console.print(f"[red]Errore: {e}[/]")


def menu_scan() -> None:
    show_back_hint()
    iface = _pick_interface()
    if not iface:
        return
    try:
        network, targets = list_arp_hosts(iface, on_status=status_line)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        return

    table = Table(title=f"Host su {network}", border_style="green")
    table.add_column("IP", style="cyan")
    table.add_column("MAC", style="magenta")
    if not targets:
        table.add_row("—", "Nessun host in ARP (prova ping / nmap)")
    else:
        for ip, mac in targets:
            table.add_row(ip, mac)
    console.print(table)
    Prompt.ask("\nInvio per continuare", default="")


def menu_info() -> None:
    show_back_hint()
    iface = _pick_interface()
    if not iface:
        return
    try:
        ip = get_my_ip(iface)
        mac = get_if_hwaddr(iface)
    except Exception as e:
        console.print(f"[red]{e}[/]")
        return
    table = Table(title="Interfaccia", border_style="blue")
    table.add_row("Nome", iface)
    table.add_row("IPv4", ip)
    table.add_row("MAC", mac)
    table.add_row("Gateway suggerito", ".".join(ip.split(".")[:3]) + ".1")
    console.print(table)
    Prompt.ask("\nInvio per continuare", default="")


def main() -> None:
    if sys.platform != "linux":
        console.print(
            "[yellow]xwifi è pensato per Kali/Linux. "
            "Alcune funzioni non funzioneranno su Windows.[/]"
        )
    show_banner()
    if sys.platform == "linux" and not require_root():
        console.print(
            "[yellow]Suggerimento:[/] per X Spoofing usa [bold]sudo xwifi[/]\n"
        )
    while True:
        show_main_menu()
        choice = Prompt.ask(
            "[bold cyan]Opzione[/]",
            choices=["0", "1", "2", "3"],
            default="1",
        )
        if choice == "0":
            console.print("[dim]Infinity X — esci in pace.[/]\n")
            break
        if choice == "1":
            menu_x_spoofing()
        elif choice == "2":
            menu_scan()
        elif choice == "3":
            menu_info()


if __name__ == "__main__":
    main()
