# MILESTONE_01 — External Spur Gear Pair on Two Parallel Axes

## Goal

Implement the first complete vertical slice of Fusion Gear Designer:

> The user selects two existing parallel shaft axes in Autodesk Fusion and generates a valid pair of external involute spur gears centered and aligned on those axes.

This milestone must prove the architecture, geometry solver, Fusion integration, and placement strategy before the project expands to more gear families.

---

## User story

As a Fusion user, I want to select two shaft axes that already exist in my model, define a spur-gear pair, and generate both gears directly on those axes so that I do not need to manually position generated gears afterward.

---

## Scope

### Included

- Autodesk Fusion add-in
- Python implementation
- one `Gear Pair` command
- selection of two shaft-axis references
- parallel-axis validation
- center-distance calculation
- external involute spur gears only
- separate components for both gears
- tooth-count-driven mode
- ratio-driven mode
- module
- pressure angle
- backlash
- gear geometry generation
- correct 3D placement
- correct relative tooth phase
- pure-core automated tests
- documented Fusion-side manual validation

### Excluded

- helical gears
- internal gears
- bevel gears
- worm drives
- crossed helical gears
- profile shift
- hypoid gears
- planetary gear trains
- automatic gearbox design
- housing generation
- bearing generation
- shaft generation
- strength calculations
- ISO/AGMA certification
- CAM
- manufacturing drawings

Do not expand scope during this milestone unless required to make the stated workflow function correctly.

---

## Study Gears strategy for Milestone 01

For spur-gear and involute geometry, treat **Study Gears by Osamu Takeuchi** as the preferred reference implementation.

Before implementing the involute/spur generator:

1. inspect the relevant upstream Study Gears code;
2. verify the current upstream license;
3. identify the smallest reusable mathematical/geometry-generation portion;
4. decide whether direct adaptation or a clean reimplementation from the same documented method is better for this architecture;
5. preserve required notices for any copied/adapted code;
6. record reuse in `THIRD_PARTY_NOTICES.md`;
7. add local regression tests.

Do **not** copy Study Gears' UI or placement workflow merely because it already exists.

Milestone 01 must still use this project's own:

- shaft-axis geometry model;
- center-distance validation;
- pair solver;
- Fusion selection flow;
- 3D placement;
- tooth clocking;
- command UX.

The purpose of using Study Gears is to avoid reinventing well-established gear geometry, not to inherit an unrelated application architecture.

---

## Primary workflow

The expected user flow is:

```text
Create > Gear Pair

1. Select Input Axis
2. Select Output Axis
3. Add-in validates axis relationship
4. Add-in calculates center distance
5. User chooses definition mode
6. User enters gear parameters
7. Add-in validates the pair
8. Add-in previews/returns derived values
9. User generates
10. Two gear components appear on the selected axes
```

---

## UI requirements

The command dialog should contain conceptually:

```text
Input Axis:        [Select]
Output Axis:       [Select]

Detected relationship:
  Parallel

Center distance:
  45.000 mm

Definition mode:
  ○ Tooth counts
  ○ Desired ratio

Module:
  1.5 mm

Pressure angle:
  20 deg

Backlash:
  0.15 mm
```

### Tooth-count mode

Additional fields:

```text
Input teeth:
  20

Output teeth:
  40
```

Derived values should include:

```text
Ratio:
  2.000 : 1

Required center distance:
  45.000 mm

Center-distance error:
  0.000 mm
```

### Ratio mode

Additional field:

```text
Desired ratio:
  2.000 : 1
```

The solver should return one or more valid integer tooth-count pairs that fit the selected axis spacing within tolerance.

If multiple results are valid, expose several candidates rather than selecting an unexplained arbitrary pair.

---

## Axis selection

The command must accept unambiguous linear shaft references.

Initial preferred target:

- Fusion construction axes

Optional additional support is acceptable if simple and robust:

- cylindrical-face axes
- sketch lines explicitly treated as shaft references

Do not broaden selection support if it complicates the MVP unnecessarily.

---

## Axis validation

For selected axis lines:

1. extract origin point and direction vector;
2. normalize direction vectors;
3. classify relationship;
4. verify they are parallel within angular tolerance;
5. compute shortest perpendicular distance.

If axes are intersecting or skew, reject generation with a clear message such as:

> The selected shaft axes are not parallel. Milestone 01 supports external spur gears on parallel axes only.

Do not attempt to reinterpret unsupported geometry.

---

## Mathematical model

For a standard external spur gear:

```text
pitch_diameter = module * tooth_count
pitch_radius   = pitch_diameter / 2
```

For a standard external pair without profile shift:

```text
center_distance = module * (z1 + z2) / 2
```

Where:

- `module > 0`
- `z1`, `z2` are positive integers
- pressure angle is valid
- backlash is non-negative

Document all additional addendum, dedendum, root, base-circle, and tooth-thickness conventions in `docs/gear-math.md`.

---

## Pressure angle

Pressure angle must be explicit.

Initial UI default:

```text
20 deg
```

Do not hard-code assumptions inside the involute generator.

