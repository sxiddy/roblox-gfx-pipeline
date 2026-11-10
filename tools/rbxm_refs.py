"""List asset ids referenced in a binary .rbxm (decompresses LZ4 chunks). Usage: python rbxm_refs.py file.rbxm"""
import re, struct, sys

def lz4_block(src, size):
    dst = bytearray(); i = 0
    while i < len(src):
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i+lit]; i += lit
        if i >= len(src): break
        off = src[i] | (src[i+1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        for _ in range(ml): dst.append(dst[-off])
    return bytes(dst)

def chunks(data):
    p = 32
    while p < len(data):
        name = data[p:p+4]; clen, ulen = struct.unpack_from("<II", data, p+4); p += 16
        raw = data[p:p+(clen or ulen)]; p += clen or ulen
        body = lz4_block(raw, ulen) if clen else raw
        yield name, body
        if name == b"END\0": break

if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    if not d.startswith(b"<roblox!"):
        print("XML file"); sys.exit()
    for name, body in chunks(d):
        if name == b"PROP":
            cls, = struct.unpack_from("<I", body, 0)
            nlen, = struct.unpack_from("<I", body, 4)
            prop = body[8:8+nlen].decode("latin1")
            ids = re.findall(rb"(?:rbxassetid://|id=)(\d+)", body)
            if ids: print(cls, prop, [i.decode() for i in ids])
        if name == b"INST":
            cid, nlen = struct.unpack_from("<II", body, 0)
            print("class", cid, body[8:8+nlen].decode())
        if name == b"PROP" and body[8:8+struct.unpack_from("<I", body, 4)[0]] == b"Name":
            print("   names:", re.findall(rb"[A-Za-z][A-Za-z0-9 ]{2,}", body[12:]))
