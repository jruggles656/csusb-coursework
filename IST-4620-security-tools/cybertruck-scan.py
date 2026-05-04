#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║   CYBERTRUCK STEALTH SCANNER                                     ║
║   Low-noise network reconnaissance tool                          ║
║   IST-4620 — AI-Assisted Stealthful Network Scan                 ║
║                                                                   ║
║   AI Tool: Claude Opus 4 (Anthropic, via Cowork)                 ║
║   Why: Integrated into lab workflow, explains flag reasoning      ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import os
import shutil
from datetime import datetime

# ── Colors ──────────────────────────────────────────────────────────
class C:
    RST  = "\033[0m"
    BOLD = "\033[1m"
    DIM  = "\033[2m"
    ITAL = "\033[3m"
    UND  = "\033[4m"
    # Cybertruck palette
    STEEL  = "\033[38;5;247m"
    BLUE   = "\033[38;5;39m"
    WHITE  = "\033[97m"
    GREEN  = "\033[38;5;46m"
    RED    = "\033[38;5;196m"
    YELLOW = "\033[38;5;220m"
    CYAN   = "\033[38;5;51m"
    GRAY   = "\033[38;5;240m"

# ── ASCII Art ───────────────────────────────────────────────────────

TRUCK = f"""
{C.STEEL}                          _______________
                   ______/               \\___
              ___/    {C.BLUE}⚡ CYBERTRUCK SCAN ⚡{C.STEEL}    \\___
         ___/              {C.DIM}stealth mode{C.RST}{C.STEEL}          \\
    ____/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\\____
   |______________|                          |______________|
      (●)    (●)                                (●)    (●){C.RST}
"""

TRUCK_SMALL = f"""{C.STEEL}    __________/{C.BLUE}CT{C.STEEL}\\____________
   |________|    |________|
     (●)(●)        (●)(●){C.RST}"""

DIVIDER     = f"  {C.STEEL}{'━' * 54}{C.RST}"
DIVIDER_DIM = f"  {C.GRAY}{'─' * 54}{C.RST}"

# ── Stealth Profiles ───────────────────────────────────────────────

PROFILES = {
    "1": {
        "key": "whisper",
        "label": "WHISPER",
        "icon": "🤫",
        "desc": "Slowest, quietest — flies under most IDS rules",
        "detail": "SYN scan, T1 timing, fragmented, padded, 50 ports",
        "flags": [
            "-sS", "-T1", "-Pn",
            "--top-ports", "50",
            "-f",
            "--data-length", "24",
            "--max-retries", "1",
            "--scan-delay", "500ms",
        ],
    },
    "2": {
        "key": "cruise",
        "label": "CRUISE",
        "icon": "🚗",
        "desc": "Balanced — good coverage without tripping alarms",
        "detail": "SYN scan, T2 timing, fragmented, padded, 100 ports",
        "flags": [
            "-sS", "-T2", "-Pn",
            "--top-ports", "100",
            "-f",
            "--data-length", "24",
            "--max-retries", "2",
        ],
    },
    "3": {
        "key": "ludicrous",
        "label": "LUDICROUS",
        "icon": "⚡",
        "desc": "Faster recon — still SYN-only but wider and quicker",
        "detail": "SYN scan, T3 timing, 500 ports, open-only",
        "flags": [
            "-sS", "-T3", "-Pn",
            "--top-ports", "500",
            "--max-retries", "2",
            "--open",
        ],
    },
}

FLAG_EXPLANATIONS = {
    "-sS":              "SYN scan — half-open, never completes handshake (quieter in logs)",
    "-T1":              "Sneaky timing — very slow probe rate to dodge rate-based IDS",
    "-T2":              "Polite timing — slow enough to stay under the radar",
    "-T3":              "Normal timing — faster recon, still SYN-only",
    "-Pn":              "No ping — skips ICMP echo so host discovery is silent",
    "-f":               "Fragment packets — makes it harder for IDS to reassemble & match",
    "--data-length":    "Pad packets with random data — disguises nmap fingerprint",
    "--max-retries":    "Limit retransmissions — less repeat traffic on the wire",
    "--scan-delay":     "Wait between probes — keeps packet rate below IDS thresholds",
    "--top-ports":      "Scan only the N most common ports — smaller footprint",
    "--open":           "Only show open ports — cleaner output",
}

