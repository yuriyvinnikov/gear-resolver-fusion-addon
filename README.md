# Fusion Gear Designer

Geometry-driven gear design for Autodesk Fusion.

## What this project is

Fusion Gear Designer is a planned Autodesk Fusion add-in that generates gear pairs from existing mechanism geometry.

Instead of generating a gear first and then manually moving it into position, the add-in treats the user's shaft layout as the source of truth:

1. select shaft axes in Fusion;
2. analyze their spatial relationship;
3. determine which transmission types are geometrically valid;
4. enter design constraints such as ratio, module, pressure angle, and backlash;
5. generate correctly positioned gear components.

The long-term goal is to support multiple transmission families while keeping one consistent workflow.

---

## Core idea

The desired interaction is:

```text
Select shaft axis A
Select shaft axis B
        ↓
Analyze axis relationship
        ↓
Parallel / Intersecting / Skew
        ↓
Determine valid transmission families
        ↓
Solve dimensions
        ↓
Generate both gears in correct 3D position
```

For example:

```text
Parallel axes
    ↓
Spur / Helical

Intersecting axes
    ↓
Bevel / Crown

Skew axes
    ↓
Crossed Helical / Worm
```

The first milestone intentionally supports only a simple subset of this concept.

---

## First milestone

The first working milestone is:

> Generate one external involute spur gear pair between two existing parallel shaft axes.

The user must be able to:

1. create two parallel construction axes in Fusion;
2. run a `Gear Pair` command;
3. select both axes;
4. enter valid spur-gear parameters;
5. generate two separate gear components;
6. get both gears correctly centered and aligned on those axes;
7. get correct relative tooth phase for meshing.

Detailed requirements are in:

[`MILESTONE_01.md`](./MILESTONE_01.md)

---

## Planned roadmap

The project should grow incrementally:

1. external spur gear pair;
2. internal spur gear pair;
3. helical gear pair;
4. bevel gear pair;
5. crossed-helical pair;
6. worm and worm wheel;
7. multi-stage gear trains;
8. optional automatic transmission-type recommendation.

No later stage should be started until the current stage is stable enough to build on.

---

## Design philosophy

### Geometry-driven

Do not ask the user to enter information that can be reliably derived from Fusion geometry.

Examples:

- shaft direction;
- center distance;
- shaft angle;
- intersection status;
- shortest distance between skew axes.

### Parametric where practical

Generated geometry should remain understandable and editable inside Fusion.

Avoid unnecessary opaque BRep generation when equivalent parametric Fusion features can be used reliably.

### Engineering-aware

The add-in should validate incompatible inputs rather than silently generating invalid geometry.

Examples:

- impossible center distance for a requested module and tooth counts;
- unsupported axis relationship;
- tooth counts below supported geometric limits;
- invalid backlash or pressure-angle values.

### Deterministic

Identical inputs should produce identical results.

### Incremental

Do one transmission family properly before adding another.

---

## Architecture overview

The project is split into three major areas.

### Pure core

No Autodesk imports.

Contains:

- 3D line and axis geometry;
- axis classification;
- involute mathematics;
- spur-gear dimensions;
- tooth-count solving;
- ratio solving;
- validation;
- tolerances.

This code must be unit-testable with ordinary Python.

### Fusion adapter

Imports `adsk`.

Contains:

- command registration;
- entity selection;
- Fusion unit conversion;
- Fusion geometry extraction;
- component creation;
- sketches and features;
- transformations and placement;
- event handling;
- UI cleanup.

### Commands

Coordinates the pure core and Fusion adapter.

Gear equations must not live inside event handlers.

---

## Suggested repository layout

```text
/
├─ AGENTS.md
├─ README.md
├─ MILESTONE_01.md
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
│     │  └─ gear_pair/
│     ├─ core/
│     │  ├─ geometry/
│     │  ├─ gears/
│     │  └─ solver/
│     └─ fusion/
└─ tests/
```

---

## Technology

Preferred implementation:

- Python
- Autodesk Fusion API
- standard Python testing tools for pure-core code

The pure-core layer must not import `adsk`.

Fusion-specific code should be kept as thin as practical.

---

## Development strategy

The recommended order is:

1. create repository skeleton;
2. implement pure 3D axis geometry;
3. test parallel/intersecting/skew classification;
4. inspect Study Gears spur/involute geometry and identify reusable code or algorithms;
5. adapt the spur-gear math behind project-owned interfaces;
6. adapt the involute profile generation and add regression tests;
7. implement fixed-axis pair solver;
8. implement Fusion selection adapter;
9. implement component creation and placement;
10. implement command UI;
11. test manually in Fusion;
12. fix integration issues before expanding scope.

---

## Testing

### Automated tests

At minimum:

- shortest distance between 3D lines;
- parallel-axis detection;
- intersecting-axis detection;
- skew-axis detection;
- angle between axes;
- spur-gear radii;
- involute point generation;
- center-distance validation;
- tooth-count solving;
- ratio error;
- tolerance boundaries.

### Fusion-side manual tests

Fusion integration must be manually validated for:

- axis selection;
- component placement;
- orientation;
- tooth phase;
- repeat execution;
- no corruption of unrelated model geometry.

A successful Python test suite does not prove Fusion integration works.

---

## Study Gears reference implementation

**Study Gears by Osamu Takeuchi is the preferred reference implementation for gear-specific geometry.**

The project should reuse or adapt compatible upstream work where it materially improves correctness and reduces duplicated effort, especially for:

- involute and spur geometry;
- helical gears;
- bevel gears;
- worm and worm-wheel geometry;
- crown gears.

Fusion Gear Designer still owns the parts that make this project distinct:

- 3D shaft-axis analysis;
- parallel/intersecting/skew classification;
- transmission solving;
- ratio-driven candidate search;
- placement and transforms;
- relative tooth clocking;
- Fusion UX and project architecture.

The goal is not to fork Study Gears wholesale. The goal is to use its proven gear mathematics behind this project's own interfaces.

Any reused or adapted code must:

- have a compatible license;
- preserve required notices;
- be recorded in `THIRD_PARTY_NOTICES.md`;
- be understood before integration;
- have local regression tests;
- remain separated from project-specific placement and solver logic.

Do not copy proprietary Marketplace add-in code.

---

## Engineering scope

The add-in is initially intended for geometry generation and prototyping.

Unless separately implemented and validated, it does not provide:

- gear strength certification;
- fatigue-life prediction;
- bearing-life calculations;
- structural simulation;
- thermal analysis;
- manufacturing certification;
- safety guarantees.

Generated geometry must not be presented as automatically safe for a real load case.

---

## Current status

The first implementation task is complete: repository skeleton, pure 3D vector
and axis geometry, tolerance-aware classification, and automated geometry tests.

Gear generation, Study Gears integration, pair solving and the Fusion command
are not implemented yet. Milestone 01 is not complete, and Fusion runtime
behavior has not been validated.

Run tests from the project root (Python 3.10+; PowerShell):

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s tests -v
```

See [development](docs/development.md), [architecture](docs/architecture.md),
[math conventions](docs/gear-math.md) and [Fusion API notes](docs/fusion-api-notes.md).
The project license still needs to be selected by its owner; no third-party
gear code has been incorporated.

Start with [`MILESTONE_01.md`](./MILESTONE_01.md) and follow the repository rules in [`AGENTS.md`](./AGENTS.md).

Do not begin later transmission families yet.
