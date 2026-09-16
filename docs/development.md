# Development

## Pure-core tests

Use Python 3.10 or newer. No third-party runtime/test dependencies are needed.
From the project root in PowerShell:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s tests -v
```

Optional editable installation: `python -m pip install -e .`; after installing,
the PYTHONPATH setting is unnecessary. The source layout and pyproject metadata
are ready for packaging, but distribution is not part of this first task.

## Fusion installation and validation status

There is no loadable add-in or Fusion manifest yet. Do not install `addin.py` as
a one-shot script. Exact install/load instructions will be added with the Fusion
entry point and manifest. None of the following runtime checks has been run.

Once implemented, use a fresh test design with two construction axes and verify:

1. 45 mm spacing, module 1.5, 20/40 teeth, 20-degree pressure angle.
2. Two separate components, centered on shafts, aligned axes and common axial plane.
3. Pitch circles tangent and initial tooth/gap phase without interference.
4. Reverse one axis; repeat on rotated and translated axes and nested components.
5. Reject nonparallel, coincident and duplicate references and missing selections.
6. Reject 42 mm spacing for the above pair with actual/required distance in error.
7. Ratio 2 at 45 mm: show ranked integer candidates and generate chosen candidate.
8. Repeat command, cancel, stop and restart add-in; no stale UI/handlers/selections.
9. Confirm unrelated geometry stays untouched, including after generation failure.

See MILESTONE_01.md for the full acceptance criteria. Passing pure tests does
not complete the milestone or verify Fusion behavior.

## Next task

The [Study Gears review](study-gears-review.md) records the license and proposed
integration boundary. Revisions and helper dependencies are now reviewed and
pinned in `study-gears-source-lock.json`. Address the documented numerical and
intersection defects during adaptation. Implement and test spur math and solving,
followed by Fusion selection, placement and command UI.
