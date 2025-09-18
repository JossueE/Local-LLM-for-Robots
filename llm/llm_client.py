from __future__ import annotations
import threading
import os
import json
from typing import Optional, Dict, Any
from typing import Any
from llama_cpp import Llama

from config.settings import CONTEXT_LLM,THREADS_LLM,N_BACH_LLM,GPU_LAYERS_LLM,CHAT_FORMAT_LLM
from config.llm_system_prompt_def import NAVIGATE_SYSTEM_PROMPT, GENERAL_SYSTEM_PROMPT

class LLM:
    def __init__(self, model_path:str, system_prompt: str | None = None):
        self.system = system_prompt or GENERAL_SYSTEM_PROMPT
        self._llm = None
        self._lock = threading.Lock()

        # Defaults sensatos (CPU-only). Ajusta por env si quieres.
        self.model_path = model_path
        self.ctx = CONTEXT_LLM         # contexto razonable
        self.threads = THREADS_LLM
        self.n_batch = N_BACH_LLM   # 256–512 bien en CPU
        self.n_gpu_layers = GPU_LAYERS_LLM  # 0 si no hay CUDA
        self.chat_format = CHAT_FORMAT_LLM.strip()

    def ensure(self):
        """ Initialize the LLM instance if not already done """
        if self._llm is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
            kwargs = dict(
                model_path=self.model_path,
                n_ctx=self.ctx,
                n_threads=self.threads,
                n_batch=self.n_batch,
                n_gpu_layers=self.n_gpu_layers,
                use_mmap=True,
                use_mlock=False,
                verbose=False,
            )
            if self.chat_format:
                kwargs["chat_format"] = self.chat_format
            self._llm = Llama(**kwargs)

    def answer_general(self, user_prompt: str) -> str:
        """ Answer a general question with the LLM """
        self.ensure()
        general_system = GENERAL_SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": general_system},
            {"role": "user", "content": user_prompt},
        ]
        with self._lock:
            out = self._llm.create_chat_completion(
                messages=messages,
                temperature=0.2,
                top_p=0.9,
                max_tokens=100,
            )
        msg = out["choices"][0]["message"]
        return (msg.get("content") or "").strip() or "No tengo una respuesta."
    
    def plan_motion(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """ Given a user prompt, return a dict with 'yaw' (radians) and 'distance' (meters), or None if not understood """
        self.ensure()
        system = NAVIGATE_SYSTEM_PROMPT
        
        messages = [
            {"role":"system","content": system},
            {"role":"user","content": user_prompt},
        ]
        tools = [{
            "type": "function",
            "function": {
                "name": "plan_motion",
                "description": "Devuelve yaw, distance y flag",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "yaw":      {"type": "number", "description": "Rotación, izquierda negativa, derecha positiva."},
                        "distance": {"type": "number", "description": "Distancia en m."},
                        "flag":     {"type": "bool", "description": "Si yaw es radianes return False, si yaw es grados return True"}
                    },
                    "required": ["yaw", "distance", "flag"]
                }
            }
        }]
        with self._lock:
            out = self._llm.create_chat_completion(
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.0,
                top_p=0.8,
                max_tokens=64,
            )
        msg = out["choices"][0]["message"]

        # llama.cpp puede devolver tool_calls o function_call
        tc = msg.get("tool_calls") or []
        if tc:
            fn = (tc[0].get("function") or {})
            if fn.get("name") == "plan_motion":
                args = fn.get("arguments") or "{}"
                return json.loads(args) if isinstance(args, str) else (args or None)

        fc = msg.get("function_call")
        if fc and fc.get("name") == "plan_motion":
            args = fc.get("arguments") or "{}"
            return json.loads(args) if isinstance(args, str) else (args or None)

        return None