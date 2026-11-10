import socket, json, sys
def run(code, timeout=600):
    s = socket.create_connection(("127.0.0.1", 9876)); s.settimeout(timeout)
    s.sendall(json.dumps({"type": "execute", "code": code, "strict_json": False}).encode() + b"\0")
    buf = b""
    while not buf.endswith(b"\0"):
        c = s.recv(65536)
        if not c: break
        buf += c
    return buf.rstrip(b"\0").decode()
if __name__ == "__main__":
    print(run(open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()))
