# LLM Module
Local-LLM-for-Robots **LLM module** is the language-and-tools brain that interprets user intents and either answers directly or calls robot tools (battery, pose, navigation) to act. It’s designed to run **fully local** (e.g., via `llama.cpp`/Qwen) and to plug neatly into the project’s STT and TTS pipeline. 

---

## Simple Query Pipeline

This is how a user query flows through the LLM module:

1. **Receive the query**  
   The raw text from the user enters the LLM pipeline.

2. **Detect the intent** (`llm/lm_intentions.py`)  
   The module analyzes the text and determines what the user wants.  
   It uses patterns declared in **`llm/llm_patterns.py`** to match known intents.

3. **Route to the handler** (`llm/llm_router.py`)  
   Based on the detected intent, the router dispatches the request to the
   appropriate handler function.

4. **Call tools / publish data (if needed)** (`llm/llm_tools.py`)  
   If the handler needs robot data or must publish information (e.g., battery,
   pose, navigation), it invokes the corresponding tool function defined here.

---

## ⚙️ Configuration

### 🔧 General Settings (`config/settings.py`)
All runtime settings live in **`config/settings.py`**. They are plain Python constants—edit the file and restart your nodes to apply changes.

### 🤖 Change the model (`config/models.yml`)

You have to modify this section. 
- **name:** exact final filename (with extension) your loader expects on disk. Must match exactly (case/spaces/underscores).  
- **url:** direct downloadable link to that file (not an HTML page). If it’s an archive, ensure extraction produces the exact `name`.

```yaml
llm:
#Qwen Models
  - name: qwen2.5-3b-instruct-q4_k_m.gguf
    url: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf?download=true
```

In the case that you want to add more models in the same yaml. Like this.
```yaml
llm:
#Qwen Models
  - name: qwen2.5-3b-instruct-q4_k_m.gguf
    url: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf?download=true
  - name: New Model Name
    url: New Url
```
Run the downloader to add new models:

```bash
cd Local-LLM-for-Robots 
bash utils/download_models.sh
```

In `llm/llm.py` (or `main.py`), pick by index from `ensure_model("llm")`:

```python
from utils.utils import LoadModel
model = LoadModel()
paths = model.ensure_model("llm")   # returns a list of local paths (same order as YAML)

app = LlmAgent(model_path=str(paths[0]))  # 0 = first (old) model
# app = LlmAgent(model_path=str(paths[1]))  # 1 = second (new) model

```

> [!IMPORTANT]
> If you switch to a **different model family (not Qwen2)**, update `ensure(self)` in `llm/llm_client.py` to:
> - pick the right file from your YAML (by index or name), and
> - apply model-specific settings (backend/loader, chat template/system prompt, stop/EOS tokens, context size).
> Otherwise it may still load or format prompts as if it were Qwen2.

---

## 🛠️ Add a New Intent / Tool
The flow is: **patterns → intent detection → router → tool implementation**.
Your text is normalized (`norm_text`) before matching (lowercase, accents removed, courtesy words stripped), so keep patterns simple.

---
### 1) Declare patterns in `llm_patterns.py` 
Add a compiled regex that captures the trigger words for your new intent (example: “time” intent).

```python
# llm_patterns.py
import re

TIME_WORDS_RE = re.compile(r"""
(?xi)
\b(
    hora|que\s+hora|time|current\s+time
)\b
""")
```
Add to the pattern executor
```python
# ______________________Cases that we want to execute_________________________________

#Here we define the functions, with the corresponding patterns, that we want to execute
INTENT_RES = {
    "battery":   BATTERY_WORDS_RE,
    "navigate":  MOV_VERB_RE,
    "time":      TIME_WORDS_RE,             #<- NEW
}

#Here we define the priority of the functions to be executed
INTENT_PRIORITY = ("time", "battery", "navigate") #<- NEW

# kind_group: "first" (short) == first or "second" (long) == second determine wich works are executed first
# need_user_input: True == needs the query to process the action, False == does not need it

INTENT_ROUTING = {
    "time":     {"kind_group": "first", "kind": "time",     "need_user_input": False},
    "battery":  {"kind_group": "first", "kind": "battery",  "need_user_input": False},
    "navigate": {"kind_group": "second", "kind": "navigate", "need_user_input": True},
}
```
---

### 2) Implement the tool in `llm_tools.py` (class GetInfo)
Tools that should be spoken by **TTS should return a string**
(if you return a dict, your loop will JSON-dump it).

```python
def tool_get_time(self) -> str:
    from datetime import datetime
    now = datetime.now()
    return now.hour:02d, now.minute:02d 
```

- Add the new function to the `handle` in `llm_router.py`

---

### 3) Wire it into the router
Pass the tool to the `Router` constructor and handle it in `llm_router.py`.

```python

# llm_router.py
class Router:
  . . .
  self.get_info = get_info
  self.handlers: Dict[str, Callable[[str], str]] = {
    "rag": self.data_return,
    "general": self.general_response_llm,
    "battery": self.battery_publisher,
    "navigate": self.navigation_publisher,
    "time": self.publish_time,             #<- NEW
  }
    . . .
    #------------ Handler or Router ------------------- 
    def handle(self, data: str, tipo: str) -> str:
       . . .

    #-------------The Publishers-------------------------
    def publish_time(self, data: str)-> str:                 #<- NEW
      hours, minutes = self.get_info.tool_get_time() 
      return f"Son las {hours}:{minutes}"

```
--- 
## 🗂️ Add New Data
---

