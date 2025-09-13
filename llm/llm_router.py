from __future__ import annotations
import json
from config.settings import MAX_MOVE_DISTANCE_LLM


class Router:
    def __init__(self, kb, poses, llm, tool_get_batt, tool_get_pose, tool_nav, natural_move_llm):
        self.kb = kb
        self.poses = poses
        self.llm = llm
        self.tool_get_batt = tool_get_batt
        self.tool_get_pose = tool_get_pose
        self.tool_nav = tool_nav
        self.natural_move_llm = natural_move_llm

    def handle(self, data: str, tipo: str) -> str: 
        """ Route the request to the appropriate handler based on 'tipo' or 'kind """
        if tipo == "rag":
            return data
        
        elif tipo == "general": 
            return self.llm.answer_general(data) 
            
        elif tipo == "battery": 
            r = self.tool_get_batt() 
            pct = r.get('percentage') 
            return f"Mi batería es: {pct:.1f}%" if isinstance(pct,(int,float)) else "Aún no tengo lectura de batería." 
        
        elif tipo == "pose": 
            r = self.tool_get_pose() 
            if any(r.get(k) is None for k in ('x','y','yaw_deg')): 
                return "Aún no tengo lectura de odometría" 
            return json.dumps({k:r.get(k) for k in ('x','y','yaw_deg','frame')}, ensure_ascii=False) 
        
        elif tipo == "navigate":
            r = self.tool_nav(data) 
            print(r, flush=True) 
            if r.get("ok"): 
                return "Por allá" if r.get("simulate") else "Voy" 
            else: 
                plan = self.llm.plan_motion(data) 
                if plan: 
                    yaw, dist = clamp_motion(plan.get("yaw", 0.0), plan.get("distance", 0.0)) 
                    m = self.natural_move_llm(yaw, dist)
                    return m
                return "No encontré ese destino ni entiendo la orden."
        else:
            return "Tu retorno no machea con nada, revisa split_and_prioritize en intentions"

            

def clamp_motion(yaw: float, dist: float,
    max_dist_m: float = MAX_MOVE_DISTANCE_LLM) -> tuple[float, float]:
    """ Limit the max distance to max_dist_m, and yaw to [-pi,pi] """
    d = max(0.0, min(max_dist_m, float(dist)))
    return yaw, d