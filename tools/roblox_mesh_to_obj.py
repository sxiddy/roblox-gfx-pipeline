"""Convert Roblox .mesh files (v1.xx text, v2.00, v3.xx binary) to Wavefront OBJ.
Usage: python roblox_mesh_to_obj.py in.mesh out.obj [scale]
Default scale 0.3 (metres per stud)."""
import re, struct, sys

def parse(data):
    head = data[:12].decode("latin1")
    ver = head.split("\n")[0].strip()
    if ver.startswith("version 1"):
        txt = data.decode("latin1").split("\n", 2)
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", txt[2])]
        scale = 0.5 if ver.endswith("1.01") else 1.0
        V, N, UV, F = [], [], [], []
        for i in range(0, len(nums) - 8, 9):
            V.append(tuple(n * scale for n in nums[i:i+3])); N.append(tuple(nums[i+3:i+6])); UV.append(tuple(nums[i+6:i+8]))
        for i in range(0, len(V), 3): F.append((i, i+1, i+2))
        return V, N, UV, F
    p = data.index(b"\n") + 1
    if ver.startswith("version 2"):
        hs, vs, fs, nv, nf = struct.unpack_from("<HBBII", data, p)
        vo = p + hs; lod = None
    elif ver.startswith("version 3"):
        hs, vs, fs, ls, nl, nv, nf = struct.unpack_from("<HBBHHII", data, p)
        vo = p + hs
        lods = struct.unpack_from("<%dI" % nl, data, vo + nv*vs + nf*fs) if nl else None
        lod = (lods[0], lods[1]) if lods and len(lods) > 1 else None
    else:
        raise ValueError("unsupported " + ver)
    V, N, UV = [], [], []
    for i in range(nv):
        o = vo + i*vs
        f = struct.unpack_from("<8f", data, o)
        V.append(f[0:3]); N.append(f[3:6]); UV.append(f[6:8])
    fo = vo + nv*vs
    F = [struct.unpack_from("<3I", data, fo + i*fs) for i in range(nf)]
    if lod: F = F[lod[0]:lod[1]]
    return V, N, UV, F

def write_obj(path, V, N, UV, F, s):
    with open(path, "w") as o:
        for v in V: o.write("v %f %f %f\n" % (v[0]*s, -v[2]*s, v[1]*s))   # Roblox Y-up -> Blender Z-up
        for n in N: o.write("vn %f %f %f\n" % (n[0], -n[2], n[1]))
        for t in UV: o.write("vt %f %f\n" % (t[0], 1 - t[1]))
        for a, b, c in F: o.write("f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (a+1,a+1,a+1,b+1,b+1,b+1,c+1,c+1,c+1))

if __name__ == "__main__":
    V, N, UV, F = parse(open(sys.argv[1], "rb").read())
    write_obj(sys.argv[2], V, N, UV, F, float(sys.argv[3]) if len(sys.argv) > 3 else 0.3)
    print(sys.argv[1], len(V), "verts", len(F), "faces")
