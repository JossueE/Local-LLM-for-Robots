from __future__ import annotations
from typing import Dict, Any, Optional, Callable
import math, json, logging, requests, os

from llm.llm_data import Battery, PosesIndex
from llm.llm_patterns import ORIENT_INTENT_RE, MAPS_COUNT_RE
from config.settings import MAX_MOVE_DISTANCE_LLM, PATH_POSES
from llm.llm_intentions import norm_text, extract_place_query

class GetInfo:
    def __init__(
        self,
        last_batt: Optional[Battery] = None,
        on_nav_cmd: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.log = logging.getLogger("Publish") 
        self.poses = PosesIndex(os.path.expanduser(PATH_POSES)) 
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
    
    # ------------------- Maps ------------------------
    
    def tool_get_maps_from_backend(self) -> list:
        try:
            response = requests.get("http://0.0.0.0:9009/maps/maps", json={}, params={}, timeout=2.0)
            response_body = response.json()

            # Check if the 'data' key exists and is a list
            if 'data' in response_body and isinstance(response_body['data'], list):
                # Use a list comprehension to extract the 'name' from each dictionary in the 'data' list
                message = [item.get('name') for item in response_body['data'] if isinstance(item, dict) and 'name' in item]
            else:
                print("Error: 'data' key not found or not a list in the response.")
                message = []

        except requests.exceptions.Timeout:
            message = "The request timed out after 2 seconds."
        except requests.exceptions.RequestException as ex:
            message = f"Server NOT available. {ex}"

        return message

    def tool_classify_maps_intention(self, text: str) -> Dict[str,Any]:
        """ Navigate to a place by name, 
            If simulate=True, only simulate the navigation (no movement commands)
            If simulate=False, emit a nav command via callback"""
        # auto simulate por intención
        t = norm_text(text)
        is_count = any(w in t for w in MAPS_COUNT_RE.findall(t)) 
        return True if is_count else False
