# TODO List:
- Pygame monitor window: show parsed board and solving progress graphically!
- Parallelize `ai.solve()` and optimize `ai.Board` (see in-code `# TODO:` notes)
- Implement `gui.find_phage_pink()`, and/or detect throw _(maybe not needed?)_
  - Both Laelath and FidelSolver do the former, none do the latter
  - Maybe that's why both coded the ~80ms pause after moves,
      to wait out (some of) the animation.
  - Pink detection might not be needed, as I can detect crouch grab (which none do)
- `gui.parse_image()`: Detect matched blocks (white contour), as Laelath does.
    Might improve performance and accuracy of `ai.solve()`
- Improve bash installer, or drop it. We have a `pyproject.toml` and `README.md` now.
- Study and take lessons from Fidel's solver
- Alternate `ai.solve()`: `GRAB`/`SWAP` for each col, derive needed `LEFT`/`RIGHT`
  - Avoids tons of duplicate, meaningless boards with same score
  - More parallelization: from 4 to 7 (cols) or 14 (7 cols x 2 actions)
- Detect game's screens and use PyAutoGUI to go from title to start game
- Improve 1366x768 so it actually works. Then announce it to
    [this poor guy](https://www.reddit.com/r/exapunks/comments/vgpzsj/)
- Config file: implement or drop the stubs. Possibly over-engineered idea anyway.
- Consider adding all exception classes to `util` module.
    (run `u.HMError.__subclasses__()` to find them)
- Nitpick: for display purposes, say THROW instead of GRAB when, well,
    throwing instead of grabbing.
