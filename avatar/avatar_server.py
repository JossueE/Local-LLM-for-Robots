# ws_hub.py — minimal (websockets 15.x), reemite en JSON {"source": "..."}
import asyncio
import json
import signal
import argparse
import websockets

HOST = "localhost"
PORT = 9030
URL_DEFAULT = f"ws://{HOST}:{PORT}"
VALID_MODES = {"USER", "TTS"}
CLIENTS = set()


def _normalize_mode(msg: str):
    """Acepta 'USER'/'TTS' o JSON con 'source'/'mode'. Devuelve 'USER'|'TTS'|None."""
    if not msg:
        return None
    s = msg.strip()
    try:
        obj = json.loads(s)
        val = (obj.get("source") or obj.get("mode") or "").upper()
        return val if val in VALID_MODES else None
    except Exception:
        val = s.upper()
        return val if val in VALID_MODES else None


async def _broadcast_json(mode: str):
    """Envía {"source": MODE} a todos los clientes."""
    if mode not in VALID_MODES or not CLIENTS:
        return
    payload = json.dumps({"source": mode})
    await asyncio.gather(*(ws.send(payload) for ws in list(CLIENTS)), return_exceptions=True)


async def _handler(ws):
    CLIENTS.add(ws)
    try:
        async for raw in ws:
            mode = _normalize_mode(raw if isinstance(raw, str) else "")
            if mode:
                await _broadcast_json(mode)
    finally:
        CLIENTS.discard(ws)


async def run_server(host=HOST, port=PORT):
    async with websockets.serve(_handler, host, port):
        print(f"WS Hub en ws://{host}:{port} (modes: USER/TTS, broadcast JSON)")
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set_result, None)
            except NotImplementedError:
                pass
        await stop


async def send_mode(mode: str, url: str = URL_DEFAULT, as_json: bool = True, timeout: float = 3.0):
    """Cliente async: envía USER/TTS al hub (por defecto en JSON)."""
    m = (mode or "").upper()
    if m not in VALID_MODES:
        raise ValueError("Modo inválido. Usa USER o TTS.")
    payload = json.dumps({"source": m}) if as_json else m
    async with websockets.connect(url, open_timeout=timeout, close_timeout=timeout) as ws:
        await asyncio.wait_for(ws.send(payload), timeout=timeout)


def send_mode_sync(mode: str, url: str = URL_DEFAULT, as_json: bool = True, timeout: float = 3.0):
    asyncio.run(send_mode(mode, url=url, as_json=as_json, timeout=timeout))


def parse_args():
    p = argparse.ArgumentParser(description="WS Hub USER/TTS (broadcast JSON)")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("server", help="Inicia el hub")
    ps.add_argument("--host", default=HOST)
    ps.add_argument("--port", type=int, default=PORT)

    pc = sub.add_parser("send", help="Envía USER o TTS")
    pc.add_argument("mode", choices=sorted(VALID_MODES))
    pc.add_argument("--url", default=URL_DEFAULT)
    pc.add_argument("--text", action="store_true", help="Enviar como texto plano en lugar de JSON")

    return p.parse_args()


def main():
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
