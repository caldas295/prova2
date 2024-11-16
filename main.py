import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import pyodbc

# Configuração da conexão com o banco de dados
CONN_STRING = (
    "Driver={SQL Server};"
    "Server=servidor11422334721142831584.database.windows.net;"  # Substitua pelo nome do servidor
    "Database=bancodados11422334721142831584;"  # Substitua pelo nome do banco de dados
    "UID=usuarioAdmin;"  # Substitua pelo nome de usuário
    "PWD=Novembro@2024;"  # Substitua pela senha
)

# Janela principal
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Cadastro e Consulta")
        self.foto_path = None
        self.doc_path = None

        # Conexão com o banco de dados
        self.conn = self.conectar_banco()

        # Criação de abas
        self.tab_control = ttk.Notebook(root)
        self.tab_cadastro = ttk.Frame(self.tab_control)
        self.tab_consulta = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_cadastro, text="Cadastro")
        self.tab_control.add(self.tab_consulta, text="Consulta")
        self.tab_control.pack(expand=1, fill="both")

        # Tela de Cadastro
        self.build_tela_cadastro()

        # Tela de Consulta
        self.build_tela_consulta()

    def conectar_banco(self):
        try:
            conn = pyodbc.connect(CONN_STRING)
            print("Conexão com o banco de dados bem-sucedida!")
            return conn
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {e}")
            exit()

    def build_tela_cadastro(self):
        ttk.Label(self.tab_cadastro, text="Nome:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_nome = ttk.Entry(self.tab_cadastro)
        self.entry_nome.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self.tab_cadastro, text="Idade:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_idade = ttk.Entry(self.tab_cadastro)
        self.entry_idade.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.tab_cadastro, text="E-mail:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_email = ttk.Entry(self.tab_cadastro)
        self.entry_email.grid(row=2, column=1, padx=10, pady=5)

        ttk.Button(self.tab_cadastro, text="Anexar Foto", command=self.anexar_foto).grid(row=3, column=0, padx=10, pady=5)
        ttk.Button(self.tab_cadastro, text="Anexar Documento", command=self.anexar_documento).grid(row=3, column=1, padx=10, pady=5)

        ttk.Button(self.tab_cadastro, text="Salvar", command=self.salvar).grid(row=4, column=0, columnspan=2, pady=10)

    def build_tela_consulta(self):
        self.tree = ttk.Treeview(self.tab_consulta, columns=("id", "nome", "idade", "email"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("idade", text="Idade")
        self.tree.heading("email", text="E-mail")
        self.tree.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        ttk.Button(self.tab_consulta, text="Atualizar Lista", command=self.carregar_dados).grid(row=1, column=0, pady=5)

    def anexar_foto(self):
        self.foto_path = filedialog.askopenfilename(filetypes=[("Imagem", "*.png;*.jpg;*.jpeg")])
        if self.foto_path:
            messagebox.showinfo("Foto", "Foto anexada com sucesso!")

    def anexar_documento(self):
        self.doc_path = filedialog.askopenfilename(filetypes=[("Documento", "*.pdf;*.docx")])
        if self.doc_path:
            messagebox.showinfo("Documento", "Documento anexado com sucesso!")

    def salvar(self):
        nome = self.entry_nome.get()
        idade = self.entry_idade.get()
        email = self.entry_email.get()

        if not nome or not idade or not email:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return

        try:
            with open(self.foto_path, "rb") as f:
                foto_bin = f.read()

            with open(self.doc_path, "rb") as d:
                doc_bin = d.read()

            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO Usuario (Nome, Idade, Email, Foto, Documento)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nome, idade, email, foto_bin, doc_bin),
            )
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
            self.entry_nome.delete(0, tk.END)
            self.entry_idade.delete(0, tk.END)
            self.entry_email.delete(0, tk.END)
            self.foto_path = None
            self.doc_path = None
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar os dados: {e}")

    def carregar_dados(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ID, Nome, Idade, Email FROM Usuario")
            for row in cursor.fetchall():
                self.tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar os dados: {e}")


# Rodar o app
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
