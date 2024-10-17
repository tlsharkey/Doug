import { OpenAI } from 'openai';
import * as speechsdk from 'microsoft-cognitiveservices-speech-sdk';

class Chatbot {
    private openaiApiKey: string;
    private openaiModel: string;
    private speechKey: string;
    private speechRegion: string;
    private speechEndpoint: string;
    private voice: string;
    private history: Array<{ role: string, content: string }>;
    private openaiClient: OpenAI;

    constructor(systemPrompt = "You are a helpful assistant.", voice = "en-US-AvaMultilingualNeural") {
        this.openaiApiKey = process.env.OPENAI_API_KEY || '';
        this.openaiModel = "gpt-4o-mini";
        this.speechKey = process.env.SPEECH_KEY || '';
        this.speechRegion = process.env.SPEECH_REGION || '';
        this.speechEndpoint = process.env.SPEECH_ENDPOINT || '';
        this.voice = voice;
        this.history = [
            { role: "system", content: systemPrompt }
        ];
        this.openaiClient = new OpenAI({ apiKey: this.openaiApiKey });
    }

    async getResponse(message: string): Promise<string> {
        this.history.push({ role: "user", content: message });
        const completion = await this.openaiClient.chat.completions.create({
            model: this.openaiModel,
            messages: this.history
        });
        this.history.push(completion.choices[0].message);
        return completion.choices[0].message.content;
    }

    async textChat() {
        let message = "";
        const regex = /bye|goodbye|exit|quit|stop|shutup/i;
        while (!regex.test(message)) {
            message = prompt("You: ") || "";
            const response = await this.getResponse(message);
            console.log("Doug:", response);
        }
    }

    async listenForSentence(): Promise<string | null> {
        const speechConfig = speechsdk.SpeechConfig.fromSubscription(this.speechKey, this.speechRegion);
        speechConfig.speechRecognitionLanguage = "en-US";

        const audioConfig = speechsdk.AudioConfig.fromDefaultMicrophoneInput();
        const speechRecognizer = new speechsdk.SpeechRecognizer(speechConfig, audioConfig);

        console.log("Listening to microphone.");
        const speechRecognitionResult = await speechRecognizer.recognizeOnceAsync();

        if (speechRecognitionResult.reason === speechsdk.ResultReason.RecognizedSpeech) {
            return speechRecognitionResult.text;
        } else if (speechRecognitionResult.reason === speechsdk.ResultReason.NoMatch) {
            console.log("No speech could be recognized:", speechRecognitionResult.noMatchDetails);
            return null;
        } else if (speechRecognitionResult.reason === speechsdk.ResultReason.Canceled) {
            const cancellationDetails = speechRecognitionResult.cancellationDetails;
            console.log("Speech Recognition canceled:", cancellationDetails.reason);
            if (cancellationDetails.reason === speechsdk.CancellationReason.Error) {
                console.log("Error details:", cancellationDetails.errorDetails);
                console.log("Did you set the speech resource key and region values?");
            }
            return null;
        }
        return null;
    }

    async speak(textToSpeak: string) {
        const speechConfig = speechsdk.SpeechConfig.fromSubscription(this.speechKey, this.speechRegion);
        speechConfig.speechSynthesisVoiceName = this.voice;
        speechConfig.speechSynthesisLanguage = "en-US";
        const speechSynthesizer = new speechsdk.SpeechSynthesizer(speechConfig);
        await speechSynthesizer.speakTextAsync(textToSpeak);
    }

    async speakSsml(ssmlText: string) {
        const speechConfig = speechsdk.SpeechConfig.fromSubscription(this.speechKey, this.speechRegion);
        speechConfig.speechSynthesisVoiceName = this.voice;
        speechConfig.speechSynthesisLanguage = "en-US";
        const speechSynthesizer = new speechsdk.SpeechSynthesizer(speechConfig);
        const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                        <voice name="${this.voice}">${ssmlText}</voice>
                      </speak>`;
        await speechSynthesizer.speakSsmlAsync(ssml);
    }

    async listenForWakeWord(wakeWord = "Hey Chatbot", wakeWordDetectorFile = "somefile.table") {
        const model = speechsdk.KeywordRecognitionModel.fromFile(wakeWordDetectorFile);
        const keywordRecognizer = new speechsdk.KeywordRecognizer();

        let done = false;

        const recognizedCb = (evt: any) => {
            const result = evt.result;
            if (result.reason === speechsdk.ResultReason.RecognizedKeyword) {
                console.log("RECOGNIZED KEYWORD:", result.text);
            }
            done = true;
        };

        const canceledCb = (evt: any) => {
            const result = evt.result;
            if (result.reason === speechsdk.ResultReason.Canceled) {
                console.log('CANCELED:', result.cancellationDetails.reason);
            }
            done = true;
        };

        keywordRecognizer.recognized = recognizedCb;
        keywordRecognizer.canceled = canceledCb;

        const resultFuture = keywordRecognizer.recognizeOnceAsync(model);
        console.log(`Say something starting with "${wakeWord}" followed by whatever you want...`);
        await resultFuture;
    }

    async audioChat(wakeWord: string | null = null, ssml = false) {
        let messageText = await this.listenForSentence();
        if (messageText === null && wakeWord !== null) {
            console.log("Sleeping chatbot.");
            await this.listenForWakeWord(wakeWord);
            console.log("Wake word detected.");
            messageText = await this.listenForSentence();
        } else if (messageText === null) {
            console.log("No speech detected.");
            return;
        }

        const response = await this.getResponse(messageText);
        console.log("Doug:", response);
        if (ssml) {
            await this.speakSsml(response);
        } else {
            await this.speak(response);
        }
        console.log("Doug spoke.");

        await this.audioChat(wakeWord, ssml);
    }

    reset() {
        this.history = [
            { role: "system", content: "You Doug from the UP movie. Behave as Doug." }
        ];
    }
}

export default Chatbot;
