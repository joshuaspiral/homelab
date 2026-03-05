#!/usr/bin/env python3
import os, sys, requests, base64, socket, time

document_id = os.environ.get("DOCUMENT_ID")
file_path = sys.argv[1]
hyperion_ip = "10.0.0.20"
hyperion_mac = "XX:XX:XX:XX:XX:XX"  # Replace with your MAC

# Wake-on-LAN logic
mac_bytes = bytes.fromhex(hyperion_mac.replace(":", ""))
magic_packet = b"\xff" * 6 + mac_bytes * 16
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(magic_packet, ("10.0.0.255", 9))

# Wait for Hyperion/Ollama to boot
while True:
    try:
        if requests.get(f"http://{hyperion_ip}:11434/").status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        time.sleep(5)

with open(file_path, "rb") as image_file:
    b64_image = base64.b64encode(image_file.read()).decode("utf-8")

ollama_payload = {
    "model": "qwen3-vl:8b",
    "prompt": "Output ONLY the LaTeX transcription of the math in this image. No thinking, no filler.",
    "images": [b64_image],
    "stream": False,
    "options": {
        "temperature": 0,  # Forces deterministic output
        "repeat_penalty": 1.5,  # Prevents loops
        "stop": [
            "Wait",
            "no",
            "Actually",
        ],  # Kills response if it starts second-guessing
    },
}

response = requests.post(
    f"http://{hyperion_ip}:11434/api/generate", json=ollama_payload
).json()
transcribed_text = response.get("response", "")

# Update Paperless record
headers = {"Authorization": f"Token {os.environ.get('PAPERLESS_API_TOKEN')}"}
requests.patch(
    f"{os.environ.get('PAPERLESS_API_URL')}{document_id}/",
    headers=headers,
    json={"content": transcribed_text},
)
