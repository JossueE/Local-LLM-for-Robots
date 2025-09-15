# audio/tts.py
import torch
import io
import wave
import numpy as np
import pyaudio
import logging
from pathlib import Path
from piper.voice import PiperVoice
from utils.utils import EnsureModel
from config.settings import  SAMPLE_RATE_TTS, SAVE_WAV_TTS, PATH_TO_SAVE_TTS, NAME_OF_OUTS_TTS

class SileroTTS:
    def __init__(self, model_path:str, model_path_conf:str):
        print("-> Loading Silero TTS model...")
        self.log = logging.getLogger("[Text-to-Speech]")    
        model_path = model_path 
        encoder = model_path_conf 

        self.voice = PiperVoice.load(model_path = model_path,config_path=encoder)
        self.sample_rate = SAMPLE_RATE_TTS
        self.count_of_audios = 0
        self.out_path = Path(PATH_TO_SAVE_TTS) / Path(NAME_OF_OUTS_TTS) / Path(f"{NAME_OF_OUTS_TTS}_{self.count_of_audios}.wav")

        self.pa = None
        self.stream = None
        

        self.log.info("Text-To-Speech Inicializado")

    def synthesize(self, text: str):
        """Convert Text to Speech using Piper, return mono audio float32 [-1,1]"""
        if not text:
            return None
        
        if SAVE_WAV_TTS:
            self.out_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(self.out_path), "wb") as wav_file:
                self.voice.synthesize_wav(text, wav_file)
                self.count_of_audios += 1
                self.out_path = Path(PATH_TO_SAVE_TTS) / Path(NAME_OF_OUTS_TTS) / Path(f"{NAME_OF_OUTS_TTS}_{self.count_of_audios}.wav")

        mem = io.BytesIO()
        with wave.open(mem, "wb") as w:
            # Piper setea params internamente; solo pásale el writer
            self.voice.synthesize_wav(text,w)

        # Lee el WAV del buffer y devuélvelo como float32 normalizado
        mem.seek(0)
        with wave.open(mem, "rb") as r:
            frames = r.readframes(r.getnframes())
            pcm_i16 = np.frombuffer(frames, dtype=np.int16)
        audio_f32 = (pcm_i16.astype(np.float32) / 32768.0)
        return audio_f32

    def play_audio_with_amplitude(self, audio_data, amplitude_callback=None):
        """
        Plays the given float32 numpy array (single-channel).
        If amplitude_callback is provided, pass the amplitude
        of each chunk to it for mouth animation, etc.
        """
        if audio_data is None or len(audio_data) == 0:
            return
        
        # Check if it's a torch Tensor
        if torch.is_tensor(audio_data):
            # Move to CPU if needed, convert to NumPy
            audio_data = audio_data.cpu().numpy()  
            # Now it's a NumPy array, e.g. float32 in [-1..1]

        self.start_stream()

        # Convert float32 [-1..1] to int16
        audio_int16 = np.clip(audio_data * 32767.0, -32767.0, 32767.0).astype(np.int16)


        chunk_size = 1024
        idx = 0
        total_frames = len(audio_int16)

        while idx < total_frames:
            chunk_end = min(idx + chunk_size, total_frames)
            chunk = audio_int16[idx:chunk_end]
            self.stream.write(chunk.tobytes())

            if amplitude_callback:
                # amplitude = mean absolute value
                amplitude = np.abs(chunk.astype(np.float32)).mean()
                amplitude_callback(amplitude)

            idx += chunk_size
        self.stop_tts

    def start_stream(self):
        """ Start the audio stream if not already started."""
        self.pa = pyaudio.PyAudio()

        if self.stream is None:
            self.stream = self.pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=self.sample_rate,
                         output=True)

    def stop_tts(self):
        """Stop the stream"""
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        

if "__main__" == __name__:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")
    
    model = EnsureModel()
    tts = SileroTTS(str(model.ensure_model("tts")[0]), str(model.ensure_model("tts")[1]))

    try: 
        print("Este es el nodo de prueba del Text to Speech 🔊 - Presione Ctrl+C para salir\n")
        while True:
            text = input("Escribe algo: ")
            get_audio = tts.synthesize(text)
            tts.play_audio_with_amplitude(get_audio)

    except KeyboardInterrupt:
        tts.stop_tts()
        print(" Saliendo")
        exit(0)