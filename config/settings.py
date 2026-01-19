import os

"""
--------------------------------------------------------------------------
GLOBAL CONFIGURATION SETTINGS
--------------------------------------------------------------------------
This file controls the behavior of the entire Local-LLM package.
Adjust these parameters to tune performance, sensitivity, and functionality.
--------------------------------------------------------------------------
"""

# --- Global Settings ---
LANGUAGE = "es"  # ISO code for the language (currently optimized for Spanish)
MODELS_PATH = "config/models.yml"  # Path to the model definition file


# --- Audio Listener (Microphone Input) ---
# Controls how the system captures raw audio from the hardware.
AUDIO_LISTENER_DEVICE_ID: int | None = None  # Force a specific device ID (None = auto-detect)
AUDIO_LISTENER_CHANNELS = 1                  # Audio channels: 1 = Mono, 2 = Stereo
AUDIO_LISTENER_SAMPLE_RATE = 16000           # Sampling rate in Hz (16000 is standard for speech)
AUDIO_LISTENER_FRAMES_PER_BUFFER = 1000      # Buffer size for audio stream


# --- Wake Word Detection (Hotword) ---
# Controls sensitivity and activation phrases.
ACTIVATION_PHRASE_WAKE_WORD = "ok robot"     # Primary activation phrase
VARIANTS_WAKE_WORD = [                       # Acceptable variations of the phrase
    "ok robot", 
    "okay robot", 
    "hey robot"
]
VAD_AGGRESSIVENESS = 3           # (0 -> 3) Voice Activity Detection aggressiveness (0 = Least, 3 = Most strict filtering)
WAKE_WORD_REQUIRED_HITS = 10     # Consecutive partial matches required to trigger activation (Higher = Less false positives)


# --- Speech-to-Text (STT - Whisper) ---
# Controls transcription accuracy and noise handling.
DEVICE_SELECTOR_STT = "cpu"      # Inference device: "cpu" or "cuda"
SAMPLE_RATE_STT = 16000          # DO NOT CHANGE - Required sample rate for Whisper
LISTEN_SECONDS_STT = 5.0         # Max recording duration after wake word detection
MIN_SILENCE_MS_TO_DRAIN_STT = 100 # Silence duration (ms) required to stop recording early
SELF_VOCABULARY_STT = "DatIA Demographics" # Custom vocabulary hints for the model

# Tuning Thresholds:
NO_SPEECH_THRESHOLD_STT = 0.5             # (0.0 -> 1.0) Higher = Stricter (better for noise), Lower = Sensitive (better for quiet)
HALLUCINATION_SILENCE_THRESHOLD_STT = 0.3 # (0.1 -> 0.9) Threshold to discard text if model suspects silence (prevents hallucinations)


# --- Large Language Model (LLM) ---
# Controls text generation and intelligence.
USE_LLM = True                   # Master switch: Set False to disable general reasoning
CONTEXT_LLM = 1024               # Context window size (tokens)
THREADS_LLM = os.cpu_count() or 8 # CPU threads allocated for inference
N_BATCH_LLM = 512                # Prompt processing batch size
GPU_LAYERS_LLM = 0               # Number of layers to offload to GPU (0 = CPU only)
CHAT_FORMAT_LLM = "chatml-function-calling" # Prompt template format
REPEAT_PENALTY_LLM = 1.1         # (1.0 -> 1.5) Penalty for repetitive text (1.1 = Moderate, 1.5 = Aggressive)


# --- RAG & Information Retrieval ---
FUZZY_LOGIC_ACCURACY_GENERAL_RAG = 0.70 # Similarity threshold (0.0 -> 1.0) to match RAG entries
PATH_GENERAL_RAG = "config/data/general_rag.json" # Path to the knowledge base


# --- Text-to-Speech (TTS) ---
# Controls the voice output generation.
SAMPLE_RATE_TTS = 24000          # Output sample rate
DEVICE_SELECTOR_TTS = "cpu"      # Inference device: "cpu" or "cuda"
VOLUME_TTS = 2.0                 # Output volume multiplier
SPEED_TTS = 1.0                  # Speech speed: 1.0 = Normal, 2.0 = Slow
PATH_TO_SAVE_TTS = "tts/audios"  # Directory to save generated audio files
NAME_OF_OUTS_TTS = "test"        # Base filename for saved audios
SAVE_WAV_TTS = False             # Flag to save audio files to disk


# --- Avatar Integration ---
AVATAR = False                   # Enable/Disable visual avatar integration