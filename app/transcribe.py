import subprocess
import sounddevice as sd
import wave
import keyboard
import string

class AudioTranscriber:
    def __init__(self, whisper_cli, model_path, audio_file, sample_rate=16000, channels=1):
        self.whisper_cli = whisper_cli
        self.model_path = model_path
        self.audio_file = audio_file
        self.sample_rate = sample_rate
        self.channels = channels

    # ---------------- CLEAN TEXT ----------------
    def clean_text(self, text):
        # Remove punctuation and lowercase
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.lower().strip()

    # ---------------- MIC RECORDER ----------------
    def record_until_enter(self):
        print("🎤 Speak now... (press ENTER to stop)")

        frames = []

        def callback(indata, frames_count, time, status):
            if status:
                print(status)
            frames.append(indata.copy())

        # Start recording
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            callback=callback
        )
        stream.start()

        # Wait until Enter is pressed
        keyboard.wait("enter")

        stream.stop()
        stream.close()

        # Save to wav
        with wave.open(self.audio_file, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join([f.tobytes() for f in frames]))

        print("✅ Recording saved to", self.audio_file)

    # ---------------- TRANSCRIBE ----------------
    def transcribe(self, file_path=None):
        if file_path is None:
            file_path = self.audio_file

        cmd = [
            self.whisper_cli,
            "-m", self.model_path,
            "-f", file_path
        ]
        print("⏳ Transcribing...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("📝 Transcription:\n")
        print(result.stdout)

        # Extract last line (basic way to get spoken text)
        lines = result.stdout.strip().splitlines()
        if not lines:
            return ""

        last_line = lines[-1]
        if "]" in last_line:
            last_line = last_line.split("]")[-1].strip()

        return self.clean_text(last_line) if last_line else ""
