import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
import google.generativeai as genai

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
EXERCICIOS_PROMPT_PATH = PROMPTS_DIR / "exercicios.txt"
CHAT_PROMPT_PATH = PROMPTS_DIR / "chat.txt"
PLACAS_DIR = BASE_DIR / "images" / "placas"

load_dotenv()

app = Flask(__name__)


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def get_model() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY nao encontrado no ambiente.")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def parse_quantity(payload: dict) -> int:
    quantity = payload.get("quantidade")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("'quantidade' deve ser um numero inteiro.")

    if quantity < 1 or quantity > 10:
        raise ValueError("'quantidade' deve estar entre 1 e 10.")

    return quantity


def extract_json(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    return json.loads(cleaned)


def list_placas() -> list[str]:
    if not PLACAS_DIR.exists():
        return []

    return sorted(
        name
        for name in os.listdir(PLACAS_DIR)
        if name.lower().endswith(".png")
    )


def build_image_url(filename: str) -> str:
    base_url = request.host_url.rstrip("/")
    return f"{base_url}/placas/{filename}"


def attach_image_urls(payload: dict, placas_disponiveis: set[str]) -> dict:
    exercicios = payload.get("exercicios")
    if not isinstance(exercicios, list):
        return payload

    for item in exercicios:
        if not isinstance(item, dict):
            continue

        placa = (item.get("placa") or "").strip()
        if placa in placas_disponiveis:
            item["imagem_url"] = build_image_url(placa)
        else:
            item["imagem_url"] = None

    return payload


@app.post("/exercicios")
def exercicios():
    payload = request.get_json(silent=True) or {}

    try:
        quantity = parse_quantity(payload)
        base_prompt = load_prompt(EXERCICIOS_PROMPT_PATH)
        model = get_model()
        placas_disponiveis = list_placas()
        placas_texto = ", ".join(placas_disponiveis) if placas_disponiveis else "(nenhuma)"
        prompt = (
            f"{base_prompt}\n\n"
            f"Gere exatamente {quantity} exercicios de CNH baseados no estilo de prova do DETRAN. "
            "Retorne somente JSON valido, sem texto extra, com este formato:\n"
            "{\n"
            '  "exercicios": [\n'
            '    {"numero": 1, "pergunta": "...", "alternativas": ["A", "B", "C", "D"], "resposta_correta": "A", "explicacao": "...", "placa": null}\n'
            "  ]\n"
            "}\n"
            "Se a questao envolver uma placa de sinalizacao, preencha o campo 'placa' com o nome do arquivo. "
            "Caso contrario, use null. Use somente um dos nomes abaixo, exatamente como listado:\n"
            f"{placas_texto}\n"
            "As perguntas precisam ser objetivas, praticas e coerentes com CNH categoria teorica."
        )
        response = model.generate_content(prompt)
        data = extract_json(response.text)
        data = attach_image_urls(data, set(placas_disponiveis))
        return jsonify(data)
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400
    except Exception as exc:
        return jsonify({"erro": "Falha ao gerar exercicios.", "detalhe": str(exc)}), 500


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("mensagem") or "").strip()
    history = payload.get("historico") or []

    if not message:
        return jsonify({"erro": "'mensagem' e obrigatoria."}), 400

    try:
        base_prompt = load_prompt(CHAT_PROMPT_PATH)
        model = get_model()

        chat_history = []
        for item in history:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if role in {"user", "model"} and content:
                chat_history.append({"role": role, "parts": [content]})

        session = model.start_chat(history=chat_history)
        response = session.send_message(f"{base_prompt}\n\nMensagem do aluno: {message}")
        return jsonify({"resposta": response.text})
    except Exception as exc:
        return jsonify({"erro": "Falha ao responder no chat.", "detalhe": str(exc)}), 500


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/placas/<path:filename>")
def placas(filename: str):
    return send_from_directory(PLACAS_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
