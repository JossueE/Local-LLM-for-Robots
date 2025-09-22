from __future__ import annotations
from config.settings import USE_GENERAL_RESPONSES_LLM
from typing import Callable, Dict


class Router:
    def __init__(self, llm, get_info):
        self.llm = llm
        self.get_info = get_info

        self.handlers: Dict[str, Callable[[str], str]] = {
            "rag": self.data_return,
            "general": self.general_response_llm,
            "battery": self.battery_publisher,
            "navigate": self.navigation_publisher,
            "cancel_navigate": self.cancel_navigate_publisher,
            "maps": self.get_maps
        }

    #------------ Handler or Router -------------------    
    def handle(self, data: str, tipo: str) -> str:
        try:
            return self.handlers.get(tipo, self.default_handler)(data)
        except Exception as e:
            return f"[LLM_Router] Error en handler '{tipo}': {e}"
    
    #-------------The Publishers-------------------------
    def data_return(self, data: str)-> str: 
        return data
    
    def general_response_llm(self, data: str)-> str: 
        if USE_GENERAL_RESPONSES_LLM: return self.llm.answer_general(data) 
    
    def battery_publisher(self, data: str)-> str: 
        battery = self.get_info.tool_get_battery() 
        pct = battery.get('percentage') 
        return f"Mi batería es: {pct:.1f}%" if isinstance(pct,(int,float)) else "Aún no tengo lectura de batería." 
    
    def navigation_publisher(self, data: str)-> str: 
        place = self.get_info.tool_nav_to_place(data) 
        #print(place, flush=True) 
        if place.get("ok"): 
            return "Por allá" if place.get("simulate") else "Voy" 
        else: 
            plan = self.llm.plan_motion(data) 
            if plan: 
                yaw, dist, flag = plan.get("yaw", 0.0), plan.get("distance", 0.0), plan.get("flag", False)
                m = self.get_info.publish_natural_move(yaw, dist, flag)
                return m
            return "No encontré ese destino ni entiendo la orden."
        
    def cancel_navigate_publisher(self, data: str)-> str: 
        return "Cancelando Navegación"
    
    def get_maps(self, data: str)-> str: 
        maps = self.get_info.tool_get_maps_from_backend()
        if not maps:
            return "Lo lamento, no cuentas con mapas cargados"
        
        elif self.get_info.tool_classify_maps_intention(data):
            num_maps = len(maps)
            return f"Tienes {num_maps} mapas cargados"
        
        else:
            return "Tus mapas son: " + ", ".join(str(m) for m in maps)
            

    #------------------------- Default Handler -----------------------
    def default_handler(self, data: str)-> str: 
        return "Lo siento lo que me has pedido no lo tengo en mi base de conocimiento"
    


            

            

