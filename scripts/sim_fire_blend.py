"""python -I sim_fire_blend.py : what the drum does in game during full-auto, with Source's delta-layer math.

Each shot restarts attack_seq (delta, fadein 0.05). The sequence transitioner keeps the previous attack layer
and fades it out while the new one fades in; every delta layer is applied as base * QuaternionScale(delta, w)
(mathlib QuaternionScale: scales the half-angle's sine -> for |angle| > 180 deg a partial weight turns the
part the OTHER way). Prints the coil drum angle over time for the current per-shot design (120 deg/frame,
360 deg per shot) and for alternatives."""
import math

FPS, RPS, FADE = 30.0, 14.1, 0.05


def qscale(angle_deg, t):
    """Source QuaternionScale for a rotation about one axis; returns the resulting angle (deg)."""
    half = math.radians(angle_deg) / 2
    w, s = math.cos(half), math.sin(half)                 # quaternion (w, s*axis)
    sinom = min(abs(s), 1.0)
    sinsom = math.sin(math.asin(sinom) * t)
    s2 = math.copysign(sinsom, s)
    w2 = math.sqrt(max(0.0, 1 - sinsom * sinsom))
    if w < 0:
        w2 = -w2
    return math.degrees(2 * math.atan2(s2, w2))


def curve(name, delta_of_frame, seconds=0.6, step=1 / 240):
    shots = [k / RPS for k in range(int(seconds * RPS) + 1)]
    out = []
    t = 0.0
    while t <= seconds:
        active = [s for s in shots if s <= t]
        cur = active[-1]
        prev = active[-2] if len(active) > 1 else None
        w_new = min(1.0, (t - cur) / FADE)
        ang = qscale(delta_of_frame((t - cur) * FPS), w_new)
        if prev is not None and w_new < 1.0:
            ang += qscale(delta_of_frame((t - prev) * FPS), 1 - w_new)
        out.append((t, ang))
        t += step
    back = sum(1 for (a0, b0), (a1, b1) in zip(out, out[1:]) if (b1 - b0) % 360 > 180)
    print(f"{name:44s} samples {len(out)}  backward steps {back:3d}  angles(first 0.2 s, 1/60 s): "
          + " ".join(f"{a % 360:4.0f}" for tt, a in out[:48:4]))


def per_frame(deg_per_frame, total):
    def f(fr):
        return min(fr * deg_per_frame, total)
    return f


curve("0.1.16: 120 deg/frame to 360 (coils)", per_frame(120, 360))
curve("0.1.16: 120 deg/frame to 720 (spinner_1/2)", per_frame(120, 720))
print("SIM_FIRE_BLEND_OK")
