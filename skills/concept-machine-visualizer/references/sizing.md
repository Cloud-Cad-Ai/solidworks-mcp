# Back-of-envelope sizing reference

Concept-stage formulas and defaults. SI units throughout (m, kg, N, s, rad) unless noted; convert mm → m before plugging in. Record every calculation as a `sizing[]` row: item · formula · inputs · result · selection · margin.

## Contents
1. Default factors & efficiencies
2. Motion profiles
3. Linear axes: forces → motor torque (screw, belt, rack & pinion)
4. Rotary loads, inertia & gearing
5. Motor selection checks (stepper, servo, AC induction)
6. Pneumatics & hydraulics
7. Guides, bearings, shafts, keys
8. Structure: beams, plates, columns, bolts
9. Springs, cams, misc.
10. Typical material properties
11. Standard-size cheat sheet

---

## 1. Default factors & efficiencies

| Item | Typical value |
|---|---|
| Safety factor on motor torque / actuator force | 1.5–2.0 (2.0 if loads uncertain) |
| SF on yield, static structure (concept) | 2–3 |
| SF on fatigue / shock loads | 3–4, or apply shock factor 1.5–3 to load |
| Ball screw efficiency | 0.90 |
| Lead (trapezoidal/ACME) screw efficiency | 0.30–0.50 (self-locking below ~0.35) |
| Timing belt drive | 0.95 |
| Rack & pinion | 0.90–0.95 |
| Spur/helical gear stage | 0.97–0.98 per stage |
| Planetary gearbox | 0.90–0.95 (1–2 stages) |
| Worm gear | 0.40–0.85 (low ratio = higher η) |
| Chain drive | 0.95–0.97 |
| Friction coeff: linear rail (rolling) | 0.005–0.01 |
| Friction: plastic bushing / slide on steel | 0.1–0.25 |
| Friction: steel on steel dry | 0.15–0.3 |
| Friction: conveyor belt on slider bed | 0.3–0.4 |
| Friction: rolling resistance, PU wheel on concrete | Crr ≈ 0.01–0.02 |
| g | 9.81 m/s² |

## 2. Motion profiles

Point-to-point move of distance `s` in time `t`:

- **Triangular** (accel then decel, no cruise): `a = 4s / t²`, `v_max = 2s / t`
- **Trapezoidal 1/3-1/3-1/3** (common default): `v_max = 1.5·s / t`, `a = 4.5·s / t²`
- With given `v_max` and `a`: `t_acc = v/a`, `s_acc = v²/(2a)`; if `2·s_acc > s` the profile is triangular.
- **Cycle time** = Σ moves + dwell (gripping ~0.1–0.3 s, pneumatic cylinder settle ~0.1 s, vision ~0.1–0.5 s) + safety margin 10–20 %.
- Throughput → cycle: `t_cycle = 3600 / (parts/h)` s.
- **RMS torque** for duty: `T_rms = sqrt( Σ(T_i² · t_i) / t_total )` — includes dwell at holding torque (or 0 if brake/unpowered).

## 3. Linear axes

Total axial force on the moving mass `m` (horizontal axis):
`F = m·a + μ·m·g + F_process` (+ `m·g·sinθ` if inclined; vertical: `F = m·(a + g) + F_process`)

**Ball/lead screw** (lead `p` in m/rev):
- Drive torque: `T = F·p / (2π·η)`
- Speed: `n_rpm = v / p · 60`
- Screw inertia: `J = π·ρ·L·d⁴ / 32` (steel ρ = 7850 kg/m³), load reflected: `J_load = m·(p/2π)²`
- Critical speed: `n_c ≈ f · 10⁷ · d_root[mm] / L²[mm]` rpm, L = unsupported length; f = 15.1 fixed–supported, 21.9 fixed–fixed, 9.7 supported–supported, 3.4 fixed–free. Keep `n_max ≤ 0.8·n_c`.
- Back-driving: ball screws back-drive → vertical axes need a brake.
- Typical leads: 5, 10, 16, 20, 25 mm. Short lead → force & resolution; long lead → speed.

