# concept.json schema

All lengths mm, masses kg, forces N, torques N·m, times s. Coordinates: +X length (left→right in front view), +Y depth (front→back), +Z up. Fields marked * are required for a valid sheet; everything else is optional but expected for a complete hand-off.

```jsonc
{
  "title": "Pick-and-place cell for 2 kg castings",   // * sheet title
  "concept_id": "MC-001",          // stable id across revisions
  "rev": "A",                       // bump on every revision
  "date": "2026-10-16",
  "author": "concept agent",
  "summary": "Two-axis gantry with pneumatic Z and vacuum gripper …",  // 1–3 sentences

  "requirements": [                 // * from the spec, plus derived/assumed
    {"id": "R1", "text": "Throughput", "value": "≥ 600 parts/h (6 s cycle)", "source": "spec"},
    {"id": "R2", "text": "Payload mass", "value": "2.0 kg", "source": "spec"},
    {"id": "R9", "text": "Supply air", "value": "6 bar (5 bar min)", "source": "assumed"}
  ],
  "assumptions": [                  // * every default you picked, with why
    "Operator loads from the front (−Y); rear is against a wall.",
    "Positioning repeatability ±0.1 mm is sufficient (spec silent)."
  ],

  "morphology": [                   // function → options → chosen
    {"function": "Move X 800 mm", "options": ["belt", "ball screw", "rodless cylinder"], "chosen": "belt"}
  ],
  "concepts": [                     // 2–3 alternatives
    {"name": "A – Belt gantry", "description": "…", "pros": ["fast", "cheap"], "cons": ["belt stretch"]},
    {"name": "B – SCARA",       "description": "…", "pros": […], "cons": […]}
  ],
  "decision": {
    "criteria": [ {"name": "Cost", "weight": 0.3}, {"name": "Cycle time", "weight": 0.25} ],  // weights sum to 1
    "scores":   { "A – Belt gantry": {"Cost": 4, "Cycle time": 4}, "B – SCARA": {"Cost": 2, "Cycle time": 5} }  // 1–5
  },
  "selected_concept": "A – Belt gantry",   // must match a concepts[].name / scores key
  "selection_rationale": "Best weighted score; SCARA reach marginal for 800 mm.",

  "sizing": [                       // one row per sized element of the selected concept
    {"item": "X-axis motor", "formula": "T = (m·a + μmg)·r/η",
     "inputs": "m=12 kg, a=10 m/s², μ=0.01, r=0.0255 m, η=0.95",
     "result": "T_peak = 3.3 N·m", "selection": "400 W servo + 5:1 planetary", "margin": "SF 1.9"}
  ],

  "envelope": {"size": [1500, 1000, 2000], "origin": [0, 0, 0]},  // max allowed L×W×H, drawn dashed

  "geometry": [                     // * primitives of the SELECTED concept
    // box: pos = min corner [x,y,z], size = [dx,dy,dz]
    {"id": "base", "name": "Base plate", "type": "box", "pos": [0,0,0], "size": [1200,800,20], "group": "frame", "item": 1},
    // cylinder: pos = centre of the base end face, axis x|y|z, r, length along +axis
    {"id": "mx", "name": "X motor", "type": "cyl", "axis": "x", "pos": [-120,400,900], "r": 40, "length": 120, "group": "drive", "item": 4}
    // optional per primitive: "color": "#hex" overrides group colour
  ],
  "motions": [
    {"type": "linear", "from": [150, 400, 950], "to": [950, 400, 950], "label": "X 800 mm @ 1.5 m/s"},
    {"type": "rotary", "center": [600, 400, 300], "axis": "z", "r": 60, "label": "C ±180°"}
  ],

  "bom": [                          // * item numbers referenced by geometry[].item
    {"item": 1, "name": "Base plate", "qty": 1, "spec": "S355 20 mm, 1200×800", "make_buy": "make", "mass_kg": 151, "notes": ""},
    {"item": 9, "name": "Control cabinet", "qty": 1, "spec": "600×400×200", "make_buy": "buy", "not_drawn": true}
  ],
  "interfaces": [
    {"name": "Infeed conveyor", "type": "mechanical", "detail": "Part datum at X=150, Y=400, Z=850"},
    {"name": "Power", "type": "electrical", "detail": "400 VAC 3ph, 16 A"}
  ],
  "risks": [
    {"risk": "Belt stretch vs ±0.1 mm", "mitigation": "Steel-cord belt; verify with tension calc"},
    "Plain strings are also fine"
  ],
  "next_steps": ["Confirm part datum with upstream line", "Detail gantry beam in CAD"]
}
```

## Modelling tips

- Group colours: frame/structure grey, drive/motor orange, transmission gold, motion/guide blue, tooling/end_effector purple, payload/workpiece green, electrical/sensor red, pneumatic/hydraulic teal, guarding light grey.
- Use one primitive per real part where possible (it keeps BOM ↔ geometry 1:1). Patterns (4 legs, 2 rails) = separate primitives sharing the same `item`.
- Represent guarding as thin boxes (e.g. 5 mm) — or leave it out of `geometry` and mark the BOM line `not_drawn` if it would hide the mechanism.
- Draw the payload at its working position and, if useful, again at the other end of stroke with a lighter `color`.
- Gearmotors: box for the gearbox + cylinder for the motor, both `item` = the gearmotor's BOM line.
- Belt / chain: a thin box spanning between pulley centres; pulleys as short cylinders.
- Rotated parts aren't supported — model them axis-aligned at the position that best explains the concept and say so in assumptions if it matters.
