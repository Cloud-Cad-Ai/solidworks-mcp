#!/usr/bin/env python3
"""Deterministic mechanical calculators with explicit SI inputs.

Every command prints one JSON record: inputs with units, the formula used,
the result, and the model's validity notes. Nothing is defaulted: material
properties, friction coefficients, service factors and allowables must be
passed in, because inventing them is the error this script exists to prevent.

Usage:  python mech_calc.py <command> --arg value ...
        python mech_calc.py list
"""
import argparse
import json
import math
import sys

G = 9.80665  # m/s^2, standard gravity (a definition, not an assumption)


def out(name, inputs, formula, result, notes):
    print(json.dumps({
        "calc": name,
        "result_source": "deterministic_calculator",
        "inputs": inputs,
        "formula": formula,
        "result": result,
        "validity": notes,
    }, indent=2))


def need_positive(**kw):
    for k, v in kw.items():
        if v is None or v <= 0:
            sys.exit(f"error: {k} must be > 0 (got {v})")


# ---------------------------------------------------------------- drives

def drive(a):
    """Linear drive: force, speed, pulley diameter -> power, rpm, torque."""
    need_positive(force_N=a.force_N, speed_mps=a.speed_mps, pulley_d_m=a.pulley_d_m)
    r = a.pulley_d_m / 2
    P = a.force_N * a.speed_mps
    omega = a.speed_mps / r
    rpm = omega * 60 / (2 * math.pi)
    T = a.force_N * r
    res = {"power_W": P, "omega_rad_s": omega, "pulley_rpm": rpm, "torque_Nm": T,
           "check_P_equals_T_omega": abs(P - T * omega) < 1e-9 * max(P, 1)}
    if a.motor_rpm:
        res["gear_ratio"] = a.motor_rpm / rpm
    if a.efficiency:
        res["motor_power_W"] = P / a.efficiency
        res["motor_torque_at_input_Nm"] = (T / res["gear_ratio"] / a.efficiency
                                          if a.motor_rpm else None)
    out("drive", vars(a), "P = F*v; omega = v/r; T = F*r = P/omega", res,
        "Steady state only. Add acceleration force m*a separately; apply service factor to the result.")


def conveyor_force(a):
    """Belt pull for a loaded conveyor: friction plus incline component."""
    need_positive(mass_kg=a.mass_kg)
    if a.mu is None:
        sys.exit("error: --mu (belt-to-bed friction coefficient) is required; take it from the belt/bed supplier")
    th = math.radians(a.incline_deg)
    F_fric = a.mu * a.mass_kg * G * math.cos(th)
    F_lift = a.mass_kg * G * math.sin(th)
    F_acc = a.mass_kg * a.accel_mps2
    out("conveyor_force", vars(a),
        "F = mu*m*g*cos(theta) + m*g*sin(theta) + m*a",
        {"friction_N": F_fric, "incline_N": F_lift, "accel_N": F_acc,
         "total_N": F_fric + F_lift + F_acc},
        "Slider-bed model. Mass is total moving mass (product + belt share). Excludes pulley/bearing drag and belt flexing losses.")


# ---------------------------------------------------------------- shafts

def shaft_diameter(a):
    """Solid round shaft, combined bending and torsion, max-shear (Tresca)."""
    need_positive(allowable_shear_Pa=a.allowable_shear_Pa)
    Te = math.sqrt((a.Kb * a.moment_Nm) ** 2 + (a.Kt * a.torque_Nm) ** 2)
    d = (16 * Te / (math.pi * a.allowable_shear_Pa)) ** (1 / 3)
    out("shaft_diameter", vars(a),
        "Te = sqrt((Kb*M)^2 + (Kt*T)^2); d = (16*Te/(pi*tau_allow))^(1/3)",
        {"equivalent_torque_Nm": Te, "min_diameter_m": d, "min_diameter_mm": d * 1e3},
        "Static strength only (Tresca). Does not cover fatigue, keyway stress concentration, deflection or critical speed. tau_allow must already include the safety factor.")


