import re
import unicodedata
from typing import List, Dict, Any, Optional, Iterable
from .llm_patterns import (COURTESY_RE, MOV_VERB_RE, BATTERY_WORDS_RE,POSE_WORDS_RE,
                           BEST_CONNECTOR_RE, NEXOS_RE, SPLIT_RE, MOVE_PREFIX_RE, TAIL_NEXOS_TRIM_RE, 
                           ARTICLE_PREFIX_RE, INTENT_RES, INTENT_PRIORITY, INTENT_ROUTING)

def norm_text(s: str) -> str:
    """ Normalize text for matching:
    - lowercase
    - remove accents
    - remove punctuation (keep spaces)
    - remove courtesy words (por favor, gracias, etc)
    - collapse multiple spaces"""

    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode("ascii")
    s = re.sub(r'[^a-z0-9 ]+',' ', s.lower())
    s = COURTESY_RE.sub(' ', s)
    return re.sub(r'\s+',' ', s).strip()

def extract_place_query(t: str) -> str:
    """ From a text with a navigation intent, extract the place name or description.
    E.g. "ve a la cocina y luego para en el salón" -> "cocina" """
    t = norm_text(t)
    # quita prefijo al inicio (ve/dirígete/dónde queda/etc.)
    t = MOVE_PREFIX_RE.sub('', t, count=1).strip()

    m = BEST_CONNECTOR_RE.search(t)
    if m:
        place = m.group(1).strip()
    else:
        # sin conector: corta la "cola" desde un nexo
        place = TAIL_NEXOS_TRIM_RE.sub('', t).strip()

    # opcional: quita artículo inicial (si tu KB NO guarda artículos)
    place = ARTICLE_PREFIX_RE.sub('', place).strip(" .,:;!?\"'")

    return place

def best_hit(res) -> Dict[str, Any]:
    """ From the result of kb.loockup (dict or list of dicts), return the best one (highest score)"""
    if isinstance(res, list) and res:
        return max((x for x in res if isinstance(x, dict)), key=lambda x: x.get('score', 0.0), default={})
    return res if isinstance(res, dict) else {}

def detect_intent(t: str, order: Optional[Iterable[str]] = None, normalizer=None) -> Optional[str]:
    nt = normalizer(t) if normalizer else t
    for name in (order or INTENT_PRIORITY):
        rex = INTENT_RES.get(name)
        if rex and rex.search(nt):
            return name
    return None

def split_and_prioritize(text: str, kb) -> List[Dict[str, Any]]:
    """
    From a text, split it into clauses (by connectors) and classify each clause
    into an action type: "battery", "pose", "navigate", "general", or
    "rag" (if a high-confidence KB answer is found).
    Return a list of actions with parameters, prioritizing short answers first.

    E.g. "Por favor ve a la cocina y luego dime tu batería" ->
    [{"kind": "battery", "params": {}},
     {"kind": "navigate", "params": {"data": "ve a la cocina"}}]    
    """
    t = norm_text(text)

    parts = SPLIT_RE.split(t)
    clauses = [p.strip() for p in parts if p and not NEXOS_RE.fullmatch(p.strip())]

    accions = []
    for c in clauses:
        # 1) Respuestas cortas por KB si hay alta confianza
        var = best_hit(kb.loockup(c))
        if var.get('answer') and var.get('score', 0.0) >= 0.75:
            accions.append(("corto", "rag", {"data": var['answer'].strip()}))
            continue
        intent = detect_intent(c, order=INTENT_PRIORITY, normalizer=norm_text)
        spec = INTENT_ROUTING.get(intent)
        
        if spec:
            params = {"data": c} if spec.get("needs_clause") else {}
            accions.append((spec["kind_group"], spec["kind"], params))
        else:
            accions.append(("largo", "general", {"data": c}))

    # Primero cortas, luego largas (orden estable preservado)
    accions.sort(key=lambda x: 0 if x[0] == "corto" else 1)
    return [{"kind": k, "params": p} for _, k, p in accions]