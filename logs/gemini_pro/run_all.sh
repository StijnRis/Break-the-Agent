#!/bin/bash
cd "C:/Users/Stijn/Programming/Challenge/Break the Agent"
T=$(.venv/Scripts/python -c "import json;print(' '.join(json.load(open('split.json'))['test']))")
for t in $T; do
  PYTHONIOENCODING=utf8 .venv/Scripts/python -m blueprint_env.agent "$t" --model gemini-3.1-pro-preview --runs 3 > "logs/gemini_pro/$t.log" 2>&1 &
  sleep 2
done
PYTHONIOENCODING=utf8 .venv/Scripts/python -m blueprint_env.agent "$(echo $T | tr ' ' ',')" --model gemini-3-flash-preview --max-calls 4 --label stop-early-gemini-3-flash-4calls > logs/stop_early_agent.log 2>&1 &
wait
echo ALL GEMINI RUNS FINISHED
