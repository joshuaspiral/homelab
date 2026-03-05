#!/usr/bin/env python3
import os, sys, glob, requests, base64, socket, time, subprocess, tempfile

document_id = sys.argv[1]
file_path = sys.argv[3]
hyperion_ip = "10.0.0.20"
hyperion_mac = "b4:2e:99:a0:7f:e9"

# Wake-on-LAN
mac_bytes = bytes.fromhex(hyperion_mac.replace(":", ""))
magic_packet = b"\xff" * 6 + mac_bytes * 16
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(magic_packet, ("10.0.0.255", 9))

# Wait for Ollama (2 min timeout)
deadline = time.time() + 120
while time.time() < deadline:
    try:
        if requests.get(f"http://{hyperion_ip}:11434/", timeout=3).status_code == 200:
            break
    except requests.exceptions.RequestException:
        time.sleep(5)
else:
    print("Hyperion did not wake in time", file=sys.stderr)
    sys.exit(1)

# Convert ALL pages of PDF to PNG
pages_text = []
with tempfile.TemporaryDirectory() as tmpdir:
    output_base = os.path.join(tmpdir, "page")
    subprocess.run(
        ["pdftoppm", "-r", "300", "-png", file_path, output_base], check=True
    )
    files = sorted(glob.glob(output_base + "*.png"))
    if not files:
        print("pdftoppm produced no output", file=sys.stderr)
        sys.exit(1)
    for page_file in files:
        with open(page_file, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")
        ollama_payload = {
            "model": "qwen3-vl:8b",
            "prompt": "/no_think Transcribe every word and number in this image exactly as written, character by character. Preserve all punctuation and line breaks.",
            "images": [b64_image],
            "stream": False,
            "options": {"temperature": 0, "repeat_penalty": 1.3},
        }
        response = requests.post(
            f"http://{hyperion_ip}:11434/api/generate", json=ollama_payload
        ).json()
        pages_text.append(response.get("response", ""))
        print(f"Page {page_file} done")

transcribed_text = "\n\n---\n\n".join(pages_text)

print(f"OCR result: {transcribed_text[:200]}")

# Patch document content
api_url = os.environ.get("PAPERLESS_API_URL", "http://localhost:8000/api/documents/")
token = os.environ.get("PAPERLESS_API_TOKEN")
headers = {"Authorization": f"Token {token}"}
result = requests.patch(
    f"{api_url}{document_id}/", headers=headers, json={"content": transcribed_text}
)
print(f"PATCH status: {result.status_code}")
