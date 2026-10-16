# xwifi — Infinity X

Tool **interattivo** per **Kali Linux**: menu con opzioni **1**, **2**, **3**, **0 (indietro/esci)**, branding **Created by Infinity X**, modulo **X Spoofing** (ARP poison + iptables — stessa logica del progetto `net_kill` / WiFi controller).

> **Solo reti di tua proprietà o con autorizzazione scritta.** Uso non autorizzato è illegale.

## Requisiti

- Kali / Debian Linux
- `root` per X Spoofing (`sudo xwifi`)
- Pacchetti: `python3-scapy`, `iptables`, `nmap`, `iproute2`, `rich`

## Installazione rapida (Kali)

```bash
git clone https://github.com/Infinity-X202/xwifi.git
cd xwifi
chmod +x install-kali.sh
sudo ./install-kali.sh
sudo xwifi
```

Lo script:

1. Installa dipendenze di sistema (`python3-scapy`, `nmap`, …)
2. Installa `rich` (apt o pip, **senza** aggiornare pip/wheel Debian)
3. Installa `xwifi` da sorgente con `pip install .`

### Se l’install si ferma su `Cannot uninstall wheel`

Su Kali è un bug noto: non aggiornare pip/wheel a mano. Aggiorna lo script e reinstalla:

```bash
cd ~/xwifi && git pull
sudo ./install-kali.sh
```

Oppure fix manuale:

```bash
cd ~/xwifi
sudo pip3 install rich --break-system-packages --ignore-installed
sudo pip3 install . --break-system-packages --force-reinstall
sudo xwifi
```

## Installazione manuale

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-scapy iptables nmap iproute2
pip3 install rich --break-system-packages
pip3 install . --break-system-packages
sudo xwifi
```

Su Kali/Debian recenti usa `--break-system-packages` se vedi `externally-managed-environment`.

## Avvio senza entry point

```bash
cd xwifi
sudo python3 -m xwifi
```

## Menu

| Opzione | Funzione |
|--------|----------|
| **1** | **X Spoofing** — avvelena ARP e blocca il forwarding per tutti tranne il tuo MAC |
| **2** | Scansione rete / elenco host (nmap + tabella ARP) |
| **3** | Info interfaccia (IP, MAC, gateway suggerito) |
| **0** | Esci |

In ogni sotto-menu: **0**, **indietro**, **back** o **b** per tornare.

Durante X Spoofing: **Ctrl+C** ripristina ARP e `iptables`.

## X Spoofing (cosa fa)

1. Scansiona la subnet con `nmap -sn`
2. Legge vicini da `/proc/net/arp`
3. ARP spoof bidirezionale (target ↔ gateway)
4. Abilita IP forward e regole `iptables` FORWARD: accetta solo il tuo MAC, DROP il resto

Equivalente CLI al vecchio script:

```bash
# Prima (script singolo):
# sudo python3 net_kill.py -i wlan0 -g 192.168.1.1

# Ora:
sudo xwifi
# → opzione 1, scegli wlan0, conferma gateway
```

## Struttura

```
xwifi/
├── install-kali.sh      # install one-shot su Kali
├── pyproject.toml
├── src/xwifi/
│   ├── cli.py           # menu interattivo
│   ├── core.py          # ARP / iptables
│   └── ui.py            # banner Infinity X
└── README.md
```

## Created by Infinity X

MIT License — usa in modo responsabile.
