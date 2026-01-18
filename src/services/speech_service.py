import azure.cognitiveservices.speech as speechsdk
from config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SpeechService:
    
    def __init__(self):
        if not settings.AZURE_SPEECH_KEY or settings.AZURE_SPEECH_KEY == "":
            error_msg = (
                "Azure Speech Key is missing! Please set AZURE_SPEECH_KEY in your .env file.\n"
                "Get your key from: https://portal.azure.com/ -> Speech Services -> Keys and Endpoint"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not settings.AZURE_SPEECH_REGION or settings.AZURE_SPEECH_REGION == "":
            error_msg = (
                "Azure Speech Region is missing! Please set AZURE_SPEECH_REGION in your .env file.\n"
                "Example: AZURE_SPEECH_REGION=eastus"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Initializing Azure Speech with region: {settings.AZURE_SPEECH_REGION}")
        
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            
            self.speech_config.speech_recognition_language = settings.SPEECH_LANGUAGE
            self.speech_config.speech_synthesis_language = settings.SPEECH_LANGUAGE
            self.speech_config.speech_synthesis_voice_name = settings.TTS_VOICE_NAME
            
            self.sample_rate = settings.SPEECH_SAMPLE_RATE
            
            logger.info("Azure Speech Service initialized successfully")
            
        except RuntimeError as e:
            error_msg = (
                f"Failed to initialize Azure Speech Service: {str(e)}\n"
                "Common causes:\n"
                "1. Invalid AZURE_SPEECH_KEY - Check your .env file\n"
                "2. Invalid AZURE_SPEECH_REGION - Use lowercase (e.g., 'eastus' not 'East US')\n"
                "3. Key has extra spaces or quotes - Remove them\n"
                "\nVerify your credentials at: https://portal.azure.com/"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def speech_to_text_from_microphone(self) -> Optional[str]:
        try:
            logger.info("Listening from microphone...")
            
            audio_config = speechsdk.AudioConfig(use_default_microphone=True)
            
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"Recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                return None
            
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            return None
    
    def text_to_speech(self, text: str) -> bytes:
        """Synthesizes text and returns the audio bytes (for web/API use)."""
        try:
            ssml = f"""
            <speak version='1.0' xml:lang='{settings.SPEECH_LANGUAGE}'>
                <voice name='{settings.TTS_VOICE_NAME}'>
                    <prosody rate='{settings.TTS_SPEAKING_RATE}' pitch='{settings.TTS_PITCH}'>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Configure to return audio data to stream instead of local speaker
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=None # None means don't play to local hardware
            )
            result = speech_synthesizer.speak_ssml(ssml)
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return b''
                
        except Exception as e:
            logger.error(f"TTS Error: {str(e)}")
            return b''
    
    def listen_and_transcribe(self) -> Optional[str]:
        return self.speech_to_text_from_microphone()
    
    def speak(self, text: str):
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            ssml = f"""
            <speak version='1.0' xml:lang='{settings.SPEECH_LANGUAGE}'>
                <voice name='{settings.TTS_VOICE_NAME}'>
                    <prosody rate='{settings.TTS_SPEAKING_RATE}' pitch='{settings.TTS_PITCH}'>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Speech completed successfully")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                    
        except Exception as e:
            logger.error(f"Speak error: {str(e)}")
            print(f"[TTS Error - Text only]: {text}")
    
    def recognize_from_microphone(self) -> Optional[str]:
        try:
            logger.info("Listening...")
            
            audio_config = speechsdk.AudioConfig(use_default_microphone=True)
            
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"Recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Recognition canceled: {cancellation.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Microphone recognition error: {str(e)}")
            return None
