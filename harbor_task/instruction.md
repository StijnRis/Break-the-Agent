# Digitize the floor plan

Use the `blueprint` MCP tools to turn the supplied Swiss apartment floor plan into a formal schematic. Call `get_task` first. Inspect the image and use zoom, room segmentation, area measurement, and preview tools as helpful, then call `submit_schematic` with your final JSON. You have 30 tool calls.

The schematic must represent all numbered rooms (with printed labels), wall centre lines, doors, windows, and sanitary/kitchen fixtures in original image pixel coordinates. Include `m_per_px` derived from the printed scale or scale bar. The JSON schema and coordinate rules are provided by `get_task`.

This is difficult because small geometric errors accumulate across many elements, room labels and boundaries must be inferred from a dense technical drawing, and the scale must be calibrated accurately. Tools expose the drawing at useful zoom levels and can propose room outlines, but you need to judge and correct their output.

Scoring uses the surveyed drawing geometry. Walls, rooms, doors, windows, fixtures, and calibrated room areas each contribute to a weighted score between 0 and 1. Missing and extra elements reduce credit. The verifier writes the score to `/logs/verifier/reward.txt` after submission.
