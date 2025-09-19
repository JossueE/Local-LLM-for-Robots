import re

#------------------------ Nexos ------------------------#

NEXOS_RE = re.compile(r"(?i)\b(?:y|luego|despues|entonces)\b")


#------------------------ Connectors ------------------------#

BEST_CONNECTOR_RE = re.compile(r"""
(?xi)
(?:^|\b)
(?: a | al | a\s+(?:la|los|las)
  | en(?:\s+(?:el|la|los|las))?
  | hacia | hasta | rumbo(?:\s+a)?
)
\s+
(?:el|la|los|las)?\s*
(.+?)                               
(?=\s+(?:y|luego|despues|entonces)\b|\s*$)
""")

ARTICLE_PREFIX_RE = re.compile(r'^(?:el|la|los|las)\s+', flags=re.I)

TAIL_NEXOS_TRIM_RE = re.compile(r'\s+(?:y|luego|despues|entonces)\b.*$', flags=re.I)

#------------------------ Courtesy words ------------------------#

COURTESY_RE = re.compile(r"""
(?ix)                                   # i: ignorecase, x: verbose
(?<!\w)                                  # borde izquierdo (no carácter de palabra)
(?:

  # --- SALUDOS / LLAMADAS DE ATENCIÓN ---
  hola|
  buen(?:os|as)?\s+d[ií]as|buenas?\s+tardes|buenas?\s+noches|buen\s+d[ií]a|
  que\s+tal|
  oye|oiga|oigan|
  con\s+permiso|

  # --- “POR FAVOR” Y VARIANTES ---
  por\s+favor|de\s+favor|favor\s+de|
  porfa(?:vor|s)?|porfis|porfai|por\s+fice|
  please|pl[ií]s|

  # --- GRACIAS Y CIERRES CORTESÍA ---
  muchas?\s+gracias|mil\s+gracias|
  gracias(?:\s+de\s+antemano)?|
  se\s+agradece|
  saludos(?:\s+cordiales)?|

  # --- DISCULPAS ---
  disculp(?:a|e|en|ame|eme)|
  perd[óo]n(?:a|e|en|ame|eme)?|

  # --- ATENUADORES / SUAVIZADORES ---
  (?:si\s+)?fueras?\s+tan\s+amable(?:\s+de)?|
  ser[íi]as?\s+tan\s+amable(?:\s+de)?|
  ser[íi]a\s+posible\s+que|
  te\s+importar[íi]a|
  si\s+no\s+es\s+molestia|
  cuando\s+(?:puedas?|gustes?|tengas?\s+tiempo)|

  # --- PATRONES DE PETICIÓN COMUNES ---
  # me podrías/puedes + verbo (decir/explicar/ayudar/indicar/repetir/confirmar)
  (?:me\s+)?podr[íi]as?\s+(?:decir|explicar|ayudar|indicar|repetir|confirmar)(?:me|nos)?|
  (?:me\s+)?puedes?\s+(?:decir|explicar|ayudar|indicar|repetir|confirmar)(?:me|nos)?|

  # me ayudas/apoyas con|a ...
  me\s+(?:ayudas?|apoyas?)\s+(?:con|a)\b|

  # te encargo + sustantivo/acción
  te\s+encargo\b|

  # verbos solos típicos de trato cortés (imperativos muy comunes)
  d[ií]me|d[ií]game|
  cu[ée]ntame|
  ind[íi]came|ind[íi]queme|

  # deseos/formulaciones suaves
  quisier[ai](?:\s+saber)?|
  me\s+gustar[íi]a\s+saber

)
(?!\w)                                  # borde derecho
""", re.IGNORECASE | re.VERBOSE)

#------------------------ Movement verbs - Navigation  ------------------------#

ORIENT_INTENT_RE = re.compile(r"""
(?xi)
\b(
    donde\s+(?:queda|esta)        
  | orienta(?:r|te|rte)?          
  | apunta(?:r)?   
  | in+di+ca(?:r|me|te)?                
  | se+n+ala(?:r|me|te)?          
)\b
""")

MOV_VERB_CORE = r"""
(?: 
    ve(?:\s+a)? | vete | vayan | vamos | vamonos | ir(?:se)? |
    anda(?:r)? | camina(?:r)? | marcha(?:r)? | pasa(?:r)? | cruza(?:r)? |
    a[bv]anza(?:r)? | avanz[ao]? | abanza | retrocede(?:r)? | regresa(?:r)? | vuelve(?:r)? |
    mueve(?:te)? | mover(?:se)? | desplaza(?:te|r)? |
    dirigete | dirijete | dirigir(?:se)? | encaminate | encaminar(?:se)? |
    orienta(?:r|rte|rse)? | apunta(?:r)? |
    gira(?:r)? | gier[a]? | voltea(?:r)? | dobla(?:r)? |
    se+n+ala(?:r)? | senala(?:r)? | ubica(?:te|r)? | localiza(?:r)? |
    lleva(?:me|nos|lo|la|les)? | llevar(?:me|nos|lo|la|les)? |
    rumbo(?:\s+a)? | hasta | hacia | a\s*donde | adonde | donde(?:\s+queda)? | dondede
)
"""

