import subprocess

class OfflineLLM:
    """Query Gemma via Ollama CLI for offline LLM responses."""
    def __init__(self, model_name="gemma3:1b"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        try:
            # Use UTF-8 encoding to avoid decode errors
            result = subprocess.run(
                ["ollama", "run", self.model_name, prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"  # <-- fix for Windows encoding issues
            )

            if result.returncode != 0:
                return f"[LLM Error] {result.stderr}"

            return result.stdout.strip()

        except Exception as e:
            return f"[LLM Exception] {e}"