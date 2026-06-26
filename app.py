"""
Leitor de IA - versao web
Cola o texto, ele gera a voz do Antonio (edge-tts) e toca.
Funciona em qualquer celular/PC pelo navegador.
"""

from flask import Flask, request, send_file, render_template
import edge_tts
import asyncio
import io
import re
import emoji

app = Flask(__name__)

VOZ_PADRAO = "pt-BR-AntonioNeural"


def limpar_texto(txt):
    """Remove markdown e lixo antes de falar."""
    txt = txt.strip()
    if txt.lower().startswith("claude respondeu:"):
        txt = txt[len("claude respondeu:"):].strip()
    # blocos de codigo inteiros
    txt = re.sub(r"```[\s\S]*?```", " ", txt)
    txt = txt.replace("`", "")
    # negrito / italico
    txt = re.sub(r"\*{1,3}", "", txt)
    txt = re.sub(r"_{1,3}", "", txt)
    # titulos
    txt = re.sub(r"^#{1,6}\s*", "", txt, flags=re.MULTILINE)
    # marcadores de lista
    txt = re.sub(r"^\s*[-*+]\s+", "", txt, flags=re.MULTILINE)
    # links [texto](url) -> texto
    txt = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", txt)
    # linhas horizontais
    txt = re.sub(r"^[-=]{3,}\s*$", "", txt, flags=re.MULTILINE)
    # tabelas
    txt = txt.replace("|", " ")
    txt = re.sub(r"[ \t]{2,}", " ", txt)
    txt = emoji.replace_emoji(txt, replace='')
    return txt.strip()


async def gerar_audio(texto, voz, velocidade):
    communicate = edge_tts.Communicate(texto, voz, rate=velocidade)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/falar", methods=["POST"])
def falar():
    dados = request.get_json()
    texto = limpar_texto(dados.get("texto", ""))
    voz = dados.get("voz", VOZ_PADRAO)
    velocidade = dados.get("velocidade", "+0%")

    if not texto:
        return {"erro": "texto vazio"}, 400

    buffer = asyncio.run(gerar_audio(texto, voz, velocidade))
    return send_file(buffer, mimetype="audio/mpeg", download_name="fala.mp3")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
