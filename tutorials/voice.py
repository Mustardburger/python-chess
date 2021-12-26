import os
import time
import pyaudio
import playsound
import speech_recognition as sr
from gtts import gTTS


def speak(text):
    """ The computer speaks the text out """
    tts = gTTS(text=text, lang="vi")
    filename = "voice.mp3"
    tts.save(filename)
    playsound.playsound(filename)


def get_audio():
    """ Get the voice from the mic """
    r = sr.Recognizer()
    #r.energy_threshold = 1200
    #r.dynamic_energy_threshold = True
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio, show_all=True)
            print(said)
            print(type(said))
        except Exception as e:
            print("There's an error: " + str(e))

    return said


if __name__ == "__main__":
    #p = pyaudio.PyAudio()
    # for i in range(p.get_device_count()):
    #    info = p.get_device_info_by_index(i)
    #    print(info['index'], info['name'])
    # for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
    #    print(microphone_name)

    # speak("chào")
    print("Ready to get microphone input")
    s = time.time()
    get_audio()
    print(time.time() - s)
