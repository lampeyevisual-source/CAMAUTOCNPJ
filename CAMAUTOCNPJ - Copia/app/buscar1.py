
import csv
import os
import re
import shutil
import subprocess
import sys
import webbrowser
import tkinter as tk

from tkinter import ttk, messagebox
from pathlib import Path
from urllib.parse import urlparse


# =====================================================
# CONFIGURAÇÃO
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_CSV = (
    BASE_DIR / "data" / "empresas_cnaes4623199_trades.csv"
)

COR_FUNDO = "#C1E5D6"
COR_VERDE = "#2DA271"
COR_VERDE_ESCURO = "#176B4A"

contato_selecionado = None
prefixo_atual = ""


# =====================================================
# LEITURA DO CSV
# =====================================================

def detectar_dialeto(amostra):
    try:
        return csv.Sniffer().sniff(
            amostra,
            delimiters=";,\t|"
        )
    except csv.Error:

        class DialetoPontoEVirgula(csv.excel):
            delimiter = ";"

        return DialetoPontoEVirgula


def ler_csv():

    if not ARQUIVO_CSV.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado:\n{ARQUIVO_CSV}"
        )

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1"
    ):
        try:
            with open(
                ARQUIVO_CSV,
                "r",
                encoding=encoding,
                newline=""
            ) as arquivo:

                amostra = arquivo.read(16384)
                arquivo.seek(0)

                dialeto = detectar_dialeto(amostra)

                leitor = csv.DictReader(
                    arquivo,
                    dialect=dialeto
                )

                if not leitor.fieldnames:
                    raise ValueError(
                        "O CSV não possui cabeçalhos."
                    )

                cabecalhos = leitor.fieldnames
                linhas = list(leitor)

            return cabecalhos, linhas, dialeto, encoding

        except UnicodeDecodeError:
            continue

    raise ValueError(
        "Não foi possível identificar a codificação do CSV."
    )


# =====================================================
# LOCALIZAR E LER COLUNAS
# =====================================================

def chave_coluna(linha, nome):

    procurada = nome.strip().casefold()

    for chave in linha.keys():
        if (
            chave is not None
            and str(chave).strip().casefold() == procurada
        ):
            return chave

    return None


def valor_coluna(linha, nome, padrao=""):

    chave = chave_coluna(linha, nome)

    if chave is None:
        return padrao

    valor = linha.get(chave, padrao)

    return str(valor).strip() if valor is not None else ""


def definir_coluna(linhas, cabecalhos, linha, nome, valor):

    chave = next(
        (
            coluna
            for coluna in cabecalhos
            if str(coluna).strip().casefold()
            == nome.strip().casefold()
        ),
        None
    )

    if chave is None:
        raise ValueError(
            f"A coluna '{nome}' não existe no CSV."
        )

    linha[chave] = valor


# =====================================================
# NORMALIZAR TELEFONES
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


def montar_numero(ddd, telefone):

    ddd = re.sub(r"\D", "", str(ddd or ""))
    telefone = re.sub(r"\D", "", str(telefone or ""))

    if telefone.startswith("55") and len(telefone) in (12, 13):
        telefone = telefone[2:]

    # Telefone já contém DDD.
    if len(telefone) in (10, 11):
        return telefone

    # Telefone contém somente o número local.
    if len(ddd) == 2 and len(telefone) in (8, 9):
        return ddd + telefone

    return ""


# =====================================================
# NOME DA EMPRESA
# =====================================================

def nome_empresa(linha):

    return (
        valor_coluna(linha, "nome_fantasia")
        or valor_coluna(linha, "razao_social")
        or "(Empresa sem nome)"
    )


# =====================================================
# VERIFICAR DISPONIBILIDADE
# =====================================================

def contato_disponivel(linha, indice):

    status = valor_coluna(
        linha,
        f"STATUS CONTATO {indice}"
    )

    return status.strip().casefold() == "disponível"


# =====================================================
# EXTRAIR CONTATOS DO CSV
# =====================================================

