from pathlib import Path
import os
import pyaudio
from config.settings import AUDIO_LISTENER_DEVICE_ID, AUDIO_LISTENER_SAMPLE_RATE, AUDIO_LISTENER_CHANNELS, AUDIO_LISTENER_FRAMES_PER_BUFFER

def ensure_model(model_name:str) -> str:
    """ Ensure the model directory exists, return its path or an error message """
    base_dir = Path(os.environ.get("OCTOPY_CACHE", os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))) / "octopy"
    model_dir = base_dir / model_name
    if not model_dir.exists():
        return f"[LLM_LOADER] Ruta directa no existe: {model_dir}\n"
    return str(model_dir)

def define_device_id(pa:pyaudio.PyAudio = None, prefered:int = AUDIO_LISTENER_DEVICE_ID) -> int:
    if prefered is not None:
        try:
            return prefered
        except Exception as e:
            print(f"[AudioListener - utils] Error al usar device_index preferido {prefered}: {e}", flush=True)
    
    elif pa is None:
        print(f"[AudioListener - utils] Pyaudio instance no proporcionada, no se puede listar dispositivos.", flush=True)
        return None

    elif pa is not None:
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                print(f"[AudioListener - utils] [{i}] {info['name']} (in={info['maxInputChannels']}, rate={int(info.get('defaultSampleRate',0))})")
                if info['name'].lower() == "pulse":
                    print(f"[AudioListener - utils]Usando dispositivo PulseAudio por defecto: {i}", flush=True)
                    return i
    
class AudioListener:
    def __init__(self):
        self.sample_rate = AUDIO_LISTENER_SAMPLE_RATE
        self.audio_interface = pyaudio.PyAudio()
        self.device_index = define_device_id(self.audio_interface, AUDIO_LISTENER_DEVICE_ID)
        self.channels = AUDIO_LISTENER_CHANNELS 
        self.frames_per_buffer = AUDIO_LISTENER_FRAMES_PER_BUFFER
        self.stream = None

    def start_stream(self):
        if self.stream is None:
            self.stream = self.audio_interface.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.frames_per_buffer,
            )

    def read_frame(self, frame_bytes: int) -> bytes:
        if self.stream is None:
            raise RuntimeError("Audio stream is not started.")
        return self.stream.read(frame_bytes)

    def stop_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def __del__(self):
        if self.stream is not None:
            self.stop_stream()
        self.audio_interface.terminate()