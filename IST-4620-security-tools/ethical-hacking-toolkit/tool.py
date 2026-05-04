"""
Ethical Hacking Toolkit
IST-4620 Semester Project

A multi-tool Gradio web app for authorized security testing.
Use only against systems you own or have explicit permission to test.
"""

import socket
import hashlib
import re
import math
import concurrent.futures
from urllib.parse import urlparse

import requests
import gradio as gr


# ---------- 1. Port Scanner ----------

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt",
}


def scan_port(host, port, timeout=1.0):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                return port
    except Exception:
        pass
    return None


def port_scanner(target):
    if not target.strip():
        return "Please enter a target host or IP."
    try:
        host = socket.gethostbyname(target.strip())
    except socket.gaierror:
        return f"Could not resolve host: {target}"

    open_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
        futures = {ex.submit(scan_port, host, p): p for p in COMMON_PORTS}
        for f in concurrent.futures.as_completed(futures):
            result = f.result()
            if result is not None:
                open_ports.append(result)

    open_ports.sort()
    if not open_ports:
        return f"Target: {target} ({host})\nNo common ports open."

    lines = [f"Target: {target} ({host})", f"Open ports: {len(open_ports)}", ""]
    for p in open_ports:
        lines.append(f"  {p:>5}/tcp  {COMMON_PORTS[p]}")
    return "\n".join(lines)


# ---------- 2. HTTP Header Security Scanner ----------

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Forces HTTPS",
    "Content-Security-Policy": "Restricts resource sources (XSS defense)",
    "X-Frame-Options": "Prevents clickjacking",
    "X-Content-Type-Options": "Blocks MIME sniffing",
    "Referrer-Policy": "Controls referrer leakage",
    "Permissions-Policy": "Controls browser features",
}


def header_scanner(url):
    if not url.strip():
        return "Please enter a URL."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        r = requests.get(url, timeout=8, allow_redirects=True)
    except requests.RequestException as e:
        return f"Request failed: {e}"

    lines = [f"URL: {r.url}", f"Status: {r.status_code}", "", "Security headers:"]
    for header, desc in SECURITY_HEADERS.items():
        if header in r.headers:
            lines.append(f"  [PRESENT] {header}: {r.headers[header][:80]}")
        else:
            lines.append(f"  [MISSING] {header}  ({desc})")

    server = r.headers.get("Server")
    if server:
        lines.append("")
        lines.append(f"Server banner: {server}")
    return "\n".join(lines)


# ---------- 3. Hash Identifier ----------

HASH_PATTERNS = [
    (32, r"^[a-f0-9]{32}$", "MD5"),
    (40, r"^[a-f0-9]{40}$", "SHA-1"),
    (64, r"^[a-f0-9]{64}$", "SHA-256"),
    (96, r"^[a-f0-9]{96}$", "SHA-384"),
    (128, r"^[a-f0-9]{128}$", "SHA-512"),
]


def hash_identifier(h):
    h = h.strip().lower()
    if not h:
        return "Please enter a hash."
    for length, pattern, name in HASH_PATTERNS:
        if len(h) == length and re.match(pattern, h):
            return f"Length: {length}\nLikely type: {name}"
    if h.startswith("$2"):
        return "Likely type: bcrypt"
    if h.startswith("$argon2"):
        return "Likely type: Argon2"
    if h.startswith("$6$"):
        return "Likely type: SHA-512 crypt (Linux /etc/shadow)"
    return f"Length: {len(h)}\nNo confident match. Could be a custom or unsupported hash."


# ---------- 4. Password Strength Analyzer ----------

COMMON_PASSWORDS = {
    "password", "123456", "qwerty", "letmein", "admin", "welcome",
    "monkey", "dragon", "master", "iloveyou", "password1", "abc123",
}


