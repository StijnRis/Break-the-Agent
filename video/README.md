# Demo video (2:00)

A browser-based video: animated scenes built from the real run data, plus clips filmed by hand.

```bash
python -m http.server 8777 --directory video
```

Open http://localhost:8777. Space plays, the bar scrubs, `[` `]` jump between scenes. **H** hides the controls for screen recording, and **F** goes fullscreen.

## Drop in your footage

| file in `video/media/` | length | shot |
|---|---|---|
| `walkin.mp4` | 12 s | Follow through a door, drop the A3 plan on a table, and say the opening line to camera. The clip's own sound is used. |
| `measure.mp4` | 13 s | Close-ups: finger on "1:100", a ruler across a room, a pencil tracing a wall |
| `ruler.mp4` | 3 s | Hold the ruler up to camera and shrug |
| `marker.mp4` | 7 s | Marker: one giant box over the plan, then dots everywhere |
| `walkout.mp4` | 6 s | Roll up the plan and walk out the door |

Print `tasks/site1047_bldg2154_floor9740/drawing.png` at A3. It's the same plan the animations use.

Voiceover: use either `media/vo/<scene id>.mp3` per scene (`walkin`, `measure`, `machine`, `demo`, `gap`, `ruler`, `scale`, `marker`, `cheat`, `walkout`, `end`) or one `media/voiceover.mp3` for the whole video. The side panel shows the current scene's script as a teleprompter.

## Change things

- `scenes.js`: scene order, durations, text, voiceover script and animations.
- `lib.js`: drawing and tween helpers.
- `build_data.py`: re-export the data, for example with another plan: `python video/build_data.py --task <id> --run run0`.
