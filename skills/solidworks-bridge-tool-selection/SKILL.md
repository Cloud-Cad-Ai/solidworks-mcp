---
name: "solidworks-bridge-tool-selection"
description: "Use before any SolidWorks MCP modeling or assembly work to pick the tool or API call that actually works through this bridge and avoid known failures."
---

# SolidWorks bridge: which call to use

The single home for bridge facts learned from real runs (SOLIDWORKS 2026 via the remote-devices solidworks MCP). Prefer the Use column; the Avoid column failed or misbehaved. The build method (what to model, assembly order, mate schemes) is in `solidworks-assembly-build`. When a run finds a new fact, add it here rather than to another skill.

## What the bridge cannot do (do not retry)
- A method with a `ref`/out parameter fails with DISP_E_TYPEMISMATCH whatever you pass (0, null, [0]): AddMate2/3/4/5, AddDistanceMate, ActivateDoc2, OpenDoc6, RunMacro2, GetMaterialPropertyName2.
- COM objects cannot be passed as arguments (handle strings and `{"Id":..}` dicts arrive as plain values; ISldWorks.IsSame returns 0), so IFeature.ModifyDefinition, CreateMate(data), EntitiesToMate and gear or limit mates through the API are out.
- Methods returning arrays (Object[], Double[]) return handles that cannot be read: GetPartBox, transforms, sketch-segment arrays, the interference manager's component and volume lists.
- IEquationMgr.Delete and SetEquationAndConfigurationOption return -1 and change nothing, linked or unlinked, in parts and assemblies.
- For any of these: design around it (alternatives below), or use `solidworks-macro-fallback` only if the user agrees to macros. Otherwise record it as an open item.

## Session safety
- Call `active_document` before the first batch and after any error; "RPC server unavailable" means SolidWorks has crashed or hung: ask the user to restart it, then re-read the model state.
- **A rejected, refused or timed-out call may still have executed.** Re-read the state (feature tree, mate list) before retrying, or you create duplicates.
- One document change per batch: chaining CloseDoc / NewDocument across parts in one batch has crashed SolidWorks. One part per batch.
- `batch` holds at most 32 steps; `$n` references the handle returned by step n. `save_as` and `set_units` are refused inside a batch: use `save` with a full path inside a batch, and call `set_units` on its own.

## Documents
| Task | Use | Avoid / note |
|---|---|---|
| Template path | app GetUserPreferenceStringValue(8) part, (9) assembly | - |
| New doc | app NewDocument(template,0,0,0), then set_units(4) for MMGS (own call) | set_units inside a batch |
| Doc handle | Re-read with active_document after any open, activate or close | Reusing old handles; they go stale |
| Open file | app OpenDoc(path,1) part or (path,2) assembly, one call at a time | Parallel OpenDoc calls (device timeout); open_or_activate_document (failed on saved files) |
| Switch doc | app ActivateDoc(title) | ActivateDoc2 (ref param) |
| Close | app CloseDoc(title) | CloseAllDocuments (refused) |
| Save | save(path) | save_as inside a batch (refused) |
| Export | save(path) with .STEP or .jpg writes a copy; doc stays native | - |

## Sketching
- Plane: create_sketch(Front) is reliable. For any other plane: Extension SelectByID2("Right Plane","PLANE",0,0,0,false,0,null,0) then SketchManager InsertSketch(true). create_sketch(Right) landed on Front.
- **Axis mapping:** on the Right Plane, sketch x = −model Z (sketch y = model Y). On a plane parallel to Top, sketch y = −model Z (sketch x = model X). Front: sketch x, y = model X, Y. Confirm on a scratch part for any other plane.
- Exit or delete a sketch: SketchManager InsertSketch(true); select "SketchN" type SKETCH then doc EditDelete.
- Circles: add_sketch_entity(circle) returns a handle that dimension accepts.
- Rectangles: add_sketch_entity(rectangle) (corner, no construction lines). Its returned handle may not dimension; get edge handles with SelectByID2("","SKETCHSEGMENT",x,y,0,...) then SelectionManager GetSelectedObject6(1,-1).
- Avoid CreateCenterRectangle: its diagonal construction lines get picked by coordinate selection, so the dimension lands on a diagonal. Check a picked segment with get_property ConstructionGeometry and invoke GetLength.
- Symmetric lug or eye: SketchManager CreateSketchSlot(0,0,width,x1,y1,0,x2,y2,0,0,0,0,1,true). Auto dims: D1 = width, D2 = centre-to-centre length. Start point stays at the origin.
- **Units:** the `dimension` tool takes DOCUMENT units (mm in MMGS) despite saying meters (0.32 gave 0.32 mm). Sketch coordinates and feature depths through `invoke` and `extrude` are meters.
- IModelDoc AddDimension2 / AddVerticalDimension2 via invoke returned nothing. Only single-entity dims via the dimension tool work, so design sketches to need no position dims: draw at exact coordinates generated from the design state, centre on the origin, place parts by mates.

