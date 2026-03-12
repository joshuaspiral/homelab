#!/usr/bin/env python3
import os
import time
import tempfile
import subprocess
import requests

API_DOCS_URL = os.environ.get(
    "PAPERLESS_API_URL", "http://paperless-ngx:8000/api/documents/"
)
API_BASE = API_DOCS_URL.split("documents/")[0]
API_TOKEN = os.environ.get("PAPERLESS_API_TOKEN", "")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}


def poll():
    try:
        tag_resp = requests.get(
            f"{API_BASE}tags/?name__iexact=chandra-ocr", headers=HEADERS
        )
        tags = tag_resp.json().get("results", [])
        if not tags:
            return
        tag_id = tags[0]["id"]

        docs_resp = requests.get(
            f"{API_DOCS_URL}?tags__id__all={tag_id}", headers=HEADERS
        )
        docs = docs_resp.json().get("results", [])

        for doc in docs:
            doc_id = doc["id"]
            print(f"Processing Document {doc_id}...", flush=True)

            dl_url = f"{API_DOCS_URL}{doc_id}/download/"
            resp = requests.get(dl_url, headers=HEADERS, stream=True)
            resp.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                for chunk in resp.iter_content(8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

            subprocess.run(
                [
                    "python3",
                    "/scripts/chandra_ocr.py",
                    str(doc_id),
                    "cron",
                    tmp_path,
                    "",
                    "",
                    "",
                    "",
                    "chandra-ocr",
                ],
                check=True,
            )

            os.remove(tmp_path)

            new_tags = [t for t in doc.get("tags", []) if t != tag_id]
            requests.patch(
                f"{API_DOCS_URL}{doc_id}/", headers=HEADERS, json={"tags": new_tags}
            )
            print(f"Finished Document {doc_id}", flush=True)

    except Exception as e:
        print(f"Error: {e}", flush=True)


if __name__ == "__main__":
    print("Starting Chandra OCR polling service (5m intervals)...", flush=True)
    while True:
        poll()
        time.sleep(300)
