from __future__ import annotations
import json
from config.settings import USE_GENERAL_RESPONSES_LLM


class Router:
    def __init__(self, general_rag, poses, llm, publish_info):
        self.general_rag = general_rag
        self.poses = poses
        self.llm = llm
        self.publish_info = publish_info

    def handle(self, data: str, tipo: str) -> str: 
        """ Route the request to the appropriate handler based on 'tipo' or 'kind """
        if tipo == "rag":
            return data
        
        elif tipo == "general" and USE_GENERAL_RESPONSES_LLM: 
            return self.llm.answer_general(data) 
            
        elif tipo == "battery": 
            r = self.publish_info.tool_get_battery() 
            pct = r.get('percentage') 
            return f"Mi batería es: {pct:.1f}%" if isinstance(pct,(int,float)) else "Aún no tengo lectura de batería." 
        
        elif tipo == "navigate":
            r = self.publish_info.tool_nav_to_place(data) 
            print(r, flush=True) 
            if r.get("ok"): 
                return "Por allá" if r.get("simulate") else "Voy" 
            else: 
                plan = self.llm.plan_motion(data) 
                if plan: 
                    yaw, dist, flag = plan.get("yaw", 0.0), plan.get("distance", 0.0), plan.get("flag", False)
                    m = self.publish_info.publish_natural_move(yaw, dist, flag)
                    return m
                return "No encontré ese destino ni entiendo la orden."
        
        elif tipo == "cancel_navigate":
            return "Cancelando Navegación"
        
        else:
            return "Tu retorno no machea con nada, revisa split_and_prioritize en intentions"

            

