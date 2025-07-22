import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime

# Impressoras e tamanhos personalizados
IMPRESSORAS = {
    "RICOH": {"size_cm": (8.00, 5.82), "layout": "horizontal"},
    "SAMSUNG": {"size_cm": (19.28, 5.14), "layout": "vertical"},
    "KYOCERA": {"size_cm": (6.83, 16.6), "layout": "horizontal"},
}

TARIFA = 0.11
FONT_SIZE = 14
LOGO_PATH = None
dados = {}


def cm_para_pt(cm):
    return cm * 28.35


def carregar_logo():
    global LOGO_PATH
    LOGO_PATH = filedialog.askopenfilename(
        filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
    if LOGO_PATH:
        messagebox.showinfo("Sucesso", "Logo carregada com sucesso!")


# Interface gráfica principal
root = tk.Tk()
root.title("Gerador de Conta FACEMP")
root.geometry("950x850")
root.configure(bg="white")


def carregar_imagem(impressora, tipo, label):
    caminho = filedialog.askopenfilename(
        filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
    if caminho:
        img = Image.open(caminho)
        img.thumbnail((160, 160))
        img_tk = ImageTk.PhotoImage(img)
        label.configure(image=img_tk)
        label.image = img_tk
        dados[impressora][f"imagem_{tipo}"] = caminho


def gerar_pdf():
    if not LOGO_PATH:
        messagebox.showerror(
            "Erro", "Por favor, carregue a logo da empresa primeiro!")
        return

    nome_arquivo = f"conta_facemp_{datetime.now().strftime('%d-%m-%Y')}.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    largura_pagina, altura_pagina = A4
    total_geral = 0
    resumo = []

    # Páginas das impressoras
    for idx, (impressora, props) in enumerate(IMPRESSORAS.items()):
        info = dados[impressora]
        largura_cm, altura_cm = props["size_cm"]
        layout = props["layout"]
        largura_pt = cm_para_pt(largura_cm)
        altura_pt = cm_para_pt(altura_cm)

        try:
            abertura = int(info['entrada_abertura'].get())
            fechamento = int(info['entrada_fechamento'].get())
        except ValueError:
            messagebox.showerror(
                "Erro", f"Valores inválidos para {impressora}. Use apenas números.")
            return

        copias = max(0, fechamento - abertura)
        custo = copias * TARIFA
        total_geral += custo
        resumo.append((impressora, abertura, fechamento, copias, custo))

        # Cabeçalho
        c.setFont("Helvetica-Bold", FONT_SIZE)
        titulo = f"IMPRESSORA {impressora}"
        texto_largura = c.stringWidth(titulo, "Helvetica-Bold", FONT_SIZE)
        c.drawString((largura_pagina - texto_largura) /
                     2, altura_pagina - 60, titulo)

        # Imagens
        y_topo = altura_pagina - 100
        if layout == "horizontal":
            espaco_total = 2 * largura_pt + 20
            x1 = (largura_pagina - espaco_total) / 2
            x2 = x1 + largura_pt + 20

            if info['imagem_abertura']:
                c.drawImage(info['imagem_abertura'], x1, y_topo -
                            altura_pt, width=largura_pt, height=altura_pt)
                c.setFont("Helvetica", FONT_SIZE)
                c.drawCentredString(x1 + largura_pt / 2,
                                    y_topo - altura_pt - 20, "Abertura")

            if info['imagem_fechamento']:
                c.drawImage(info['imagem_fechamento'], x2, y_topo -
                            altura_pt, width=largura_pt, height=altura_pt)
                c.drawCentredString(x2 + largura_pt / 2,
                                    y_topo - altura_pt - 20, "Fechamento")

            y_texto = y_topo - altura_pt - 60

        else:  # vertical
            x = (largura_pagina - largura_pt) / 2
            if info['imagem_abertura']:
                c.drawImage(info['imagem_abertura'], x, y_topo -
                            altura_pt, width=largura_pt, height=altura_pt)
                c.setFont("Helvetica", FONT_SIZE)
                c.drawCentredString(x + largura_pt / 2,
                                    y_topo - altura_pt - 20, "Abertura")
                y_topo -= altura_pt + 60

            if info['imagem_fechamento']:
                c.drawImage(info['imagem_fechamento'], x, y_topo -
                            altura_pt, width=largura_pt, height=altura_pt)
                c.drawCentredString(x + largura_pt / 2,
                                    y_topo - altura_pt - 20, "Fechamento")
                y_topo -= altura_pt

            y_texto = y_topo - 60

        # Cálculos
        c.setFont("Helvetica", FONT_SIZE)
        calc1 = f"Abril em {abertura} | Fechou em {fechamento}"
        calc2 = f"{fechamento} - {abertura} = {copias} * R$ {TARIFA:.2f} = R$ {custo:.2f}"

        text1_w = c.stringWidth(calc1, "Helvetica", FONT_SIZE)
        text2_w = c.stringWidth(calc2, "Helvetica-Bold", FONT_SIZE)

        c.drawString((largura_pagina - text1_w) / 2, y_texto, calc1)
        y_texto -= 25
        c.setFont("Helvetica-Bold", FONT_SIZE)
        c.drawString((largura_pagina - text2_w) / 2, y_texto, calc2)

        c.showPage()

    # Página de Resumo
    c.setFont("Helvetica-Bold", FONT_SIZE)

    # Logo
    try:
        logo = ImageReader(LOGO_PATH)
        logo_width, logo_height = logo.getSize()
        aspect = logo_height / logo_width
        new_width = 200
        new_height = new_width * aspect
        c.drawImage(LOGO_PATH, (largura_pagina - new_width)/2, altura_pagina - 50 - new_height,
                    width=new_width, height=new_height)
        y_pos = altura_pagina - 60 - new_height
    except:
        y_pos = altura_pagina - 60

    # Informações das empresas com separação vertical
    c.setFont("Helvetica-Bold", FONT_SIZE)
    c.drawString(50, y_pos - 30, "NEWTEC GRÁFICA RÁPIDA")
    c.drawString(largura_pagina/2 + 30, y_pos - 30,
                 "UNIFACEMP - Centro universitário")

    # Linha vertical separadora
    c.line(largura_pagina/2, y_pos - 40, largura_pagina/2, y_pos - 80)

    c.setFont("Helvetica", FONT_SIZE)
    c.drawString(50, y_pos - 60, "CNPJ: 30.562.248/0001-07")
    c.drawString(largura_pagina/2 + 30, y_pos - 60, "CNPJ: 04.696.652/0001-63")

    # Linha divisória horizontal
    y_pos -= 90
    c.line(50, y_pos, largura_pagina - 50, y_pos)
    y_pos -= 40

    # Resumo dos cálculos
    c.setFont("Helvetica-Bold", FONT_SIZE + 2)
    c.drawCentredString(largura_pagina/2, y_pos, "RESUMO DOS CÁLCULOS")
    y_pos -= 40

    c.setFont("Helvetica", FONT_SIZE)
    for item in resumo:
        impressora, abertura, fechamento, copias, custo = item
        texto = f"{impressora}: {fechamento} - {abertura} = {copias} cópias × R$ {TARIFA:.2f} = R$ {custo:.2f}"
        c.drawString(100, y_pos, texto)
        y_pos -= 25

    # Linha divisória
    y_pos -= 20
    c.line(50, y_pos, largura_pagina - 50, y_pos)
    y_pos -= 40

    # Total geral
    c.setFont("Helvetica-Bold", FONT_SIZE + 4)
    total_text = f"TOTAL GERAL: R$ {total_geral:.2f}"
    tw = c.stringWidth(total_text, "Helvetica-Bold", FONT_SIZE + 4)
    c.drawString((largura_pagina - tw) / 2, y_pos, total_text)

    c.save()
    messagebox.showinfo("Sucesso", f"PDF gerado: {nome_arquivo}")
    os.startfile(nome_arquivo)


# Frame para carregar a logo
frame_logo = tk.LabelFrame(
    root, text="Logo da Empresa", padx=10, pady=10, bg="white")
frame_logo.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="n")

btn_logo = tk.Button(frame_logo, text="Carregar Logo",
                     command=carregar_logo, bg="blue", fg="white")
btn_logo.pack(pady=10)

# Interface para cada impressora
for i, impressora in enumerate(IMPRESSORAS):
    frame = tk.LabelFrame(
        root, text=f"Impressora {impressora}", padx=10, pady=10, bg="white")
    frame.grid(row=i, column=0, padx=20, pady=10, sticky="w")

    img1_label = tk.Label(frame, text="Imagem Abertura",
                          width=18, height=6, bg="lightgray")
    img1_label.grid(row=0, column=0, rowspan=3, padx=5)
    btn1 = tk.Button(frame, text="Carregar Abertura", command=lambda imp=impressora,
                     lbl=img1_label: carregar_imagem(imp, "abertura", lbl))
    btn1.grid(row=3, column=0)

    img2_label = tk.Label(frame, text="Imagem Fechamento",
                          width=18, height=6, bg="lightgray")
    img2_label.grid(row=0, column=1, rowspan=3, padx=5)
    btn2 = tk.Button(frame, text="Carregar Fechamento", command=lambda imp=impressora,
                     lbl=img2_label: carregar_imagem(imp, "fechamento", lbl))
    btn2.grid(row=3, column=1)

    tk.Label(frame, text="Leitura de Abertura:", bg="white").grid(
        row=0, column=2, sticky="e", padx=5)
    entrada_abertura = tk.Entry(frame)
    entrada_abertura.grid(row=0, column=3)

    tk.Label(frame, text="Leitura de Fechamento:", bg="white").grid(
        row=1, column=2, sticky="e", padx=5)
    entrada_fechamento = tk.Entry(frame)
    entrada_fechamento.grid(row=1, column=3)

    dados[impressora] = {
        "entrada_abertura": entrada_abertura,
        "entrada_fechamento": entrada_fechamento,
        "imagem_abertura": None,
        "imagem_fechamento": None,
    }

btn_gerar = tk.Button(root, text="Gerar PDF da Conta", command=gerar_pdf,
                      bg="green", fg="white", font=("Helvetica", 14))
btn_gerar.grid(row=len(IMPRESSORAS) + 1, column=0, pady=30, columnspan=2)

root.mainloop()
