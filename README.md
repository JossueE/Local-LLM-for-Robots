# Local LLM for Robots 🤖🦾

[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


**Local-LLM-for-Robots** is a python package that fuses a local Large Language Model with a full offline speech pipeline so robots can understand and respond to natural language without the cloud.

---
## 📝 Flowchart
<div style="overflow:auto; border:1px solid #eaecef; padding:6px;">
  <object data="Diagrama de Flujo.svg" type="image/svg+xml" width="4400">
    <!-- Fallback para visores viejos -->
    <img src="/docs/Diagrama de Flujo.svg" alt="Flowchart" />
  </object>
</div>

<p align="right">
  <a href="https://lucid.app/lucidchart/50ed3019-62f3-460d-a3e3-071d72727e35/view">Open in real size</a>
</p>

---

## 📚 Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing) 
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

<h2 id="installation">🛠️ Installation</h2>
> [!IMPORTANT]
> Ensure ROS2 Humble and Python ≥3.10 are installed before continuing.

### Prerequisites
- Ubuntu 22.04
- Python 3.10.12 
- Git, CMake, colcon
- (Optional) NVIDIA CUDA for GPU acceleration

### Setup
```bash
sudo apt update
sudo apt install -y python3-dev python3-venv build-essential portaudio19-dev curl unzip ffmpeg
sudo snap install yq
```

```bash
# Clone the repository
git clone https://github.com/JossueE/Local-LLM-for-Robots.git 
cd Local-LLM-for-Robots
bash utils/download_models.sh

```
```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate
```
> [!TIP]
> Whit (.venv) Active

```bash
# Install dependencies
pip install -r requirements.txt
```

Check if the models were downloaded right:

```bash
cd Local-LLM-for-Robots && bash utils/download_models.sh
```
The script installs everything into your cache (`~/.cache/octopy`, or `$OCTOPY_CACHE` if set).
You’re done when you see:
```bash
"OK. Modelos listos en: $CACHE_DIR ✅ "
```
---

<h2 id="configuration">⚙️ Configuration</h2>

> [!WARNING] 
> LLMs and audio models can be large. Ensure you have enough **disk space** and **RAM/VRAM** for your chosen settings.

### 🔧 General Settings (`config/config.py`)
All runtime settings live in **`config/config.py`**. They are plain Python constants—edit the file and restart your nodes to apply changes.

### 📦 Model catalog (`config/models.yml`)
Define which models Octybot uses (LLM, STT, TTS, wake-word) along with their URLs and sample rates.

### 🔗 Sytem Prompt Definition with `config/llm_system_prompt_def.py`
To re-write or define a new **LLM - System Prompt**  

### 🌎 Data for Commun Questions and Places in a Map
All general questions live in `config/general_rag.json`. Define the **New Question** in `triggers` and define the `answer`.

<h2 id="quick-start">⚡ Quick Start</h2>

### Launch the full pipeline (Wake-Word → STT → LLM → TTS)

Start everything with:

```bash
python -m main
```
Now say `ok robot` — the system will start listening and run the pipeline.

### Run a Single Module’s Tests

```bash
cd Local-LLM-for-Robots 
```

LLM Module
```bash
python -m llm.llm
```

Speech to Text Module
```bash
#To test the Audio Listener 
python -m stt.AudioListener

#To test the Wake Word Detector
python -m stt.wake_word

#To test the Speech To Text
python -m stt.speech_to_text
```

Text to Speech Module
```bash
python -m tts.text_to_speech
```

> [!TIP]
> If you have some problems to launch modules, you should try to run with the `venv` as `./.venv/bin/python -m stt.speech_to_text`

<h2 id="usage">🧪 Usage</h2>

### LLM Module

#### Agent intents (`handle(data, tipo)`)
| `tipo`     | What it does | Input `data` | Output shape |
|---|---|---|---|
| `rag` | Returns `data` as-is (external RAG already resolved). |  Pre-composed **string** from your RAG - `general_rag.json`| `str` |
| `general` | Free-form Q&A via `llm.answer_general`. | Question | `str` |
| `battery` | Reads `%` via `tool_get_batt()`. | Reads `Battery` status| `str` like `Mi batería es: 84.0%` (or no-reading msg) |
| `pose` | Reads AMCL pose via `tool_get_pose()`. | Reads `Pose` status | `str` (no pose) **or** JSON `{"x","y","yaw_deg","frame"}` |
| `navigate` | Navigate to a named place or generate a short motion. Tries `tool_nav(data)` first (GENERAL_RAG/`poses.json`): if found, replies **"Voy"** (execute) or **"Por allá"** (indicate/simulate). If not found, falls back to `llm.plan_motion(data)` → `_clamp_motion(...)` → `natural_move_llm(...)`. | Pre-composed string from your RAG - poses.json and `str` Natural-language place or motion command (e.g., `ve a la enfermería`, `gira 90° y avanza 0.5 m`). | Usually `str`. On fallback may return a **tuple**: `(mensaje, '{"yaw": <deg>, "distance": <m>}' )`. |

> If you consume the agent’s reply topic, handle both cases for `navigate`: always speak/log the **string**; optionally route the **JSON** telemetry if present.

---

#### Add a New Intent / Tool
The flow is: **patterns → intent detection → router → tool implementation**.
Your text is normalized (`norm_text`) before matching (lowercase, accents removed, courtesy words stripped), so keep patterns simple.

---
##### 1) Declare patterns in `llm_patterns.py` 
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

##### 2) Implement the tool in `llm_tools.py` (class GetInfo)
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

##### 3) Wire it into the router
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


<h2 id="contributing">🤝 Contributing</h2>
Contributions are welcome! Please fork the repository and submit a pull request. For major changes, open an issue first to discuss what you would like to change.

---

<h2 id="license">📄 License</h2>
This project is licensed under the [MIT License](LICENSE).

---

<h2 id="acknowledgements">🙏 Acknowledgements</h2>

- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Vosk](https://alphacephei.com/vosk/)
- [Qwen Models](https://huggingface.co/Qwen)
- The ROS2 community