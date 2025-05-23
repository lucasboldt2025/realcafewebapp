from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io
from datetime import datetime
from typing import List
from pydantic import BaseModel
import pandas as pd
from fpdf import FPDF

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SENHAS = {
    "1234": "Usuário A",
    "2345": "Usuário B",
    "3456": "Usuário C",
    "4567": "Usuário D"
}

ferramentas = []
log_alteracoes = []

class Ferramenta(BaseModel):
    id: int
    nome: str
    descricao: str

usuario_logado = None
senha_usada = None

def verificar_senha(senha: str):
    global usuario_logado, senha_usada
    if senha in SENHAS:
        usuario_logado = SENHAS[senha]
        senha_usada = senha
        return True
    return False

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "ferramentas": ferramentas, "usuario": usuario_logado})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, senha: str = Form(...)):
    if verificar_senha(senha):
        response = RedirectResponse("/", status_code=302)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "erro": "Senha inválida"})

@app.get("/logout")
async def logout():
    global usuario_logado, senha_usada
    usuario_logado = None
    senha_usada = None
    return RedirectResponse("/login", status_code=302)

@app.post("/add_ferramenta", response_class=HTMLResponse)
async def add_ferramenta(request: Request, nome: str = Form(...), descricao: str = Form(...), senha: str = Form(...)):
    if not verificar_senha(senha):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ferramentas": ferramentas,
            "erro": "Senha inválida para adicionar ferramenta",
            "usuario": usuario_logado
        })
    nova_id = max([f.id for f in ferramentas], default=0) + 1
    ferramenta = Ferramenta(id=nova_id, nome=nome, descricao=descricao)
    ferramentas.append(ferramenta)
    log_alteracoes.append(f"{datetime.now()} - {usuario_logado} adicionou a ferramenta: {nome}")
    return RedirectResponse("/", status_code=302)

@app.post("/remover_ferramenta", response_class=HTMLResponse)
async def remover_ferramenta(request: Request, id: int = Form(...), senha: str = Form(...)):
    global ferramentas  # <- Aqui está o global no lugar CERTO

    if not verificar_senha(senha):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ferramentas": ferramentas,
            "erro": "Senha inválida para remover ferramenta",
            "usuario": usuario_logado
        })

    ferramenta = next((f for f in ferramentas if f.id == id), None)
    if ferramenta:
        ferramentas = [f for f in ferramentas if f.id != id]
        log_alteracoes.append(f"{datetime.now()} - {usuario_logado} removeu a ferramenta: {ferramenta.nome}")
    return RedirectResponse("/", status_code=302)

@app.post("/importar_excel", response_class=HTMLResponse)
async def importar_excel(request: Request, senha: str = Form(...), file=Form(...)):
    global ferramentas  # <- Aqui também

    if not verificar_senha(senha):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ferramentas": ferramentas,
            "erro": "Senha inválida para importar Excel",
            "usuario": usuario_logado
        })

    form = await request.form()
    upload = form.get("file")
    if not upload or upload.filename == "":
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ferramentas": ferramentas,
            "erro": "Nenhum arquivo selecionado",
            "usuario": usuario_logado
        })

    df = pd.read_excel(upload.file)
    ferramentas.clear()
    for i, row in df.iterrows():
        ferramentas.append(Ferramenta(id=i+1, nome=row['nome'], descricao=row['descricao']))
    log_alteracoes.append(f"{datetime.now()} - {usuario_logado} importou ferramentas do Excel")
    return RedirectResponse("/", status_code=302)

@app.get("/gerar_pdf")
async def gerar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Relatório de Ferramentas", ln=True, align="C")
    pdf.ln(10)
    for f in ferramentas:
        pdf.cell(0, 10, f"ID: {f.id} - Nome: {f.nome} - Descrição: {f.descricao}", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, "Log de Alterações:", ln=True)
    for log in log_alteracoes:
        pdf.cell(0, 10, log, ln=True)
    pdf_output = pdf.output(dest='S').encode('latin1')
    return FileResponse(io.BytesIO(pdf_output), media_type='application/pdf', filename='relatorio_ferramentas.pdf')