def contatos_da_linha(linha):

    contatos = []

    cnpj = valor_coluna(linha, "cnpj")

    for indice in (1, 2):

        # Somente contatos marcados como DISPONÍVEL.
        if not contato_disponivel(linha, indice):
            continue

        ddd = valor_coluna(
            linha,
            f"ddd_{indice}"
        )

        telefone = valor_coluna(
            linha,
            f"telefone_{indice}"
        )

        numero = montar_numero(
            ddd,
            telefone
        )

        # Se não houver telefone válido nas colunas próprias,
        # tenta extrair o número de CONTATO 1 ou CONTATO 2.
        if not numero:
            numero_alternativo = normalizar_numero(
                valor_coluna(
                    linha,
                    f"CONTATO {indice}"
                )
            )

            if len(numero_alternativo) in (10, 11):
                numero = numero_alternativo

        # Ignora telefones inválidos.
        if len(numero) not in (10, 11):
            continue

        contatos.append({
            "cnpj": cnpj,
            "ddd": numero[:2],
            "numero": numero,
            "nome": valor_coluna(
                linha,
                f"CONTATO {indice}"
            ),
            "empresa": nome_empresa(linha),
            "status": valor_coluna(
                linha,
                f"STATUS CONTATO {indice}"
            ),
            "indice_contato": indice,
            "razao_social": valor_coluna(
                linha,
                "razao_social"
            ),
            "nome_fantasia": valor_coluna(
                linha,
                "nome_fantasia"
            ),
            "email": valor_coluna(
                linha,
                "email"
            )
        })

    return contatos


# =====================================================
# SALVAR CSV COM BACKUP
# =====================================================

def salvar_csv(cabecalhos, linhas, dialeto, encoding):

    backup = ARQUIVO_CSV.with_suffix(
        ARQUIVO_CSV.suffix + ".bak"
    )

    temporario = ARQUIVO_CSV.with_suffix(
        ARQUIVO_CSV.suffix + ".tmp"
    )

    # Cria uma cópia de segurança antes de substituir o original.
    shutil.copy2(
        ARQUIVO_CSV,
        backup
    )

    try:
        with open(
            temporario,
            "w",
            encoding=encoding,
            newline=""
        ) as arquivo:

            escritor = csv.DictWriter(
                arquivo,
                fieldnames=cabecalhos,
                dialect=dialeto,
                extrasaction="ignore"
            )

            escritor.writeheader()
            escritor.writerows(linhas)

        os.replace(
            temporario,
            ARQUIVO_CSV
        )

    finally:
        if temporario.exists():
            temporario.unlink()

    return backup


# =====================================================
# ATUALIZAR CONTATO NO CSV
# =====================================================

def atualizar_registro_contato(
    contato,
    novos_valores=None
):

    cabecalhos, linhas, dialeto, encoding = ler_csv()

    cnpj_procurado = re.sub(
        r"\D",
        "",
        contato.get("cnpj", "")
    )

    indice = int(
        contato.get("indice_contato", 1)
    )

    telefone_procurado = normalizar_numero(
        contato.get("numero", "")
    )

    encontrada = None

    # Localiza a empresa pelo CNPJ e confirma pelo telefone.
    for linha in linhas:

        cnpj_linha = re.sub(
            r"\D",
            "",
            valor_coluna(linha, "cnpj")
        )

        if not cnpj_procurado or cnpj_linha != cnpj_procurado:
            continue

        numero_linha = montar_numero(
            valor_coluna(linha, f"ddd_{indice}"),
            valor_coluna(linha, f"telefone_{indice}")
        )

        if not numero_linha:
            numero_linha = normalizar_numero(
                valor_coluna(linha, f"CONTATO {indice}")
            )

        if numero_linha == telefone_procurado:
            encontrada = linha
            break

    if encontrada is None:
        raise ValueError(
            "Não foi possível localizar o cadastro original "
            "pelo CNPJ e telefone selecionado."
        )

    # Atualiza somente as colunas existentes solicitadas.
    if novos_valores:
        for nome_coluna, valor in novos_valores.items():
            definir_coluna(
                linhas,
                cabecalhos,
                encontrada,
                nome_coluna,
                valor
            )

    return salvar_csv(
        cabecalhos,
        linhas,
        dialeto,
        encoding
    )


# =====================================================
# ABRIR WHATSAPP
# =====================================================

def abrir_whatsapp(numero):

    numero = normalizar_numero(numero)

    if len(numero) not in (10, 11):
        messagebox.showwarning(
            "Atenção",
            "Número inválido."
        )
        return

    numero_internacional = "55" + numero

    url = (
        "https://web.whatsapp.com/send?phone="
        + numero_internacional
    )

    chrome = Path(
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    )

    try:
        if chrome.exists():
            subprocess.Popen([
                str(chrome),
                "--profile-directory=Default",
                url
            ])
        else:
            webbrowser.open(url)

    except Exception as erro:
        messagebox.showerror(
            "Erro ao abrir WhatsApp",
            str(erro)
        )


