from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
import regex as re
import os
import time

class Chatbot:
    def __init__(self, system_prompt="You are a helpful assistant.", voice="en-US-AvaMultilingualNeural"):
        self.__openai_api_key = os.environ["OPENAI_API_KEY"]
        self.__openai_model = "gpt-4o-mini"
        self.__speech_key = os.environ["SPEECH_KEY"]
        self.__speech_region = os.environ["SPEECH_REGION"]
        self.__speech_endpoint = os.environ["SPEECH_ENDPOINT"]
        self.__voice = voice
        self.__history = [
            {"role": "system", "content": system_prompt}
        ]
        self.__openai_client = OpenAI(api_key=self.__openai_api_key)

    def get_response(self, message):
        self.__history.append({"role": "user", "content": message})
        completion = self.__openai_client.chat.completions.create(
            model=self.__openai_model,
            messages=self.__history
        )
        self.__history.append(completion.choices[0].message)
        return completion.choices[0].message.content
    
    def text_chat(self):
        message = ""
        while re.search(r"bye|goodbye|exit|quit|stop|shutup", message) is None:
            message = input("You: ")
            response = self.get_response(message)
            print("Doug:", response)
    
    def listen_for_sentence(self):
        '''
        Listens from the microphone until there is a pause in speech.
        If no speech is detected, returns None.
        '''
        speech_config = speechsdk.SpeechConfig(subscription=self.__speech_key, region=self.__speech_region)
        speech_config.speech_recognition_language="en-US"

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        print("Listening to microphone.")
        speech_recognition_result = speech_recognizer.recognize_once_async().get()

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # print("Recognized: {}".format(speech_recognition_result.text))
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
            return None
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
            return None
        
    def speak(self, text_to_speak):
        '''
        Converts text into audio and plays that audio.
        Audio is played synchronously.
        '''
        speech_config = speechsdk.SpeechConfig(subscription=self.__speech_key, region=self.__speech_region)
        speech_config.speech_synthesis_voice_name = self.__voice
        speech_config.speech_synthesis_language = "en-US"
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = speech_synthesizer.speak_text_async(text_to_speak).get()
        return
    
    def speak_ssml(self, ssml_text):
        '''
        Converts text into audio and plays that audio.
        Audio is played synchronously.
        '''
        speech_config = speechsdk.SpeechConfig(subscription=self.__speech_key, region=self.__speech_region)
        speech_config.speech_synthesis_voice_name = self.__voice
        speech_config.speech_synthesis_language = "en-US"
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        # play the audio
        ssml_text = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>" + \
                        "<voice name=\""+self.__voice+"\">" + \
                            ssml_text + \
                        "</voice>" + \
                    "</speak>"
        result = speech_synthesizer.speak_ssml_async(ssml_text).get()
        return
    
    def listen_for_wake_word(self, wake_word="Hey Chatbot", wake_word_detector_file="somefile.table"):
        '''
        Listens from the microphone until the wake word is detected.
        '''
        model = speechsdk.KeywordRecognitionModel(wake_word_detector_file)

        # The phrase your keyword recognition model triggers on.
        keyword = wake_word

        # Create a local keyword recognizer with the default microphone device for input.
        keyword_recognizer = speechsdk.KeywordRecognizer()

        done = False

        def recognized_cb(evt):
            # Only a keyword phrase is recognized. The result cannot be 'NoMatch'
            # and there is no timeout. The recognizer runs until a keyword phrase
            # is detected or recognition is canceled (by stop_recognition_async()
            # or due to the end of an input file or stream).
            result = evt.result
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                print("RECOGNIZED KEYWORD: {}".format(result.text))
            nonlocal done
            done = True

        def canceled_cb(evt):
            result = evt.result
            if result.reason == speechsdk.ResultReason.Canceled:
                print('CANCELED: {}'.format(result.cancellation_details.reason))
            nonlocal done
            done = True

        # Connect callbacks to the events fired by the keyword recognizer.
        keyword_recognizer.recognized.connect(recognized_cb)
        keyword_recognizer.canceled.connect(canceled_cb)

        # Start keyword recognition.
        result_future = keyword_recognizer.recognize_once_async(model)
        print('Say something starting with "{}" followed by whatever you want...'.format(keyword))
        result = result_future.get()
        return

        # Read result audio (incl. the keyword).
        if result.reason == speechsdk.ResultReason.RecognizedKeyword:
            time.sleep(2) # give some time so the stream is filled
            result_stream = speechsdk.AudioDataStream(result)
            result_stream.detach_input() # stop any more data from input getting to the stream

            save_future = result_stream.save_to_wav_file_async("AudioFromRecognizedKeyword.wav")
            print('Saving file...')
            saved = save_future.get()

        # If active keyword recognition needs to be stopped before results, it can be done with
        #
        #   stop_future = keyword_recognizer.stop_recognition_async()
        #   print('Stopping...')
        #   stopped = stop_future.get()


    def audio_chat(self, wake_word=None, ssml=False):
        message_text = self.listen_for_sentence()
        if (message_text is None and wake_word is not None):
            print("Sleeping chatbot.")
            self.listen_for_wake_word(wake_word=wake_word)
            print("Wake word detected.")
            message_text = self.listen_for_sentence()
        elif message_text is None:
            print("No speech detected.")
            return
        
        response = self.get_response(message_text)
        print("Doug:", response)
        if ssml:
            self.speak_ssml(response)
        else:
            self.speak(response)
        print("Doug spoke.")

        self.audio_chat(wake_word=wake_word, ssml=ssml)


        
    
    def reset(self):
        self.__history = [
            {"role": "system", "content": "You Doug from the UP movie. Behave as Doug."}
        ]




if __name__ == "__main__":
    doug = Chatbot("""
                   You Doug from the UP movie. Behave as Doug.
                   You should use speech markers to be more expressive.
                   e.g. : I am a dog <break time="200ms"/> I am a talking dog.
                   Note that there's a break after punctuation. This is only needed for added pauses.
                   e.g. : <mstts:express-as style="sad" styledegree="2">I am a sad dog.</mstts:express-as> 
                   where styledegree is between 0.01 and 2 with a default of 1.
                   style="affectionate", "angry", "calm", "chat", "cheerful", "depressed", "disgruntled", "embarrassed", "empathetic", "envious", "excited", "fearful", "friendly", "gentle", "hopeful", "lyrical","sad", "serious", "shouting", "whispering", "terrified", "unfriendly"
                   <prosody rate="+10.00%" pitch="+10.00%">Hi there</prosody>
                   this will increase the speed and pitch of the voice. Since you're an energetic dog, you might want to use this.
                   """,
                   voice = "en-US-AndrewMultilingualNeural")
    # doug.text_chat()
    doug.audio_chat(
        # wake_word="Hey Doug", 
        ssml=True
        )