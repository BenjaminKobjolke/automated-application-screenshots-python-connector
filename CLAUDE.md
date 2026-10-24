# Version
2

# Coding Rules (Pointer)

This project's rules live in two files in the project root:

- `CODING_RULES.md` — code quality and conventions. BINDING for all code work in
  this repository, always.
- `IMPLEMENTATION_FLOW.md` — the end-to-end flow to follow when planning and
  implementing a change (checks, gates, Definition of Done).

MANDATORY: Before writing or editing ANY code, you MUST Read BOTH files in full
**in the current session**. Do not rely on memory of a previous session, a
summary, or partial reads.

If you are about to make a code change and have not read both files in this
session: STOP, read them, then continue.

An external tool may orchestrate the implementation itself. When a skill or run
states that the implementation is orchestrated, ignore `IMPLEMENTATION_FLOW.md`
entirely — the orchestrator runs those steps as its own phases. `CODING_RULES.md`
stays binding either way.

Do not inline rules back into this file and do not use `@import` for either file —
they are intentionally referenced, not imported.


graphify scan root: `automated_screenshot_connector/` — rebuild with `/graphify automated_screenshot_connector --directed`.

## Code Analysis

Two analysis modes — use the changed-files run after implementing a feature, finishing a plan,
or fixing a bug:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\automated-application-screenshots-python-connector'; cmd /c '.\tools\analyze_changed_and_new_files.bat'"
```

This uses `--only-changed`, so reports include new or modified files only. The full run is:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\automated-application-screenshots-python-connector'; cmd /c '.\tools\analyze_code.bat'"
```

Use the full run for explicit audits, before releases or merges, after shared-code refactors, or when
the working tree is clean. Results go to `code_analysis_results/` as per-rule CSV files. Fix findings
in changed files before considering the work complete.
