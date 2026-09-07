# Writing demo scripts

A demo is a `DemoScript` built from the step types below, registered in your app
in a `DemoRegistry`. The recording tool selects one by id via
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

## Registering demos

`DemoRegistry` is the lookup the tool's `--automation-demo <id>` resolves
against. It exists so every app stops writing the same dict, the same
"unknown id" error and the same special case for generated demos:

```python
from automated_screenshot_connector import DemoRegistry

REGISTRY = DemoRegistry()
REGISTRY.add_all(DEMOS)                                    # id -> DemoScript
REGISTRY.add_factory(2, "themes", build_themes_script)     # built on demand

script = REGISTRY.get(options.demo, names=installed_themes())
```

- `add(*scripts)` / `add_all(dict)` register finished scripts; a duplicate id is
  rejected at registration, not discovered during a recording.
- `add_factory(id, name, factory)` registers a demo **built at lookup time**.
  This is what keeps a generated demo honest: one `Screenshot` per installed
  theme, plugin or locale stays complete without anyone editing a list when one
  is added. The factory must return a script whose `id` matches, or the tool
  would file the frames under the wrong demo.
- `get(id, **params)` passes `params` to a factory and ignores them for a
  finished script, so you can pass the same ones for every id. An unknown id
  raises `UnknownDemoError`, whose message already lists the available ids —
  print it and exit.
- `ids()` and `name_of(id)` answer "what can this app record?" without building
  anything.

## Integrating demo mode

Five things every app has to get right, and each one is invisible until it
ruins a take:

1. **Detect the flag before anything else initializes.** `is_demo_argv(sys.argv)`
   at the top of your entry point — earlier than argparse, config loading or
   single-instance handling. (`DEMO_FLAG` is the flag itself, if you need the
   string; neither costs a Qt import.)
2. **Bypass single-instance forwarding.** If an instance is already running,
   the usual "forward the arguments and exit" path swallows the demo launch and
   the tool records the wrong window (or times out).
3. **Suppress onboarding.** First-run tours, changelog popups, update prompts
   and tip-of-the-day dialogs all appear on camera. Gate them on a demo-mode
   flag.
4. **Pin every visual state the script depends on** — window opacity, zoom,
   sidebar visibility. Force the value; never read it from the user's profile,
   or a re-recording will not match the first take.
5. **Hand the rest of argv back to your app.** `parse_demo_args` consumes only
   `--automation-demo*` and returns the leftovers; assign them back
   (`sys.argv[1:] = leftover`) if any of your code reads raw argv.

Size and position: `showNormal()`, then `resize(demo_width, demo_height)`, then
centre — that order defeats both maximize-on-first-run and remembered geometry.
See also the `KeyEventDemoPlayer` size gotcha below.

## Step types

| Step | What it does |
|---|---|
| `TypeText(text, char_delay_ms=60)` | Types `text` char by char into the input widget; `\n` starts a new line. Fires the same signals as human typing. |
| `Pause(seconds)` | Does nothing — reading time for viewers. |
| `Command(line)` | Types the full line, then posts a real Return key event so your widget's `keyPressEvent` handles it (commands, submit, etc.). |
| `Screenshot(name)` | Waits 400 ms for the UI to settle, then asks the tool to save `<name>.png`. |
| `PressKey(chord, delay_ms=60)` | Presses a key chord (`"Ctrl+Shift+P"`, `"Down"`, `"Return"`, `"Escape"`, …), parsed with `QKeySequence`. Only executed by `KeyEventDemoPlayer`. |

## Two players

- **`DemoPlayer(input_edit, client, script, hwnd)`** — the original typing
  player for apps with one `QPlainTextEdit` input (e.g. FastCalculator).
  `TypeText` inserts via the text cursor; `PressKey` is not supported.
- **`KeyEventDemoPlayer(window, client, script, hwnd)`** — for shortcut-driven
  apps (command palettes, modal search dialogs; e.g. FastFileViewer). Every
  `TypeText` char and `PressKey` chord is posted as a real `QKeyEvent` to the
  window's own focus widget, so modal `exec()` dialogs receive input too
  (QTimers keep firing inside nested modal loops). `start()` raises and
  activates the window first: the recording tool pins the window's z-order but
  does not reliably activate it, and `QApplication.focusWidget()` is `None`
  while the window is inactive — which used to send every key to the top-level
  window and record an app doing nothing.

Both players work with **PySide6 or PyQt5** — whichever your app already
has. The two bindings disagree on exactly one thing (how a `QKeySequence`
combination unpacks), which `_qtbind` handles, so there is no reason to
fork the player.

`KeyEventDemoPlayer` validates every `PressKey` chord in its constructor, so
a typo like `"Ctrl+Nope"` fails in the first second instead of five minutes
into a recording.

`KeyEventDemoPlayer` is extensible: any step type `flatten` doesn't know is
delivered to `handle_step(step)` — subclass it for app-specific steps:

```python
class ViewerDemoPlayer(KeyEventDemoPlayer):
    def handle_step(self, step: object) -> None:
        if isinstance(step, OpenFile):          # app-defined dataclass
            self._window.open_pdf(step.path())
            return
        super().handle_step(step)               # raises on unknown steps
```

Two hard-won gotchas for `KeyEventDemoPlayer` apps:

- **Set the demo window size AFTER `show()`** (and prefer `setFixedSize`): the
  first show pass can re-lay the window out to Qt's screen-derived default and
  discard a pre-show `resize()`; later UI appearing (e.g. a status bar) can
  grow the window and drift the recording off the configured aspect ratio.
- **You do not have to be closable, but you do have to be interruptible**: the
  players end the run with `QCoreApplication.exit(0)`, not `QApplication.quit()`,
  because since Qt 6.5 `quit()` closes the windows first and any window that
  ignores its close event cancels the whole quit — the app then lingers until
  the tool kills it 10 s later. Pass `exit_when_done=False` to keep the app
  alive after the demo (a manual preview, say), and do the ending yourself.

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
- **Check the length before you record.** `estimated_duration(script)`
  returns the seconds a script will take without running it (delays plus the
  player's start delay and end hold). The tool aborts a demo at 300 s, and
  gives up after 60 s with no event — a script that estimates near either is
  a script to split.
- **Test your registry**: unique ids, `script.id == dict key`, non-empty steps,
  known commands — cheap tests that catch broken demos before a recording run.

## Playing without the tool

`your-app --automation-demo 1` (no port) plays the demo visually with a no-op
client — the fastest way to iterate on pacing.
