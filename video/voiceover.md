# Voiceover script

Pitch structure: hook → problem → what we built → demo → results → insight → reward integrity → reproducibility → close. Audio: media/vo/<id>.mp3 (intro is your own audio).

## intro · Intro (33.4 s, FILMED: media/intro.mp4)

Yo everybody. After a long day of hacking, I need the toilet. But where is it? I got the schematics of this building. Secret intel. So I take out Gemini 4 Hydrogen, take a picture, and ask: where are the toilets? It’s thinking… it says they’re over there. And that is wrong. Frontier intelligence, and it can’t even tell me where to go. Well, I’m finding an organizer.

## problem · The problem (10 s)

That’s the problem. Reading a floor plan looks easy. For an AI agent, it isn’t. So we built an environment around it: Blueprint to Schematic.

## measure · By hand (9 s, FILMED: media/measure.mp4)

To read it, you have to see the walls, find the scale, and measure every room. That’s spatial reasoning. There’s no answer to look up.

## machine · The setup (12.5 s)

Here’s the environment. The agent gets one drawing and eight tools: zoom, OCR, segmentation, measurement. No shell. No code. Just its eyes and its judgement.

## demo · Replay (25 s)

Watch Gemini 3.1 Pro work. Zoom. Zoom. Zoom. It works out the right scale, then second-guesses itself. Then it draws every room by hand: loose boxes, no interior walls. Our plain computer-vision solver traces the walls and snaps rooms to the lines, with no model in the loop. Point five one against point zero four.

## gap · The gap (16 s)

Across fifteen unseen plans, three runs each, Gemini scores point three four. Our solver: point five nine. Stop our solver halfway, and it still beats the frontier agent. Three runs, within two hundredths.

## scale · Why it fails (13 s)

So what goes wrong? It computed the right scale. Then it eyeballed the scale bar, used a different number, and every area came out six percent off. It can see. It can’t measure.

## marker · Cheat (paper) (7 s, FILMED: media/marker.mp4)

So can you cheat?

## cheat · Cheat (score) (10 s)

One giant room: zero. A thousand doors: point zero one. A wall around it all: point zero seven.

## repro · Reproducible (13 s)

And it’s reproducible. Everything runs in Harbor, with OpenCode, over MCP. A real playthrough is logged with its verifier score, and one command reproduces every number.

## end · End card (9 s)

Blueprint to Schematic. Agents can see the drawing. Now let’s teach them to measure it.

Total: 157.9 s
