# ws_hub.py — minimal (websockets 15.x), reemite en JSON {"source": "..."}
import asyncio
import json
import signal
import websockets

HOST = "localhost"
PORT = 9030
URL_DEFAULT = f"ws://{HOST}:{PORT}"
VALID_MODES = {"USER", "TTS"}
CLIENTS = set()

async def broadcast_json(mode: str):
    """Send {"source": MODE} to every client."""
    if mode not in VALID_MODES or not CLIENTS:
        return
    payload = json.dumps({"source": mode})
    await asyncio.gather(*(ws.send(payload) for ws in list(CLIENTS)), return_exceptions=True)

async def handler(ws):
    CLIENTS.add(ws)
    try:
        async for raw in ws:
            mode =  raw if isinstance(raw, str) else ""
            if mode:
                await broadcast_json(mode)
    finally:
        CLIENTS.discard(ws)

async def run_server(host=HOST, port=PORT):
    async with websockets.serve(handler, host, port):
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

if __name__ == "__main__":
    asyncio.run(run_server())
