# AGENTS.md

## Mission

Build a production-quality Autodesk Fusion add-in for designing gear pairs and, later, complete gear trains from existing 3D mechanism geometry.

The core workflow is geometry-driven:

1. The user defines shaft axes or other placement references in Fusion.
2. The add-in analyzes their spatial relationship.
3. The add-in determines which transmission families are geometrically valid.
4. The user supplies engineering constraints such as ratio, module, pressure angle, and backlash.
5. The add-in generates correctly positioned gear components.

The mechanism layout is the source of truth. Generated gears must adapt to it.

---

## Current milestone

Implement only an **external involute spur gear pair between two parallel shaft axes**.

The milestone is complete when a user can:

1. create two parallel construction axes in Fusion;
2. run a `Gear Pair` command;
3. select both axes;
4. enter a valid spur-gear definition;
5. generate two separate gear components;
6. find both gears centered and aligned on the selected axes;
7. see correct pitch geometry and tooth clocking for meshing;
8. repeat the operation reliably.

Do not expand scope to helical, bevel, worm, hypoid, planetary, or automatic gearbox design until this milestone works.

---

## Long-term roadmap

Add transmission families incrementally:

1. external spur
2. internal spur
3. helical
4. bevel
5. crossed helical
6. worm and worm wheel
7. multi-stage gear trains
8. optional automatic transmission-type recommendation

Do not implement speculative abstractions for future families unless existing code genuinely needs them.

---

## Technical baseline

- Target: Autodesk Fusion add-in
- Preferred language: Python
- Use the official Autodesk Fusion API as the primary API reference.
- Build an add-in, not a one-shot script.
- Keep pure mathematics runnable without Fusion installed.
- Treat Fusion runtime behavior as unverified until actually tested in Fusion.

Fusion uses the same API for scripts and add-ins, but add-ins persist for the Fusion session and can register UI commands. Design accordingly.

---

## Architecture

Keep these layers separate.

### `core`

Must not import `adsk`.

Contains:

- vector and line geometry
- axis classification
- involute math
- spur-gear dimensions
- tooth-count and ratio solving
- geometric validation
- tolerances

### `fusion`

May import `adsk`.

Contains:

- entity selection
- Fusion unit conversion
- construction/reference extraction
- sketch and component creation
- transformations
- feature/BRep creation
- parameter creation
- event wiring
- UI registration and cleanup

### `commands`

Orchestrates `core` and `fusion`.

Do not put gear equations inside Fusion event handlers.

---

## Preferred repository layout

```text
/
├─ AGENTS.md
├─ README.md
├─ LICENSE
├─ THIRD_PARTY_NOTICES.md
├─ docs/
│  ├─ architecture.md
│  ├─ gear-math.md
│  ├─ fusion-api-notes.md
│  └─ development.md
├─ src/
│  └─ fusion_gear_designer/
│     ├─ addin.py
│     ├─ commands/
│     ├─ core/
│     │  ├─ geometry/
│     │  ├─ gears/
│     │  └─ solver/
│     └─ fusion/
└─ tests/
```

Adapt the layout only for a concrete reason.

---

## Geometry-first rules

Never ask the user to enter a value that can be robustly derived from selected Fusion geometry.

Examples:

- derive shaft direction from selected axes;
- calculate center distance from the axes;
- later, calculate shaft angle from intersecting axes;
- later, classify axis pairs as parallel, intersecting, or skew.

Manual overrides may exist later, but geometry-derived values are the default.

Use tolerances for geometric comparisons. Never test floating-point vectors or distances using exact equality.

Normalize direction vectors before angular calculations.

Centralize geometric tolerances.

---

## Axis classification

The geometry layer should support these classifications even before every transmission type is implemented.

### Parallel

Potential families:

- spur
- helical

### Intersecting

Potential families:

- bevel
- crown where appropriate

The shaft angle must be derived from the selected axes.

### Skew

Potential families:

- crossed helical
- worm

Do not automatically choose a skew-axis transmission without additional design criteria.

For the current milestone, only `parallel` is supported. Other classifications must fail cleanly with a useful message.

