import json
import os
import re
import time
import requests
from flask import Flask, Response, jsonify, render_template, request

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "10m")

# The four project files can all live in this same folder.
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 65_000

TONES = {
    "friendly", "professional", "playful",
    "persuasive", "informative", "inspiring",
}
LENGTHS = {"short", "standard", "detailed"}
CONTENT_TYPES = {"blog", "caption"}
PLATFORMS = {"Instagram", "LinkedIn", "Facebook", "X", "General"}

TOKEN_LIMITS = {
    "blog": {"short": 240, "standard": 520, "detailed": 900},
    "caption": {"short": 100, "standard": 180, "detailed": 280},
}


class AppError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status


def error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def read_text(data, key, required=False, limit=500):
    value = data.get(key, "")
    if not isinstance(value, str):
        raise AppError("INVALID_INPUT", f"{key} must be text.")
    value = value.strip()
    if required and not value:
        raise AppError("INVALID_INPUT", f"{key.capitalize()} is required.")
    if len(value) > limit:
        raise AppError("INVALID_INPUT", f"{key.capitalize()} must be {limit} characters or fewer.")
    return value


def validate_generation(data):
    if not isinstance(data, dict):
        raise AppError("INVALID_INPUT", "Send the form as JSON.")

    content_type = data.get("contentType")
    tone = data.get("tone")
    length = data.get("length")
    platform = data.get("platform", "General")
    call_to_action = data.get("callToAction", False)

    if not isinstance(content_type, str) or content_type not in CONTENT_TYPES:
        raise AppError("INVALID_INPUT", "Choose blog post or social caption.")
    if not isinstance(tone, str) or tone not in TONES:
        raise AppError("INVALID_INPUT", "Choose a tone from the list.")
    if not isinstance(length, str) or length not in LENGTHS:
        raise AppError("INVALID_INPUT", "Choose short, standard, or detailed length.")
    if not isinstance(platform, str) or platform not in PLATFORMS:
        raise AppError("INVALID_INPUT", "Choose a supported platform.")
    if not isinstance(call_to_action, bool):
        raise AppError("INVALID_INPUT", "Call to action must be true or false.")

    return {
        "contentType": content_type,
        "topic": read_text(data, "topic", required=True, limit=240),
        "tone": tone,
        "length": length,
        "audience": read_text(data, "audience", limit=160),
        "keyPoints": read_text(data, "keyPoints", limit=600),
        "platform": platform,
        "callToAction": call_to_action,
    }


def validate_refinement(data):
    if not isinstance(data, dict):
        raise AppError("INVALID_INPUT", "Send the refinement as JSON.")

    content_type = data.get("contentType")
    tone = data.get("tone", "friendly")
    platform = data.get("platform", "General")

    if not isinstance(content_type, str) or content_type not in CONTENT_TYPES:
        raise AppError("INVALID_INPUT", "Choose blog post or social caption.")
    if not isinstance(tone, str) or tone not in TONES:
        raise AppError("INVALID_INPUT", "Choose a tone from the list.")
    if not isinstance(platform, str) or platform not in PLATFORMS:
        raise AppError("INVALID_INPUT", "Choose a supported platform.")

    return {
        "contentType": content_type,
        "tone": tone,
        "platform": platform,
        "draft": read_text(data, "draft", required=True, limit=10_000),
        "instruction": read_text(data, "instruction", required=True, limit=240),
    }


def generation_messages(values):
    if values["contentType"] == "blog":
        system = (
            "You are a skilled blog writer. Write clear, useful prose. "
            "Do not invent statistics, quotations, or factual claims. "
            "Return only the finished blog in simple Markdown, with a title "
            "and clear section headings."
        )
        label = "blog post"
    else:
        system = (
            "You are a social media copywriter. Return only the finished "
            "caption, with natural line breaks. Avoid hashtag stuffing and "
            "unsupported claims."
        )
        label = f"{values['platform']} social media caption"

    details = [
        f"Create a {label} about: {values['topic']}",
        f"Tone: {values['tone']}.",
        {
            "short": "Keep it brief and focused.",
            "standard": "Give useful detail without repetition.",
            "detailed": "Develop the main ideas with useful detail.",
        }[values["length"]],
    ]

    if values["audience"]:
        details.append(f"Intended audience: {values['audience']}.")
    if values["keyPoints"]:
        details.append(f"Points to include: {values['keyPoints']}")
    if values["contentType"] == "caption" and values["callToAction"]:
        details.append("End with a natural call to action.")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(details)},
    ]


def refinement_messages(values):
    kind = "blog post" if values["contentType"] == "blog" else f"{values['platform']} caption"
    return [
        {
            "role": "system",
            "content": (
                f"You are editing a {kind}. Apply the requested change while "
                "preserving the draft's meaning and factual claims. Return only "
                "the complete revised text. Do not add explanations or invent facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Tone: {values['tone']}.\n"
                f"Requested change: {values['instruction']}\n\n"
                f"Current draft:\n{values['draft']}"
            ),
        },
    ]