# =====================================================
# JANELA PRINCIPAL
# =====================================================

def iniciar_janela():

    global contato_selecionado, prefixo_atual

    janela = tk.Tk()

    janela.title(
        "CAM AGROLOG - Busca de Transportadores Disponíveis"
    )

    janela.geometry("1250x780")
    janela.minsize(1000, 650)
    janela.configure(bg=COR_FUNDO)

    # -------------------------------------------------
    # TÍTULO
    # -------------------------------------------------

    tk.Label(
        janela,
        text="CAM AGROLOG | TRANSPORTADORES DISPONÍVEIS",
        font=("Arial", 17, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    ).pack(pady=(15, 5))

    tk.Label(
        janela,
        text="Pesquise por DDD. Somente contatos DISPONÍVEIS serão exibidos.",
        font=("Arial", 10),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    ).pack(pady=(0, 10))

    # -------------------------------------------------
    # PESQUISA
    # -------------------------------------------------

    frame_busca = tk.Frame(
        janela,
        bg=COR_FUNDO
    )

    frame_busca.pack(
        fill="x",
        padx=15,
        pady=8
    )

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

    # -------------------------------------------------
    # TABELA
    # Cada linha representa UM contato.
    # -------------------------------------------------

    colunas = (
        "CNPJ",
        "DDD",
        "TELEFONE",
        "NOME",
        "EMPRESA",
        "STATUS",
        "TIPO"
    )

    frame_tabela = tk.Frame(janela)

    frame_tabela.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=8
    )

    tabela = ttk.Treeview(
        frame_tabela,
        columns=colunas,
        show="headings",
        selectmode="browse"
    )

    larguras = {
        "CNPJ": 145,
        "DDD": 60,
        "TELEFONE": 125,
        "NOME": 180,
        "EMPRESA": 340,
        "STATUS": 125,
        "TIPO": 95
    }

    for coluna in colunas:

        tabela.heading(
            coluna,
            text=coluna
        )

        tabela.column(
            coluna,
            width=larguras[coluna],
            anchor=(
                "center"
                if coluna in (
                    "CNPJ",
                    "DDD",
                    "TELEFONE",
                    "STATUS",
                    "TIPO"
                )
                else "w"
            )
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

    # -------------------------------------------------
    # TOTAL DE CONTATOS
    # -------------------------------------------------

    label_total = tk.Label(
        janela,
        text="0 contatos disponíveis encontrados",
        font=("Arial", 11, "bold"),
        bg=COR_FUNDO,
        fg=COR_VERDE_ESCURO
    )

    label_total.pack(pady=5)

    # -------------------------------------------------
    # VISUALIZADOR
    # -------------------------------------------------

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

    contatos_exibidos = {}

    # -------------------------------------------------
    # OBTER TELEFONE COM PREFIXO
    # -------------------------------------------------

    def obter_numero_com_prefixo():

        if not contato_selecionado:
            return ""

        numero = normalizar_numero(
            contato_selecionado.get("numero", "")
        )

        prefixo = re.sub(
            r"\D",
            "",
            prefixo_atual
        )

        return prefixo + numero
    
    # -------------------------------------------------
    # ATUALIZAR VISUALIZADOR
    # -------------------------------------------------

    def atualizar_visualizador():

        if not contato_selecionado:
            label_visual_nome.config(
                text="Selecione um contato na tabela"
            )

            label_visual_numero.config(
                text="Nenhum número selecionado"
            )

            return

        nome = (
            contato_selecionado.get("nome")
            or "Contato sem nome"
        )

        empresa = (
            contato_selecionado.get("empresa")
            or "Empresa sem nome"
        )

        status = (
            contato_selecionado.get("status")
            or "Sem status"
        )

        indice = contato_selecionado["indice_contato"]

        label_visual_nome.config(
            text=(
                f"{empresa} | {nome} | "
                f"Contato {indice} | {status}"
            )
        )

        label_visual_numero.config(
            text="+" + obter_numero_com_prefixo()
        )

    # -------------------------------------------------
    # SELECIONAR CONTATO
    # -------------------------------------------------

    def selecionar_contato(event=None):

        global contato_selecionado

        selecionados = tabela.selection()

        if not selecionados:
            contato_selecionado = None
            atualizar_visualizador()
            return

        contato_selecionado = contatos_exibidos.get(
            selecionados[0]
        )

        atualizar_visualizador()

    tabela.bind(
        "<<TreeviewSelect>>",
        selecionar_contato
    )

    # -------------------------------------------------
    # PESQUISAR DDD
    # -------------------------------------------------

    def pesquisar():

        global contato_selecionado

        entrada = campo_ddd.get().strip()

        # Permite digitar, por exemplo: 62;64;11.
        ddds = set(
            re.findall(r"\d{2}", entrada)
        )

        if not ddds:
            messagebox.showwarning(
                "Atenção",
                "Digite DDDs válidos, como 62;64;11."
            )
            return

        try:
            _, linhas, _, _ = ler_csv()

        except Exception as erro:
            messagebox.showerror(
                "Erro ao ler CSV",
                str(erro)
            )
            return

        resultados = []

        # A extração já elimina contatos que não estão disponíveis.
        for linha in linhas:
            resultados.extend(
                contatos_da_linha(linha)
            )

        # Filtra pelos DDDs digitados.
        resultados = [
            contato
            for contato in resultados
            if contato["ddd"] in ddds
        ]

        # Evita duplicações do mesmo contato.
        unicos = {}

        for contato in resultados:

            chave = (
                contato["cnpj"],
                contato["numero"],
                contato["indice_contato"]
            )

            unicos.setdefault(
                chave,
                contato
            )

        resultados = list(unicos.values())

        # Limpa os resultados anteriores.
        for item_id in tabela.get_children():
            tabela.delete(item_id)

        contatos_exibidos.clear()

        contato_selecionado = None
        atualizar_visualizador()

        # Preenche a tabela: um contato por linha.
        for contato in resultados:

            item_id = tabela.insert(
                "",
                "end",
                values=(
                    contato["cnpj"],
                    contato["ddd"],
                    contato["numero"],
                    contato["nome"] or "—",
                    contato["empresa"],
                    "DISPONÍVEL",
                    f"CONTATO {contato['indice_contato']}"
                )
            )

            contatos_exibidos[item_id] = contato

        label_total.config(
            text=(
                f"{len(resultados)} contatos disponíveis encontrados"
            )
        )

        if not resultados:
            messagebox.showinfo(
                "Pesquisa",
                "Nenhum contato DISPONÍVEL foi encontrado "
                "para os DDDs informados."
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

    # -------------------------------------------------
    # COPIAR NÚMERO
    # -------------------------------------------------

    def copiar_numero():

        telefone = obter_numero_com_prefixo()

        if not telefone:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        janela.clipboard_clear()
        janela.clipboard_append("+" + telefone)
        janela.update()

        messagebox.showinfo(
            "Copiado",
            "Número copiado para a área de transferência."
        )

    # -------------------------------------------------
    # LIGAR
    # -------------------------------------------------

    def ligar_selecionado():

        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        telefone = "+" + obter_numero_com_prefixo()

        try:
            if sys.platform == "win32":
                os.startfile("tel:" + telefone)
            else:
                webbrowser.open("tel:" + telefone)

        except Exception:
            janela.clipboard_clear()
            janela.clipboard_append(telefone)
            janela.update()

            messagebox.showinfo(
                "Número copiado",
                "Não foi possível abrir o discador. "
                "O número foi copiado."
            )

    # -------------------------------------------------
    # ABRIR WHATSAPP
    # -------------------------------------------------

    def abrir_whatsapp_selecionado():

        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        abrir_whatsapp(
            contato_selecionado["numero"]
        )

    # -------------------------------------------------
    # EDITAR CONTATO
    # -------------------------------------------------

    def editar_contato():

        if not contato_selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione um contato primeiro."
            )
            return

        contato = contato_selecionado.copy()
        indice = contato["indice_contato"]

        editor = tk.Toplevel(janela)

        editor.title(
            f"Editar empresa - Contato {indice}"
        )

        editor.geometry("520x470")
        editor.configure(bg=COR_FUNDO)
        editor.transient(janela)
        editor.grab_set()

        tk.Label(
            editor,
            text="EDITAR CADASTRO",
            font=("Arial", 15, "bold"),
            bg=COR_FUNDO,
            fg=COR_VERDE_ESCURO
        ).pack(pady=12)

        campos = {}

        dados_edicao = [
            ("Nome fantasia", contato.get("nome_fantasia", "")),
            ("Razão social", contato.get("razao_social", "")),
            ("Nome do contato", contato.get("nome", "")),
            ("DDD", contato.get("ddd", "")),
            ("Telefone", contato.get("numero", "")),
            ("E-mail", contato.get("email", ""))
        ]

        for rotulo, valor in dados_edicao:

            tk.Label(
                editor,
                text=rotulo,
                font=("Arial", 10, "bold"),
                bg=COR_FUNDO,
                fg=COR_VERDE_ESCURO
            ).pack(
                anchor="w",
                padx=28
            )

            campo = tk.Entry(
                editor,
                font=("Arial", 11),
                width=52
            )

            campo.pack(
                padx=28,
                pady=(2, 7)
            )

            campo.insert(0, valor)
            campos[rotulo] = campo

        def salvar_edicao():

            novo_ddd = re.sub(
                r"\D",
                "",
                campos["DDD"].get()
            )

            novo_telefone = normalizar_numero(
                campos["Telefone"].get()
            )

            # Se o campo já contém o DDD completo,
            # separa DDD e número local.
            if len(novo_telefone) in (10, 11):

                novo_ddd = novo_telefone[:2]
                numero_local = novo_telefone[2:]

            elif (
                len(novo_ddd) == 2
                and len(novo_telefone) in (8, 9)
            ):

                numero_local = novo_telefone
                novo_telefone = novo_ddd + numero_local

            else:
                messagebox.showwarning(
                    "Telefone inválido",
                    "Informe um DDD com 2 dígitos e um telefone válido.",
                    parent=editor
                )
                return

            if not messagebox.askyesno(
                "Confirmar",
                "Salvar as alterações diretamente no CSV?",
                parent=editor
            ):
                return

            try:

                valores = {
                    "nome_fantasia":
                        campos["Nome fantasia"].get().strip(),

                    "razao_social":
                        campos["Razão social"].get().strip(),

                    f"CONTATO {indice}":
                        campos["Nome do contato"].get().strip(),

                    f"ddd_{indice}":
                        novo_ddd,

                    f"telefone_{indice}":
                        numero_local,

                    "email":
                        campos["E-mail"].get().strip()
                }

                backup = atualizar_registro_contato(
                    contato,
                    novos_valores=valores
                )

                contato_selecionado.update({
                    "nome": valores[f"CONTATO {indice}"],
                    "ddd": novo_ddd,
                    "numero": novo_telefone,
                    "empresa": (
                        valores["nome_fantasia"]
                        or valores["razao_social"]
                    ),
                    "nome_fantasia": valores["nome_fantasia"],
                    "razao_social": valores["razao_social"],
                    "email": valores["email"]
                })

                # Atualiza a linha selecionada.
                selecionados = tabela.selection()

                if selecionados:

                    item_id = selecionados[0]

                    tabela.item(
                        item_id,
                        values=(
                            contato_selecionado["cnpj"],
                            contato_selecionado["ddd"],
                            contato_selecionado["numero"],
                            contato_selecionado["nome"] or "—",
                            contato_selecionado["empresa"],
                            contato_selecionado["status"],
                            f"CONTATO {indice}"
                        )
                    )

                    contatos_exibidos[item_id] = (
                        contato_selecionado
                    )

                atualizar_visualizador()
                editor.destroy()

                messagebox.showinfo(
                    "Sucesso",
                    "Cadastro atualizado no CSV.\n\n"
                    f"Backup criado em:\n{backup}"
                )

            except Exception as erro:
                messagebox.showerror(
                    "Erro ao salvar",
                    str(erro),
                    parent=editor
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

    # -------------------------------------------------
    # BOTÕES
    # -------------------------------------------------

    frame_botoes = tk.Frame(
        janela,
        bg=COR_FUNDO
    )

    frame_botoes.pack(pady=12)

    botoes = [
        ("LIGAR", ligar_selecionado, COR_VERDE_ESCURO),
        ("COPIAR NÚMERO", copiar_numero, COR_VERDE),
        ("EDITAR CADASTRO", editar_contato, "#128C7E"),
        ("ABRIR WHATSAPP", abrir_whatsapp_selecionado, "#075E54")
    ]

    for texto, comando, cor in botoes:

        tk.Button(
            frame_botoes,
            text=texto,
            command=comando,
            bg=cor,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=14,
            pady=9
        ).pack(
            side="left",
            padx=5
        )

    # Pressionar Enter no campo de DDD também pesquisa.
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
