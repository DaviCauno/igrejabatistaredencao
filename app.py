from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

load_dotenv()

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = "igreja123"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://postgres.takcpetublqyufrskidy:Catitu18%40red4488@aws-1-us-west-2.pooler.supabase.com:5432/postgres"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELOS ----------------

class Movimentacao(db.Model):
    __tablename__ = "movimentacoes"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date)
    tipo = db.Column(db.String(50))
    categoria = db.Column(db.String(50))
    descricao = db.Column(db.Text)
    valor = db.Column(db.Numeric(10, 2))
    forma_pagamento = db.Column(db.String(30))
    observacao = db.Column(db.Text)
    usuario_nome = db.Column(db.String(100))

class Membro(db.Model):
    __tablename__ = "membros"

    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(200))

    data_inscricao = db.Column(db.DateTime, default=datetime.now)

    idade = db.Column(db.SmallInteger)

    membresia = db.Column(db.Text)

    aniversario = db.Column(db.Date)
    data_nascimento = db.Column(db.Date)
    mes_aniversario = db.Column(db.String(20))

    endereco = db.Column(db.Text)
    bairro = db.Column(db.Text)
    cidade = db.Column(db.Text)

    celular = db.Column(db.Text)

    batizado = db.Column(db.Boolean)

    diagnostico = db.Column(db.Text)

    alergia = db.Column(db.Boolean)

    casamento = db.Column(db.Boolean)
    data_casamento = db.Column(db.Date)

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    perfil = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime)


# ---------------- ROTAS ----------------

@app.route("/")
def dashboard():
    if not session.get("logado"):
        return redirect(url_for("login"))

    entradas = db.session.execute(
        text("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE tipo='entrada'")
    ).scalar()

    saidas = db.session.execute(
        text("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE tipo='saida'")
    ).scalar()

    saldo = float(entradas) - float(saidas)

    return render_template(
        "dashboard.html",
        entradas=entradas,
        saidas=saidas,
        saldo=saldo
    )


@app.route("/movimentacoes")
def movimentacoes():
    if not session.get("logado"):
        return redirect(url_for("login"))

    lista = Movimentacao.query.order_by(Movimentacao.id.desc()).all()
    return render_template("movimentacoes.html", lista=lista)


@app.route("/nova", methods=["POST"])
def nova_movimentacao():
    if not session.get("logado"):
        return redirect(url_for("login"))

    nova = Movimentacao(
        data=datetime.strptime(request.form["data"], "%Y-%m-%d"),
        tipo=request.form["tipo"],
        categoria=request.form["categoria"],
        descricao=request.form["descricao"],
        valor=request.form["valor"],
        forma_pagamento=request.form["forma_pagamento"],
        observacao=request.form["observacao"],
        usuario_nome=session.get("usuario")  # 🔥 AQUI CORRETO
    )

    db.session.add(nova)
    db.session.commit()

    return redirect(url_for("movimentacoes"))


