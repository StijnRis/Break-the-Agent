"""Independently transcribe generated TTS clips and check their spoken text."""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import requests

from generate_slide_voiceover import BUILD
from render_final_video import CLIPS
from test_voice_replication import key


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def main() -> None:
    failures = []
    results = []
    for index, (_, expected, _, _) in enumerate(CLIPS):
        clip = BUILD / f"tts_{index:02}.wav"
        request = {"contents": [{"parts": [
            {"text": "Transcribe this audio exactly. Return only the words spoken, with no commentary."},
            {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(clip.read_bytes()).decode("ascii")}},
        ]}]}
        response = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", params={"key": key()}, json=request, timeout=90)
        response.raise_for_status()
        body = response.json()
        actual = "".join(part.get("text", "") for part in body["candidates"][0]["content"]["parts"])
        # The verifier can vary capitalization/punctuation. A successful result
        # must contain both the opening and closing portion of the target line.
        expected_words = normalize(expected).split()
        actual_normalized = normalize(actual)
        opening = " ".join(expected_words[:min(4, len(expected_words))])
        closing = " ".join(expected_words[-min(4, len(expected_words)):])
        ok = opening in actual_normalized and closing in actual_normalized
        results.append({"clip": index, "ok": ok, "transcript": actual})
        if not ok:
            failures.append(index)
    (BUILD / "verification.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        raise SystemExit("Transcript verification failed for clips: " + ", ".join(map(str, failures)))


if __name__ == "__main__":
    main()
