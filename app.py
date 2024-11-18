from flask import Flask, request, render_template, jsonify
import os
import uuid
import shutil
import pyodbc
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

# Configurações do Flask
app = Flask(__name__)

# Configurações do Azure
ENDPOINT = "https://brazilsouth.api.cognitive.microsoft.com/"
KEY = "54b90dfa62ed46cd941bf1bfb2e5908b"
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

# Configurações do Banco de Dados
server = 'sever1142233472-1142831584.database.windows.net'
database = 'BancoDosCria'
username = 'adminuser'
password = 'SuaSenhaForte123!'
driver = '{SQL Server}'

# Caminhos compartilhados
WINDOWS_SHARED_PATH = r"\\191.232.170.155\fotos"
LINUX_SHARED_PATH = r"\\191.234.180.95\SharedFolder"

# Função para conectar ao banco de dados
def get_db_connection():
    conn = pyodbc.connect(
        f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    return conn

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

# Rotas
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/criar", methods=["GET"])
def criar_registro():
    return render_template("criar_registro.html")

@app.route("/consultar", methods=["GET"])
def consultar_registros():
    return render_template("consultar_registros.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        # Verifica se os arquivos foram enviados
        if 'foto' not in request.files or 'documento' not in request.files:
            return jsonify({"error": "Foto ou documento não enviados."}), 400

        foto = request.files['foto']
        documento = request.files['documento']

        # Verifica se os campos obrigatórios estão preenchidos
        nome = request.form.get("nome")
        email = request.form.get("email")
        if not nome or not email:
            return jsonify({"error": "Campos obrigatórios ausentes."}), 400

        # Gera nomes únicos para os arquivos
        foto_filename = f"{uuid.uuid4()}_{foto.filename}"
        documento_filename = f"{uuid.uuid4()}_{documento.filename}"

        # Salva os arquivos nos compartilhamentos remotos
        foto_path = os.path.join(WINDOWS_SHARED_PATH, foto_filename)
        documento_path = os.path.join(LINUX_SHARED_PATH, documento_filename)

        with open(foto_path, 'wb') as img_file:
            shutil.copyfileobj(foto.stream, img_file)

        with open(documento_path, 'wb') as doc_file:
            shutil.copyfileobj(documento.stream, doc_file)

        # Detecta rostos na imagem
        face_count = detect_faces(foto_path)
        validacao_cognitiva = face_count > 0

        # Insere os dados no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Usuario (Nome, Email, Foto, Documento, ValidacaoCognitivo, QuantidadeRostos)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (nome, email, foto_path, documento_path, validacao_cognitiva, face_count)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Registro criado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/registros", methods=["GET"])
def registros():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Nome, Email, Foto, Documento FROM Usuario")
        rows = cursor.fetchall()
        conn.close()

        registros = [
            {"id": row[0], "nome": row[1], "email": row[2], "foto": row[3], "documento": row[4]}
            for row in rows
        ]
        return jsonify(registros)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