# ── Known Lab Targets ──────────────────────────────────────────────

LAB_TARGETS = {
    "1": ("metasploitable2",  "10.100.0.105"),
    "2": ("metasploitable3",  "10.100.0.106"),
    "3": ("makulu-lab",       "10.100.0.104"),
    "4": ("win11-target",     "10.100.0.107"),
    "5": ("snort-ids",        "10.100.0.108"),
    "6": ("docker-lab",       "10.100.0.110"),
}

# ── Utility ─────────────────────────────────────────────────────────

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def prompt(text=""):
    try:
        return input(f"  {C.BLUE}▸{C.RST} {text}").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {C.STEEL}Exiting Cybertruck Scanner.{C.RST}\n")
        sys.exit(0)

def pause():
    prompt(f"{C.DIM}Press Enter to continue...{C.RST}")

def check_nmap():
    if not shutil.which("nmap"):
        print(f"  {C.RED}[✘]{C.RST} nmap not found. Install it first.")
        sys.exit(1)

def check_root():
    if os.geteuid() != 0:
        print(f"  {C.YELLOW}[!]{C.RST} SYN scans need root. Re-run with {C.BOLD}sudo{C.RST}.")
        sys.exit(1)

# ── Menu Screens ────────────────────────────────────────────────────

def main_menu():
    """Main menu loop."""
    while True:
        clear()
        print(TRUCK)
        print(f"  {C.BLUE}{C.BOLD}CYBERTRUCK STEALTH SCANNER{C.RST}")
        print(f"  {C.DIM}AI-assisted low-noise reconnaissance{C.RST}")
        print(f"  {C.GRAY}{datetime.now().strftime('%Y-%m-%d  %H:%M')}{C.RST}")
        print()
        print(DIVIDER)
        print()
        print(f"  {C.WHITE}{C.BOLD}  MAIN MENU{C.RST}")
        print()
        print(f"  {C.BLUE}  [1]{C.RST}  Launch Stealth Scan")
        print(f"  {C.BLUE}  [2]{C.RST}  Quick Scan — Lab Target")
        print(f"  {C.BLUE}  [3]{C.RST}  View Stealth Profiles")
        print(f"  {C.BLUE}  [4]{C.RST}  Flag Explainer")
        print(f"  {C.BLUE}  [5]{C.RST}  Scan History")
        print(f"  {C.BLUE}  [0]{C.RST}  Exit")
        print()
        print(DIVIDER)
        print()

        choice = prompt("Select: ")

        if choice == "1":
            launch_scan()
        elif choice == "2":
            quick_scan()
        elif choice == "3":
            view_profiles()
        elif choice == "4":
            flag_explainer()
        elif choice == "5":
            scan_history()
        elif choice == "0":
            clear()
            print(f"\n  {C.STEEL}Cybertruck out. Stay stealthy.{C.RST}\n")
            sys.exit(0)

def pick_profile():
    """Profile selection submenu. Returns profile dict or None."""
    print()
    print(f"  {C.WHITE}{C.BOLD}  SELECT PROFILE{C.RST}")
    print()
    for num, p in PROFILES.items():
        print(f"  {C.BLUE}  [{num}]{C.RST}  {p['icon']}  {C.BOLD}{p['label']:<12}{C.RST} {C.DIM}{p['desc']}{C.RST}")
    print()

    choice = prompt("Profile [1-3]: ")
    return PROFILES.get(choice)

def pick_target():
    """Target selection — lab list or custom IP. Returns IP string or None."""
    print()
    print(f"  {C.WHITE}{C.BOLD}  SELECT TARGET{C.RST}")
    print()
    for num, (name, ip) in LAB_TARGETS.items():
        print(f"  {C.BLUE}  [{num}]{C.RST}  {name:<20} {C.DIM}{ip}{C.RST}")
    print(f"  {C.BLUE}  [c]{C.RST}  Custom IP")
    print()

    choice = prompt("Target: ")
    if choice.lower() == "c":
        ip = prompt("Enter IP/hostname: ")
        return ip if ip else None
    elif choice in LAB_TARGETS:
        return LAB_TARGETS[choice][1]
    return None

