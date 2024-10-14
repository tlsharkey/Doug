'''
Simple audio-audio chat application using ChatGPT 4o
'''

from Chatbot import Chatbot

## Set the API key and model name
doug = Chatbot("You Doug from the UP movie. Behave as Doug.")
# doug.text_chat()
doug.listen_for_wake_word()

