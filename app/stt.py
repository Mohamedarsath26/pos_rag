import os
import sys
import json
import wave
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer


class OfflineSTT:
    """Offline Speech-to-Text with Vosk.
    Supports both WAV transcription and real-time microphone transcription.
    """

    def __init__(self, model_dir: str, sample_rate: int = 16000):
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Vosk model directory not found: {model_dir}")
        self.model = Model(model_dir)
        self.sample_rate = sample_rate
        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        """Callback from sounddevice: pushes audio data into queue."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen_realtime(self):
        """Start microphone transcription in real-time."""
        rec = KaldiRecognizer(self.model, self.sample_rate)
        rec.SetWords(True)

        last_partial = ""

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=16000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            print("🎤 Speak now (Ctrl+C to stop)...")
            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    # Final recognized text
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        print("✅ Final:", result["text"])
                else:
                    # Partial recognition (only if changed)
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial and partial != last_partial:
                        print("⌛ Partial:", partial)
                        last_partial = partial

    def transcribe_wav(self, wav_path: str) -> str:
        """Transcribe a WAV file and return final text."""
        if not os.path.isfile(wav_path):
            raise FileNotFoundError(f"WAV not found: {wav_path}")

        wf = wave.open(wav_path, "rb")
        if (
            wf.getnchannels() != 1
            or wf.getsampwidth() != 2
            or wf.getframerate()
            not in [8000, 16000, 32000, 44100, 48000]
        ):
            raise ValueError(
                "WAV must be mono PCM 16-bit. Convert with: sox input.wav -r 16000 -c 1 -b 16 output.wav"
            )

        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)
        transcript = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                transcript.append(res.get("text", ""))

        final_res = json.loads(rec.FinalResult())
        transcript.append(final_res.get("text", ""))

        return " ".join([t for t in transcript if t]).strip().lower()



