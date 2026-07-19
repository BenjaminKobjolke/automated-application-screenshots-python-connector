# Writing demo scripts

A demo is a `DemoScript` built from four step types, registered in your app as
`DEMOS: dict[int, DemoScript]`. The recording tool selects one by id via
`--automation-demo <id>`.

```python
from automated_screenshot_connector import (
    Command, DemoScript, Pause, Screenshot, TypeText,
)

DEMOS: dict[int, DemoScript] = {
    1: DemoScript(
        id=1,
        name="basic-math",          # output folder name: demos/basic-math/
        steps=(
            Pause(0.5),             # let the window settle before typing
            TypeText("1+1\n"),      # typed char by char, 60 ms per char
            Pause(0.8),             # give viewers time to read the result
            Screenshot("basic"),    # tool saves demos/basic-math/basic.png
            Command("/clear"),      # typed + Return through real key events
            Pause(1.0),             # hold the final state before the demo ends
        ),
    ),
}
```

## Step types

| Step | What it does |
|---|---|
| `TypeText(text, char_delay_ms=60)` | Types `text` char by char into the input widget; `\n` starts a new line. Fires the same signals as human typing. |
| `Pause(seconds)` | Does nothing — reading time for viewers. |
| `Command(line)` | Types the full line, then posts a real Return key event so your widget's `keyPressEvent` handles it (commands, submit, etc.). |
| `Screenshot(name)` | Waits 400 ms for the UI to settle, then asks the tool to save `<name>.png`. |

## Guidelines

- **Pace for viewers, not machines.** 0.8–1.2 s pauses after each result; end
  with a `Pause(1.0)` so the recording doesn't cut off abruptly.
- **Screenshot names** must be filesystem-friendly and unique within a demo —
  they become `<name>.png` in the demo's output folder.
- **Set up state, then screenshot**: a demo can exist purely to arrange the UI
  for stills — type, `Screenshot`, `Command("/clear")`, type the next state,
  `Screenshot` again.
- **Watch app-side input interception.** `Command` goes through your widget's
  real key handling — if your app has autocompletion, an ambiguous prefix may
  open a menu instead of executing (e.g. FastCalculator's `/copy` vs
  `/copy-last`). Use unambiguous lines; pin it with a unit test against your
  command registry (see `calculator/tests/test_demo_scripts.py`).
- **Appearance settings don't belong in scripts.** Font size, theme, window
  size come from the tool config (`app_settings`, `width`/`height`) so the same
  script records correctly everywhere.
- **Language is a run parameter, not script content.** When the tool config
  lists demo `languages`, each run gets `--automation-demo-language <lang>`;
  read it from `options.demo_language` and set your app's UI language before
  building the window. One script records once per language.
- **Localize typed text with placeholders.** Write `TypeText("{price} = 20\n")`
  and keep the wording in one JSON file per language (tool config `texts_dir`,
  delivered as `--automation-demo-texts <path>`). Apply it with
  `localize_script(DEMOS[options.demo], dict(options.demo_texts))` before
  handing the script to the player. Empty texts leave the script unchanged;
  literal braces need `{{`/`}}`; `Screenshot` names are never localized.
  Manual preview: pass `--automation-demo-texts path/to/de.json` yourself —
  without it, placeholders are typed literally.
- **Test your registry**: unique ids, `script.id == dict key`, non-empty steps,
  known commands — cheap tests that catch broken demos before a recording run.

## Playing without the tool

`your-app --automation-demo 1` (no port) plays the demo visually with a no-op
client — the fastest way to iterate on pacing.
