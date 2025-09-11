from __future__ import annotations
from typing import Optional,List, Callable
import logging, json, os
import webrtcvad
import vosk

import threading
from collections import deque

from stt.audio_listener import AudioListener
from config.settings import  ACTIVATION_PHRASE_WAKE_WORD, LISTEN_SECONDS_STT, AUDIO_LISTENER_SAMPLE_RATE, VARIANTS_WAKE_WORD, DEFAULT_MODEL_FILENAME_WAKE_WORD, AUDIO_LISTENER_CHANNELS
from utils.utils import ensure_model

class WakeWord:
    def __init__(
        self,
        audio_listener: AudioListener,
        wake_word: Optional[str] = None,
        listen_seconds: Optional[int] = None,
        variants: Optional[List[str]] = None,
        on_say: Optional[Callable[[str], None]] = None,
    ) -> None:

        self.log = logging.getLogger("Wake_Word")     
        self.wake_word = wake_word or ACTIVATION_PHRASE_WAKE_WORD
        self.listen_seconds = listen_seconds or LISTEN_SECONDS_STT
        self.sample_rate = AUDIO_LISTENER_SAMPLE_RATE
        self.variants = variants or VARIANTS_WAKE_WORD
        
        #State Machine 
        self.on_say = on_say or (lambda s: print(f"[state_machine] {s}"))

        #Audio input
        self.audio_listener = audio_listener
        grammar = json.dumps(self.variants, ensure_ascii=False)
        model_path = ensure_model(os.path.expanduser(DEFAULT_MODEL_FILENAME_WAKE_WORD))
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, self.sample_rate, grammar)

        #Flags
        self.listening_confirm = False
        self.listening = False

        #Debounce parameters 
        self.partial_hits = 0
        self.required_hits = 15

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

        if not self.vad.is_speech(frame, self.sample_rate):
            if self.partial_hits > -self.required_hits:
                self.partial_hits -= 1

            self.rec.AcceptWaveform(frame)
            
            if (self.listening or self.listening_confirm) and self.partial_hits <= -self.required_hits:
                if self.listening_confirm and self.size > 0:
                    return self.buffer_drain()  
                else:
                    self.on_say("Hubo una detección pero no se confirmó, limpiando buffer")
                    self.buffer_clear()
                return
        
        if self.listening or self.listening_confirm:
            drained = self.buffer_add(frame)  
            if drained is not None:
                return drained
        
        if self.rec.AcceptWaveform(frame):
            result = json.loads(self.rec.Result() or "{}")
            text = (result.get("text") or "").lower().strip()
            if text and self.matches_wake(text):
                self.log.info(f"[FULL] Wake word: {text!r}")
                if not self.listening_confirm:           
                    self.listening_confirm = True
                    self.listening = True   
                    drained = self.buffer_add(frame)  
                    if drained is not None:
                        return drained
                    print("Confirmo Grabación")
                self.partial_hits = 0
                return
            self.partial_hits = 0

        else:
            partial = json.loads(self.rec.PartialResult() or "{}").get("partial", "").lower().strip()
            if partial:
                if self.matches_wake(partial):
                    self.partial_hits += 1
                    if self.partial_hits >= self.required_hits:
                        self.log.info(f"[PARTIAL] Wake word: {partial!r}")
                        if not self.listening:
                            self.listening = True
                            print("Empiezo a Grabar")
                            drained = self.buffer_add(frame)  
                            if drained is not None:
                                return drained
                        self.partial_hits = 0
                        return
                else:
                    self.partial_hits = 0
    
    def buffer_add(self, frame: bytes) -> None | bytes:
        """ Add a frame to the audio buffer."""
        with self.lock:
            self.buffer.append(frame)
            self.size += len(frame)
            # Si sobrepasamos límite y ya hay confirmación, drenamos
            if self.size > self.max and self.buffer and self.listening_confirm:
                return self.buffer_drain(True)
        return None

    def buffer_clear(self) -> None:
        """ Clear the audio buffer and reset flags. """
        print("Limpiando Buffer")
        self.listening = False
        self.listening_confirm = False
        with self.lock:
            self.buffer.clear()
            self.size = 0
    
    def buffer_drain(self, lock:bool = False) -> bytes:
        """
        Return all buffered audio (as a single bytes object) and clear the buffer.
        Operates atomically under `self.lock`.
        """
        self.on_say("Envío Información a STT")
        if lock:
            data = b"".join(self.buffer)
            self.buffer.clear()
            self.size = 0
        else:
            with self.lock:
                data = b"".join(self.buffer)
                self.buffer.clear()
                self.size = 0
        # Reset de flags FUERA del lock para no bloquear
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
        

if "__main__" == __name__:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")

    
    audio_listener = AudioListener()
    ww = WakeWord(audio_listener)
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