def password_strength(pw):
    if not pw:
        return "Please enter a password."

    length = len(pw)
    pool = 0
    if re.search(r"[a-z]", pw): pool += 26
    if re.search(r"[A-Z]", pw): pool += 26
    if re.search(r"[0-9]", pw): pool += 10
    if re.search(r"[^a-zA-Z0-9]", pw): pool += 32

    entropy = length * math.log2(pool) if pool else 0

    if entropy < 28: rating = "Very Weak"
    elif entropy < 36: rating = "Weak"
    elif entropy < 60: rating = "Reasonable"
    elif entropy < 128: rating = "Strong"
    else: rating = "Very Strong"

    notes = []
    if pw.lower() in COMMON_PASSWORDS:
        notes.append("- Found in common-passwords list")
    if length < 12:
        notes.append("- Shorter than 12 characters")
    if pw.isalpha():
        notes.append("- Letters only")
    if pw.isdigit():
        notes.append("- Digits only")

    out = [
        f"Length: {length}",
        f"Character pool: {pool}",
        f"Entropy: {entropy:.1f} bits",
        f"Rating: {rating}",
    ]
    if notes:
        out.append("\nIssues:")
        out.extend(notes)
    return "\n".join(out)


# ---------- 5. Subdomain Finder ----------

DEFAULT_SUBS = [
    "www", "mail", "ftp", "admin", "api", "dev", "staging", "test",
    "blog", "shop", "portal", "vpn", "remote", "secure", "app",
    "m", "mobile", "static", "cdn", "assets", "img", "media",
    "support", "help", "docs", "wiki", "git", "jenkins", "ci",
]


def check_sub(domain, sub):
    full = f"{sub}.{domain}"
    try:
        ip = socket.gethostbyname(full)
        return f"{full} -> {ip}"
    except socket.gaierror:
        return None


def subdomain_finder(domain):
    domain = domain.strip().lower()
    if not domain:
        return "Please enter a domain."
    domain = domain.replace("https://", "").replace("http://", "").strip("/")

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(check_sub, domain, s) for s in DEFAULT_SUBS]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                found.append(r)

    if not found:
        return f"No subdomains found for {domain} from default wordlist."
    return f"Found {len(found)} subdomain(s) for {domain}:\n\n" + "\n".join(sorted(found))


# ---------- Gradio UI ----------

DISCLAIMER = (
    "## Ethical Hacking Toolkit\n"
    "**For authorized testing only.** Use against systems you own or have "
    "written permission to test. Unauthorized scanning is illegal."
)

with gr.Blocks(title="Ethical Hacking Toolkit") as demo:
    gr.Markdown(DISCLAIMER)

    with gr.Tab("Port Scanner"):
        ps_in = gr.Textbox(label="Target host or IP", placeholder="example.com or 192.168.1.1")
        ps_out = gr.Textbox(label="Results", lines=12)
        gr.Button("Scan").click(port_scanner, ps_in, ps_out)

    with gr.Tab("HTTP Header Scanner"):
        hs_in = gr.Textbox(label="URL", placeholder="https://example.com")
        hs_out = gr.Textbox(label="Results", lines=12)
        gr.Button("Scan").click(header_scanner, hs_in, hs_out)

    with gr.Tab("Hash Identifier"):
        hi_in = gr.Textbox(label="Hash", placeholder="paste a hash")
        hi_out = gr.Textbox(label="Results", lines=4)
        gr.Button("Identify").click(hash_identifier, hi_in, hi_out)

    with gr.Tab("Password Strength"):
        pw_in = gr.Textbox(label="Password", type="password")
        pw_out = gr.Textbox(label="Results", lines=8)
        gr.Button("Analyze").click(password_strength, pw_in, pw_out)

    with gr.Tab("Subdomain Finder"):
        sd_in = gr.Textbox(label="Domain", placeholder="example.com")
        sd_out = gr.Textbox(label="Results", lines=12)
        gr.Button("Find").click(subdomain_finder, sd_in, sd_out)


if __name__ == "__main__":
    demo.launch(share=True)
