from __future__ import annotations
from typing import Dict, Any, Optional, Callable
import math, json, logging

from llm.llm_data import Pose, Battery
from llm.llm_patterns import ORIENT_INTENT_RE
from config.settings import MAX_MOVE_DISTANCE_LLM
from llm.llm_intentions import norm_text, extract_place_query

class PublishInfo:
    def __init__(
        self,
        poses,
        last_pose: Optional[Pose] = None,
        last_batt: Optional[Battery] = None,
        on_nav_cmd: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        
        self.log = logging.getLogger("Publish") 
        self.poses = poses
        self.last_pose: Optional[Pose] = None or last_pose
        self.last_batt: Optional[Battery] = None or last_batt

        self.on_nav_cmd = on_nav_cmd or (lambda payload: print(f"[nav_cmd] {json.dumps(payload, ensure_ascii=False)}"))
        

    #------- Battery ----------

    def set_battery(self, percentage: Optional[float]) -> None:
        self.last_batt = Battery(percentage=percentage)
    
    def tool_get_battery(self) -> Dict[str, Any]:
        """ Return the battery percentage as dict with 'percentage' (0.0-100.0), or error if no data """
        if self.last_batt is None or self.last_batt.percentage is None:
            return {"error":"sin_datos_bateria","percentage": None}
        pct = float(self.last_batt.percentage)
        if pct > 1.5: pct /= 100.0
        return {"percentage": round(pct*100.0,1)}

    #------- Navigation --------

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
    
    def publish_natural_move(self, yaw:float , dist:float, flag:bool, max_dist_m: float = MAX_MOVE_DISTANCE_LLM) -> str:
        """ Emit a natural_move command via callback """
        adjusted_dist = max(-max_dist_m, min(max_dist_m, float(dist)))
        if flag:
            yaw = math.radians(yaw)
        payload = {"yaw":yaw, "distance":adjusted_dist, "flag":flag}
        self.on_nav_cmd({"type": "natural_move", **payload})
        if dist > max_dist_m:
            return f"Estoy avanzando, pero recuerda que no puedo avanzar más de {max_dist_m} metros"
        elif yaw != 0 or adjusted_dist != 0:
            return "Avanzando"
        return "No encontré destino, ni instucción de movimiento."
    