The mathematical layer should accept the pressure angle as input.

---

## Backlash

Backlash must be an explicit design input.

Initial default may be:

```text
0.15 mm
```

The exact default is a UI convenience, not an engineering guarantee.

The core must clearly define how backlash modifies tooth thickness or equivalent generated geometry.

Document the convention.

---

## Involute profile

Implement a mathematically explicit involute tooth profile.

Requirements:

- calculate base circle;
- calculate involute flank points;
- create left and right flanks;
- create tip transition;
- create root transition;
- replicate the tooth around the gear;
- avoid duplicated or self-intersecting sketch geometry.

Do not approximate the involute with an arbitrary visual curve merely because it looks correct.

Any discretization tolerance must be documented.

---

## Root geometry

The first milestone may use a simplified root treatment if necessary, provided:

- the approximation is documented;
- it does not interfere with neighboring teeth for validated inputs;
- it does not pretend to reproduce an exact generating cutter process.

A more exact trochoidal root may be deferred.

---

## Tooth-count mode

Inputs:

- `z1`
- `z2`
- `module`
- `pressure_angle`
- `backlash`

Process:

1. calculate theoretical center distance;
2. compare with selected-axis center distance;
3. calculate absolute and relative error;
4. reject if outside tolerance;
5. otherwise generate.

Example error:

> Selected axes are 42.000 mm apart, but 20T and 40T gears at module 1.5 require 45.000 mm.

Do not silently scale geometry to fit.

---

## Ratio mode

Inputs:

- desired ratio
- module
- pressure angle
- backlash
- selected-axis center distance

Need to find integer tooth counts satisfying approximately:

```text
z2 / z1 ≈ desired_ratio
```

and:

```text
module * (z1 + z2) / 2 ≈ selected_center_distance
```

The solver must:

- search a bounded, documented tooth-count range;
- reject geometrically invalid counts;
- rank candidates by center-distance error and ratio error;
- return several useful candidates when possible.

Do not hide the fact that the solution is discrete.

---

## Minimum tooth-count handling

The project must define a minimum supported tooth count for the current involute assumptions.

If undercut/interference checks are implemented mathematically, use them.

If not yet fully implemented:

- enforce a conservative documented minimum;
- clearly label it as an MVP constraint.

Do not generate obviously invalid gears simply because the equations produce a radius.

---

## Component generation

Each gear must become a separate Fusion component.

Suggested naming:

```text
Gear_Input_z20_m1.5
Gear_Output_z40_m1.5
```

Each component should contain its own generated geometry.

Do not place both gears into one anonymous body.

---

## Placement

Each generated gear must satisfy all of the following:

### Center

The gear center lies exactly on the selected shaft axis.

### Axis direction

The gear rotation axis is aligned with the selected shaft direction.

### Axial position

The gear is generated on a deterministic reference plane.

For the first milestone, choose and document one rule, for example:

- gear mid-plane passes through the closest-point segment between shaft axes; or
- gear base plane passes through a reference point derived from the selected geometry.

Do not use arbitrary world-origin placement.

### Tooth phase

The gear pair must be rotationally phased so that:

- a tooth on one gear does not initially overlap a tooth on the other;
- the pair begins in a plausible meshing orientation.

The phase must be calculated from gear geometry, not guessed by visual inspection.

---

## Gear thickness

The UI may include:

```text
Gear thickness:
  8.0 mm
```

If implemented, thickness must be explicit and documented.

If omitted from the first implementation pass, use one centralized default and expose it before milestone completion.

Do not bury thickness as an unexplained constant.

---

## Error handling

The command must report understandable failures.

Examples:

- fewer than two axes selected;
- same axis selected twice;
- non-parallel axes;
- zero/negative module;
- invalid pressure angle;
- negative backlash;
- invalid tooth count;
- incompatible center distance;
- no ratio solution in search range;
- Fusion geometry creation failure.

Do not show raw exceptions to the user as the only error message.

For debugging, preserve traceback information in logs or developer output.

---

## Core data objects

Prefer explicit value types.

Example conceptual models:

```python
@dataclass(frozen=True)
class Line3D:
    origin: Vec3
    direction: Vec3

@dataclass(frozen=True)
class SpurGearSpec:
    module_mm: float
    teeth: int
    pressure_angle_rad: float
    backlash_mm: float
    thickness_mm: float

@dataclass(frozen=True)
class SpurPairSolution:
    input_gear: SpurGearSpec
    output_gear: SpurGearSpec
    center_distance_mm: float
    ratio: float
```

Names may differ, but avoid passing loose tuples of unrelated floats across the codebase.

---

## Required pure-core modules

At minimum implement equivalents of:

```text
core/geometry/vector.py
core/geometry/line.py
core/geometry/axis_relation.py

core/gears/involute.py
core/gears/spur.py
core/gears/validation.py

core/solver/spur_pair.py
core/solver/ratio_search.py
```

Do not import `adsk` from these modules.

---

## Required Fusion modules

At minimum implement equivalents of:

