# Ethical Hacking Toolkit

IST-4620 semester project. A multi-tool Gradio web app for authorized security testing.

## Tools included

1. **Port Scanner** — checks common TCP ports against a target host
2. **HTTP Header Scanner** — checks a URL for missing security headers
3. **Hash Identifier** — identifies hash type from format/length
4. **Password Strength Analyzer** — entropy + common-password check
5. **Subdomain Finder** — DNS-based subdomain enumeration

## Setup

```bash
pip install -r requirements.txt
python tool.py
```

The script prints a local URL and a public `*.gradio.live` share link.

## Legal

For use against systems you own or have explicit written authorization to test. Unauthorized scanning is illegal under the Computer Fraud and Abuse Act and equivalent laws.
