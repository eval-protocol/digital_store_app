import os
import sys
from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient


def main() -> None:
    backend = "http://localhost:8010/sse"
    args = sys.argv[1:]
    if "--backend" in args:
        try:
            backend = args[args.index("--backend") + 1]
        except Exception:
            pass
    backend = os.getenv("BACKEND_SSE_URL", backend)
    proxy = FastMCP.as_proxy(ProxyClient(backend), name="postgres-proxy")
    proxy.run()


if __name__ == "__main__":
    main()