def shaft_stress(a):
    """Stresses in a given solid round shaft."""
    need_positive(d_m=a.d_m)
    d = a.d_m
    sigma = 32 * a.moment_Nm / (math.pi * d ** 3)
    tau = 16 * a.torque_Nm / (math.pi * d ** 3)
    vm = math.sqrt(sigma ** 2 + 3 * tau ** 2)
    tmax = math.sqrt((sigma / 2) ** 2 + tau ** 2)
    res = {"bending_Pa": sigma, "torsion_Pa": tau, "von_mises_Pa": vm, "max_shear_Pa": tmax}
    if a.yield_Pa:
        res["safety_factor_von_mises"] = a.yield_Pa / vm if vm else math.inf
    out("shaft_stress", vars(a),
        "sigma = 32M/(pi d^3); tau = 16T/(pi d^3); vm = sqrt(sigma^2+3tau^2)", res,
        "Nominal stresses; multiply by Kt for shoulders/keyways. Static only.")


def shaft_twist(a):
    need_positive(d_m=a.d_m, length_m=a.length_m, G_Pa=a.G_Pa)
    J = math.pi * a.d_m ** 4 / 32
    phi = a.torque_Nm * a.length_m / (a.G_Pa * J)
    out("shaft_twist", vars(a), "phi = T*L/(G*J); J = pi d^4/32",
        {"twist_rad": phi, "twist_deg": math.degrees(phi), "twist_deg_per_m": math.degrees(phi) / a.length_m},
        "Linear elastic, uniform solid section.")


# ---------------------------------------------------------------- beams

def beam(a):
    """Classic beam cases. Section given by I and c (or rectangle/round)."""
    need_positive(length_m=a.length_m, E_Pa=a.E_Pa)
    if a.rect_b_m and a.rect_h_m:
        I = a.rect_b_m * a.rect_h_m ** 3 / 12; c = a.rect_h_m / 2
    elif a.round_d_m:
        I = math.pi * a.round_d_m ** 4 / 64; c = a.round_d_m / 2
    elif a.I_m4 and a.c_m:
        I, c = a.I_m4, a.c_m
    else:
        sys.exit("error: give --rect_b_m and --rect_h_m, or --round_d_m, or --I_m4 and --c_m")
    L, E = a.length_m, a.E_Pa
    cases = {
        "cantilever_end_load": (a.load * L, a.load * L ** 3 / (3 * E * I), "M = P*L; delta = P L^3/(3EI)"),
        "cantilever_udl": (a.load * L ** 2 / 2, a.load * L ** 4 / (8 * E * I), "w in N/m; M = wL^2/2; delta = wL^4/(8EI)"),
        "simple_center_load": (a.load * L / 4, a.load * L ** 3 / (48 * E * I), "M = PL/4; delta = PL^3/(48EI)"),
        "simple_udl": (a.load * L ** 2 / 8, 5 * a.load * L ** 4 / (384 * E * I), "w in N/m; M = wL^2/8; delta = 5wL^4/(384EI)"),
    }
    if a.case not in cases:
        sys.exit(f"error: --case must be one of {list(cases)}")
    M, d, f = cases[a.case]
    res = {"I_m4": I, "max_moment_Nm": M, "max_stress_Pa": M * c / I, "max_deflection_m": d,
           "max_deflection_mm": d * 1e3, "L_over_deflection": L / d if d else math.inf}
    if a.yield_Pa:
        res["safety_factor_yield"] = a.yield_Pa / res["max_stress_Pa"]
    out("beam", vars(a), f + "; sigma = M*c/I", res,
        "Euler-Bernoulli, small deflection, linear elastic, prismatic. Load units: N for point cases, N/m for udl cases.")


# ---------------------------------------------------------------- bearings

def bearing_life(a):
    need_positive(C_N=a.C_N, P_N=a.P_N, rpm=a.rpm)
    p = 3.0 if a.type == "ball" else 10 / 3
    L10_rev = (a.C_N / a.P_N) ** p * 1e6
    hours = L10_rev / (60 * a.rpm)
    res = {"exponent_p": p, "L10_million_rev": L10_rev / 1e6, "L10_hours": hours}
    if a.required_hours:
        res["meets_requirement"] = hours >= a.required_hours
        res["required_C_N"] = a.P_N * (a.required_hours * 60 * a.rpm / 1e6) ** (1 / p)
    out("bearing_life", vars(a), "L10 = (C/P)^p * 1e6 rev; h = L10/(60 n)", res,
        "Basic rating life, 90% reliability. C from the catalog for the exact bearing. P is equivalent dynamic load (combine radial/axial with catalog X, Y).")


