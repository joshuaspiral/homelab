#!/usr/bin/env python3
"""
chandra_ocr.py: Paperless-ngx post-consume script.
Uses Chandra via llama-server on hyperion.

Place in: hosts/lxc-productivity/productivity/scripts/chandra_ocr.py
Set in compose: PAPERLESS_POST_CONSUME_SCRIPT=/scripts/chandra_ocr.py

Paperless passes these positional args to post-consume scripts:
  $1 = document_id
  $2 = generated filename
  $3 = source path (original file)
  $4 = thumbnail path
  $5 = download URL
  $6 = thumbnail URL
  $7 = correspondent
  $8 = tags (comma-separated)
"""

import os
import sys
import base64
import glob
import socket
import subprocess
import tempfile
import time
import re

try:
    import requests
except ImportError:
    sys.exit("Missing requests module")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
document_id = sys.argv[1]
file_path = sys.argv[3]
tags = sys.argv[8] if len(sys.argv) > 8 else ""

HYPERION_IP = os.environ.get("HYPERION_IP", "10.0.0.20")
HYPERION_MAC = os.environ.get("HYPERION_MAC", "b4:2e:99:a0:7f:e9")
CHANDRA_PORT = os.environ.get("CHANDRA_PORT", "8080")
CHANDRA_API = f"http://{HYPERION_IP}:{CHANDRA_PORT}"
CHANDRA_DPI = int(os.environ.get("CHANDRA_DPI", "150"))

# Only OCR documents with this tag. Leave empty to OCR everything.
CHANDRA_TAG = os.environ.get("CHANDRA_TAG", "chandra-ocr")

API_URL = os.environ.get("PAPERLESS_API_URL", "http://localhost:8000/api/documents/")
API_TOKEN = os.environ.get("PAPERLESS_API_TOKEN", "")


# ---------------------------------------------------------------------------
# Tag filter — skip documents that don't need Chandra
# ---------------------------------------------------------------------------
if CHANDRA_TAG and CHANDRA_TAG not in tags:
    print(f"Document {document_id} not tagged '{CHANDRA_TAG}', skipping Chandra OCR")
    sys.exit(0)

print(f"Document {document_id}: tagged '{CHANDRA_TAG}', running Chandra OCR")


# ---------------------------------------------------------------------------
# Wake-on-LAN
# ---------------------------------------------------------------------------
def wake_hyperion():
    mac_bytes = bytes.fromhex(HYPERION_MAC.replace(":", ""))
    magic_packet = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic_packet, ("10.0.0.255", 9))
    print("WOL packet sent")


def wait_for_chandra(timeout=180):
    """Wait for llama-server to respond."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{CHANDRA_API}/health", timeout=3)
            if resp.status_code == 200:
                print("Chandra server ready")
                return True
        except requests.exceptions.RequestException:
            time.sleep(5)
    return False


wake_hyperion()
if not wait_for_chandra():
    print("Hyperion/Chandra did not come up in time", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTML to Markdown
# ---------------------------------------------------------------------------
def html_to_md(text):
    s = text
    for i in range(6, 0, -1):
        s = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf'{"#" * i} \1', s, flags=re.DOTALL)
    s = re.sub(r"<b>(.*?)</b>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s, flags=re.DOTALL)
    s = re.sub(r"<em>(.*?)</em>", r"*\1*", s, flags=re.DOTALL)
    s = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.DOTALL)
    s = re.sub(r"<li>(.*?)</li>", r"- \1", s, flags=re.DOTALL)
    s = re.sub(r'<math\s+display="block">(.*?)</math>', r"$$\1$$", s, flags=re.DOTALL)
    s = re.sub(r"<math>(.*?)</math>", r"$\1$", s, flags=re.DOTALL)
    s = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*/?\s*>', r"*[\1]*", s, flags=re.DOTALL)
    s = re.sub(r"<img[^>]*/?\s*>", "", s, flags=re.DOTALL)
    s = re.sub(r'<input\s+checked="[^"]*"\s+type="radio"\s*/?\s*>', "●", s)
    s = re.sub(r'<input\s+type="radio"\s*/?\s*>', "○", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
def ocr_image(img_b64):
    payload = {
        "model": "chandra",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Return the markdown representation of this document page. "
                            "Preserve all layout, tables, math, and formatting. "
                            "Output only the content, no commentary."
                        ),
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }
    resp = requests.post(
        f"{CHANDRA_API}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()
    return html_to_md(resp.json()["choices"][0]["message"]["content"])


# ---------------------------------------------------------------------------
# Process document
# ---------------------------------------------------------------------------
pages_text = []

with tempfile.TemporaryDirectory() as tmpdir:
    output_base = os.path.join(tmpdir, "page")

    # Convert PDF pages to PNG
    subprocess.run(
        ["pdftoppm", "-r", str(CHANDRA_DPI), "-png", file_path, output_base],
        check=True,
    )

    files = sorted(glob.glob(output_base + "*.png"))
    if not files:
        print("pdftoppm produced no output", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(files)} pages at {CHANDRA_DPI} DPI")

    for i, page_file in enumerate(files):
        with open(page_file, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode()

        print(f"  Page {i+1}/{len(files)}...", end=" ", flush=True)
        start = time.time()
        text = ocr_image(b64_image)
        elapsed = time.time() - start
        print(f"done ({elapsed:.1f}s)")

        pages_text.append(text)

transcribed_text = "\n\n---\n\n".join(pages_text)
print(f"OCR complete: {len(transcribed_text)} chars")

# Patch document content in Paperless
headers = {"Authorization": f"Token {API_TOKEN}"}
result = requests.patch(
    f"{API_URL}{document_id}/",
    headers=headers,
    json={"content": transcribed_text},
)
print(f"PATCH status: {result.status_code}")