def run_scan(profile, target, save=False):
    """Execute the nmap scan and optionally save output."""
    clear()
    print()
    print(TRUCK_SMALL)
    print()
    print(f"  {C.GREEN}[▸]{C.RST} Profile:  {C.BOLD}{profile['icon']}  {profile['label']}{C.RST}")
    print(f"  {C.GREEN}[▸]{C.RST} Target:   {C.BOLD}{target}{C.RST}")
    print()

    cmd = ["nmap"] + profile["flags"]

    outfile = None
    if save:
        os.makedirs("scans", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile = f"scans/{profile['key']}_{target.replace('.','_')}_{ts}.txt"
        cmd += ["-oN", outfile]

    cmd.append(target)

    print(f"  {C.DIM}$ {' '.join(cmd)}{C.RST}")
    print()
    print(DIVIDER)
    print()

    try:
        result = subprocess.run(cmd, text=True, capture_output=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"  {line}")
        if result.stderr:
            print(f"\n  {C.YELLOW}{result.stderr.strip()}{C.RST}")
    except KeyboardInterrupt:
        print(f"\n  {C.YELLOW}[!]{C.RST} Scan interrupted.")
        pause()
        return

    print()
    print(DIVIDER)
    print()
    print(f"  {C.GREEN}[✔]{C.RST} Scan complete.")
    if outfile:
        print(f"  {C.GREEN}[✔]{C.RST} Saved to {C.BOLD}{outfile}{C.RST}")
    print()
    pause()

def launch_scan():
    """Full scan flow: pick profile → pick target → options → go."""
    clear()
    print()
    print(TRUCK_SMALL)

    profile = pick_profile()
    if not profile:
        return

    target = pick_target()
    if not target:
        return

    print()
    save_choice = prompt(f"Save results to file? {C.DIM}[y/N]{C.RST}: ")
    save = save_choice.lower() in ("y", "yes")

    run_scan(profile, target, save=save)

def quick_scan():
    """One-tap scan: pick a lab target, runs cruise profile, saves output."""
    clear()
    print()
    print(TRUCK_SMALL)
    print()
    print(f"  {C.WHITE}{C.BOLD}  QUICK SCAN{C.RST}  {C.DIM}(cruise profile, auto-save){C.RST}")

    target = pick_target()
    if not target:
        return

    run_scan(PROFILES["2"], target, save=True)

def view_profiles():
    """Display all profiles with their flags."""
    clear()
    print()
    print(TRUCK_SMALL)
    print()
    print(f"  {C.WHITE}{C.BOLD}  STEALTH PROFILES{C.RST}")
    print()

    for _num, p in PROFILES.items():
        print(f"  {p['icon']}  {C.BLUE}{C.BOLD}{p['label']}{C.RST}")
        print(f"     {p['desc']}")
        print(f"     {C.DIM}{p['detail']}{C.RST}")
        flags_str = " ".join(p["flags"])
        print(f"     {C.CYAN}nmap {flags_str} <target>{C.RST}")
        print()

    pause()

def flag_explainer():
    """Show what every flag does and why it matters for stealth."""
    clear()
    print()
    print(TRUCK_SMALL)
    print()
    print(f"  {C.WHITE}{C.BOLD}  FLAG EXPLAINER{C.RST}")
    print(f"  {C.DIM}  Why each flag was chosen (AI-assisted reasoning){C.RST}")
    print()
    print(DIVIDER_DIM)

    for flag, reason in FLAG_EXPLANATIONS.items():
        print(f"  {C.CYAN}{flag:<20}{C.RST} {reason}")

    print(DIVIDER_DIM)
    print()
    pause()

def scan_history():
    """List saved scan files."""
    clear()
    print()
    print(TRUCK_SMALL)
    print()
    print(f"  {C.WHITE}{C.BOLD}  SCAN HISTORY{C.RST}")
    print()

    if not os.path.isdir("scans"):
        print(f"  {C.DIM}No scans yet. Run a scan with save enabled.{C.RST}")
        print()
        pause()
        return

    files = sorted(os.listdir("scans"), reverse=True)
    if not files:
        print(f"  {C.DIM}No scans yet.{C.RST}")
        print()
        pause()
        return

    for i, f in enumerate(files[:15], 1):
        size = os.path.getsize(os.path.join("scans", f))
        print(f"  {C.BLUE}  [{i:>2}]{C.RST}  {f}  {C.DIM}({size} bytes){C.RST}")

    print()
    choice = prompt(f"View a scan {C.DIM}[number or Enter to go back]{C.RST}: ")
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        clear()
        filepath = os.path.join("scans", files[int(choice) - 1])
        print()
        print(f"  {C.WHITE}{C.BOLD}  {files[int(choice) - 1]}{C.RST}")
        print(DIVIDER_DIM)
        with open(filepath) as fh:
            for line in fh:
                print(f"  {line}", end="")
        print()
        print(DIVIDER_DIM)
        print()
        pause()

# ── Entrypoint ──────────────────────────────────────────────────────

def main():
    # If args are passed, run in CLI mode (backwards compatible)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        cli_mode()
        return

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        cli_mode()
        return

    # Interactive menu
    check_nmap()
    check_root()
    main_menu()

def cli_mode():
    """Original CLI argument mode for scripting / one-liners."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cybertruck Stealth Scanner — AI-assisted low-noise nmap wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="Target IP or hostname (e.g. 10.100.0.105)")
    parser.add_argument(
        "-p", "--profile",
        choices=["whisper", "cruise", "ludicrous"],
        default="cruise",
        help="Stealth profile (default: cruise)",
    )
    parser.add_argument("-o", "--output", help="Save results to file")
    parser.add_argument("--explain", action="store_true", help="Show flag reasoning")
    parser.add_argument("--dry-run", action="store_true", help="Print command only")

    args = parser.parse_args()

    # Map name to profile
    profile = next(p for p in PROFILES.values() if p["key"] == args.profile)

    print(TRUCK)
    print(f"  {C.BLUE}{C.BOLD}CYBERTRUCK STEALTH SCANNER{C.RST}")
    print(f"  {C.DIM}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RST}\n")

    check_nmap()
    check_root()

    print(f"  {C.GREEN}[▸]{C.RST} Profile:  {C.BOLD}{profile['icon']}  {profile['label']}{C.RST}")
    print(f"  {C.GREEN}[▸]{C.RST} Target:   {C.BOLD}{args.target}{C.RST}\n")

    if args.explain:
        print(f"  {C.WHITE}{C.BOLD}WHY THESE FLAGS{C.RST}")
        print(DIVIDER_DIM)
        for f in profile["flags"]:
            if f in FLAG_EXPLANATIONS:
                print(f"  {C.CYAN}{f:<18}{C.RST} {FLAG_EXPLANATIONS[f]}")
        print()

    cmd = ["nmap"] + profile["flags"]
    if args.output:
        cmd += ["-oN", args.output]
    cmd.append(args.target)

    print(f"  {C.DIM}$ {' '.join(cmd)}{C.RST}\n")

    if args.dry_run:
        print(f"  {C.YELLOW}[DRY RUN]{C.RST} Command printed but not executed.")
        return

    print(DIVIDER)
    try:
        result = subprocess.run(cmd, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print(f"{C.YELLOW}{result.stderr}{C.RST}")
    except KeyboardInterrupt:
        print(f"\n  {C.YELLOW}[!]{C.RST} Scan interrupted.")
        sys.exit(130)

    print(DIVIDER)
    print(f"  {C.GREEN}[✔]{C.RST} Scan complete.")
    if args.output:
        print(f"  {C.GREEN}[✔]{C.RST} Results saved to {C.BOLD}{args.output}{C.RST}")
    print()

if __name__ == "__main__":
    main()