def equivalent_load(a):
    need_positive(Fr_N=a.Fr_N)
    if a.X is None or a.Y is None:
        sys.exit("error: --X and --Y come from the bearing catalog for Fa/Fr and e; they are required")
    P = a.X * a.Fr_N + a.Y * a.Fa_N
    out("equivalent_load", vars(a), "P = X*Fr + Y*Fa", {"P_N": max(P, a.Fr_N)},
        "X, Y per catalog for the computed Fa/Fr vs e. P is never below Fr.")


# ---------------------------------------------------------------- motion

def inertia_torque(a):
    """Torque to accelerate a load reflected to the motor shaft."""
    need_positive(J_load_kgm2=a.J_load_kgm2, ratio=a.ratio, accel_time_s=a.accel_time_s, motor_rpm=a.motor_rpm)
    J_ref = a.J_load_kgm2 / a.ratio ** 2 + a.J_motor_kgm2
    alpha = (a.motor_rpm * 2 * math.pi / 60) / a.accel_time_s
    T = J_ref * alpha
    out("inertia_torque", vars(a),
        "J_ref = J_load/i^2 + J_motor; alpha = omega/t; T = J_ref*alpha",
        {"J_reflected_kgm2": J_ref, "alpha_rad_s2": alpha, "accel_torque_Nm": T,
         "inertia_ratio": (a.J_load_kgm2 / a.ratio ** 2) / a.J_motor_kgm2 if a.J_motor_kgm2 else None},
        "Linear ramp, ignores gearbox inertia unless included in J_motor. Add to steady torque.")


def linear_inertia(a):
    need_positive(mass_kg=a.mass_kg, pulley_d_m=a.pulley_d_m)
    J = a.mass_kg * (a.pulley_d_m / 2) ** 2
    out("linear_inertia", vars(a), "J = m*r^2", {"J_kgm2": J},
        "Translating mass reflected to the pulley shaft. Add rotating parts separately.")


def bolt_preload(a):
    need_positive(d_m=a.d_m, torque_Nm=a.torque_Nm)
    if a.K is None:
        sys.exit("error: --K (nut factor) is required; it depends on finish and lubrication")
    F = a.torque_Nm / (a.K * a.d_m)
    res = {"preload_N": F}
    if a.stress_area_m2:
        res["bolt_stress_Pa"] = F / a.stress_area_m2
    out("bolt_preload", vars(a), "F = T/(K*d)", res,
        "Short-form torque relation. Scatter in K is commonly +/-25%; treat as an estimate.")


def tipping(a):
    """Static tipping check about an edge: restoring vs overturning moment."""
    need_positive(mass_kg=a.mass_kg, base_half_width_m=a.base_half_width_m)
    M_restore = a.mass_kg * G * a.base_half_width_m
    M_over = a.horizontal_force_N * a.force_height_m + a.mass_kg * a.lateral_accel_mps2 * a.cg_height_m
    out("tipping", vars(a),
        "M_restore = m*g*b; M_over = F_h*h_F + m*a_lat*h_cg",
        {"restoring_Nm": M_restore, "overturning_Nm": M_over,
         "stability_factor": M_restore / M_over if M_over else math.inf},
        "Rigid body, CG directly above base centre, tipping edge at base_half_width from CG. Not dynamic.")


def units(a):
    """Convert between common units so CAD inputs land in meters/radians."""
    f = {"mm": 1e-3, "cm": 1e-2, "in": 0.0254, "ft": 0.3048, "m": 1.0, "deg": math.pi / 180, "rad": 1.0,
         "lbf": 4.4482216152605, "N": 1.0, "kgf": G, "lb": 0.45359237, "kg": 1.0,
         "MPa": 1e6, "ksi": 6.894757293168e6, "psi": 6894.757293168, "Pa": 1.0, "GPa": 1e9,
         "Nm": 1.0, "lbf_in": 0.112984829, "lbf_ft": 1.3558179483, "hp": 745.69987158, "kW": 1e3, "W": 1.0}
    if a.unit not in f:
        sys.exit(f"error: unit must be one of {sorted(f)}")
    base = {"mm": "m", "cm": "m", "in": "m", "ft": "m", "m": "m", "deg": "rad", "rad": "rad",
            "lbf": "N", "N": "N", "kgf": "N", "lb": "kg", "kg": "kg", "MPa": "Pa", "ksi": "Pa", "psi": "Pa",
            "Pa": "Pa", "GPa": "Pa", "Nm": "Nm", "lbf_in": "Nm", "lbf_ft": "Nm", "hp": "W", "kW": "W", "W": "W"}
    out("units", vars(a), "value * factor", {"value_SI": a.value * f[a.unit], "SI_unit": base[a.unit]}, "Exact factors.")


