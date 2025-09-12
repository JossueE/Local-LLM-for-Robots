
from typing import Optional

import logging
import onnx
import onnxruntime
import numpy as np
import torch
from pathlib import Path
from stt.wake_word import WakeWord
from stt.audio_listener import AudioListener
from config.settings  import SAMPLE_RATE_STT, CHANNELS_INPUT_STT, DEVICE_SELECTOR_STT, LANGUAGE, LISTENER_STT
from utils.utils import ensure_model

class SpeechToText:
    def __init__(
        self,
        audio_listener: AudioListener,
        wake_word: WakeWord,
    ) -> None:
        
        self.log = logging.getLogger("Speech_To_Text")    
        self.sample_rate = SAMPLE_RATE_STT
        self.channels = CHANNELS_INPUT_STT
        self.device =  DEVICE_SELECTOR_STT
        self.language =  LANGUAGE

        self.wake_word = wake_word
        self.audio_listener = audio_listener

        model, self.decoder, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_stt",          # stt
            language=self.language,      # depende del modelo disponible
            device="cpu" if self.device not in ("cuda", "cpu") else self.device,
        )

        onnx_model_path = ensure_model(LISTENER_STT)
        onnx_model = onnx.load(str(onnx_model_path))
        onnx.checker.check_model(onnx_model)
        self.ort_session = onnxruntime.InferenceSession(onnx_model_path)

        self.ort_in_name = self.ort_session.get_inputs()[0].name 
    
    def worker_lopp(self, audio_bytes: bytes) -> Optional[str]:
        if audio_bytes is None:
            return None
        try:
            text = self.stt_from_bytes(audio_bytes)
            if text:  
                self.log.info(f"📝 {text}")
                return text
            else:
                self.log.info(f"📝 (vacío)")
            
        except Exception as e:
            self.log.info(f"Error en STT: {e}")

    def stt_from_bytes (self, audio_bytes: bytes) -> Optional[str]:
        """
        Convert bytes Int16→tensor float32 normalizado y ejecuta Silero.
        """
        if not audio_bytes:
            return None

        # Int16 → float32 [-1, 1]
        pcm = np.frombuffer(audio_bytes, dtype=np.int16)
        if pcm.size == 0:
            return None

        x = pcm.astype(np.float32) / 32768.0

        onnx_in = x[np.newaxis, :]

        outs = self.ort_session.run(None, {self.ort_in_name: onnx_in})
        # Usa el decoder oficial de Silero sobre los logits
        text = self.decoder(torch.Tensor(outs[0])[0])
        
        #text = text.strip()
        return text or None
    
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")

    
    audio_listener = AudioListener()
    ww = WakeWord(audio_listener)
    stt = SpeechToText(audio_listener, ww)

    audio_listener.start_stream()

    try:
        while True:
            result = audio_listener.read_frame(ww.frame_samples)
            n_result = ww.wake_word_detector(result)
            stt.worker_lopp(n_result)
    except KeyboardInterrupt:
        audio_listener.deleate()
        ww.stop()
        ww.deleate()  
        print("Saliendo")
        exit(0)

