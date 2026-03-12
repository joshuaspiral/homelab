#!/usr/bin/env python3
import os
import json
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

API_URL = os.environ.get(
    "PAPERLESS_API_URL", "http://paperless-ngx:8000/api/documents/"
)
API_TOKEN = os.environ.get("PAPERLESS_API_TOKEN", "")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read the webhook payload
        content_length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))

        # Acknowledge the request immediately so Paperless doesn't time out
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

        doc_id = payload.get("document", {}).get("id")
        if not doc_id:
            return

        print(f"Webhook received for Document ID: {doc_id}")

        # Download the document to a temporary file for pdftoppm to process
        headers = {"Authorization": f"Token {API_TOKEN}"}
        dl_url = f"{API_URL}{doc_id}/download/"
        resp = requests.get(dl_url, headers=headers, stream=True)

        if resp.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name

            # Execute existing OCR script
            print(f"Triggering OCR script for {doc_id}...")
            subprocess.run(
                [
                    "python3",
                    "/scripts/chandra_ocr.py",
                    str(doc_id),
                    "webhook_trigger",
                    tmp_file_path,
                    "",
                    "",
                    "",
                    "",
                    "chandra-ocr",
                ]
            )

            # Clean up the temp file
            os.remove(tmp_file_path)
            print(f"Finished processing Document ID: {doc_id}")
        else:
            print(f"Failed to download document {doc_id}. HTTP {resp.status_code}")


if __name__ == "__main__":
    server_address = ("0.0.0.0", 9000)
    httpd = HTTPServer(server_address, WebhookHandler)
    print("Webhook listener running on port 9000...")
    httpd.serve_forever()