# ---------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd")

    def cmd(name, fn, args, help_):
        sp = s.add_parser(name, help=help_)
        for n, t, req, d in args:
            sp.add_argument("--" + n, type=t, required=req, default=d)
        sp.set_defaults(fn=fn)

    F = float
    cmd("drive", drive, [("force_N", F, True, None), ("speed_mps", F, True, None), ("pulley_d_m", F, True, None),
                         ("motor_rpm", F, False, None), ("efficiency", F, False, None)],
        "power, pulley rpm, torque, gear ratio from belt force and speed")
    cmd("conveyor_force", conveyor_force, [("mass_kg", F, True, None), ("mu", F, False, None),
                                           ("incline_deg", F, False, 0.0), ("accel_mps2", F, False, 0.0)],
        "belt pull for a slider-bed conveyor")
    cmd("shaft_diameter", shaft_diameter, [("moment_Nm", F, True, None), ("torque_Nm", F, True, None),
                                           ("allowable_shear_Pa", F, True, None), ("Kb", F, False, 1.0), ("Kt", F, False, 1.0)],
        "minimum solid shaft diameter, static Tresca")
    cmd("shaft_stress", shaft_stress, [("d_m", F, True, None), ("moment_Nm", F, True, None), ("torque_Nm", F, True, None),
                                       ("yield_Pa", F, False, None)], "stresses in a given shaft")
    cmd("shaft_twist", shaft_twist, [("d_m", F, True, None), ("length_m", F, True, None), ("torque_Nm", F, True, None),
                                     ("G_Pa", F, True, None)], "angle of twist")
    cmd("beam", beam, [("case", str, True, None), ("load", F, True, None), ("length_m", F, True, None), ("E_Pa", F, True, None),
                       ("rect_b_m", F, False, None), ("rect_h_m", F, False, None), ("round_d_m", F, False, None),
                       ("I_m4", F, False, None), ("c_m", F, False, None), ("yield_Pa", F, False, None)],
        "beam stress and deflection: cantilever_end_load, cantilever_udl, simple_center_load, simple_udl")
    cmd("bearing_life", bearing_life, [("C_N", F, True, None), ("P_N", F, True, None), ("rpm", F, True, None),
                                       ("type", str, False, "ball"), ("required_hours", F, False, None)], "L10 life")
    cmd("equivalent_load", equivalent_load, [("Fr_N", F, True, None), ("Fa_N", F, False, 0.0), ("X", F, False, None),
                                             ("Y", F, False, None)], "bearing equivalent dynamic load")
    cmd("inertia_torque", inertia_torque, [("J_load_kgm2", F, True, None), ("ratio", F, True, None),
                                           ("motor_rpm", F, True, None), ("accel_time_s", F, True, None),
                                           ("J_motor_kgm2", F, False, 0.0)], "acceleration torque at motor")
    cmd("linear_inertia", linear_inertia, [("mass_kg", F, True, None), ("pulley_d_m", F, True, None)],
        "reflected inertia of a translating mass")
    cmd("bolt_preload", bolt_preload, [("d_m", F, True, None), ("torque_Nm", F, True, None), ("K", F, False, None),
                                       ("stress_area_m2", F, False, None)], "preload from tightening torque")
    cmd("tipping", tipping, [("mass_kg", F, True, None), ("base_half_width_m", F, True, None), ("cg_height_m", F, False, 0.0),
                             ("horizontal_force_N", F, False, 0.0), ("force_height_m", F, False, 0.0),
                             ("lateral_accel_mps2", F, False, 0.0)], "static tipping stability factor")
    cmd("units", units, [("value", F, True, None), ("unit", str, True, None)], "convert to SI")
    s.add_parser("list", help="list commands")

    a = p.parse_args()
    if not a.cmd or a.cmd == "list":
        for name, sp in s.choices.items():
            print(f"{name:16s} {sp.description or ''}")
        p.print_help()
        return
    fn = a.fn
    del a.fn, a.cmd
    fn(a)


if __name__ == "__main__":
    main()
