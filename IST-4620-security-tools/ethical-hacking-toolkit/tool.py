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

HEADER = """
<div style="text-align:center; padding: 18px 0 6px 0;">
  <h1 style="margin:0; font-size: 2.2em;">🛡️ Ethical Hacking Toolkit</h1>
  <p style="margin:4px 0 0 0; opacity:0.85; font-size:1.05em;">
    A multi-tool reconnaissance &amp; security analysis suite · IST-4620
  </p>
</div>
"""

DISCLAIMER = """
> ⚠️ **For authorized testing only.** Use this tool against systems you own or
> have **explicit written permission** to test. Unauthorized scanning is
> illegal under the Computer Fraud and Abuse Act and equivalent laws.
"""

CSS = """
.gradio-container { max-width: 1100px !important; }
#title-card { border-radius: 12px; }
button.primary { font-weight: 600 !important; }
footer { visibility: hidden; }
"""

with gr.Blocks(title="Ethical Hacking Toolkit", theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="slate"), css=CSS) as demo:
    gr.HTML(HEADER)
    gr.Markdown(DISCLAIMER)

    with gr.Tab("🔍 Port Scanner"):
        gr.Markdown("### Scan a target for open TCP ports\nChecks 16 common service ports (SSH, HTTP, SMB, RDP, etc.).")
        with gr.Row():
            ps_in = gr.Textbox(label="🎯 Target host or IP", placeholder="example.com or 192.168.1.1", scale=4)
            ps_btn = gr.Button("Scan", variant="primary", scale=1)
        ps_out = gr.Textbox(label="📋 Results", lines=12, show_copy_button=True)
        gr.Examples(["scanme.nmap.org", "example.com"], inputs=ps_in, label="Try one")
        ps_btn.click(port_scanner, ps_in, ps_out)

    with gr.Tab("🌐 HTTP Header Scanner"):
        gr.Markdown("### Audit a website's security headers\nFlags missing protections like CSP, HSTS, and X-Frame-Options.")
        with gr.Row():
            hs_in = gr.Textbox(label="🔗 URL", placeholder="https://example.com", scale=4)
            hs_btn = gr.Button("Scan", variant="primary", scale=1)
        hs_out = gr.Textbox(label="📋 Results", lines=12, show_copy_button=True)
        gr.Examples(["https://github.com", "https://example.com"], inputs=hs_in, label="Try one")
        hs_btn.click(header_scanner, hs_in, hs_out)

    with gr.Tab("🔐 Hash Identifier"):
        gr.Markdown("### Identify a hash by format and length\nDetects MD5, SHA-1, SHA-256, SHA-512, bcrypt, Argon2, and more.")
        with gr.Row():
            hi_in = gr.Textbox(label="#️⃣ Hash", placeholder="paste a hash here", scale=4)
            hi_btn = gr.Button("Identify", variant="primary", scale=1)
        hi_out = gr.Textbox(label="📋 Results", lines=4, show_copy_button=True)
        gr.Examples(
            [
                "5f4dcc3b5aa765d61d8327deb882cf99",
                "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",
                "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyHWUKW0G4GfDi",
            ],
            inputs=hi_in,
            label="Try one",
        )
        hi_btn.click(hash_identifier, hi_in, hi_out)

    with gr.Tab("🔑 Password Strength"):
        gr.Markdown("### Analyze password entropy\nCalculates entropy in bits and checks against a common-passwords list.")
        with gr.Row():
            pw_in = gr.Textbox(label="🔒 Password", type="password", scale=4)
            pw_btn = gr.Button("Analyze", variant="primary", scale=1)
        pw_out = gr.Textbox(label="📋 Results", lines=8, show_copy_button=True)
        pw_btn.click(password_strength, pw_in, pw_out)

    with gr.Tab("🌍 Subdomain Finder"):
        gr.Markdown("### Discover subdomains via DNS\nResolves common subdomain names against a target domain.")
        with gr.Row():
            sd_in = gr.Textbox(label="🌐 Domain", placeholder="example.com", scale=4)
            sd_btn = gr.Button("Find", variant="primary", scale=1)
        sd_out = gr.Textbox(label="📋 Results", lines=12, show_copy_button=True)
        gr.Examples(["github.com", "iana.org"], inputs=sd_in, label="Try one")
        sd_btn.click(subdomain_finder, sd_in, sd_out)

    gr.Markdown(
        "<div style='text-align:center; opacity:0.6; font-size:0.85em; padding-top:14px;'>"
        "Built with 🐍 Python &amp; ⚡ Gradio · CSUSB IST-4620 · 2026"
        "</div>"
    )


if __name__ == "__main__":
    demo.launch(share=True)
