from flask import Flask, request, jsonify, render_template
import os
import uuid
import shutil
import pyodbc
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

# Configurações do Flask
app = Flask(__name__)

# Configurações do Banco de Dados
server = 'sever1142233472-1142831584.database.windows.net'
database = 'BancoDosCria'
username = 'adminuser'
password = 'SuaSenhaForte123!'
driver = '{SQL Server}'

# Caminhos compartilhados
WINDOWS_SHARED_PATH = r"\\191.232.245.246\fotos"
usuarioVMWindows = "azureuser"
senhaVMWindows = "P@ssw0rd2024!"

# Mapeia o compartilhamento de rede com autenticação
def mapear_rede(caminho, usuario, senha):
    comando = f'net use {caminho} /user:{usuarioVMWindows} {senhaVMWindows}'
    os.system(comando)

LINUX_SHARED_PATH = "//191.234.213.204/documentos/mnt/documentos"

# Função para conectar ao banco de dados
def get_db_connection():
    conn = pyodbc.connect(
        f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    return conn


# Configurações do Azure Cognitive Services
ENDPOINT = "https://brazilsouth.api.cognitive.microsoft.com/"
KEY = "54b90dfa62ed46cd941bf1bfb2e5908b"
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

# Função para detectar rostos na imagem
def detect_faces(image_path):
    with open(image_path, 'rb') as image_stream:
        detected_faces = face_client.face.detect_with_stream(
            image=image_stream,
            detection_model="detection_01",
            recognition_model="recognition_04",
            return_face_id=False
        )
    return len(detected_faces)

# Rota principal (Página Inicial)
@app.route("/", methods=["GET"])
def pagina_inicial():
    return render_template("pagina_inicial.html")

# Rota pagina de criar registro 
@app.route("/criar", methods=["GET"])
def criar_registro_pagina():
    return render_template("criar_registro.html")

# Rota pagina de consultar registro 
@app.route("/consultar", methods=["GET"])
def consultar_Registro_pagina():
    return render_template("Consultar_Registro.html")

# Função para criar registro no Azure
@app.route("/criarRegistroAzure", methods=["POST"])
def criarRegistroAzure():
    try:
        if 'foto' not in request.files or 'documento' not in request.files:
            return jsonify({"error": "Foto ou documento não enviados."}), 400

        foto = request.files['foto']
        documento = request.files['documento']
        nome = request.form.get("nome")
        email = request.form.get("email")
        idade = request.form.get("idade")

        if not nome or not email:
            return jsonify({"error": "Campos obrigatórios ausentes."}), 400

        # Gerar nomes únicos
        foto_filename = f"{uuid.uuid4()}_{foto.filename}"
        documento_filename = f"{uuid.uuid4()}_{documento.filename}"

        mapear_rede(WINDOWS_SHARED_PATH, usuarioVMWindows, senhaVMWindows)

        # Salvar arquivos
        print('WINDOWS_SHARED_PATH>>>>'+ WINDOWS_SHARED_PATH)
        foto_path = os.path.join(WINDOWS_SHARED_PATH, foto_filename)

        # Criar diretório se necessário
        if not os.path.exists(WINDOWS_SHARED_PATH):
            os.makedirs(WINDOWS_SHARED_PATH)

        documento_path = os.path.join(LINUX_SHARED_PATH, documento_filename)

        with open(foto_path, 'wb') as img_file:
            shutil.copyfileobj(foto.stream, img_file)
        # with open(documento_path, 'wb') as doc_file:
        #     shutil.copyfileobj(documento.stream, doc_file)

        # Detectar rostos
        face_count = detect_faces(foto_path)
        temPessoaNaFoto = face_count > 0;

        # Salvar dados no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Usuario (Nome, Email, Idade,Documento, Foto, QuantidadeRostos, TemPessoaNaFoto)
               VALUES (?, ?, ?, ?, ?, ?,?)''',
            (nome, email,idade,documento_path, foto_path, face_count,temPessoaNaFoto)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Registro criado com sucesso!"}), 201
    except Exception as e:
        print('error>>>>'+ str(e))
        return jsonify({"error": str(e)}), 500

# Função para consultar dados no banco
@app.route("/consultarDados", methods=["GET"])
def consultarDados():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Nome, Email, Foto, Documento, QuantidadeRostos,TemPessoaNaFoto FROM Usuario")
        rows = cursor.fetchall()
        conn.close()

        registros = [
            {
                "id": row[0],
                "nome": row[1],
                "email": row[2],
                "foto": row[3],
                "documento": row[4],
                "quantidade_rostos": row[5],
                "TemPessoaNaFoto": row[6]
            }
            for row in rows
        ]
        return jsonify(registros), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
