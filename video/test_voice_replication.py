"""One-shot, stateless Gemini voice-replication eligibility test.

The request deliberately uses ``store: false`` so Google does not retain a
custom voice. It writes no API key or returned voice key to disk.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\Stijn\Downloads\drive-download-20261114T180429Z-1-001\14 Nov at 20-01(5).m4a")
CONSENT = Path(r"C:\Users\Stijn\Downloads\14 Nov at 20-06.mp3")
BUILD = ROOT / "video" / "build"


def key() -> str:
    value = os.environ.get("GEMINI_API_KEY")
    if value:
        return value
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError("GEMINI_API_KEY is not configured.")


def wav(source: Path, name: str) -> Path:
    if not source.exists():
        raise FileNotFoundError(source)
    BUILD.mkdir(parents=True, exist_ok=True)
    output = BUILD / name
    subprocess.run(["ffmpeg", "-y", "-i", str(source), "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(output)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output


def audio_payload(path: Path) -> dict[str, str]:
    return {"mime_type": "audio/wav", "data": base64.b64encode(path.read_bytes()).decode("ascii")}


def main() -> None:
    source, consent = wav(SOURCE, "voice_reference.wav"), wav(CONSENT, "voice_consent.wav")
    payload = {
        "store": False,
        "voice": {
            "model": "gemini-3.8-flash-tts",
            "type": "replicated",
            "display_name": "Blueprint Lab one-shot test",
            "replicated": {"source_audio": audio_payload(source), "consent_audio": audio_payload(consent)},
        },
    }
    response = requests.post("https://generativelanguage.googleapis.com/v1beta/voices", params={"key": key()}, json=payload, timeout=90)
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text[:500]}
    if response.ok:
        # Deliberately don't reveal or persist the 7-day voice key.
        print(json.dumps({"ok": True, "status": response.status_code, "result": "Voice replication passed consent verification."}))
        return
    error = body.get("error", body)
    print(json.dumps({"ok": False, "status": response.status_code, "error": error}, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
