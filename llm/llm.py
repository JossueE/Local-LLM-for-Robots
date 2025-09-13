from __future__ import annotations
from typing import Optional, Dict, Any, Callable, List
import logging, json, os

from .llm_patterns import ORIENT_INTENT_RE
from config.settings import PATH_KB, PATH_POSES
from llm.llm_intentions import split_and_prioritize, norm_text, extract_place_query
from llm.llm_data import KB, PosesIndex, Pose, Battery
from llm.llm_client import LLM
from llm.llm_router import Router
from utils.utils import EnsureModel


class LlmAgent:
    def __init__(
        self,
        model_path: str,
        last_pose: Optional[Pose] = None,
        last_batt: Optional[Battery] = None,
        on_nav_cmd: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        
        self.log = logging.getLogger("LLM")     
        self.kb = KB(os.path.expanduser(PATH_KB)) 
        self.poses = PosesIndex(os.path.expanduser(PATH_POSES)) 
        self.llm = LLM(model_path =  model_path)
        self.router = Router(self.kb, self.poses, self.llm,  self.tool_get_battery, self.tool_get_current_pose, self.tool_nav_to_place, self.publish_natural_move)

        self.last_pose: Optional[Pose] = None or last_pose
        self.last_batt: Optional[Battery] = None or last_batt

        self.on_nav_cmd = on_nav_cmd or (lambda payload: print(f"[nav_cmd] {json.dumps(payload, ensure_ascii=False)}"))

        self.log.info("LLM initialized - Octybot listo ✅ ")

    def ask(self, text: str) -> None:
        """ Process a user input:
        - classify into actions (battery/pose/navigate/general)
        - execute via router.handle()"""
        outs: List[str] = []
        if not isinstance(text, str) or not text.strip():
            text = "No tengo mensaje para procesar."
            return [text]
        
        try:
            actions = split_and_prioritize(text, self.router.kb)
            for action in actions:
                data = action.get("params", {}).get("data")
                kind = action.get("kind")
                ans = self.router.handle(data, kind)
                if not isinstance(ans, str):
                    ans = json.dumps(ans, ensure_ascii=False)
                self.log.info(ans)
                outs.append(ans)

        except Exception as e:
            self.log.exception("Error procesando ask()")
            ans = json.dumps({"error": type(e).__name__, "msg": str(e)}, ensure_ascii=False)
        return outs

    # ---- Setters for Baterry and Pose ----
    def set_battery(self, percentage: Optional[float]) -> None:
        self.last_batt = Battery(percentage=percentage)

    def set_pose(self, x: float, y: float, yaw: float, frame_id: str = "map", name: str = "") -> None:
        self.last_pose = Pose(x=x, y=y, yaw=yaw, frame_id=frame_id, name=name)
    
    # ---- tools ----
    def tool_get_battery(self) -> Dict[str, Any]:
        """ Return the battery percentage as dict with 'percentage' (0.0-100.0), or error if no data """
        if self.last_batt is None or self.last_batt.percentage is None:
            return {"error":"sin_datos_bateria","percentage": None}
        pct = float(self.last_batt.percentage)
        if pct > 1.5: pct /= 100.0
        return {"percentage": round(pct*100.0,1)}

    def tool_get_current_pose(self) -> Dict[str, Any]:
        """ Return the current pose as dict with 'x', 'y', 'yaw_deg', 'frame', or error if no data """
        if self.last_pose is None:
            return {"error":"sin_datos_amcl","x":None,"y":None,"yaw_deg":None,"frame":"map"}
        p = self.last_pose
        return {"x": round(p.x,3), "y": round(p.y,3), "yaw_deg": round(p.yaw,1), "frame": "map"}

    def publish_nav_cmd(self, pose: Dict[str,Any], simulate: bool):
        """ Emit a nav command via callback """
        payload = {"type":"goto","simulate": bool(simulate), "target": {k: pose.get(k) for k in ("x","y","yaw","frame_id","name")}}
        self.log.info(f"[nav_cmd] simulate={simulate} target={payload['target']}")
        self.on_nav_cmd(payload)

    def tool_nav_to_place(self, text: str, simulate: bool=False) -> Dict[str,Any]:
        """ Navigate to a place by name, 
            If simulate=True, only simulate the navigation (no movement commands)
            If simulate=False, emit a nav command via callback"""
        key = extract_place_query(text)
        pose = self.poses.loockup(key)
        if 'error' in pose: return {"error":"destino_no_encontrado","q": key}
        # auto simulate por intención
        t = norm_text(text)
        is_orient = any(w in t for w in ORIENT_INTENT_RE.findall(t)) 
        simulate = True if is_orient else False
        self.publish_nav_cmd(pose, simulate)
        return {"ok": True, "simulate": simulate, "name": pose.get("name"), "target": pose}
    
    def publish_natural_move(self, yaw:float , dist:float) -> str:
        """ Emit a natural_move command via callback """
        payload = {"yaw":yaw, "distance":dist}
        self.on_nav_cmd({"type": "natural_move", **payload})
        return "Avanzando"
    
if "__main__" == __name__:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")

    model =  EnsureModel()
    app = LlmAgent(model_path = str(model.ensure_model("llm")[0]))
    last_pose=app.set_pose(x=1.0, y=2.0, yaw=90.0),
    last_batt=app.set_battery(percentage=0.67),

    print("Prueba de LLM:")
    print("Escribe una orden - Presiona (Ctrl+C para salir):")
    print("(Ejemplos: '¿Dónde estoy?', '¿Cuál es tu batería?', 'Ve a la enfermería', '¿Cuándo fue la Independencia de México y cuál es mi batería?')")
    try:
        while True:
            try:
                text = input("> ").strip()
                if not text:
                    continue
                for out in app.ask(text):
                    print(out)
            except KeyboardInterrupt:
                print("\nPrueba Terminada")
                break
    except Exception:
        logging.exception("Error fatal en el loop principal")
        
