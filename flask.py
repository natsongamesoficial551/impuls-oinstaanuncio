from flask import Flask, jsonify
import os
from dotenv import load_dotenv

# ==========================
# 🔧 Configurações Iniciais
# ==========================
load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot de Pagamentos Unibot está rodando com sucesso!"

@app.route("/status")
def status():
    return jsonify({"status": "online", "bot": "Unibot Pagamentos", "version": "1.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
