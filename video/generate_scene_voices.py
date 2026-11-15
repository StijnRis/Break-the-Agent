"""Generate per-scene voiceover for the browser demo video (scenes.js `vo`) -> media/vo/<id>.mp3"""
from __future__ import annotations
import json, subprocess
from pathlib import Path
import requests
from generate_slide_voiceover import create_voice, generate
import generate_slide_voiceover as g

HERE = Path(__file__).resolve().parent
OUT = HERE / "media" / "vo"


def scenes() -> list[dict]:
    js = r"""
    const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');
    const f=new Function('D','padBox','div','slam','fadeIn','R','S','return '+src.slice(src.indexOf('const SCENES = ')+15).replace(/;\s*$/,''));
    console.log(JSON.stringify(f({bbox:[0,0,1,1],summary:{}},()=>0,0,0,0,0,0).map(s=>({id:s.id,vo:s.vo,noTTS:!!s.noTTS}))));"""
    return json.loads(subprocess.check_output(["node", "-e", js, str(HERE / "scenes.js")], text=True))


def main() -> None:
    import sys
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    g.BUILD = HERE / "clean_tts_scenes"
    g.BUILD.mkdir(exist_ok=True)
    voice = create_voice()
    for i, s in enumerate(scenes()):
        if s.get("noTTS") or (only and s["id"] not in only):
            continue
        wav = generate(voice, i, s["vo"])
        mp3 = OUT / f"{s['id']}.mp3"
        subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-ar", "44100", "-b:a", "128k", str(mp3)], check=True, capture_output=True)
        print(f"{s['id']}: {mp3.name}")


if __name__ == "__main__":
    main()