**Timing belt / pulley** (pulley pitch radius `r`):
- `T = F·r / η`, `n_rpm = v / (2π·r) · 60`
- Reflected inertia: `J_load = m·r²` (+ pulleys, idlers)
- Belt tension check: effective pull `F` ≤ belt's allowable working tension (e.g. AT10/HTD-5M 25 mm wide ≈ 600–1000 N, check catalogue). Belt axes good to ~5 m/s, repeatability ~±0.05–0.1 mm.

**Rack & pinion**: same as belt with `r` = pinion pitch radius. Good for long strokes (> 3 m), heavy gantries.

**Linear motor**: `F_cont ≥ F_rms`, `F_peak ≥ F_max`. No transmission inertia.

## 4. Rotary loads, inertia & gearing

- Solid cylinder about own axis: `J = ½·m·r²`; hollow: `J = ½·m·(r_o² + r_i²)`
- Rectangular plate about centre normal: `J = m·(a² + b²)/12`
- Point mass at radius: `J = m·r²`; parallel axis: `J = J_cg + m·d²`
- Torque: `T = J_total·α + T_friction + T_process`, `α = Δω / t`
- Through a gearbox of ratio `i` (motor turns `i` times per output turn): `T_motor = T_out / (i·η)`, `ω_motor = i·ω_out`, `J_reflected = J_out / i²`
- Optimal ratio for minimum motor torque in pure inertia drive: `i_opt = sqrt(J_load / J_motor)`
- Conveyor: `F = μ·(m_load + m_belt)·g + m·a`; drive torque `T = F·r_drum/η`
- Rotary indexer / turntable: model as plate + point masses for fixtures/parts.
- Lifting: `P = m·g·v / η`; winch drum `T = m·g·r_drum / η`.
- Wheel drive (vehicle/cart): `F = m·g·(Crr + sinθ) + m·a`; per-wheel torque `T = F·r_wheel / (n_driven·η)`. Check traction: `F ≤ μ_grip · N_driven`.

## 5. Motor selection checks

| Motor type | When | Check |
|---|---|---|
| Stepper (NEMA 17/23/34) | Low cost, < ~1000 rpm, open-loop OK | Use the pull-out torque *at the operating speed* (falls fast above ~300–600 rpm); add 50–100 % margin; inertia ratio ≲ 10 |
| Servo (AC/BLDC) | Speed, dynamics, accuracy | `T_rms ≤ T_cont`, `T_peak ≤ T_max`, `n_max ≤ rated`, inertia ratio ≲ 10 (≲ 3–5 for high dynamics) |
| AC induction + VFD/gearmotor | Continuous running: conveyors, pumps, mixers | Power `P = T·ω`, pick next IEC size; service factor 1.25–1.5; starting torque for high-inertia loads |
| DC gearmotor | Small, battery, simple | Stall current, rated torque at rated speed |

Indicative continuous torque: NEMA 17 ≈ 0.3–0.6 N·m, NEMA 23 ≈ 0.6–3 N·m, NEMA 34 ≈ 3–12 N·m (holding). Servo 100 W ≈ 0.32 N·m @ 3000 rpm, 200 W ≈ 0.64, 400 W ≈ 1.27, 750 W ≈ 2.4, 1 kW ≈ 3.2. IEC 71 ≈ 0.37–0.55 kW, 80 ≈ 0.75–1.1, 90 ≈ 1.5–2.2, 100 ≈ 3, 112 ≈ 4, 132 ≈ 5.5–7.5 kW (4-pole ≈ 1450 rpm @ 50 Hz).

## 6. Pneumatics & hydraulics