@app.route("/excluir/<int:id>")
def excluir_movimentacao(id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    mov = Movimentacao.query.get_or_404(id)
    db.session.delete(mov)
    db.session.commit()

    return redirect(url_for("movimentacoes"))

@app.route("/membros")
def membros():
    if not session.get("logado"):
        return redirect(url_for("login"))

    lista = Membro.query.order_by(Membro.nome_completo).all()
    return render_template("membros.html", lista=lista)
@app.route("/membros/novo", methods=["POST"])
def novo_membro():
    if not session.get("logado"):
        return redirect(url_for("login"))

    nascimento = request.form.get("data_nascimento")
    aniversario = request.form.get("aniversario")

    membro = Membro(
        nome_completo=request.form["nome_completo"],
        idade=request.form.get("idade") or None,
        membresia=request.form.get("membresia"),

        data_nascimento=datetime.strptime(nascimento, "%Y-%m-%d") if nascimento else None,
        aniversario=datetime.strptime(aniversario, "%Y-%m-%d") if aniversario else None,

        mes_aniversario=request.form.get("mes_aniversario"),

        endereco=request.form.get("endereco"),
        bairro=request.form.get("bairro"),
        cidade=request.form.get("cidade"),

        celular=request.form.get("celular"),

        batizado=True if request.form.get("batizado") == "on" else False,

        diagnostico=request.form.get("diagnostico"),

        alergia=True if request.form.get("alergia") == "on" else False,

        casamento=True if request.form.get("casamento") == "on" else False,

        data_casamento=datetime.strptime(request.form["data_casamento"], "%Y-%m-%d")
        if request.form.get("data_casamento") else None
    )

    db.session.add(membro)
    db.session.commit()

    return redirect(url_for("membros"))


#----HOME----
@app.route("/home")
def home():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return render_template("home.html")



#------------EXPORT--------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import send_file

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from flask import send_file

@app.route("/exportar/<int:id>")
def exportar_movimentacao(id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    mov = Movimentacao.query.get_or_404(id)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # 🎨 estilos personalizados
    titulo = ParagraphStyle(
        name="Titulo",
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    subtitulo = ParagraphStyle(
        name="SubTitulo",
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey
    )

    normal = styles["Normal"]

    conteudo = []

    # 🏛️ NOME DA IGREJA
    conteudo.append(Paragraph("IGREJA BATISTA REDENÇÃO", titulo))
    conteudo.append(Paragraph("Recibo de Movimentação Financeira", subtitulo))
    conteudo.append(Spacer(1, 20))

    # 📄 TÍTULO
    conteudo.append(Paragraph("<b>RECIBO</b>", titulo))
    conteudo.append(Spacer(1, 20))

    # 📊 DADOS EM TABELA
    dados = [
        ["Data", mov.data.strftime("%d/%m/%Y")],
        ["Tipo", mov.tipo],
        ["Categoria", mov.categoria],
        ["Valor", f"R$ {mov.valor}"],
        ["Forma de Pagamento", mov.forma_pagamento],
        ["Registrado por", mov.usuario_nome or "-"],
    ]

    tabela = Table(dados, colWidths=[180, 250])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    conteudo.append(tabela)
    conteudo.append(Spacer(1, 20))

    # 📝 DESCRIÇÃO
    conteudo.append(Paragraph("<b>Descrição:</b>", normal))
    conteudo.append(Paragraph(mov.descricao or "-", normal))
    conteudo.append(Spacer(1, 10))

    conteudo.append(Paragraph("<b>Observação:</b>", normal))
    conteudo.append(Paragraph(mov.observacao or "-", normal))
    conteudo.append(Spacer(1, 40))

    # ✍️ ASSINATURA
    conteudo.append(Paragraph("_____________________________________", normal))
    conteudo.append(Paragraph("Responsável", normal))

    # 📌 RODAPÉ
    conteudo.append(Spacer(1, 30))
    conteudo.append(Paragraph(
        "Documento gerado automaticamente pelo Sistema Financeiro",
        subtitulo
    ))

    doc.build(conteudo)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"recibo_{id}.pdf",
        mimetype="application/pdf"
    )


# ---------------- USUÁRIOS ----------------


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":

        # 🔐 valida palavra-chave
        palavra_chave = request.form["palavra_chave"]
        if palavra_chave != "redencao":
            return render_template("cadastro.html", erro="Palavra-chave inválida")

        # verifica email
        existe = Usuario.query.filter_by(email=request.form["email"]).first()
        if existe:
            return render_template("cadastro.html", erro="Este email já está em uso")

        novo = Usuario(
            nome=request.form["nome"],
            email=request.form["email"],
            senha=generate_password_hash(request.form["senha"]),
            perfil="admin",
            ativo=True,
            criado_em=datetime.now()
        )

        db.session.add(novo)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email, ativo=True).first()

        if usuario and check_password_hash(usuario.senha, senha):
            session["logado"] = True
            session["usuario"] = usuario.nome
            session["perfil"] = usuario.perfil

            return redirect(url_for("home"))

        return render_template("login.html", erro="Email ou senha inválidos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



# ---------------- ANALISE ----------------

@app.route("/analise", methods=["GET"])
def analise():
    if not session.get("logado"):
        return redirect(url_for("login"))

    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    tipo = request.args.get("tipo")
    categorias = request.args.getlist("categoria")

    query = Movimentacao.query

    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        query = query.filter(Movimentacao.data >= data_inicio)

    if data_fim:
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        query = query.filter(Movimentacao.data <= data_fim)

    if tipo:
        query = query.filter(Movimentacao.tipo == tipo)

    if categorias:
        query = query.filter(Movimentacao.categoria.in_(categorias))

    lista = query.order_by(Movimentacao.data.desc()).all()

    return render_template("analise.html", lista=lista)


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)