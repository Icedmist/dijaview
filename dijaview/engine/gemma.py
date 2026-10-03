import json
import urllib.error
import urllib.request
from typing import Dict, Any, Optional


class GemmaClient:
    """Client for local Gemma 2 inference via Ollama."""

    def __init__(self, model_name: str = "gemma2:2b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is active and responsive."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generates a completion from local Gemma 2."""
        if not self.is_available():
            return {
                "available": False,
                "response": "Local Ollama daemon is offline. Run 'ollama serve' and 'ollama pull gemma2:2b'.",
            }

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "available": True,
                    "response": result.get("response", "").strip(),
                    "total_duration": result.get("total_duration", 0),
                }
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            if "not found" in error_body.lower():
                return {
                    "available": False,
                    "response": f"Model '{self.model_name}' not found in Ollama. Run 'ollama pull {self.model_name}' to download it.",
                }
            return {
                "available": False,
                "response": f"Error communicating with local Gemma 2: HTTP {e.code} - {e.reason}",
            }
        except Exception as e:
            return {
                "available": False,
                "response": f"Error communicating with local Gemma 2: {str(e)}",
            }
