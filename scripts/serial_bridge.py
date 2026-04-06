#!/usr/bin/env python3
"""
USB serial -> Railway (or any) LOT AND FOUND API.

Reads lines from Arduino (STATUS:OCCUPIED / STATUS:EMPTY) and POSTs occupancy.

Setup:
  pip install -r requirements-hardware.txt
  Copy bridge.env.sample -> bridge.env and fill values.

Run (from repo root):
  python scripts/serial_bridge.py

Env (or bridge.env):
  BRIDGE_BASE_URL   https://your-app.up.railway.app  (no trailing slash)
  BRIDGE_SPOT_ID    integer from admin UI (spot you wired to this sensor)
  BRIDGE_API_TOKEN  same as OCCUPANCY_API_TOKEN on Railway
  BRIDGE_SERIAL_PORT  COM3  (Windows) or /dev/ttyUSB0 (Linux) or /dev/cu.usbserial-* (macOS)
  BRIDGE_BAUD       9600 (default)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

try:
    import serial  # pyserial
except ImportError:
    print("Install: pip install pyserial", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_a, **_k):
        pass


STATUS_RE = re.compile(r"^\s*STATUS:\s*(OCCUPIED|EMPTY)\s*$", re.I)
LEGACY_RE = re.compile(r"^\s*Status:\s*(OCCUPIED|EMPTY)\s*$", re.I)


def parse_status_line(line: str) -> bool | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = STATUS_RE.match(line) or LEGACY_RE.match(line)
    if not m:
        return None
    return m.group(1).upper() == "OCCUPIED"


def post_occupied(base_url: str, spot_id: int, token: str, occupied: bool) -> tuple[bool, str]:
    url = f"{base_url.rstrip('/')}/api/spot/{spot_id}/status"
    body = json.dumps({"occupied": occupied}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Api-Token": token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return True, raw
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = str(e)
        return False, f"HTTP {e.code}: {raw}"
    except Exception as e:
        return False, str(e)


def main() -> None:
    load_dotenv()
    load_dotenv("bridge.env")

    p = argparse.ArgumentParser(description="Arduino serial -> parking API bridge")
    p.add_argument("--base-url", default=os.getenv("BRIDGE_BASE_URL", ""))
    p.add_argument("--spot-id", type=int, default=int(os.getenv("BRIDGE_SPOT_ID", "0")))
    p.add_argument("--token", default=os.getenv("BRIDGE_API_TOKEN", os.getenv("OCCUPANCY_API_TOKEN", "")))
    p.add_argument("--port", default=os.getenv("BRIDGE_SERIAL_PORT", ""))
    p.add_argument("--baud", type=int, default=int(os.getenv("BRIDGE_BAUD", "9600")))
    args = p.parse_args()

    if not args.base_url or not args.port or args.spot_id <= 0:
        print(
            "Set BRIDGE_BASE_URL, BRIDGE_SERIAL_PORT, BRIDGE_SPOT_ID (see bridge.env.sample).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not args.token:
        print("Set BRIDGE_API_TOKEN (must match OCCUPANCY_API_TOKEN on the server).", file=sys.stderr)
        sys.exit(1)

    print(f"Opening {args.port} @ {args.baud} -> {args.base_url} spot {args.spot_id}", flush=True)
    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(2)

    last_sent: bool | None = None
    while True:
        try:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace")
            occ = parse_status_line(line)
            if occ is None:
                continue
            if occ == last_sent:
                continue
            ok, msg = post_occupied(args.base_url, args.spot_id, args.token, occ)
            if ok:
                print(f"OK occupied={occ} -> {msg}", flush=True)
                last_sent = occ
            else:
                print(f"ERR occupied={occ} -> {msg}", flush=True)
                if "409" in msg or "active booking" in msg.lower():
                    print("(409: spot has a live booking in the app — sensor sync skipped)", flush=True)
        except KeyboardInterrupt:
            print("\nStopped.", flush=True)
            break
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