def open_ollama_stream(messages, token_limit):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": True,
                "keep_alive": KEEP_ALIVE,
                "think": False,
                "options": {
                    "num_predict": token_limit,
                    "temperature": 0.7,
                    "top_p": 0.9,
                },
            },
            stream=True,
            timeout=(3, 120),
        )
    except requests.Timeout as error:
        raise AppError(
            "OLLAMA_TIMEOUT",
            "Ollama took too long to respond. Try a shorter draft.",
            504,
        ) from error
    except requests.RequestException as error:
        raise AppError(
            "OLLAMA_UNAVAILABLE",
            "Ollama is not responding. Start Ollama and try again.",
            503,
        ) from error

    if response.status_code >= 400:
        try:
            details = response.json().get("error", "")
        except (ValueError, AttributeError):
            details = ""
        response.close()

        if response.status_code == 404 or "model" in str(details).lower():
            raise AppError(
                "MODEL_NOT_FOUND",
                f"Model {MODEL} was not found. Run: ollama pull {MODEL}",
                503,
            )
        raise AppError("OLLAMA_ERROR", "Ollama could not generate a response.", 502)

    return response


def event(name, payload):
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {name}\ndata: {data}\n\n"


def stream_response(upstream):
    parts = []
    started = time.monotonic()
    finished = False

    try:
        for line in upstream.iter_lines():
            if not line:
                continue

            try:
                item = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                yield event("error", {
                    "code": "INVALID_MODEL_RESPONSE",
                    "message": "Ollama returned an unreadable response.",
                })
                return

            if not isinstance(item, dict):
                continue
            if item.get("error"):
                yield event("error", {
                    "code": "OLLAMA_ERROR",
                    "message": "Ollama reported a generation error. Try again.",
                })
                return

            message = item.get("message", {})
            text = message.get("content", "") if isinstance(message, dict) else ""
            if text:
                parts.append(text)
                yield event("token", {"text": text})

            if item.get("done") is True:
                finished = True
                break

        full_text = "".join(parts)
        if not finished:
            yield event("error", {
                "code": "INCOMPLETE_RESPONSE",
                "message": "The stream ended before generation finished. Try again.",
            })
        elif not full_text.strip():
            yield event("error", {
                "code": "EMPTY_RESPONSE",
                "message": "The model returned an empty response. Try again.",
            })
        else:
            yield event("done", {
                "wordCount": len(full_text.split()),
                "characterCount": len(full_text),
                "durationMs": round((time.monotonic() - started) * 1000),
            })

    except requests.Timeout:
        yield event("error", {
            "code": "OLLAMA_TIMEOUT",
            "message": "Ollama stopped responding. Try a shorter draft.",
        })
    except Exception:
        app.logger.exception("Ollama stream failed")
        yield event("error", {
            "code": "STREAM_FAILED",
            "message": "Generation stopped unexpectedly. Please try again.",
        })
    finally:
        upstream.close()


def start_stream(messages, token_limit):
    try:
        upstream = open_ollama_stream(messages, token_limit)
    except AppError as error:
        return error_response(error.code, error.message, error.status)

    response = Response(stream_response(upstream), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@app.get("/")
def home():
    return render_template("index.html", model_name=MODEL)





@app.get("/api/health")
def health():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=(2, 5))
        response.raise_for_status()
        models = response.json().get("models", [])
    except (requests.RequestException, ValueError, AttributeError):
        return jsonify({
            "status": "unavailable",
            "model": MODEL,
            "message": "Ollama is not responding. Start it and refresh this page.",
        })

    installed = any(
        model.get("name") == MODEL or model.get("model") == MODEL
        for model in models
        if isinstance(model, dict)
    )
    if not installed:
        return jsonify({
            "status": "model_missing",
            "model": MODEL,
            "message": f"Model missing. Run: ollama pull {MODEL}",
        })

    return jsonify({"status": "ready", "model": MODEL, "message": "Local model ready"})


@app.post("/api/generate")
def generate():
    try:
        values = validate_generation(request.get_json(silent=True))
    except AppError as error:
        return error_response(error.code, error.message, error.status)

    token_limit = TOKEN_LIMITS[values["contentType"]][values["length"]]
    return start_stream(generation_messages(values), token_limit)


@app.post("/api/refine")
def refine():
    try:
        values = validate_refinement(request.get_json(silent=True))
    except AppError as error:
        return error_response(error.code, error.message, error.status)

    token_limit = min(max(len(values["draft"].split()) * 2, 150), 1000)
    return start_stream(refinement_messages(values), token_limit)


@app.errorhandler(413)
def too_large(_error):
    return error_response(
        "REQUEST_TOO_LARGE",
        "That request is too large. Shorten the draft or key points.",
        413,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)