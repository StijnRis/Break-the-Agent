"""Subtitle cues for the demo video -> media/subs.json (+ out/subtitles.srt). Used by the player and by render_demo.py.

Voiceover scenes: the scene's text is split into short phrases and spread over the length of its voiceover mp3 (by character count).
The intro is your own recording, so its cues come from a timestamped transcript (original clip time - 2.2 s)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

INTRO = [  # (seconds in the cut, text)
    (0.8, "Yo everybody."), (1.9, "Just after a long day of hacking, just like you, I need to go to the toilet."),
    (5.5, "But where is it here?"), (6.9, "I don't know."), (7.8, "So I got the schematics of this building here."),
    (9.6, "Secret intel."), (10.5, "And since I have not been thinking all day long, I will continue doing that."),
    (14.2, "So, I take out my AI."), (15.6, "I'm gonna take a picture of it."), (17.9, "And then I will ask it, where are the toilets here?"),
    (21.0, "So, well, let's see where they are."), (22.9, "It's thinking a bit."), (24.1, "It's thinking, it's thinking."),
    (25.3, "It says they're over there, and that is wrong."), (27.7, "My god, what is this?"),
    (28.8, "Frontier intelligence, and it cannot even tell me where I need to go to the toilet."), (32.7, "Well, I'm finding an organizer."),
]


def scenes() -> list[dict]:
    js = r"""
    const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');
    const f=new Function('D','padBox','div','slam','fadeIn','R','S','return '+src.slice(src.indexOf('const SCENES = ')+15).replace(/;\s*$/,''));
    let t=0;console.log(JSON.stringify(f({bbox:[0,0,1,1],summary:{}},()=>0,0,0,0,0,0).map(s=>{const o={id:s.id,start:t,dur:s.dur,vo:s.vo,noTTS:!!s.noTTS};t+=s.dur;return o})));"""
    return json.loads(subprocess.check_output(["node", "-e", js, str(HERE / "scenes.js")], text=True))


def phrases(text: str, max_words: int = 6) -> list[str]:
    out = []
    for sent in re.findall(r"[^.!?:]+[.!?:]?", text):
        sent = sent.strip()
        if not sent:
            continue
        words = sent.split()
        if len(words) <= max_words:
            out.append(sent)
            continue
        parts = re.split(r"(?<=,)\s+", sent)
        buf = ""
        for p in parts:
            if buf and len((buf + " " + p).split()) > max_words:
                out.append(buf); buf = p
            else:
                buf = (buf + " " + p).strip()
        if buf:
            out.append(buf)
    return out


def mp3_len(p: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], text=True).strip())


def build() -> list[dict]:
    cues: list[dict] = []
    for s in scenes():
        if s["noTTS"]:
            pts = INTRO
            for i, (t, text) in enumerate(pts):
                end = pts[i + 1][0] - 0.05 if i + 1 < len(pts) else min(s["dur"], t + 2.6)
                end = min(end, t + 4.5)
                ph = phrases(text) or [text]
                tot = sum(len(p) for p in ph); a0 = t
                for p in ph:
                    d = (end - t) * len(p) / tot
                    cues.append({"start": round(s["start"] + a0, 2), "end": round(s["start"] + a0 + d - 0.03, 2), "text": p})
                    a0 += d
            continue
        mp3 = HERE / "media" / "vo" / f"{s['id']}.mp3"
        vl = min(mp3_len(mp3), s["dur"]) if mp3.exists() else s["dur"] * 0.85
        ph = phrases(s["vo"])
        total = sum(len(p) for p in ph)
        t = s["start"] + 0.1
        for p in ph:
            d = (vl - 0.1) * len(p) / total
            cues.append({"start": round(t, 2), "end": round(t + d - 0.03, 2), "text": p})
            t += d
    return cues


def srt_time(x: float) -> str:
    ms = round(x * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


_MAP = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "...", " ": " ", "→": "to"}


def plain(text: str) -> str:
    """captions are plain ASCII: players that guess the wrong encoding for the .srt turn curly quotes into 'â€™'"""
    for k, v in _MAP.items():
        text = text.replace(k, v)
    return "".join(c if ord(c) < 128 else "" for c in text)


def export() -> list[dict]:
    cues = build()
    for c in cues:
        c["text"] = plain(c["text"])
    (HERE / "media" / "subs.json").write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / "subtitles.srt").write_text("\n".join(f"{i + 1}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n" for i, c in enumerate(cues)), encoding="utf-8")
    return cues


if __name__ == "__main__":
    c = export()
    print(len(c), "cues")
