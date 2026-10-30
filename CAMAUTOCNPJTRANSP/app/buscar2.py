import subprocess
import csv
from datetime import datetime
import re
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from urllib.parse import urlparse

# =====================================================
# CONFIGURAÇÃO
# =====================================================

ARQUIVO_CSV = Path(
    r"C:\Users\marqu\OneDrive\Desktop\AUTOMACOES LUIZ"
    r"\CAMAUTOTRANSP\data\CONTATOS GERAL - TRANSPORTADORES.csv"
)

COR_FUNDO = "#C1E5D6"
COR_VERDE = "#2DA271"
COR_VERDE_ESCURO = "#176B4A"

contato_selecionado = None
prefixo_atual = ""


# =====================================================
# NORMALIZAR TELEFONE
# =====================================================

def normalizar_numero(valor):
    if not valor:
        return ""

    valor = str(valor).strip()

    if "wa.me" in valor.lower():
        valor = urlparse(valor).path.strip("/")

    numero = re.sub(r"\D", "", valor)

    if numero.startswith("55") and len(numero) in (12, 13):
        numero = numero[2:]

    return numero

# =====================================================
# CARREGAR CONTATOS
# =====================================================

def carregar_contatos():
    if not ARQUIVO_CSV.exists():
        messagebox.showerror(
            "Arquivo não encontrado",
            f"Não encontrei o CSV:\n\n{ARQUIVO_CSV}"
        )
        return []

    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(
                ARQUIVO_CSV,
                "r",
                encoding=encoding,
                newline=""
            ) as arquivo:

                amostra = arquivo.read(8192)
                arquivo.seek(0)

                try:
                    dialeto = csv.Sniffer().sniff(
                        amostra,
                        delimiters=",;|\t"
                    )
                except csv.Error:
                    dialeto = csv.excel
                    dialeto.delimiter = ";"

                leitor = csv.DictReader(
                    arquivo,
                    dialect=dialeto
                )

                contatos = []

                for linha in leitor:

                    dados = {
                        str(chave).strip().upper(): (
                            str(valor).strip()
                            if valor
                            else ""
                        )
                        for chave, valor in linha.items()
                        if chave
                    }

                    # =================================
                    # DADOS ORIGINAIS
                    # =================================

                    nome = dados.get(
                        "NOME",
                        ""
                    )

                    transportadora = dados.get(
                        "TRANSPORTADORA",
                        ""
                    )

                    telefone = (
                        dados.get("WPP", "")
                        or dados.get("CONTATO", "")
                    )

                    numero = normalizar_numero(
                        telefone
                    )

                    if len(numero) not in (10, 11):
                        continue

                    # =================================
                    # DADOS QUE JÁ ESTÃO NO CSV
                    # =================================

                    codigo = dados.get(
                        "CÓDIGO",
                        ""
                    )

                    ultimo_contato = dados.get(
                        "ULTIMO CONTATO",
                        ""
                    )

                    # =================================
                    # CONTATO
                    # =================================

                    contatos.append({
                        "codigo": codigo,
                        "ddd": numero[:2],
                        "numero": numero,
                        "nome": nome,
                        "transportadora": transportadora,
                        "ultimo_contato": ultimo_contato
                    })

                return contatos

        except UnicodeDecodeError:
            continue

        except Exception as erro:
            messagebox.showerror(
                "Erro ao ler CSV",
                str(erro)
            )
            return []

    messagebox.showerror(
        "Erro",
        "Não foi possível ler o arquivo CSV."
    )

    return []

# =====================================================
# ABRIR WHATSAPP
# =====================================================

def abrir_whatsapp(numero):
    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        messagebox.showwarning(
            "Atenção",
            "Número inválido."
        )
        return

    if not numero.startswith("55"):
        numero = "55" + numero

    url = f"https://web.whatsapp.com/send?phone={numero}"

    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    subprocess.Popen([
        chrome,
        "--profile-directory=Default",
        url
    ])

# =====================================================
# JANELA PRINCIPAL
# =====================================================

