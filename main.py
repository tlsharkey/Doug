import time
from Chatbot import Chatbot

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
    while True:
        try:
            doug.speak_ssml("<prosody rate=\"+10.00%\" pitch=\"+10.00%\">Squirrel!</prosody>")
            doug.audio_chat(
                wake_word_detector_file="./final_lowfa.table",
                ssml=True
                )
        except Exception as e:
            print("\nERROR:", e)
            doug.speak_ssml("<prosody rate=\"+10.00%\" pitch=\"+10.00%\">I think I lost my last brain cell. Let me reset.</prosody>")
            doug.reset()
            continue
    # doug.speak_ssml("<prosody rate=\"+10.00%\" pitch=\"+10.00%\">Squirrel!</prosody>")
    # while str(input("Press enter to continue.")) == "":
    #     doug.listen_for_wake_word(wake_word_detector_file="./final_lowfa.table")
    #     print("[main.py] Wake word returned.")