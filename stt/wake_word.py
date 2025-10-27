from __future__ import annotations
import logging, json
import webrtcvad
import vosk

import threading
from collections import deque

from config.settings import (
    MIN_SILENCE_MS_TO_DRAIN_STT, ACTIVATION_PHRASE_WAKE_WORD, LISTEN_SECONDS_STT, 
    AUDIO_LISTENER_SAMPLE_RATE, VARIANTS_WAKE_WORD, AUDIO_LISTENER_CHANNELS, AVATAR
)

if AVATAR:
    import webbrowser, subprocess, sys
    from pathlib import Path
    from avatar.avatar_server import send_mode_sync


class WakeWord:
    def __init__(self, model_path:str) -> None:

        self.log = logging.getLogger("Wake_Word")     
        self.wake_word = ACTIVATION_PHRASE_WAKE_WORD
        self.listen_seconds = LISTEN_SECONDS_STT
        self.sample_rate = AUDIO_LISTENER_SAMPLE_RATE
        self.variants = VARIANTS_WAKE_WORD
        
        #State Machine 
        self.on_say = (lambda s: print(f"[Wake_word] {s}"))

        grammar = json.dumps(self.variants, ensure_ascii=False)
        model_path = model_path
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, self.sample_rate, grammar)

        #Flags
        self.listening_confirm = False
        self.listening = False

        #Debounce parameters 
        self.partial_hits = 0
        self.required_hits = 10
        self.silence_frames_to_drain = MIN_SILENCE_MS_TO_DRAIN_STT

        #VAD parameters
        # 10 ms → less latency (160 samples - 16 kHz)
        self.vad = webrtcvad.Vad(1)  # Aggressiveness mode (0-3)
        self.frame_ms = 10
        self.frame_samples = int(self.sample_rate / 1000 * self.frame_ms)  # int16 mono

        #Audio buffer for Output
        self.lock = threading.Lock()
        self.buffer = deque() 
        self.size = 0
        self.max = int(self.listen_seconds * self.sample_rate * AUDIO_LISTENER_CHANNELS * 2) #2 bytes per int16 sample
        self.max_2 = int(1 * self.sample_rate * AUDIO_LISTENER_CHANNELS * 2) #2 bytes per int16 sample

        #Initialize Avatar Server if needed
        if AVATAR:
            subprocess.Popen([sys.executable, "-m", "avatar.avatar_server"], stdin=subprocess.DEVNULL, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text=True)
            webbrowser.open(Path("avatar/OctoV.html").resolve().as_uri(), new=0, autoraise=True)

    def wake_word_detector(self, frame:bytes) -> None | bytes:
        
        """Process one 10 ms PCM int16 mono frame for wake-word detection.

        - Uses WebRTC VAD to gate non-speech: decays `partial_hits`, feeds Vosk to keep
        buffers synced, and may auto-`deactivate_whisper()` when silence persists.
        - For speech, feeds Vosk:
            * Full result (`AcceptWaveform=True`): if text matches wake, logs and
            `confirm_active_whisper()`; else resets counters (and deactivates if listening).
            * Partial result: increments `partial_hits` on match; when threshold is
            reached, logs and `activate_whisper()`, then resets.
        - Mutates internal state (`partial_hits`, `listening`, `listening_confirm`,
        `wake_word_flag`) and may call `activate_whisper()`, `confirm_active_whisper()`,
        or `deactivate_whisper()`.
        - Requires: `self.sample_rate`, `self.vad`, `self.rec`, `self.matches_wake()`.
        """
        if self.listening or self.listening_confirm: #If I'm listening or If I got a confirmation i save the info
            drained = self.buffer_add(frame)  
            if drained is not None:
                send_mode_sync(mode = "TTS", as_json=False) if AVATAR else None
                return drained
        
        if not self.vad.is_speech(frame, self.sample_rate): # If I hear silence
            if self.partial_hits > -self.silence_frames_to_drain:  # I count how much silence I have
                self.partial_hits -= 1         
            if (self.listening or self.listening_confirm) and self.partial_hits <= -self.silence_frames_to_drain: #If I'm listening and I pass my umbral of silence
                self.partial_hits = 0
                send_mode_sync(mode = "TTS", as_json=False) if AVATAR else None
                if self.listening_confirm and self.size > 0: # If I have the wake_word comfirm and I have something
                    return self.buffer_drain()
                self.on_say("Hubo una detección pero no se confirmó, limpiando buffer")
                self.buffer_clear()
                return
        
        if self.rec.AcceptWaveform(frame): 
            result = json.loads(self.rec.Result() or "{}")
            text = (result.get("text") or "").lower().strip()
            if text and self.matches_wake(text):
                self.log.info(f"[FULL] Wake word: {text!r}")
                if not self.listening_confirm:           
                    self.listening_confirm = True
                    self.listening = True   
                    print("Confirmo Grabación")
                self.partial_hits = 0
                return
            self.partial_hits = 0

        else:
            partial = json.loads(self.rec.PartialResult() or "{}").get("partial", "").lower().strip()
            if partial:
                if self.matches_wake(partial): #If I got something that looks like partial     
                    if not self.listening: 
                        self.listening = True
                        send_mode_sync(mode = "USER", as_json=False) if AVATAR else None
                        print("Empiezo a Grabar (primer partial)")
                        drained = self.buffer_add(frame)
                        if drained is not None:
                            return drained
                    self.partial_hits += 1
                    if self.partial_hits >= self.required_hits:
                        self.log.info(f"[PARTIAL] Wake word: {partial!r}")
                        self.partial_hits = 0
                        return
                else:
                    self.partial_hits = 0

    
    def buffer_add(self, frame: bytes) -> None | bytes:
        with self.lock:
            self.buffer.append(frame)
            self.size += len(frame)
        if self.size > self.max and self.listening_confirm:
            return self.buffer_drain()
        if self.size > self.max_2 and self.listening and not self.listening_confirm:
            self.on_say("Límite de tiempo alcanzado, enviando a STT")
            self.buffer_clear()
            send_mode_sync(mode = "TTS", as_json=False) if AVATAR else None
        return None

    def buffer_clear(self) -> None:
        """ Clear the audio buffer and reset flags. """
        print("Limpiando Buffer")
        self.listening = False
        self.listening_confirm = False
        with self.lock:
            self.buffer.clear()
            self.size = 0
    
    def buffer_drain(self) -> bytes:
        """
        Return all buffered audio (as a single bytes object) and clear the buffer.
        Operates atomically under `self.lock`.
        """
        self.on_say("Envío Información a STT")

        with self.lock:
            data = b"".join(self.buffer)
            self.buffer.clear()

        print("Limpio el Buffer")
        self.size = 0
        self.listening = False
        self.listening_confirm = False
        return data

    def norm(self, s: str) -> str:
        """Normalize string: lowercase, remove accents."""
        s = s.lower()
        return (s.replace("á","a").replace("é","e").replace("í","i")
                .replace("ó","o").replace("ú","u").replace("ü","u"))
    
    def matches_wake(self, text: str) -> bool:
        """ Return True if text matches any variant of the wake word. """
        t = self.norm(text)
        for v in self.variants:
            if self.norm(v) in t:
                return True
        return False
        
 #———— Example Usage ————
if "__main__" == __name__:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")

    from utils.utils import LoadModel
    from stt.audio_listener import AudioListener

    model = LoadModel()
    audio_listener = AudioListener()
    ww = WakeWord(str(model.ensure_model("wake_word")[0]))
    audio_listener.start_stream()

    try: 
        print("Este es el nodo de prueba del Wake Word con Audio Listener 🔊, si tiene una detección parcial dirá [PARTIAL], si es completa [FULL]\n" \
    "La Palabara de activación es 'ok Robot' - Presione Ctrl+C para salir\n")
        while True:
            result = audio_listener.read_frame(ww.frame_samples)
            n_result = ww.wake_word_detector(result)
            if n_result is not None:
                print(f"Wake Word detectada, enviando {len(n_result)} bytes de audio para STT")

    except KeyboardInterrupt:
        audio_listener.deleate()
        print(" Saliendo")
        exit(0)