def iniciar_janela():
    global contato_selecionado, prefixo_atual

    janela = tk.Tk()
    janela.title("CAM AGROLOG - Busca de Contatos")
    janela.geometry("1120x760")
    janela.minsize(900, 650)
    janela.configure(bg=COR_FUNDO)

    # =================================================
    # TÍTULO
    # =================================================

    tk.Label(
        janela,
        text="CAM AGROLOG | BUSCA DE TRANSPORTADORES",
        font=("Arial", 17, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    ).pack(pady=(15, 5))

    tk.Label(
        janela,
        text="Pesquise por DDD e selecione um contato",
        font=("Arial", 10),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    ).pack(pady=(0, 10))

    # =================================================
    # PESQUISA
    # =================================================

    frame_busca = tk.Frame(
        janela,
        bg=COR_FUNDO
    )
    frame_busca.pack(fill="x", padx=15, pady=8)

    tk.Label(
        frame_busca,
        text="DDDs:",
        font=("Arial", 11, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    ).pack(side="left", padx=5)

    campo_ddd = tk.Entry(
        frame_busca,
        font=("Arial", 12),
        width=25
    )
    campo_ddd.pack(side="left", padx=5)
    campo_ddd.insert(0, "62;")

    # =================================================
    # TABELA
    # =================================================

    frame_tabela = tk.Frame(janela)
    frame_tabela.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=8
    )

    colunas = (
        "CÓDIGO",
        "DDD",
        "CONTATO",
        "NOME",
        "TRANSPORTADORA",
        "ULTIMO CONTATO"
    )

    tabela = ttk.Treeview(
        frame_tabela,
        columns=colunas,
        show="headings",
        selectmode="browse"
    )

    for coluna in colunas:
        tabela.heading(
            coluna,
            text=coluna
        )

    tabela.column(
        "CÓDIGO",
        width=80,
        anchor="center"
    )

    tabela.column(
        "DDD",
        width=60,
        anchor="center"
    )

    tabela.column(
        "CONTATO",
        width=130,
        anchor="center"
    )


    tabela.column(
        "NOME",
        width=220
    )

    tabela.column(
        "TRANSPORTADORA",
        width=300
    )

    tabela.column(
        "ULTIMO CONTATO",
        width=150,
        anchor="center"
    )

    barra = ttk.Scrollbar(
        frame_tabela,
        orient="vertical",
        command=tabela.yview
    )

    tabela.configure(
        yscrollcommand=barra.set
    )

    tabela.pack(
        side="left",
        fill="both",
        expand=True
    )

    barra.pack(
        side="right",
        fill="y"
    )

    label_total = tk.Label(
        janela,
        text="0 contatos encontrados",
        font=("Arial", 11, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    )

    label_total.pack(pady=5)
    # =================================================
    # VISUALIZADOR DO CONTATO
    # =================================================

    frame_visualizador = tk.LabelFrame(
        janela,
        text="CONTATO SELECIONADO",
        font=("Arial", 11, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO,
        padx=12,
        pady=10
    )

    frame_visualizador.pack(
        fill="x",
        padx=15,
        pady=8
    )

    label_visual_nome = tk.Label(
        frame_visualizador,
        text="Selecione um contato na tabela",
        font=("Arial", 11, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    )
    label_visual_nome.pack(pady=3)

    label_visual_numero = tk.Label(
        frame_visualizador,
        text="Nenhum número selecionado",
        font=("Arial", 20, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    )
    label_visual_numero.pack(pady=8)

    # =================================================
    # FUNÇÕES DO VISUALIZADOR
    # =================================================

    def obter_numero_com_prefixo():
        if not contato_selecionado:
            return ""

        numero = contato_selecionado["numero"]
        prefixo = re.sub(r"\D", "", prefixo_atual)

        if numero.startswith("55") and len(numero) in (12, 13):
            numero = numero[2:]

        return prefixo + numero

    def atualizar_visualizador():
        if not contato_selecionado:
            label_visual_nome.config(
                text="Selecione um contato na tabela"
            )
            label_visual_numero.config(
                text="Nenhum número selecionado"
            )
            return

        nome = contato_selecionado.get("nome", "")
        empresa = contato_selecionado.get(
            "transportadora", ""
        )

        label_visual_nome.config(
            text=f"{nome or 'Sem nome'} | {empresa or 'Sem transportadora'}"
        )

        telefone = obter_numero_com_prefixo()

        label_visual_numero.config(
            text="" + telefone
        )

    # =================================================
    # SELECIONAR CONTATO
    # =================================================

    def selecionar_contato(event=None):
        global contato_selecionado

        selecionados = tabela.selection()

        if not selecionados:
            contato_selecionado = None
            atualizar_visualizador()
            return

        valores = tabela.item(
            selecionados[0],
            "values"
        )

        contato_selecionado = {
            "codigo": str(valores[0]),
            "ddd": str(valores[1]),
            "numero": str(valores[2]),
            "nome": str(valores[3]),
            "transportadora": str(valores[4]),
            "ultimo_contato": str(valores[5])
        }

        atualizar_visualizador()


    tabela.bind(
        "<<TreeviewSelect>>",
        selecionar_contato
)
    # =================================================
    # PESQUISAR
    # =================================================

    def pesquisar():
        global contato_selecionado

        entrada = campo_ddd.get().strip()
        ddds = set(re.findall(r"\d{2}", entrada))

        if not ddds:
            messagebox.showwarning(
                "Atenção",
                "Digite DDDs válidos, como 62;64;11."
            )
            return

        contatos = carregar_contatos()

        resultados = [
            c for c in contatos
            if c["ddd"] in ddds
        ]

        unicos = {}

        for contato in resultados:
            unicos.setdefault(
                contato["numero"],
                contato
            )

        resultados = list(unicos.values())

        for item in tabela.get_children():
            tabela.delete(item)

        contato_selecionado = None
        atualizar_visualizador()

        for contato in resultados:

            tabela.insert(
                "",
                "end",
                values=(
                    contato["codigo"],
                    contato["ddd"],
                    contato["numero"],
                    contato["nome"],
                    contato["transportadora"],
                    contato["ultimo_contato"]
                )
            )
                    
        label_total.config(
            text=f"{len(resultados)} contatos encontrados"
        )

        if not resultados:
            messagebox.showinfo(
                "Pesquisa",
                "Nenhum contato encontrado."
            )

    tk.Button(
        frame_busca,
        text="PESQUISAR",
        command=pesquisar,
        bg=COR_VERDE,
        fg="white",
        font=("Arial", 10, "bold"),
        padx=15,
        pady=5
    ).pack(side="left", padx=8)

    # =================================================
    # ALTERAR PREFIXO
    # =================================================

    def alterar_prefixo(abrir_discador=False):
        global prefixo_atual

        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        janela_prefixo = tk.Toplevel(janela)
        janela_prefixo.title("Adicionar prefixo")
        janela_prefixo.geometry("390x240")
        janela_prefixo.configure(bg=COR_FUNDO)
        janela_prefixo.transient(janela)
        janela_prefixo.grab_set()

        tk.Label(
            janela_prefixo,
            text="ADICIONAR / ALTERAR PREFIXO",
            font=("Arial", 12, "bold"),
            bg=COR_FUNDO,
            fg=COR_VERDE_ESCURO
        ).pack(pady=(18, 8))

        tk.Label(
            janela_prefixo,
            text="Exemplo: +55, +1, +351",
            font=("Arial", 10),
            bg=COR_FUNDO
        ).pack()

        campo_prefixo = tk.Entry(
            janela_prefixo,
            font=("Arial", 14),
            justify="center",
            width=15
        )
        campo_prefixo.pack(pady=8)
        campo_prefixo.insert(0, prefixo_atual)

        def aplicar(fazer_ligacao=False):
            global prefixo_atual

            valor = campo_prefixo.get().strip()

            if not valor or not re.search(r"\d", valor):
                messagebox.showwarning(
                    "Prefixo inválido",
                    "Digite um prefixo contendo números."
                )
                return

            prefixo_atual = valor
            atualizar_visualizador()

            telefone = obter_numero_com_prefixo()
            janela_prefixo.destroy()

            if fazer_ligacao:
                telefone = "+" + telefone

                try:
                    if sys.platform == "win32":
                        os.startfile("tel:" + telefone)
                    else:
                        webbrowser.open("tel:" + telefone)

                except Exception:
                    janela.clipboard_clear()
                    janela.clipboard_append(telefone)
                    janela.update()

            
        frame_prefixo_botoes = tk.Frame(
            janela_prefixo,
            bg=COR_FUNDO
        )
        frame_prefixo_botoes.pack(pady=10)

        tk.Button(
            frame_prefixo_botoes,
            text="APLICAR",
            command=lambda: aplicar(False),
            bg=COR_VERDE,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12
        ).pack(side="left", padx=5)

        tk.Button(
            frame_prefixo_botoes,
            text="APLICAR E LIGAR",
            command=lambda: aplicar(True),
            bg=COR_VERDE_ESCURO,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12
        ).pack(side="left", padx=5)

    # =================================================
    # COPIAR NÚMERO
    # =================================================

    def copiar_numero():
        telefone = obter_numero_com_prefixo()

        if not telefone:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        telefone = "+" + telefone

        janela.clipboard_clear()
        janela.clipboard_append(telefone)
        janela.update()

    # =================================================
    # LIGAR
    # =================================================

    def ligar_selecionado():
        alterar_prefixo(abrir_discador=True)

    # =================================================
    # EDITAR CONTATO NO CSV
    # =================================================

    def editar_contato():
        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        contato = contato_selecionado.copy()

        editor = tk.Toplevel(janela)
        editor.title("Editar contato")
        editor.geometry("480x370")
        editor.configure(bg=COR_FUNDO)
        editor.transient(janela)
        editor.grab_set()

        tk.Label(
            editor,
            text="EDITAR CONTATO",
            font=("Arial", 15, "bold"),
            bg=COR_FUNDO,
            fg=COR_VERDE_ESCURO
        ).pack(pady=15)

        campos = {}

        for rotulo, valor in [
            ("Nome", contato["nome"]),
            ("Transportadora", contato["transportadora"]),
            ("Telefone", contato["numero"])
        ]:
            tk.Label(
                editor,
                text=rotulo,
                font=("Arial", 10, "bold"),
                bg=COR_FUNDO,
                fg=COR_VERDE_ESCURO
            ).pack(anchor="w", padx=30)

            campo = tk.Entry(
                editor,
                font=("Arial", 11),
                width=45
            )
            campo.pack(padx=30, pady=(3, 10))
            campo.insert(0, valor)

            campos[rotulo] = campo

  
        def salvar_edicao():
            novo_nome = campos["Nome"].get().strip()
            nova_transportadora = (
                campos["Transportadora"].get().strip()
            )
            novo_numero = normalizar_numero(
                campos["Telefone"].get()
            )

            if len(novo_numero) not in (10, 11):
                messagebox.showwarning(
                    "Telefone inválido",
                    "Informe um telefone com DDD e 10 ou 11 dígitos."
                )
                return

            if not messagebox.askyesno(
                "Confirmar",
                "Salvar as alterações diretamente no CSV?"
            ):
                return

            try:
                linhas = []
                cabecalhos = None
                dialeto = None
                encoding_usado = None

                for encoding in (
                    "utf-8-sig",
                    "utf-8",
                    "latin-1"
                ):
                    try:
                        with open(
                            ARQUIVO_CSV,
                            "r",
                            encoding=encoding,
                            newline=""
                        ) as arquivo:
                            amostra = arquivo.read(8192)
                            arquivo.seek(0)

                            try:
                                dialeto = csv.Sniffer().sniff(
                                    amostra,
                                    delimiters=",;|\t"
                                )
                            except csv.Error:
                                dialeto = csv.excel
                                dialeto.delimiter = ";"

                            leitor = csv.DictReader(
                                arquivo,
                                dialect=dialeto
                            )

                            cabecalhos = leitor.fieldnames
                            linhas = list(leitor)

                        encoding_usado = encoding
                        break

                    except UnicodeDecodeError:
                        continue

                if not cabecalhos or not encoding_usado:
                    raise ValueError(
                        "Não foi possível ler o CSV."
                    )

                telefone_antigo = contato["numero"]
                encontrada = False

                for linha in linhas:
                    dados = {
                        str(chave).strip().upper(): (
                            str(valor).strip() if valor else ""
                        )
                        for chave, valor in linha.items()
                        if chave
                    }

                    telefone_csv = (
                        dados.get("WPP", "")
                        or dados.get("CONTATO", "")
                    )

                    if (
                        normalizar_numero(telefone_csv)
                        == telefone_antigo
                        and dados.get("NOME", "")
                        == contato["nome"]
                        and dados.get("TRANSPORTADORA", "")
                        == contato["transportadora"]
                    ):
                        for coluna in cabecalhos:
                            nome_coluna = coluna.strip().upper()

                            if nome_coluna == "NOME":
                                linha[coluna] = novo_nome

                            elif nome_coluna == "TRANSPORTADORA":
                                linha[coluna] = nova_transportadora

                            elif nome_coluna == "WPP":
                                linha[coluna] = novo_numero

                            elif (
                                nome_coluna == "CONTATO"
                                and not linha.get("WPP")
                            ):
                                linha[coluna] = novo_numero

                        encontrada = True
                        break

                if not encontrada:
                    messagebox.showerror(
                        "Contato não encontrado",
                        "Não foi possível localizar a linha original "
                        "do contato no CSV."
                    )
                    return

                # Cria uma cópia de segurança antes de sobrescrever.
                backup = ARQUIVO_CSV.with_suffix(
                    ARQUIVO_CSV.suffix + ".bak"
                )

                import shutil
                shutil.copy2(ARQUIVO_CSV, backup)

                with open(
                    ARQUIVO_CSV,
                    "w",
                    encoding=encoding_usado,
                    newline=""
                ) as arquivo:
                    escritor = csv.DictWriter(
                        arquivo,
                        fieldnames=cabecalhos,
                        dialect=dialeto
                    )
                    escritor.writeheader()
                    escritor.writerows(linhas)

                contato_selecionado.update({
                    "nome": novo_nome,
                    "transportadora": nova_transportadora,
                    "numero": novo_numero,
                    "ddd": novo_numero[:2]
                })

                atualizar_visualizador()

                selecionados = tabela.selection()

                if selecionados:
                    tabela.item(
                        selecionados[0],
                        values=(
                            novo_numero[:2],
                            novo_numero,
                            novo_nome,
                            nova_transportadora
                        )
                    )

                messagebox.showinfo(
                    "Sucesso",
                    "Contato atualizado no CSV.\n\n"
                    f"Cópia de segurança criada em:\n{backup}"
                )

                editor.destroy()

            except Exception as erro:
                messagebox.showerror(
                    "Erro ao salvar",
                    f"Não foi possível atualizar o CSV:\n\n{erro}"
                )

        tk.Button(
            editor,
            text="SALVAR ALTERAÇÕES NO CSV",
            command=salvar_edicao,
            bg=COR_VERDE_ESCURO,
            fg="white",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=9
        ).pack(pady=12)

    # =================================================
    # ATUALIZAR CONTATO NO CSV
    # =================================================

    def atualizar_contato_csv(contato):

        try:
            linhas = []
            cabecalhos = None
            dialeto = None
            encoding_usado = None

            # -----------------------------------------
            # LER CSV
            # -----------------------------------------

            for encoding in ("utf-8-sig", "utf-8", "latin-1"):

                try:

                    with open(
                        ARQUIVO_CSV,
                        "r",
                        encoding=encoding,
                        newline=""
                    ) as arquivo:

                        amostra = arquivo.read(8192)
                        arquivo.seek(0)

                        try:
                            dialeto = csv.Sniffer().sniff(
                                amostra,
                                delimiters=",;|\t"
                            )

                        except csv.Error:
                            dialeto = csv.excel
                            dialeto.delimiter = ";"

                        leitor = csv.DictReader(
                            arquivo,
                            dialect=dialeto
                        )

                        cabecalhos = leitor.fieldnames
                        linhas = list(leitor)

                    encoding_usado = encoding
                    break

                except UnicodeDecodeError:
                    continue

            if not cabecalhos:
                raise ValueError(
                    "Não foi possível identificar as colunas do CSV."
                )

            # -----------------------------------------
            # TELEFONE DO CONTATO
            # -----------------------------------------

            telefone_procurado = normalizar_numero(
                contato.get("numero", "")
            )

            if not telefone_procurado:
                raise ValueError(
                    "O contato não possui telefone válido."
                )

            data_hora = contato.get(
                "ultimo_contato",
                ""
            )

            encontrada = False

            # -----------------------------------------
            # PROCURAR O CONTATO
            # -----------------------------------------

            for linha in linhas:

                telefone_csv = (
                    linha.get("WPP", "")
                    or linha.get("CONTATO", "")
                )

                telefone_csv = normalizar_numero(
                    telefone_csv
                )

                if telefone_csv != telefone_procurado:
                    continue

                # -------------------------------------
                # ATUALIZAR CÓDIGO
                # -------------------------------------

                for coluna in cabecalhos:

                    nome_coluna = (
                        str(coluna).strip().upper()
                    )

                    if nome_coluna == "CÓDIGO":

                        linha[coluna] = "DISPONÍVEL"

                    elif nome_coluna == "ULTIMO CONTATO":

                        linha[coluna] = data_hora

                encontrada = True
                break

            if not encontrada:
                raise ValueError(
                    "Contato não encontrado no CSV."
                )

            # -----------------------------------------
            # SALVAR
            # -----------------------------------------

            with open(
                ARQUIVO_CSV,
                "w",
                encoding=encoding_usado,
                newline=""
            ) as arquivo:

                escritor = csv.DictWriter(
                    arquivo,
                    fieldnames=cabecalhos,
                    dialect=dialeto
                )

                escritor.writeheader()
                escritor.writerows(linhas)

            return True

        except Exception as erro:

            messagebox.showerror(
                "Erro ao atualizar CSV",
                f"Não foi possível atualizar o contato:\n\n{erro}"
            )

            return False
        
    # =================================================
    # REGISTRAR CONTATO BEM-SUCEDIDO
    # =================================================

    def registrar_disponibilidade():

        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        agora = datetime.now()
        data_hora = agora.strftime("%d/%m/%Y %H:%M")

        # -----------------------------------------
        # ATUALIZA O CONTATO SELECIONADO
        # -----------------------------------------

        contato = contato_selecionado.copy()

        contato["ultimo_contato"] = data_hora
        contato["codigo"] = "DISPONÍVEL"

        # -----------------------------------------
        # ATUALIZA O CSV
        # -----------------------------------------

        sucesso = atualizar_contato_csv(contato)

        if sucesso == False:
            return

        # -----------------------------------------
        # ATUALIZA O CONTATO EM MEMÓRIA
        # -----------------------------------------

        contato_selecionado.update({
            "codigo": "DISPONÍVEL",
            "ultimo_contato": data_hora
        })

        # -----------------------------------------
        # ATUALIZA A LINHA DA TABELA NA HORA
        # -----------------------------------------

        selecionados = tabela.selection()

        if selecionados:

            tabela.item(
                selecionados[0],
                values=(
                    contato_selecionado.get(
                        "codigo",
                        ""
                    ),
                    contato_selecionado.get(
                        "ddd",
                        ""
                    ),
                    contato_selecionado.get(
                        "numero",
                        ""
                    ),
                    contato_selecionado.get(
                        "nome",
                        ""
                    ),
                    contato_selecionado.get(
                        "transportadora",
                        ""
                    ),
                    contato_selecionado.get(
                        "ultimo_contato",
                        ""
                    )
                )
            )

        # -----------------------------------------
        # ATUALIZA O VISUALIZADOR
        # -----------------------------------------

        atualizar_visualizador()

        # -----------------------------------------
        # CONFIRMA
        # -----------------------------------------

        messagebox.showinfo(
            "Contato registrado",
            f"Contato registrado com sucesso.\n\n"
            f"Último contato: {data_hora}"
        ) 

        
    # =================================================
    # BOTÕES DE AÇÃO
    # =================================================

    frame_botoes = tk.Frame(
        janela,
        bg=COR_FUNDO
    )
    frame_botoes.pack(pady=12)

    tk.Button(
        frame_botoes,
        text="LIGAR",
        command=ligar_selecionado,
        bg=COR_VERDE_ESCURO,
        fg="white",
        font=("Arial", 11, "bold"),
        padx=25,
        pady=10
    ).pack(side="left", padx=8)

    tk.Button(
        frame_botoes,
        text="COPIAR NÚMERO",
        command=copiar_numero,
        bg=COR_VERDE,
        fg="white",
        font=("Arial", 11, "bold"),
        padx=25,
        pady=10
    ).pack(side="left", padx=8)

    tk.Button(
        frame_botoes,
        text="EDITAR CONTATO",
        command=editar_contato,
        bg="#128C7E",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=25,
        pady=10
    ).pack(side="left", padx=8)

    tk.Button(
        frame_botoes,
        text="DISPONÍVEL",
        command=registrar_disponibilidade,
        bg=COR_VERDE_ESCURO,
        fg="white",
        font=("Arial", 10, "bold"),
        padx=15,
        pady=8
    ).pack(
        side="left",
        padx=5
    )
    tk.Button(
        frame_botoes,
        text="ABRIR WHATSAPP",
        command=lambda: (
            abrir_whatsapp(contato_selecionado["numero"])
            if contato_selecionado
            else messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
        ),
        bg="#075E54",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=25,
        pady=10
    ).pack(side="left", padx=8)

    campo_ddd.bind(
        "<Return>",
        lambda evento: pesquisar()
    )

    janela.mainloop()


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    iniciar_janela()