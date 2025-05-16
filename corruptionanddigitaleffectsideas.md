# Text-Based Corruption & Distortion Effects

## Character-Level Corruption & Glitching:

* **Symbolic Decay:** Use unsettling Unicode characters (combining characters, broken box-drawing, obscure symbols) to replace original characters.
* **Repeating/Stuttering Characters:** Occasionally repeat a character multiple times (e.g., `e-e-e-error`).
* **Inverted/Corrupted Blocks:** Use ANSI escape codes for color inversion or drastic color changes on random text blocks.
* **"Worm" Trails:** Print a trail of corrupted characters or symbols behind the cursor that quickly disappear.

## Line & Layout Distortion:

* **Sudden Line Breaks/Wrapping:** Force unexpected line breaks mid-word using newlines based on a "corruption chance."
* **Vertical Shifting/Jitter:** Add small, random vertical offsets to lines using cursor positioning.
* **Horizontal Displacement (Screen Tear):** Briefly shift portions of lines horizontally using cursor positioning, creating gaps or overlaps, then potentially restore or print a corrupted version.
* **Overwriting/Binary Injections:** Simulate data overwrite by printing and quickly overwriting parts of text with '0's and '1's or glitch symbols.

## Animation & Timing Effects:

* **Uneven Typing Speed:** Vary delays between characters wildly; include sudden long pauses.
* **Flicker/Phase Shift:** Text blocks or lines rapidly alternate between normal, corrupted, or absent states.
* **Textual "Breathing":** Slowly pulse text color lighter and darker or subtly change background colors.

## Color & Visual Noise:

* **Random Color Spikes:** Individual characters or sequences flash vivid, unsettling colors using ANSI color codes.
* **Simulated Scan Lines/Static:** Regularly print lines of noise characters (`.`, `,`, `-`) with subtle colors overlaid.
* **"Bleeding" Colors:** Have a line's ending color briefly appear at the start of the next line.

## Contextual & Narrative Effects:

* **"Redacted" Terminal Output:** Use block characters (`█`) or background color effects to black out parts of text.
* **Intrusive Thoughts/Echoes:** Fragmented, disturbing words appear and are quickly overwritten before main text finishes.
* **Dynamic Error Messages:** Error messages are corrupted, contain personal data fragments, or disturbing phrases.