All data lives in `config/data/` as **JSON**.

> [!TIP]
> When adding values, **store them in lowercase** (and normalize inputs to lowercase) to ensure consistent matching.
> The system is prepared to receive unnormalized text, but I recommend normalizing it for greater reliability.

### General Q&A (RAG)
Add entries to `config/data/general_rag.json`:

```json
{
  "triggers": [
    "question you want to add",
    "variant 1",
    "variant 2"
  ],
  "answer": "expected output"
}

```
### Places / Waypoints

Add entries to `config/data/poses.json`:
```json
{
  "name": "New Place",
  "aliases": ["Variant 1", "Variant 2"],
  "x": 1.5,
  "y": -0.5,
  "yaw": 90.0,
  "frame_id": "map"
}
```

### 📦 Create a New Data Source
- **Add your JSON** to `config/data/your_file.json`.
- **Define a loader & lookup** in `llm/llm_data.py`.

```python
# llm/llm_data.py
import json
from pathlib import Path

class YourData:
    def __init__(self, path: Path = Path("config/data/your_file.json")): #This path should be added to 'config/setting.py'
        self.items = []

    def load_json(self):
        with open(self.path, "r", encoding="utf-8") as f:
            self.items = json.load(f)

    def lookup(self, query: str):
        # TODO: implement your matching logic (exact, fuzzy, etc.)
        # Return the best match or None
        q = query.lower().strip()
        return next((it for it in self.items if q in it.get("name","").lower()), None)

```
- **Expose helpers** in `llm/llm_tools.py`:

```python
# llm/llm_tools.py
from llm.llm_data import YourData

class GetInfo:
    def __init__(self):
        self.your_data = YourData()
        self.your_data.load_json()

    def tool_get_from_your_data(self, query: str):
        return self.your_data.lookup(query)
```
- **Wire into the router** (`llm/llm_router.py`):
    - Add a handler that calls `tool_get_from_your_data.`
    - Add/extend patterns in `llm_patterns.py` to trigger this `intent`.

```python
# llm/llm_router.py (excerpt)
self.handlers: Dict[str, Callable[[str], str]] = {
    "your_intent": self.handle_your_intent
}

def handle_your_intent(self, data: str):
    result = self.get_info.tool_get_from_your_data(data)
    return result or "No match found."

```

> [!NOTE]
> Keep names consistent: `load_json()` for loading, `lookup()` for searching. Avoid trailing commas in JSON.

---

## 🧠 Implement or Modify the LLM Agents

---

You can define new agents by (1) adding a system prompt and (2) exposing a tool the model can call.

- All the system_prompts lives in `config/llm_system_prompt_def.py`. Create or edit one there:

```python
# config/llm_system_prompt_def.py
NEW_SYSTEM_PROMPT = (
    "You are Octopy's LED helper. "
    "When the user asks to turn an LED on or off, always use the set_led tool."
)
```
- **Expose a simple tool** (example: `set_led`)
    - Below is a **minimal agent method** that lets the model call a function named `set_led(color, on)`.

```python
# inside your LLM wrapper class
import json
from typing import Optional, Dict, Any
from config.llm_system_prompt_def import NEW_SYSTEM_PROMPT

def set_led_call(self, user_prompt: str) -> Optional[Dict[str, Any]]:
    """
    Returns: {"color": "<red|green|blue>", "on": true|false} or None
    """
    self.ensure()  # make sure the backend LLM is ready
    system = NEW_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_prompt},
    ]

    tools = [{
        "type": "function",
        "function": {
            "name": "set_led",
            "description": "Turn an LED on or off with a given color.",
            "parameters": {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "description": "LED color",
                        "enum": ["red", "green", "blue"]
                    },
                    "on":   {
                        "type": "boolean",
                        "description": "True to turn on, False to turn off"
                    }
                },
                "required": ["color", "on"]
            }
        }
    }]

    with self._lock:
        out = self._llm.create_chat_completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.0, # + = more creativity / - = less creativity
            top_p=0.8,       # + = more creativity / - = less creativity
            max_tokens=64, # max_tokens of the response 
        )

    msg = out["choices"][0]["message"]

    # llama.cpp may return either `tool_calls` or `function_call`
    tc = msg.get("tool_calls") or []
    if tc:
        fn = (tc[0].get("function") or {})
        if fn.get("name") == "set_led":
            args = fn.get("arguments") or "{}"
            return json.loads(args) if isinstance(args, str) else (args or None)

    fc = msg.get("function_call")
    if fc and fc.get("name") == "set_led":
        args = fc.get("arguments") or "{}"
        return json.loads(args) if isinstance(args, str) else (args or None)

    return None

```

- **Wire into the router** (`llm/llm_router.py`):
    - Add/extend patterns in `llm_patterns.py` to trigger this `intent`.

```python
# llm/llm_router.py (excerpt)
self.handlers: Dict[str, Callable[[str], str]] = {
    "LED": self.led_function
}

def led_function(self, data: str):
    return self.llm.set_led_call(data) 

```
---


