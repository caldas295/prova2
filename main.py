import os
import requests
import pyodbc
from flask import Flask, request, jsonify
_name_ = "_name_";
app = Flask(_name_)

# Configurações
COGNITIVE_ENDPOINT = "https://brazilsouth.api.cognitive.microsoft.com/"
COGNITIVE_KEY = "54b90dfa62ed46cd941bf1bfb2e5908b"
FOTO_DIR = r"\\<ip_vm_windows>\fotos"  # Compartilhamento de rede ou local
DOC_DIR = r"\\<ip_vm_linux>\documentos"  # Compartilhamento de rede ou local

# Conexão com Azure SQL Database
DB_CONNECTION_STRING = (
    "Driver={SQL Server};"
    "SERVER=sever1142233472-1142831584.database.windows.net;"
    "DATABASE=BancoDosCria ;"
    "UID=adminuser;"
    "PWD=SuaSenhaForte123!;"
)

# Função para verificar a presença de uma pessoa na imagem
def verificar_imagem(foto_path):
    with open(foto_path, "rb") as foto:
        headers = {
            "Ocp-Apim-Subscription-Key": COGNITIVE_KEY,
            "Content-Type": "application/octet-stream",
        }
        params = {"visualFeatures": "Description"}
        response = requests.post(
            f"{COGNITIVE_ENDPOINT}/vision/v3.1/analyze",
            headers=headers,
            params=params,
            data=foto,
        )
        response.raise_for_status()
        analysis = response.json()
        descriptions = analysis["description"]["tags"]
        return "person" in descriptions

# Rota para processar dados
@app.route("/submit", methods=["POST"])
def processar_dados():
    nome = request.form.get("nome")
    idade = request.form.get("idade")
    email = request.form.get("email")
    foto = request.files.get("foto")
    documento = request.files.get("documento")

    if not all([nome, idade, email, foto, documento]):
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    # Salvar foto e verificar presença de pessoa
    foto_path = os.path.join(FOTO_DIR, foto.filename)
    foto.save(foto_path)
    if not verificar_imagem(foto_path):
        return jsonify({"error": "A imagem não contém uma pessoa"}), 400

    # Salvar documento
    documento_path = os.path.join(DOC_DIR, documento.filename)
    documento.save(documento_path)

    # Salvar dados no banco de dados
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO usuarios (nome, idade, email, foto_path, documento_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            nome, idade, email, foto_path, documento_path
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Erro ao salvar no banco de dados: {str(e)}"}), 500

    return jsonify({"message": "Dados processados com sucesso"}), 200

if _name_ == "_name_":
    app.run(debug=True)
