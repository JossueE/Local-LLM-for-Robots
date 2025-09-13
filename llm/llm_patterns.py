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

COURTESY_RE = re.compile(
    r"\b(?:"
    r"por\s+favor|porfa(?:vor|s)?|porfis|"
    r"gracias(?:\s+de\s+antemano)?|muchas\s+gracias|please|"
    r"disculp(?:a|ame)|perdon(?:ame)?|"
    r"hola|buen(?:os|as)\s+(?:dias|tardes|noches)|"
    r"me\s+puedes\s+decir|me\s+podrias\s+decir|puedes\s+decirme|podrias\s+decirme|"
    r"puedes|podrias|"
    r"dime|cuentame|indica(?:me)?"
    r")\b"
)

#------------------------ Movement verbs - Navigation  ------------------------#

ORIENT_INTENT_RE = re.compile(r"""
(?xi)
\b(
    donde\s+(?:queda|esta)        
  | orienta(?:r|te|rte)?          
  | apunta(?:r)?                  
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

#------------------------ Pose verbs - Pose ------------------------#
POSE_WORDS_RE = re.compile(r"""
(?xi)
\b(
    pose(?:2d|3d)? |
    posicion(?:\s+actual)? | ubicacion(?:\s+actual)? |
    where\s+are\s+you | donde\s+estas | donde\s+te\s+encuentras |
    orientacion(?:\s+actual)? | angulo | theta | rumbo | heading | bearing |
    yaw | roll | pitch | posee | poseen |
    coordenadas? | coordenades? |
    odom(?:etria|etry)? | odom\b | amcl | tf\b | frame\b | base[_\s-]?link | map\b
)\b
""")
#------------------------ New Patterns  ------------------------#

"""Here you can define new patterns using regex."""

# ______________________Cases that we want to execute_________________________________

#Here we define the functions, with the corresponding patterns, that we want to execute
INTENT_RES = {
    "battery":   BATTERY_WORDS_RE,
    "pose":      POSE_WORDS_RE,
    "navigate":  MOV_VERB_RE,
}

#Here we define the priority of the functions to be executed
INTENT_PRIORITY = ("battery", "pose", "navigate")

# kind_group: "corto" (short) == first or "largo" (long) == second determine wich works are executed first
# needs_clause: True == needs the query to process the action, False == does not need it

INTENT_ROUTING = {
    "battery":  {"kind_group": "corto", "kind": "battery",  "needs_clause": False},
    "pose":     {"kind_group": "corto", "kind": "pose",     "needs_clause": False},
    "navigate": {"kind_group": "largo", "kind": "navigate", "needs_clause": True},
}