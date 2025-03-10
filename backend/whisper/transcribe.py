import whisper
import sys
import warnings
sys.stdout.reconfigure(encoding='utf-8')  # Force UTF-8 output

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

# Load the Whisper model
model = whisper.load_model("base")

def transcribe(audio_path):
    try:
        # Transcribe the audio file
        result = model.transcribe(audio_path)
        # Log transcription to terminal
        return result['text']
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the audio file path.")
        sys.exit(1)

    audio_file = sys.argv[1]
    transcription = transcribe(audio_file)
    # Only print the final transcription to the console
    print(transcription)  # This will be captured by Node.js
