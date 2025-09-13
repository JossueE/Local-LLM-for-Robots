import logging
from utils.utils import EnsureModel
from stt.wake_word import WakeWord
from stt.audio_listener import AudioListener
from stt.speech_to_text import SpeechToText
from llm.llm import LlmAgent
from tts.text_to_speech import SileroTTS
    

class OctybotAgent:
    def __init__(self):
        self.log = logging.getLogger("Octybot")
        model = EnsureModel()
        
        #Speech-to-Text
        self.audio_listener = AudioListener()
        self.wake_word = WakeWord(str(model.ensure_model("wake_word")[0]))
        self.stt = SpeechToText(str(model.ensure_model("stt")[0]))

        #LLM
        self.llm = LlmAgent(model_path = str(model.ensure_model("llm")[0]))

        #Text-to-Speech
        self.tts = SileroTTS(str(model.ensure_model("tts")[0]), str(model.ensure_model("tts")[1]))
        
        self.log.info("Octybot Agent Listo ✅")
    

    def main(self):
        """" This is the state machine logic to work with the system.
            - First you start the Audio Listener Process 
            - Then check if wake_word is detected
            - If is detected you make the stt process
            - Pass this info to the llm
            - The llm split the answers 
            - Publish the answer as tts"""
        
        self.audio_listener.start_stream()
        text_transcribed = None

        while text_transcribed == None:
            audio_capture = self.audio_listener.read_frame(self.wake_word.frame_samples)
            wake_word_buffer =  self.wake_word.wake_word_detector(audio_capture)
            text_transcribed = self.stt.worker_lopp(wake_word_buffer)
        
        for out in self.llm.ask(text_transcribed):
            get_audio = self.tts.synthesize(out)
            self.tts.play_audio_with_amplitude(get_audio)
    
    def stop(self):
        self.audio_listener.deleate()
        self.tts.stop_tts()

    

            

if "__main__" == __name__:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s %(asctime)s] [%(name)s] %(message)s")

    try:
        llm = OctybotAgent()
        print("Hola soy tu Agente vistual Octybot:")
        print("Prueba a decir 'ok robot' y darme una instrucción - Presiona (Ctrl+C para salir):")
        print("(Ejemplos: '¿Dónde estoy?', '¿Cuál es tu batería?', 'Ve a la enfermería', '¿Cuándo fue la Independencia de México y cuál es mi batería?')")
        while True:
            print("> Quieres preguntar algo: ")
            llm.main() 
    except KeyboardInterrupt:
        llm.stop()
        print("Saliendo")
        exit(0)