import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

# ---------------------------------
# Configuration
# ---------------------------------

API_KEY = 'apikey'
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

HOST = "127.0.0.1"
PORT = 8000
BASE_DIR = Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"


# ---------------------------------
# AI Study Planner
# ---------------------------------


def generate_plan(goal, level, daily_minutes, duration):
    system_prompt = """
You are an expert learning path designer.
The user wants to reach a learning goal.
Assume the user is a beginner.
Create a realistic step-by-step roadmap.
Consider:
- prerequisites
- required skills
- logical learning order
- simple exercises
- mini projects

Return ONLY valid JSON.
Do not write anything outside the JSON object.
Use this exact structure:
{
    "goal": "...",
    "level": "...",
    "roadmap": [
        {
            "step": 1,
            "title": "...",
            "reason": "...",
            "topics": ["...", "..."],
            "exercises": ["...", "..."]
        }
    ]
}
"""

    user_prompt = f"""
Goal: {goal}
Current level: {level}
Study time per day: {daily_minutes} minutes
Available time: {duration}

Create a realistic learning roadmap based on this information.
Respond in English.
"""

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    if not API_KEY or API_KEY == "YOUR_OPENROUTER_API_KEY":
        raise ValueError("OpenRouter API key is not configured. Put it in API_KEY in app.py.")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        URL,
        headers=headers,
        json=data,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    return json.loads(answer)


# ---------------------------------
# HTTP Server
# ---------------------------------


class MyGPTHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path):
        if not path.exists() or not path.is_file():
            self.send_error(404, "File not found")
            return

        body = path.read_bytes()
        content_type = "text/html; charset=utf-8"

        if path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_file(INDEX_FILE)
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path != "/api/plan":
            self._send_json(404, {"error": "Route not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))

            goal = str(data.get("goal", "")).strip()
            level = str(data.get("level", "")).strip()
            daily_minutes = str(data.get("daily_minutes", "")).strip()
            duration = str(data.get("duration", "")).strip()

            if not all([goal, level, daily_minutes, duration]):
                self._send_json(400, {"error": "Please fill in all fields."})
                return

            plan = generate_plan(goal, level, daily_minutes, duration)
            self._send_json(200, {"plan": plan})

        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON request."})
        except requests.RequestException as error:
            self._send_json(502, {"error": f"Could not connect to OpenRouter: {error}"})
        except (KeyError, TypeError, RuntimeError, json.JSONDecodeError) as error:
            self._send_json(500, {"error": str(error)})
        except Exception as error:
            self._send_json(500, {"error": f"Unexpected error: {error}"})

    def log_message(self, format, *args):
        # Keep the classroom console clean.
        return


def open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    if not INDEX_FILE.exists():
        print("index.html was not found next to app.py")
        return

    server = ThreadingHTTPServer((HOST, PORT), MyGPTHandler)

    print("=" * 60)
    print("MY GPT - AI STUDY PLANNER")
    print("=" * 60)
    print(f"Open: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")

    threading.Timer(0.8, open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
