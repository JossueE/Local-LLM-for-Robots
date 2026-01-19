import re

#------------------------ Nexos ------------------------#
NEXOS_RE = re.compile(r"(?i)\b(?:y|luego|despues|entonces)\b")

#------------------------ Connectors ------------------------#
# (Simplified split pattern just for connectors)
SPLIT_RE = re.compile(r"(?i)\b(?:y\s+)?(?:luego|despues|entonces)\b")

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
  porfa(?:vor|s)?|porfis|porfai|por\s+fis|
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
  (?:me\s+)?podr[íi]as?\s+(?:decir|explicar|ayudar|indicar|repetir|confirmar)(?:me|nos)?|
  (?:me\s+)?puedes?\s+(?:decir|explicar|ayudar|indicar|repetir|confirmar)(?:me|nos)?|
  me\s+(?:ayudas?|apoyas?)\s+(?:con|a)\b|
  te\s+encargo\b|
  d[ií]me|d[ií]game|
  cu[ée]ntame|
  ind[íi]came|ind[íi]queme|

  # deseos/formulaciones suaves
  quisier[ai](?:\s+saber)?|
  me\s+gustar[íi]a\s+saber
)
(?!\w)                                  # borde derecho
""", re.IGNORECASE | re.VERBOSE)