```text
fusion/selection.py
fusion/axis_adapter.py
fusion/components.py
fusion/sketches.py
fusion/placement.py
fusion/units.py
```

Keep Fusion-specific concerns out of the pure core.

---

## Required command modules

At minimum:

```text
commands/gear_pair/
```

Responsibilities:

- register command;
- collect selections;
- collect inputs;
- call core solver;
- display validation state;
- call Fusion generation layer;
- handle cleanup.

Do not implement involute math here.

---

## Automated tests

### Axis geometry

Test:

- exactly parallel lines;
- anti-parallel direction vectors;
- near-parallel lines inside tolerance;
- near-parallel lines outside tolerance;
- intersecting lines;
- skew lines;
- shortest distance;
- angle calculation.

### Spur gear math

Test:

- pitch diameter;
- pitch radius;
- base radius;
- outside radius;
- root radius;
- circular pitch;
- tooth angular pitch;
- backlash handling.

### Involute

Test:

- point at base circle;
- monotonic radial growth;
- symmetry between left/right flanks;
- finite values across supported domain.

### Pair solver

Test:

- valid exact center-distance pair;
- invalid center-distance pair;
- valid ratio search;
- multiple ratio candidates;
- no-solution case;
- deterministic ranking.

### Edge cases

Test:

- very small valid module;
- invalid zero module;
- negative backlash;
- invalid tooth count;
- floating-point tolerance boundaries.

---

## Manual Fusion test matrix

Test at least these cases in Fusion:

### Case A — simple exact pair

```text
module: 1.5
z1: 20
z2: 40
center distance: 45 mm
pressure angle: 20 deg
```

Expected:

- both gears generate;
- pitch geometry fits selected axes;
- components are separate;
- teeth are correctly phased.

### Case B — reversed axis directions

Use the same physical shaft locations but reverse one construction-axis direction.

Expected:

- placement remains correct;
- generation does not mirror or invert unexpectedly.

### Case C — non-parallel axes

Expected:

- generation blocked;
- clear unsupported-geometry message.

### Case D — incompatible center distance

Expected:

- generation blocked;
- message contains actual and required distance.

### Case E — run twice

Generate twice in one Fusion session.

Expected:

- no stale selections;
- no duplicate event-handler problems;
- no command-state corruption.

---

## Logging

Provide lightweight diagnostic logging for development.

Useful log data:

- selected entity types;
- extracted axis origins/directions;
- detected relationship;
- center distance;
- solved tooth counts;
- calculated transforms;
- Fusion API failure details.

Do not spam end users with developer logs.

---

## Documentation deliverables

Before Milestone 01 is considered complete, create/update:

```text
README.md
docs/architecture.md
docs/gear-math.md
docs/fusion-api-notes.md
docs/development.md
```

At minimum, `docs/development.md` must explain how to install/load the add-in in Fusion for testing.

---

## Definition of done

Milestone 01 is complete only when all of the following are true:

- repository structure exists;
- add-in can be loaded in Fusion;
- `Gear Pair` command appears in the UI;
- two construction axes can be selected;
- parallel relationship is detected correctly;
- center distance is derived from geometry;
- tooth-count mode works;
- ratio mode works for supported cases;
- involute gears are generated;
- gears are separate components;
- gears are centered on selected axes;
- gear axes align with selected shaft axes;
- tooth phase is suitable for meshing;
- invalid inputs fail cleanly;
- pure-core automated tests pass;
- required manual Fusion test cases pass;
- docs describe assumptions and known limitations.

---

## Explicit non-goals for Codex

Do not, during this milestone:

- implement bevel gears;
- implement worm gears;
- implement helical gears;
- create gearbox housings;
- add motors or bearings;
- add FEA;
- add ISO/AGMA claims;
- optimize for every possible Fusion entity type;
- redesign the entire architecture unless a concrete blocker is found.

Finish the vertical slice first.

---

## First Codex task

Start with:

1. create the repository skeleton from `AGENTS.md`;
2. create the pure-core geometry package;
3. implement and test:
   - vector normalization;
   - line/axis representation;
   - line-to-line shortest distance;
   - parallel detection;
   - intersecting detection;
   - skew detection;
   - angle between axes;
4. do not write Fusion model-generation code yet;
5. do not integrate Study Gears yet;
6. run the tests;
7. report:
   - files created;
   - tests run;
   - test results;
   - assumptions;
   - next recommended task.

This first task should produce a clean mathematical foundation before any Fusion API complexity is introduced.

### Second Codex task

After the first task passes:

1. inspect the current Study Gears repository by Osamu Takeuchi;
2. verify and document its current license;
3. locate the spur/involute geometry implementation;
4. summarize which parts are suitable for reuse or adaptation;
5. propose the smallest integration boundary compatible with this project's pure-core architecture;
6. do not copy code yet unless the license and integration plan are both clear;
7. report:
   - relevant upstream files;
   - reusable algorithms/components;
   - license obligations;
   - recommended adaptation strategy;
   - risks or assumptions.

Only after that review should Codex implement or adapt the spur/involute generator.