MOV_VERB_RE = re.compile(rf"\b{MOV_VERB_CORE}\b", flags=re.IGNORECASE | re.VERBOSE)

# If in other part you use a trim ONLY at the beginning ("go to...", "where is..."):
MOVE_PREFIX_RE = re.compile(rf"""
^
(?:
    {MOV_VERB_CORE} |           # imperativos/verbos
    donde\s+(?:queda|esta) |    # preguntas
    a\s*donde | adonde
)
(?:\s+(?:a|hacia|hasta|rumbo(?:\s+a)?))?
\s+
""", flags=re.IGNORECASE | re.VERBOSE)


# Split by connectors; "y" only if it introduces another movement action
SPLIT_RE = re.compile(rf"""
(?xi)
\b(?: 
    (?:y\s+)?(?:luego|despues|entonces)  
  | y(?=\s+{MOV_VERB_CORE}\b)
)\b
""")

#------------------------ Cancel Navigation -----------------------------#

CANCEL_NAVIGATION_RE = re.compile(r"""
(?xi)
\b(
    # Español — formas directas
    cancela(?:r)?(?:\s+(?:la\s+)?
        (?:navegaci[oó]n|ruta|misi[oó]n|trayecto|viaje|objetivo|destino)
    )?
  | cancelar(?:\s+(?:la\s+)?
        (?:navegaci[oó]n|ruta|misi[oó]n|trayecto|viaje|objetivo|destino)
    )
  | aborta(?:r)?(?:\s+(?:la\s+)?
        (?:navegaci[oó]n|ruta|misi[oó]n|objetivo|destino)
    )?
  | det[eé]n(?:te)?(?:\s+ya)?        # detén / detente / detente ya
  | det[eé]ngase
  | detener(?:\s+(?:la\s+)?
        (?:navegaci[oó]n|ruta|trayecto|viaje)
    )?
  | para(?:te)?(?:\s+ya)?            # para / párate / párate ya
  | alto
  | quiet[oa]                         # quieto / quieta
  | qu[eé]date\s+quiet[oa]
  | espera(?:\s+(?:tantito|un\s+momento))?

    # Negaciones de movimiento
  | no\s+te\s+(?:muevas|vayas)
  | no\s+vayas
  | ya\s+no\s+(?:vayas|sigas|contin[uú]es|avances|camines|te\s+muevas)
  | deja\s+de\s+(?:navegar|moverte|avanzar|caminar|seguir)

    # “Objetivo/destino”
  | (?:borra|quita|elimina)\s+(?:el\s+)?(?:objetivo|goal|destino)
  | (?:cancela|cancelar)\s+(?:el\s+)?(?:objetivo|goal|destino)
)\b
""")

#------------------------ Baterry verbs - Battery ------------------------#

BATTERY_WORDS_RE = re.compile(r"""
(?xi)
\b(
    bateria|battery|pila|
    nivel\s+de\s+(?:bateria|pila)|
    estado\s+(?:de\s+)?(?:bateria|pila|carga)|
    (?:porcentaje|percent(?:age)?)\s+(?:de\s+)?(?:bateria|pila)|
    cu[aá]nta?\s+(?:bateria|pila|carga)\s+(?:queda|tienes|te\s+queda)|
    how\s+much\s+(?:battery|charge)\s+(?:left|remaining)|
    battery\s+(?:level|status)|
    state\s+of\s+charge|soc
)\b
""")

#------------------------ New Patterns  ------------------------#

"""Here you can define new patterns using regex."""

# ______________________Cases that we want to execute_________________________________

#Here we define the functions, with the corresponding patterns, that we want to execute
INTENT_RES = {
    "battery":   BATTERY_WORDS_RE,
    "navigate":  MOV_VERB_RE,
    "cancel_navigate": CANCEL_NAVIGATION_RE,
}

#Here we define the priority of the functions to be executed
INTENT_PRIORITY = ("battery", "cancel_navigate", "navigate")

# kind_group: "first" (short) == first or "second" (long) == second determine wich works are executed first
# need_user_input: True == needs the query to process the action, False == does not need it

INTENT_ROUTING = {
    "battery":         {"kind_group": "first", "kind": "battery",  "need_user_input": False},
    "navigate":        {"kind_group": "second", "kind": "navigate", "need_user_input": True},
    "cancel_navigate": {"kind_group": "first", "kind": "cancel_navigate", "need_user_input": False},
}