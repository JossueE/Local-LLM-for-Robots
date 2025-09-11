import pyaudio
from config.settings import AUDIO_LISTENER_DEVICE_ID, AUDIO_LISTENER_SAMPLE_RATE, AUDIO_LISTENER_CHANNELS, AUDIO_LISTENER_FRAMES_PER_BUFFER
import logging

def define_device_id(pa:pyaudio.PyAudio = None, prefered:int = AUDIO_LISTENER_DEVICE_ID, log:logging.getLogger = None) -> int:

    """ Define the device id to use for audio input."""
    if prefered is not None:
        try:
            return prefered
        except Exception as e:
            log.info(f"Error al usar device_index preferido {prefered}: {e}")
    
    elif pa is None:
        log.warning(f"Pyaudio instance no iniciado, no se puede listar dispositivos.")
        return None

    elif pa is not None:
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)   
            if info.get('maxInputChannels', 0) > 0:
                log.info(f"[{i}] {info['name']} (in={info['maxInputChannels']}, rate={int(info.get('defaultSampleRate',0))})")
                if info['name'].lower() == "pulse":
                    log.warning(f"[AudioListener - utils]Usando dispositivo PulseAudio por defecto: {i}")
                    return i
    
class AudioListener:
    def __init__(self):
        self.log = logging.getLogger("AudioListener")  
        self.sample_rate = AUDIO_LISTENER_SAMPLE_RATE
        self.audio_interface = pyaudio.PyAudio()
        self.device_index = define_device_id(self.audio_interface, AUDIO_LISTENER_DEVICE_ID, self.log)
        self.channels = AUDIO_LISTENER_CHANNELS 
        self.frames_per_buffer = AUDIO_LISTENER_FRAMES_PER_BUFFER
        self.stream = None
        self.log.info(f"AudioListener initialized with device_index={self.device_index}, sample_rate={self.sample_rate}, channels={self.channels}, frames_per_buffer={self.frames_per_buffer} ✅ ")

    def start_stream(self):
        """ Start the audio stream if not already started."""
        if self.stream is None:
            self.stream = self.audio_interface.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.frames_per_buffer,
            )

    def read_frame(self, frame_samples: int) -> bytes:
        """ Read a frame of audio data from the stream."""
        if self.stream is None:
            raise RuntimeError("El Audio stream no se ha comenzado o está fallando la lectura.")
        return self.stream.read(frame_samples, exception_on_overflow=False)

    def stop_stream(self):
        """ Stop the audio stream if it is running."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def deleate(self):
        """ Clean up the audio interface and stream."""
        if self.stream is not None:
            self.stop_stream()
        self.audio_interface.terminate()

if "__main__" == __name__:
    al = AudioListener()
    time_test = 3
    al.start_stream()
    import time
    time.sleep(time_test)
    data = al.read_frame(3200)
    print(f"Durante {time_test} segundos, leíste {len(data)} bytes. Tu AudioListener funciona correctamente ✅")
    al.stop_stream()