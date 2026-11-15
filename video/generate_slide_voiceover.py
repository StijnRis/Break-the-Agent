"""Generate slide narration with Gemini using a stateless replicated voice."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

from render_final_video import CLIPS
from test_voice_replication import CONSENT, ROOT, SOURCE, audio_payload, key, wav

BUILD = ROOT / "video" / "clean_tts"


def create_voice() -> str:
    reference, consent = wav(SOURCE, "voice_reference.wav"), wav(CONSENT, "voice_consent.wav")
    request = {
        "store": False,
        "voice": {
            "model": "gemini-3.8-flash-tts", "type": "replicated", "display_name": "Blueprint Lab pitch (temporary)",
            "replicated": {"source_audio": audio_payload(reference), "consent_audio": audio_payload(consent)},
        },
    }
    response = requests.post("https://generativelanguage.googleapis.com/v1beta/voices", params={"key": key()}, json=request, timeout=90)
    response.raise_for_status()
    voice = response.json().get("key")
    if not voice:
        raise RuntimeError("Gemini did not return a temporary voice key.")
    return voice


def generate(voice: str, index: int, text: str) -> Path:
    request = {
        # TTS receives only the words that should be spoken. Do not prepend a
        # style or instruction prompt: some preview models can read it aloud.
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"voice": voice}, "languageCode": "en-US"},
        },
    }
    response = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent", params={"key": key()}, json=request, timeout=120)
    response.raise_for_status()
    body = response.json()
    try:
        data = body["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    except (KeyError, IndexError) as error:
        raise RuntimeError("Gemini returned no audio: " + json.dumps(body)[:800]) from error
    raw = base64.b64decode(data)
    output = BUILD / f"tts_{index:02}.wav"
    # Gemini 3.8 typically returns a WAV; handle raw 24 kHz LINEAR16 too.
    if raw[:4] == b"RIFF":
        output.write_bytes(raw)
    else:
        subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "pipe:0", str(output)], input=raw, check=True)
    return output


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=int, choices=range(len(CLIPS)))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    voice = create_voice()
    for i, (_, text, _, _) in enumerate(CLIPS):
        if args.only is not None and i != args.only:
            continue
        output = generate(voice, i, text)
        print(f"Generated narration {i + 1}/8: {output.name}")


if __name__ == "__main__":
    main()
