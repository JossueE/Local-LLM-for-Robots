import os
#THIS IS THE CONFIG FILE
#Here you can control everything of the LLM Package

"""Global"""
LANGUAGE = "es" #The code is actually not prepared to work with other languages, but for future improvements
MODELS_PATH = "config/models.yml"

"""Audio Listener is the node to hear something from the MIC"""
AUDIO_LISTENER_DEVICE_ID: int | None = None #The system is prepared to detect the best device, but if you want to force a device, put the id here
AUDIO_LISTENER_CHANNELS = 1 # "mono" or "stereo"
AUDIO_LISTENER_SAMPLE_RATE = 16000
AUDIO_LISTENER_FRAMES_PER_BUFFER = 1000

"""LLM node"""
CONTEXT_LLM = 1024 #The size of the context that your model is going to recieve
THREADS_LLM = os.cpu_count() or 8 #Threads that has available your model 
N_BACH_LLM = 512 #The size of the info that gpu or cpu is going to process
GPU_LAYERS_LLM = 0 #How many layers your model is going to use in GPU, for CPU use "0"
MAX_MOVE_DISTANCE_LLM = 10.0 #Max distance in meters of the robot movement
CHAT_FORMAT_LLM = "chatml-function-calling" #NOT recomended to change unless you change the model

"""Information - data"""
FUZZY_LOGIC_ACCURACY_KB = 0.75 
FUZZY_LOGIC_ACCURACY_POSE = 0.70
PATH_KB = "config/data/kb.json"
PATH_POSES = "config/data/poses.json"

"""Audio Publisher Node"""
AUDIO_PUBLISHER_DEVICE_ID = -1 #This is the default output
AUDIO_PUBLISHER_CHANELS = 1 # "mono" or "stereo"
AUDIO_PUBLISHER_FRAMES_PER_BUFFER = 256
AUDIO_PUBLISHER_DEBUG = True #Show in terminal the debug process

"""Text-to-Speech Node"""
SAMPLE_RATE_TTS = 24000
DEVICE_SELECTOR_TTS = "cpu" # "cpu" or "cuda"

"""Speech-to-Text Node"""
SAMPLE_RATE_STT = 16000 #Silero works at this sample_rate doesn't change unless it is necesarry
CHANNELS_INPUT_STT = 1 #mono or stereo, silero use mono
DEVICE_SELECTOR_STT = "cpu" # "cpu" or "cuda"
#IMPORTANT the system is prepare to work without this variable, but we have it for noisy enviroments, as a protection method
LISTEN_SECONDS_STT = 5.0 #The time of the phrase that the tts is going to be active after de wake_word detection
MIN_SILENCE_MS_TO_DRAIN_STT = 50 # 500 ms of time required to drain the buffer, if you want 1 second, put 100

"""Wake-Word Node"""
ACTIVATION_PHRASE_WAKE_WORD = "ok robot" #The Activation Word that the model is going to detect
VARIANTS_WAKE_WORD =  ["ok robot", "okay robot", "hey robot"] #variatons