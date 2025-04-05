import os
import speech_recognition as sr
import openai
import pyttsx3
import time
import threading

# Load API key from environment variable
API_KEY = "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"

if not API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable.")

# Configure OpenAI API
openai.api_key = API_KEY

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty("voices")
        self.engine.setProperty("voice", voices[0].id)
        self.engine.setProperty("rate", 170)
        self.is_listening = False

    def speak(self, audio):
        """Convert text to speech"""
        print(f"Assistant: {audio}")
        self.engine.say(audio)
        self.engine.runAndWait()

    def chat_with_ai(self, user_input):
        """Send message to OpenAI and get response"""
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}],
            temperature=1,
            max_tokens=4096,
            top_p=1
        )
        return response["choices"][0]["message"]["content"]

    def start_listening(self):
        """Start the voice assistant"""
        self.is_listening = True
        print("Voice Assistant started. Say something...")

        # Start listening in a separate thread
        threading.Thread(target=self.listening_loop, daemon=True).start()

        try:
            while self.is_listening:
                time.sleep(0.1)
                if input() == "q":
                    self.stop_listening()
        except KeyboardInterrupt:
            self.stop_listening()

    def stop_listening(self):
        """Stop the voice assistant"""
        self.is_listening = False
        print("Voice Assistant stopped.")

    def listening_loop(self):
        """Main listening loop"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")

            while self.is_listening:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print("Recognizing...")
                    user_input = recognizer.recognize_google(audio, language="en-US")
                    print(f"You said: {user_input}")

                    if user_input.lower() in ["quit", "exit"]:
                        self.stop_listening()
                        break

                    print("Getting response...")
                    ai_response = self.chat_with_ai(user_input)
                    self.speak(ai_response)

                    time.sleep(1)

                except sr.UnknownValueError:
                    print("Sorry, could not understand audio.")
                except sr.RequestError:
                    print("Could not request results. Check your internet connection.")
                except Exception as e:
                    print(f"Error: {str(e)}")
                time.sleep(1)

def main():
    print("Voice Assistant\nPress 'q' and Enter at any time to quit.")
    try:
        assistant = VoiceAssistant()
        assistant.start_listening()
    except Exception as e:
        print(f"Error initializing voice assistant: {str(e)}")

if __name__ == "__main__":
    main()
