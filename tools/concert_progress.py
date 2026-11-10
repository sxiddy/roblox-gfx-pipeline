"""Live progress for the anim_concert2 job (no Claude tokens): prints stage, frames done and time left every minute."""
import os, time, glob

D = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\anim_concert2"
END = 285
t0 = None; n0 = 0
while True:
    frames = glob.glob(os.path.join(D, "frames", "f*.png"))
    mp4 = os.path.join(r"C:\Users\Siddharth D\Downloads", "suhaa_concert.mp4")
    now = time.time()
    if frames:
        n = len(frames)
        if t0 is None or n < n0:
            t0, n0 = now, n
        rate = (n - n0) / max(now - t0, 1)
        left = (END - n) / rate / 60 if rate > 0 else None
        msg = f"RENDER {n}/{END} frames" + (f" | ~{left:.0f} min left" if left else " | measuring speed...")
        if n >= END:
            msg = "RENDER done | grading + adding song (~5 min)"
    elif os.path.exists(os.path.join(D, "build.log")) and now - os.path.getmtime(os.path.join(D, "scene.blend")) > 600:
        msg = "BUILDING scene (dance keyframes) | ~25-40 min total, then stills check, then render"
    else:
        msg = "Scene built | checking stills, render starts soon"
    print(time.strftime("%H:%M"), msg, flush=True)
    time.sleep(60)