---

## Spur gear model

Use standard involute terminology and keep equations centralized.

At minimum model:

- module `m`
- tooth count `z`
- pressure angle `alpha`
- pitch diameter
- pitch radius
- base-circle radius
- outside radius
- root radius
- circular pitch
- tooth thickness
- backlash

For a standard external spur gear:

```text
d = m * z
```

For a standard external pair without profile shift:

```text
a = m * (z1 + z2) / 2
```

Record conventions and equations in `docs/gear-math.md`.

Do not silently introduce profile shift merely to force incompatible geometry to fit.

---

## Pair-solving modes

Support these modes separately.

### Tooth-count-driven

Inputs:

- `z1`
- `z2`
- module
- pressure angle
- backlash

Validate that the theoretical center distance matches the selected shaft spacing within tolerance.

### Ratio-driven

Inputs:

- desired ratio
- module
- pressure angle
- backlash

Search integer tooth-count pairs that:

- fit the available center distance;
- approximate the requested ratio;
- satisfy minimum geometry constraints.

When several solutions are valid, return several candidates. Do not pretend an arbitrary one is uniquely correct.

---

## Placement is a first-class requirement

A generated pair is not correct merely because each individual gear has the right tooth profile.

Each gear must:

- be centered on its selected shaft axis;
- have its rotation axis aligned with that shaft;
- be placed at the intended axial location;
- have the correct relative angular phase so teeth mesh rather than overlap.

Keep explicit functions for:

- coordinate-frame construction;
- axis-to-component transforms;
- relative tooth clocking.

Do not use unexplained angular offsets.

---

## Fusion model rules

Create each gear as a separate component.

Use deterministic names, for example:

```text
Gear_A_z20_m1.5
Gear_B_z40_m1.5
```

Prefer editable parametric Fusion features where practical.

Avoid producing opaque monolithic geometry when a reasonably editable construction is possible.

Do not modify unrelated user geometry.

If generated objects need metadata for future regeneration, store it explicitly and document the format.

---

## MVP UI

The command should conceptually expose:

```text
Create > Gear Pair

Input axis:        [Select]
Output axis:       [Select]

Detected:
  Relationship:    Parallel
  Center distance: 45.000 mm

Definition:
  Tooth counts / Desired ratio

Module:            1.5 mm
Pressure angle:    20 deg
Backlash:          0.15 mm

Input teeth:       20
Output teeth:      40

[Generate]
```

Show derived values before generation where practical.

Reject invalid combinations early and explain why.

Prefer:

> Selected axes are 42.0 mm apart, but a 20T/40T pair at module 1.5 requires 45.0 mm.

over:

> Invalid input.

---

## Units

Be explicit about units at every boundary.

Core conventions:

- mechanical lengths: millimeters
- mathematical angles: radians

Convert to/from Fusion units only in the Fusion adapter.

Never rely on undocumented unit assumptions.

---

## Testing

Every pure mathematical feature requires automated tests.

At minimum cover:

- parallel-axis detection
- intersecting-axis detection
- skew-axis detection
- shortest distance between 3D lines
- angle between axes
- spur-gear radii
- involute point generation
- center-distance validation
- tooth-count solving
- ratio error
- tolerance boundaries

Add a regression test for every confirmed mathematical bug.

Fusion-only behavior must have a documented manual test procedure.

---

## Manual Fusion validation

For changes affecting model creation, validate in Fusion:

1. create a test design;
2. create two construction axes with known spacing;
3. start the add-in;
4. run `Gear Pair`;
5. select both axes;
6. enter known-valid values;
7. generate;
8. verify:
   - two separate components exist;
   - both are centered on the selected axes;
   - axes align correctly;
   - pitch circles are positioned correctly;
   - initial tooth phase permits meshing;
   - unrelated geometry is untouched;
   - the command can be run again without stale state.

Do not claim Fusion integration is verified unless it was actually run in Fusion or the user supplied successful runtime evidence.

---

## Fusion API rules

When an API detail is uncertain:

1. check current official Autodesk Fusion API documentation;
2. inspect official samples when available;
3. do not invent API calls from memory;
4. isolate version-sensitive behavior.

Clean up event handlers and UI objects when the add-in stops.

Avoid broad exception handlers that hide tracebacks.

---

## Study Gears as the reference implementation

Use **Study Gears by Osamu Takeuchi** as the preferred reference implementation for gear geometry where its license and implementation are compatible with this project.

The intended division of responsibility is:

### Study Gears should be preferred for

- involute tooth geometry
- standard spur-gear geometry
- helical-gear geometry
- bevel-gear geometry
- worm and worm-wheel geometry
- crown-gear geometry
- established gear-specific mathematical conventions already implemented and tested upstream

### This project must own

- 3D shaft-axis analysis
- parallel/intersecting/skew classification
- transmission-family selection
- fixed-geometry pair solving
- ratio-driven solution search
- 3D placement
- component transforms
- tooth clocking between generated gears
- Fusion command UX
- integration architecture
- regeneration/metadata strategy
- project-specific validation and tests

Do not rewrite complex gear geometry from scratch merely to avoid using Study Gears when a compatible, understandable upstream implementation already exists.

However, do not import Study Gears wholesale as an opaque dependency. Prefer to:

1. inspect and understand the relevant upstream implementation;
2. isolate the minimum reusable mathematical or geometry-generation logic;
3. adapt it behind this project's own clean interfaces;
4. keep Study Gears-specific code separate from project-specific solver and placement code;
5. add regression tests around adapted behavior.

Before reusing code:

1. verify the current upstream license;
2. preserve all required copyright and license notices;
3. record reused or adapted code in `THIRD_PARTY_NOTICES.md`;
4. document important upstream files or algorithms used;
5. note substantial local modifications.

If the upstream implementation conflicts with this project's geometry-driven architecture, keep the upstream gear mathematics but replace its placement/UI assumptions with project-specific logic.

Never copy proprietary Autodesk Marketplace add-in code.

Never assume code found online is reusable without checking its license.

---

## Documentation policy

Keep `AGENTS.md` concise. It is a map and rule set, not the project encyclopedia.

Use:

- `README.md` for setup and user-facing overview;
- `docs/architecture.md` for architecture decisions;
- `docs/gear-math.md` for formulas and engineering assumptions;
- `docs/fusion-api-notes.md` for Fusion-specific discoveries;
- `docs/development.md` for development and manual-test workflows.

Update relevant documentation in the same change when behavior or assumptions change.

---

## Coding style

Prefer clear, boring Python.

Use:

- type hints in pure core code;
- dataclasses for value objects where useful;
- small pure functions;
- explicit names;
- focused modules;
- docstrings for non-obvious mathematics.

Avoid:

- giant command-handler files;
- duplicated equations;
- hidden global state;
- unexplained constants;
- premature framework-building;
- clever metaprogramming.

---

## Engineering limits

Until explicitly expanded:

- gears are treated as rigid;
- elastic tooth deflection is ignored;
- manufacturing errors are not modeled;
- strength and fatigue certification are out of scope;
- backlash is a geometric input, not a manufacturing guarantee;
- generated geometry is intended for design/prototyping, not automatic safety certification.

Never claim a generated transmission is safe for a load without separate engineering analysis.

---

## Work sequence

Unless the user explicitly reprioritizes, work in this order:

1. repository skeleton
2. pure 3D axis geometry
3. axis-classification tests
4. spur-gear mathematical model
5. involute profile generator
6. spur-pair solver for fixed parallel axes
7. Fusion selection adapter
8. Fusion component/placement adapter
9. `Gear Pair` command UI
10. manual Fusion validation
11. regression fixes and stabilization

Do not skip directly to a broader gear family because it looks more interesting.

---

## Change discipline

Before coding:

1. inspect existing architecture;
2. identify the correct layer;
3. understand the relevant tests and docs.

After coding:

1. run relevant automated tests;
2. add tests for new core behavior;
3. report exactly what was tested;
4. list manual Fusion checks still required;
5. update documentation if assumptions changed.

Do not report untested behavior as working.
