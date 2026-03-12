#!/usr/bin/env python3
import os
import requests
import subprocess
import time

API_URL = os.environ.get("PAPERLESS_API_URL", "http://localhost:8000/api/")
API_TOKEN = os.environ.get("PAPERLESS_API_TOKEN", "")
TARGET_TAG_NAME = "chandra-ocr"
OCR_SCRIPT_PATH = "/scripts/chandra_ocr.py"

headers = {"Authorization": f"Token {API_TOKEN}"}


def get_tag_id(tag_name):
    resp = requests.get(f"{API_URL}tags/?name__icontains={tag_name}", headers=headers)
    results = resp.json().get("results", [])
    return results[0]["id"] if results else None


def poll_and_process():
    tag_id = get_tag_id(TARGET_TAG_NAME)
    if not tag_id:
        print(f"Tag '{TARGET_TAG_NAME}' not found in Paperless. Create it first.")
        return

    # Find docs with the tag
    resp = requests.get(f"{API_URL}documents/?tags__id__all={tag_id}", headers=headers)
    docs = resp.json().get("results", [])

    for doc in docs:
        doc_id = doc["id"]
        # Basic check to avoid re-processing if content is already 'rich'
        if len(doc["content"]) > 500 and "---" in doc["content"]:
            continue

        print(f"Found document {doc_id} to process...")
        # Arg 3 is the file path; Arg 8 is the tags string
        subprocess.run(
            [
                "python3",
                OCR_SCRIPT_PATH,
                str(doc_id),
                "",
                doc["source_path"],
                "",
                "",
                "",
                "",
                TARGET_TAG_NAME,
            ]
        )


if __name__ == "__main__":
    while True:
        try:
            poll_and_process()
        except Exception as e:
            print(f"Error in poll loop: {e}")
        time.sleep(60)  # Run every 60 seconds
