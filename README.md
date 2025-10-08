# Local LLM for Robots 🤖🦾

[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


**Local-LLM-for-Robots** is a python package that fuses a local Large Language Model with a full offline speech pipeline so robots can understand and respond to natural language without the cloud. This repo includes everything about the `Wake Word (activation word)` -> `STT (speech-to-text)` -> `LLM Module` -> `TTS (text-to-speech)` every module is organize in different folders. But If you want more details about the `LLM Module`, you can check the `README.md`that is into the `/llm` folder.

---
## 📝 Flowchart
<div style="overflow:auto; border:1px solid #eaecef; padding:6px;">
  <object data="Local-LLM-for-Robots.svg" type="image/svg+xml" width="4400">
    <!-- Fallback para visores viejos -->
    <img src="/docs/Local-LLM-for-Robots.svg" alt="Flowchart" />
  </object>
</div>

<p align="right">
  <a href="https://lucid.app/lucidchart/50ed3019-62f3-460d-a3e3-071d72727e35/view">Open in real size</a>
</p>

---
## 🎥 Small Demo
Here’s a **small demo of the Avatar system in action** — showing how the visualization reacts when you say the wake-word and trigger the full interaction pipeline.

<p align="center">
  <a href="https://youtu.be/PP4M3LmFDbM" target="_blank">
    <img src="https://img.youtube.com/vi/PP4M3LmFDbM/hqdefault.jpg" width="720" alt="Avatar Demo YouTube">
  </a>
</p>

When the **wake word is detected**, the avatar changes color and responds with speech.
![Avatar Demo](docs/avatar/avatar.gif)

---

## 📚 Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Contributing](#contributing) 
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

<h2 id="installation">🛠️ Installation</h2>

> [!IMPORTANT]
> This implementation was tested with Ubuntu 22.04 and Python 3.10.12 

### Prerequisites
- Git, CMake
- (Optional) NVIDIA CUDA for GPU acceleration

### Setup
```bash
sudo apt update

# --- General installations ---
sudo apt install -y python3-dev python3-venv build-essential curl unzip

# --- STT (Speech-to-Text) ---
sudo apt install -y portaudio19-dev ffmpeg

# --- TTS (Text-to-Speech) ---
# ffmpeg is already installed above, uncomment if you prefer to keep it separate
# sudo apt install -y ffmpeg

# --- LLM (YAML manipulation) ---
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

### 🔧 General Settings (`config/settings.py`)
All runtime settings live in **`config/settings.py`**. They are plain Python constants—edit the file and restart your nodes to apply changes.

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

This is a **Minimal Example** of what you can do with this package.  
Here you will find examples of how to run commands in the terminal, trigger actions based on pattern matches, retrieve information from an endpoint, and more.  

> [!TIP]  
> When integrating this into your system, consider using the power of the LLM **only when truly necessary**.  
> In most cases, tasks can be solved with regular expressions, consuming information from a RAG, running commands in the terminal, or calling an endpoint.

#### Agent Intents (`handle(data, tipo)`)
| `tipo`     | What it does | Input `data` | Output shape | What it represents |
|------------|--------------|---------------|--------------|--------------------|
| `rag`      | Returns `data` as-is (external RAG already resolved). | Pre-composed **string** from your RAG (e.g., `general_rag.json`) | `str` | Consult information from a RAG or dataset. |
| `general`  | Free-form Q&A via `llm.answer_general`. | Question | `str` | Minimal example of how to implement the LLM for general queries. |
| `battery`  | Reads battery percentage via `tool_get_batt()`. | Reads **Battery** status | `str` like `Mi batería es: 84.0%` (or a “no reading” message) | Retrieve system information. |
| `maps`     | Reads maps via `tool_get_maps_from_backend()` and classifies between “return maps” and “the number of maps”. | Reads **Maps** from an endpoint | Either the number of maps or the list of maps | Minimal example of consuming an API. |
| `navigate` | Navigates to a named place or generates a short motion. Attempts `tool_nav(data)` first (RAG/`poses.json`): if found, replies **"Voy"** (execute) or **"Por allá"** (indicate/simulate). If not found, falls back to `llm.plan_motion(data)` → `_clamp_motion(...)` → `natural_move_llm(...)`. | Pre-composed string from your RAG (`poses.json`) or a natural-language command (e.g., `ve a la enfermería`, `gira 90° y avanza 0.5 m`). | Usually `str`. On fallback may return a **tuple**: `(mensaje, '{"yaw": <deg>, "distance": <m>}' )`. | Represents full integration: minimal example of running terminal commands to execute actions (`publish_natural_move()`). |

> If you consume the agent’s reply topic, handle both cases for `navigate`:  
> - Always log or speak the **string**.  
> - Optionally route the **JSON** telemetry if present.  

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
---
#### Avatar
This avatar system was originally developed by [TheBIGduke](https://github.com/TheBIGduke/OctoV) 

Enable a simple on-screen “avatar” to visualize the pipeline (wake-word → STT → LLM → TTS).

##### 1) Turn it on

Open `config/settings.py` and set:

```python
AVATAR = True
```
##### 2) Give it access to your I/O
The avatar uses your microphone and speakers.
For setup notes (devices, permissions, troubleshooting), see the `avatar/README.md`

##### 3) Start the avatar
From your project root, either:

**Run the full pipeline** (recommended):
```python
python -m main
```
Or **run only the Wake Word** test (for a quick check):
```python
python -m stt.wake_word
```
---
##### What you should see

- **Wake-word detected →** the ball/badge turns active (listening).
- **STT running →** partial/Final transcripts appear.
- **TTS speaking →** the indicator switches back while audio plays.

Overview (idle state):
![Avatar – Idle](docs/avatar/normal.png)

Wake-word Detection:
![Avatar – Wake Word Full](docs/avatar/STT.png)

TTS speaking state:
![Avatar – TTS Speaking](docs/avatar/TTS.png)



This will open a local HTML page (the avatar UI). Try the full flow: say “ok robot, ¿cómo te llamas?” and watch the indicators change.

Then run this to validate if the system works, an html file is going to be oppened and you migth see this. try to follow the full pipeline as ok robot como te llamas. You can see How your ball change of color when you saw ok robot and then is set again to the other color when it start to speek. 




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