## Features
- Blind boss: extrude tool (depth in meters, from sketch plane along normal).
- Mid-plane boss: FeatureManager FeatureExtrusion2(true,false,false,6,0,depth,0.01,false,false,false,false,0,0,false,false,false,false,true,true,true,0,0,false).
- Through-all cut both sides: FeatureManager FeatureCut4(false,false,false,1,1,0.01,0.01,false,false,false,false,0,0,false,false,false,false,false,true,true,true,true,false,0,0,false,false).
- **Cut direction:** with FeatureCut4, Dir = false cuts opposite to the sketch-plane normal; Dir = true along it. A keyway cut the wrong way removes the wrong side or misses: check the volume change.
- Offset-start cut (e.g. a keyway that starts part-way along a shaft): FeatureCut4 with start condition T0 = 3 (offset) and the StartOffset value; describe_api it once before use.
- Revolve: one closed half-profile on a plane through the axis, with a centreline on the axis; expected volume = Σ π/4·(D²−d²)·L.
- Offset plane: select base plane, FeatureManager InsertRefPlane(8,dist,0,0,0,0). Dim name D1@PlaneN.
- Read a value: doc Parameter("D1@Sketch1") then get_property SystemValue (meters).
- Delete a feature: doc FeatureByName("Name") → Feature.Select2(false,0) → doc EditDelete.
- Feature and sketch names keep counting after a delete (Sketch2 deleted, next is Sketch3). List the feature tree before writing equations or deleting by name.
- Materials: see `set-material`; unknown names fail silently.

## Equations / global variables
- doc GetEquationMgr; set_property FilePath; set_property LinkToFile true; invoke UpdateValuesFromExternalEquationFile; then Add2(-1, "\"D1@Sketch1\" = \"Bore\"", true). Values in the file are mm.
- Dimension equations added in a part are NOT written back to the shared file.
- Equations cannot be deleted (see above), and deleting a feature or mate leaves its equation behind, broken (Status -1). Never put an equation on something you may delete. Get the dimension right first; if wrong, close without saving and rebuild the document.

## Assembly
- Parts (or sub-assemblies) must be loaded before IAssemblyDoc AddComponent5(path,0,"",false,"",x,y,z). It places the component by its **bounding-box centre**, not its origin, so position by mates.
- The first inserted component is auto-fixed off-origin. Before mating it: SelectByID2("Comp-1@AsmName","COMPONENT",...) then assembly UnfixComponent. Missing this caused an unsolvable coincident mate (55 mm off) and false interference.
- Mates: legacy assembly AddMate(type, align, flip, dist, angle) after selecting two entities with mark 1. Types: 0 coincident, 1 concentric, 5 distance, 6 angle. Align: 0 aligned, 1 anti-aligned, 2 closest.
  - Plane-to-plane distance: align 0 (aligned).
  - Axis-to-plane distance: align 2 (closest); aligned returns error 47 (ill-defined).
  - For a rotated standard part, choose aligned/anti-aligned per plane pair so the mapped frame stays right-handed.
- Plane selection names: "Front Plane@Comp-1@AsmName" type PLANE; assembly planes just "Front Plane"; inside a sub-assembly "Front Plane@Part-1@SubAsm-1@AsmName".
- A distance mate can solve to the wrong side with no error. Fix: doc FeatureByName("DistanceN") then GetSpecificFeature2 then set_property Flipped; if that doesn't clear an error, delete and recreate with the other align option. Confirm with a view or section.
- Mate dim names: D1@DistanceN, so assembly equations can drive positions.
- **Mate status:** mates don't list under the Mates folder through `list`. Walk them: doc FeatureByName("Mates") → GetFirstSubFeature → loop GetNextSubFeature, reading Name and GetErrorCode (0 = ok). Decode with get_enum swFeatureError_e (46 over-defined, 47 ill-defined). Check after every new mate. Mates inside a sub-assembly are checked in the sub-assembly document.
- Delete a mate: FeatureByName("CoincidentN") → Select2(false,0) → EditDelete.
- Suppress / unsuppress a component: select it, then EditSuppress2 / EditUnsuppress2. EditUnsuppress2 can return false without unsuppressing: read the component's suppression state back before saving. Hide/show the same way, and restore before saving.
- Gear and limit mates need AddMate5 (ref param) or object arguments: not possible directly. See `solidworks-assembly-build` 5.2 and 5.3.

## Checks
- Interference: check_interference, or doc InterferenceDetectionManager with TreatCoincidenceAsInterference = false to ignore line-to-line fits; read the count. Results are cached: call Done() and get a fresh manager before recounting. The pair list is an unreadable array, so find pairs by suppressing groups and recounting.
- Sections: `create_section_view` through the shaft axes or gear mid-plane, then `capture_view` (or save a .jpg) to inspect inside a housing.
- mass_properties (volume, CG) against a hand calculation catches a wrong dimension; mass ÷ volume catches a missing material.
- capture_view front/top/isometric after each major step; it resets zoom. Keep images few and small.