- Cylinder force (extend): `F = p·π·D²/4`; retract: `F = p·π·(D² − d_rod²)/4`. 1 bar = 0.1 MPa = 0.1 N/mm².
- Size for **load ratio ≤ 0.5–0.7** for dynamic moves (i.e. theoretical force ≥ 1.5–2× required), ≤ 0.85 for static clamping.
- Design at the *minimum* guaranteed supply (commonly 5–6 bar on a 6–7 bar line).
- ISO bores: 8, 10, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125 mm. At 6 bar: Ø32 ≈ 480 N, Ø40 ≈ 750 N, Ø50 ≈ 1180 N, Ø63 ≈ 1870 N, Ø80 ≈ 3000 N, Ø100 ≈ 4700 N.
- Air consumption (free air per double stroke): `Q ≈ 2·(π·D²/4)·stroke·(p_gauge+1.013)/1.013`.
- Typical speed 50–500 mm/s; cushioning needed above ~200 mm/s or for heavy loads; kinetic energy `½mv²` must be within cushion/shock absorber rating.
- Rod buckling for long strokes: Euler `F_cr = π²·E·I / (K·L)²`, `I = π·d⁴/64`, K = 2 for free-ended rod (worst case); SF ≥ 3.
- Vacuum cup holding force: `F = Δp·A / SF`, Δp ≈ 0.6–0.8 bar, SF 2 (horizontal) to 4 (vertical/shear).
- Hydraulic: `F = p·A`; 100–250 bar typical; pump power `P = p·Q / η` (η ≈ 0.8–0.85).

## 7. Guides, bearings, shafts, keys

- **Profile rail life**: `L = (C / (f_w·P))³ · 50 km` (balls; rollers use exponent 10/3 and 100 km). `f_w` load factor 1.0–1.5 (smooth) / 1.5–2 (shock). Static SF `C₀/P_max ≥ 2–3`.
- Size starting points (per block, dynamic C): size 15 ≈ 10–14 kN, 20 ≈ 17–23 kN, 25 ≈ 27–35 kN, 30 ≈ 38–47 kN. Moment loads from offset payload: split into block forces `F = M / (block spacing)`.
- **Rolling bearing life**: `L10 = (C/P)^k · 10⁶` revs, k = 3 ball, 10/3 roller; hours `= L10 / (60·n)`. Targets: intermittent machinery 4–8 kh, 8-h/day 20–30 kh, 24/7 40–60 kh.
- **Shaft (combined bending + torsion)**: `d³ ≥ (32·SF / (π·S_y)) · sqrt(M² + 0.75·T²)`; deflection under gears/pulleys ≲ 0.1–0.2 mm; slope at bearings ≲ 0.001 rad (ball).
- Torsion only: `τ = 16·T / (π·d³)`, allowable τ ≈ 0.3·S_y.
- Parallel key: shear `τ = 2T/(d·b·L)`, bearing `σ = 4T/(d·h·L)` (allowable ~100 MPa steel hub).
- Linear bushing / plain shaft guides: deflection of unsupported shaft `δ = F·L³/(48·E·I)` (simply supported centre load) — often the limiting factor.

## 8. Structure

