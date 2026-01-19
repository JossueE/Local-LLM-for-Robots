from __future__ import annotations
from config.settings import USE_LLM
from typing import Callable, Dict

class Router:
    def __init__(self, llm):
        self.llm = llm

        self.handlers: Dict[str, Callable[[str], str]] = {
            "rag": self.data_return,
            "general": self.general_response_llm
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
        if USE_LLM: 
            return self.llm.answer_general(data) 
        else: 
            return self.default_handler(data)

    #------------------------- Default Handler -----------------------
    def default_handler(self, data: str)-> str: 
        return "Lo siento lo que me has pedido no lo tengo en mi base de conocimiento"