"""Roblox animation asset (KeyframeSequence .rbxm, zstd from assetdelivery v2) -> plain JSON keyframes.

Get the asset: in the logged-in Chrome open https://assetdelivery.roblox.com/v2/asset?id=<animId>, curl the
`location` URL to <name>.bin. Then: python tools/rbx_anim_json.py library/anims/<name>.bin ...
Output <name>.json: {"length": s, "loop": bool, "keys": [{"t": s, "poses": {"RightUpperArm": [x,y,z, r00..r22]}}]}
Pose CFrames are Motor6D transforms in Roblox axes (+Y up, -Z forward, +X right), translation in studs.
Uses the binary parser from rigs_community/rbx_anims (RBXMonkey, GPL-3) without its Blender imports.
"""
import sys, os, json, types, importlib.util

CORE = os.path.join(os.path.dirname(__file__), "..", "rigs_community", "rbx_anims", "core")
pkg = types.ModuleType("rc"); pkg.__path__ = [CORE]; sys.modules["rc"] = pkg


def _load(n):
    s = importlib.util.spec_from_file_location("rc." + n, os.path.join(CORE, n + ".py")); m = importlib.util.module_from_spec(s)
    sys.modules["rc." + n] = m; s.loader.exec_module(m); return m


_load("schema"); rbxm = _load("rbxm")
rbxm._PROPS_CLASSES = frozenset(set(rbxm._PROPS_CLASSES) | {"Pose", "Keyframe", "KeyframeSequence"})


def convert(path):
    data = open(path, "rb").read()
    if data[:4] == b"\x28\xb5\x2f\xfd":
        import zstandard
        data = zstandard.ZstdDecompressor().decompressobj().decompress(data)
    inst, _ = rbxm._parse_chunks(data)
    seq = next(i for i in inst.values() if i.class_name == "KeyframeSequence")
    keys = []
    for kf in sorted((i for i in inst.values() if i.class_name == "Keyframe"), key=lambda k: float(k.props.get("Time", 0))):
        poses = {}

        def walk(p):
            for c in p.children:
                if c.class_name == "Pose":
                    if float(c.props.get("Weight", 1)) > 0:
                        poses[c.name] = [float(v) for v in c.props["CFrame"]]
                    walk(c)
        walk(kf)
        keys.append({"t": float(kf.props.get("Time", 0)), "poses": poses})
    out = {"length": keys[-1]["t"], "loop": bool(seq.props.get("Loop", True)), "keys": keys}
    dst = os.path.splitext(path)[0] + ".json"
    json.dump(out, open(dst, "w"))
    print(os.path.basename(dst), "keys", len(keys), "length", round(out["length"], 2), "bones", sorted({b for k in keys for b in k["poses"]}))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        convert(p)