- Cantilever, end load: `δ = F·L³ / (3·E·I)`, `σ = F·L·c / I`
- Simply supported, centre load: `δ = F·L³ / (48·E·I)`, `M_max = F·L/4`
- Simply supported, UDL `w` (N/m): `δ = 5·w·L⁴ / (384·E·I)`, `M_max = w·L²/8`
- Fixed–fixed, centre load: `δ = F·L³ / (192·E·I)`
- Rectangular section: `I = b·h³/12`; tube: `I = (B·H³ − b·h³)/12`; round tube: `I = π(D⁴ − d⁴)/64`
- Column buckling: `F_cr = π²·E·I / (K·L)²` (K: 0.5 fixed-fixed, 0.7 fixed-pinned, 1 pinned, 2 fixed-free)
- Stiffness target: deflection at the tool point ≲ 1/3–1/5 of the accuracy requirement; general machine frames L/1000–L/2000; viewing/handling frames L/250–L/500.
- Natural frequency estimate: `f ≈ (1/2π)·sqrt(k/m)`, or `f ≈ 15.76/sqrt(δ_static[mm])` Hz. Keep > 2–3× the excitation frequency.
- Bolt preload (8.8, oiled, ~70 % proof): M6 ≈ 10 kN, M8 ≈ 18 kN, M10 ≈ 29 kN, M12 ≈ 42 kN, M16 ≈ 80 kN. Friction joint capacity ≈ μ·n·F_preload / SF (μ ≈ 0.15–0.2).
- Welds (fillet, steel, static): allowable shear on throat ≈ 0.3·S_u; throat = 0.707·leg.
- Aluminium extrusion (40×40, 6063-T5): I ≈ 7–9·10⁴ mm⁴; 45×45 ≈ 1.4·10⁵; 40×80 ≈ 4·10⁵ (strong axis). Check catalogue.

## 9. Springs, cams, misc.

- Helical compression spring: `k = G·d⁴ / (8·D³·n)` (G steel ≈ 79 GPa).
- Gas spring: force roughly constant ±30 % over stroke; good for counterbalancing lids/arms.
- Counterweight / counterbalance: `m_cw·r_cw = m_load·r_load`.
- Cam follower: keep pressure angle ≲ 30°; use cycloidal or modified-sine motion laws for speed.
- Toggle / knee mechanism: force amplification → ∞ near dead centre, good for presses/clamps.
- Lever: `F_out = F_in · a/b`.
- Thermal expansion: `ΔL = α·L·ΔT` (steel 12·10⁻⁶/K, Al 23·10⁻⁶/K) — matters for long aluminium frames carrying steel screws.
- Energy for impact/stop: `E = ½·m·v²` → shock absorber or bumper rating.

## 10. Typical material properties

| Material | E (GPa) | ρ (kg/m³) | S_y (MPa) | S_u (MPa) | Notes |
|---|---|---|---|---|---|
| Structural steel S235/S355 | 210 | 7850 | 235 / 355 | 360 / 510 | Welded frames |
| C45 / 1045 steel (normalised) | 210 | 7850 | ~350 | ~600 | Shafts |
| 42CrMo4 Q&T | 210 | 7850 | ~650 | ~900 | Heavily loaded shafts, pins |
| Stainless 304 | 193 | 8000 | 215 | 505 | Food / washdown |
| Aluminium 6061-T6 | 69 | 2700 | 275 | 310 | Plates, brackets |
| Aluminium 6063-T5 (extrusion) | 69 | 2700 | ~145 | ~185 | Profile frames |
| Cast iron (grey) | 100–120 | 7200 | — | 200–300 | Damping bases |
| POM (acetal) | 3 | 1410 | ~65 | — | Slides, low-load gears |
| UHMW-PE | 0.7 | 940 | ~20 | — | Wear strips, conveyor guides |
| Nylon PA6 | 2.5–3 | 1140 | ~60 | — | Wheels, bushings |

## 11. Standard-size cheat sheet

- Steel SHS (mm): 30, 40, 50, 60, 80, 100 × wall 2–6. RHS: 60×40, 80×40, 100×50, 120×60.
- Aluminium profile systems: 20, 30, 40, 45, 60, 80 series.
- Plate thicknesses: 3, 5, 6, 8, 10, 12, 15, 20, 25 mm.
- Ball screw diameters: 12, 16, 20, 25, 32, 40 mm.
- Profile rail sizes: 9, 12, 15, 20, 25, 30, 35, 45.
- Shafts / bearing bores: 10, 12, 15, 17, 20, 25, 30, 35, 40, 50 mm.
- Timing belt pitches: GT2 2 mm, HTD 3M/5M/8M, AT5/AT10/T10.
- Motors: NEMA 17/23/34; servo 60/80/130 mm flange; IEC 63–132.
