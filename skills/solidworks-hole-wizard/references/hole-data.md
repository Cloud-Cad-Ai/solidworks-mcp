# Hole Wizard reference data

## Enum values (verified)

| Item | Values |
|---|---|
| GenericHoleType | Hole = 2, Tap = 4 |
| StandardIndex | ISO = 8 |
| FastenerTypeIndex | ISO Drill sizes = 143, ISO Tapped hole = 147. The dowel-hole enum could not be resolved, so use drill sizes plus H7 metadata. |
| EndType (swEndConditions_e) | Blind = 0, Through All = 1 |
| CosmeticThreadType (V7) | 1 = with callout, 2 = without callout, 0 = none |
| ThreadEndCondition (V8) | 0 = blind, 1 = through |
| SSize | Must match the standard table exactly: `M6x1.0`, `Ø15.0`, `Ø8.0` (Ø is U+00D8) |
| ThreadClass | `6H` is accepted and stored for ISO |

For other standards (ANSI, DIN) or types (counterbore, countersink), look up the enum with `solidworks-api`, probe on a throwaway part, read the definition back, and add the verified values here.

## HoleWizard5 argument map

`IFeatureManager.HoleWizard5(GenericHoleType, StandardIndex, FastenerTypeIndex, SSize, EndType, Diameter, Depth, Length, V1..V12, ThreadClass, RevDir, FeatureScope, AutoSelect, AssemblyFeatureScope, AutoSelectComponents, PropagateFeatureToParts)`

### Tapped hole (type 4)

| Arg | Meaning |
|---|---|
| Diameter | Tap drill diameter |
| Depth | Tap drill depth to the shoulder (the cone is extra) |
| Length | Pass the thread depth too; it does not set it |
| V1 | Thread depth (the only slot that sets it) |
| V2–V5 | Near/far countersink diameter and angle; pass −1 |
| V6 | Drill-point angle: 2.0594885 = 118° |
| V7 | Cosmetic thread type: 1 = with callout |
| V8 | Thread end condition: 0 blind, 1 through |
| V9–V12 | −1 |

Blind M6, thread 12, drill Ø5 × 18:

```json
[4,8,147,"M6x1.0",0,0.005,0.018,0.012, 0.012,-1,-1,-1,-1,2.0594885,1,0,-1,-1,-1,-1, "6H",false,true,true,true,true,false]
```

Through M6 in a 16 mm plate:

```json
[4,8,147,"M6x1.0",1,0.005,0.016,0.016, 0.016,-1,-1,-1,-1,2.0594885,1,1,-1,-1,-1,-1, "6H",false,true,true,true,true,false]
```

### Plain hole (type 2)

V1 is the screw fit and V2 the drill angle. Passing −1 in every V slot makes the call fail. Ø15 through all:

```json
[2,8,143,"Ø15.0",1,0.015,0.016,0, 1,2.0943951,0,0,0,0,0,0,0,-1,-1,-1, "",false,true,true,true,true,false]
```

## Metric coarse threads and ISO 273 clearance (mm)

| Thread | Tap drill | Fine / medium / coarse clearance |
|---|---|---|
| M3 | 2.5 | 3.2 / 3.4 / 3.6 |
| M4 | 3.3 | 4.3 / 4.5 / 4.8 |
| M5 | 4.2 | 5.3 / 5.5 / 5.8 |
| M6 | 5.0 | 6.4 / 6.6 / 7.0 |
| M8 | 6.8 | 8.4 / 9.0 / 10.0 |
| M10 | 8.5 | 10.5 / 11.0 / 12.0 |
| M12 | 10.2 | 13.0 / 13.5 / 14.5 |
| M14 | 12.0 | 15.0 / 15.5 / 16.5 |
| M16 | 14.0 | 17.0 / 17.5 / 18.5 |
| M20 | 17.5 | 21.0 / 22.0 / 24.0 |

## H7 hole limits (lower deviation 0)

| Nominal size (mm) | Upper deviation |
|---|---|
| over 3 to 6 | +0.012 |
| over 6 to 10 | +0.015 |
| over 10 to 18 | +0.018 |
| over 18 to 30 | +0.021 |

## Volume check example

On a plate 110 × 65 × 16, four Ø15 through holes plus two blind M6 holes (Ø5 drill 18 and 15) removed 363.26 + 304.35 mm³: 102,962.3 → 102,294.6 mm³. The Ø5 drill-point cone alone is 9.83 mm³.
