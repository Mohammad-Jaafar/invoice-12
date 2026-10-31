import argparse
import os
import time
from pathlib import Path
 
import httpx
from dotenv import load_dotenv
 
load_dotenv()
SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
 
parser = argparse.ArgumentParser()
parser.add_argument("--dir", type=Path, required=True)
parser.add_argument("--tag", default="real")
parser.add_argument("--url", default="http://localhost:8000")
parser.add_argument("--limit", type=int)
parser.add_argument("--pause", type=float, default=0.0)
args = parser.parse_args()
 
headers = {"X-API-Key": os.environ["API_TOKEN"]} if os.environ.get("API_TOKEN") else {}
for path in sorted(p for p in args.dir.iterdir() if p.suffix.lower() in SUFFIXES)[: args.limit]:
    with path.open("rb") as handle:
        response = httpx.post(
            f"{args.url}/extract",
            params={"tag": args.tag},
            files={"file": (path.name, handle)},
            headers=headers,
            timeout=120,
        )
    if response.status_code != 200:
        print(f"{path.name}: HTTP {response.status_code} {response.text[:200]}")
        continue
    body = response.json()
    print(f"{path.name}: id={body['id']} {body['status']} duplicate={body['duplicate']}")
    time.sleep(args.pause)
