from stt.wake_word import WakeWord
from stt.audio_listener import AudioListener
from stt.speech_to_text import SpeechToText
    

class Main:
    def __init__(self):
        audio_listener = AudioListener()
        wake_word = WakeWord(audio_listener)
        stt = SpeechToText(audio_listener, wake_word)


    

    def main():
        #cosas que tengo que implementar

        #jalar de utils el cargador de yaml, a todas las clases habilitarles la opción de pasarles la data para no gastar recursos a lo pendejo.

if "__main__" == __name__:

    


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