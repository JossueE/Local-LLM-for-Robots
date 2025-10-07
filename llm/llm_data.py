import json
from typing import List, Dict, Any
from difflib import SequenceMatcher
from dataclasses import dataclass 
from rapidfuzz import fuzz as rf_fuzz
HAS_RF = True


from config.settings import FUZZY_LOGIC_ACCURACY_GENERAL_RAG, FUZZY_LOGIC_ACCURACY_POSE
from llm.llm_intentions import norm_text, extract_place_query

@dataclass
class Battery:
    def __init__(self, percentage: float | None = None):
        self.percentage = percentage

class Pose: 
    def __init__(self, x: float, y: float, yaw: float = 0.0, frame_id: str = "map", name: str = ""):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.frame_id = frame_id
        self.name = name

class GENERAL_RAG:
    def __init__(self, path: str):
        self.items: List[Dict[str,str]] = []
        self.load(path)
    
    def load(self, path: str) -> None:
        """ Load the GENERAL_RAG from a JSON file or line-separated JSON objects """
        print("[llm_data] Cargando GENERAL_RAG", flush=True)
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read().strip()

            try:
                obj = json.loads(txt)
                items: List[Dict[str,str]] = []
                
                if isinstance(obj, dict):
                    for _, lst in obj.items():
                        if isinstance(lst, list):
                            for it in lst:
                                ans = it.get('answer','')
                                for trig in it.get('triggers',[]):
                                    trig = norm_text(trig, False)
                                    if trig and ans:
                                        items.append({'q': trig, 'a': ans})
                elif isinstance(obj, list):
                    items = obj
                self.items = items
            except json.JSONDecodeError:
                self.items = [json.loads(line) for line in txt.splitlines() if line.strip()]
                print("[llm_data] No se pudo cargar", flush=True)
        except Exception as e:
            self.items = []
            print("[llm_data] No se pudo abrir", flush=True)
    
    def lookup(self, query: str) -> Dict[str, Any]:
        """ Simple exact or fuzzy match in the GENERAL_RAG. Returns dict with 'answer' and 'score' (0.0–1.0) """
        if not self.items:
            return {"error":"general_rag_vacia","answer":"","score":FUZZY_LOGIC_ACCURACY_GENERAL_RAG}
        query = norm_text(query, False)
        best, best_s = None, 0.0

        for item in self.items:
            q = item.get('q','')
            fuzzy = (rf_fuzz.ratio(query, q)/100.0) if HAS_RF else SequenceMatcher(None, query, q).ratio()
            s = fuzzy
            if s > best_s:
                best, best_s = item, s
        print(f"[llm_data] GENERAL_RAG lookup '{query}' -> '{best.get('a','') if best else ''}' ({best_s})", flush=True)
        if best and best_s >= FUZZY_LOGIC_ACCURACY_GENERAL_RAG:
            return {"answer": best.get('a',''), "score": round(best_s,3)}
        return {"answer":"","score": round(best_s,3)}


class PosesIndex:
    def __init__(self, path: str):
        self.by_key: Dict[str,Pose] = {}
        self.load(path)

    def load(self, path: str):
        """ Load poses from a JSON file with a list of poses with 'name', 'x', 'y', 'yaw_deg', 'frame', and optional 'aliases' """
        print("[llm_data] Cargando Poses", flush=True)
        try:
            with open(path,'r',encoding='utf-8') as f:
                data = json.load(f)
            for p in data.get('poses', []):
                pose = Pose(x=p.get('x'), y=p.get('y'), yaw=p.get('yaw_deg',0.0), frame_id=p.get('frame','map'), name=p.get('name',''))
                keys = [p.get('name','')] + p.get('aliases',[])
                for k in keys:
                    nk = norm_text(k, True)
                    if nk:
                        self.by_key[nk] = pose
        except Exception:
            self.by_key = {}
            print("[llm_data] No se pudo cargar las poses", flush=True)

    def lookup(self, name: str) -> Dict[str,Any]:
        """ Exact or fuzzy match of a place name to a Pose. Returns the Pose as dict, or {'error':'no_encontrado'} """
        key = norm_text(extract_place_query(name) or name, True)
        #print(f"[llm_tools] {self.by_key}", flush=True)
        if key in self.by_key:
            p = self.by_key[key]
            #print(f"[llm_tools] {p}", flush=True)
            return p.__dict__
        # fuzzy simple
        best_k, best_s = None, 0.0
        for k in self.by_key.keys():
            s = (rf_fuzz.ratio(key,k)/100.0) if HAS_RF else SequenceMatcher(None, key, k).ratio()
        if s > best_s:
            best_k, best_s = k, s
        if best_k and best_s >= FUZZY_LOGIC_ACCURACY_POSE:
            return {**self.by_key[best_k].__dict__, "note":"fuzzy"}
        return {"error":"no_encontrado"}