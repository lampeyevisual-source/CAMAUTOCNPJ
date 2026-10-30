import csv
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from tkinter import messagebox
from playwright.sync_api import sync_playwright

from pathlib import Path

# =====================================================
# CONFIGURAÇÕES
# =====================================================

ARQUIVO_CSV = Path(
    r"C:\Users\marqu\OneDrive\Desktop\AUTOMACOES LUIZ\CAMAUTOCNPJ - Copia\data\empresas_cnaes_1091101_1091102_4721102_5611201_5611203_estados_GO.csv"
)

# =====================================================
# CHROME
# =====================================================

CHROME = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

# =====================================================
# PERFIL EXCLUSIVO DESTA AUTOMAÇÃO
# =====================================================

PERFIL_CHROME = (
    Path.home()
    / "AppData"
    / "Local"
    / "CAMAUTOCNPJ"
    / "Chrome"
)

PERFIL_CHROME.mkdir(
    parents=True,
    exist_ok=True
)

# =====================================================
# STATUS
# =====================================================

STATUS_DISPONIVEL = "DISPONÍVEL"
STATUS_INDISPONIVEL = "INDISPONÍVEL"


# =====================================================
# UTILITÁRIOS DE CABEÇALHO E TELEFONE
# =====================================================

def normalizar_cabecalho(valor):
    """Aceita cabeçalhos com espaços e asteriscos extras."""
    return str(valor or "").strip().strip("*").strip().upper()


def encontrar_coluna(cabecalhos, nome):
    nome = normalizar_cabecalho(nome)

    for coluna in cabecalhos or []:
        if normalizar_cabecalho(coluna) == nome:
            return coluna

    return None


def normalizar_numero(valor):
    if not valor:
        return ""

    valor = str(valor).strip()

    # Aceita links wa.me
    if "wa.me" in valor.lower():
        valor = urlparse(valor).path.strip("/")

    # Mantém somente números
    numero = re.sub(r"\D", "", valor)

    # Remove o código do Brasil quando presente
    if numero.startswith("55") and len(numero) in (12, 13):
        numero = numero[2:]

    # O telefone deve conter DDD + número
    if len(numero) not in (10, 11):
        return ""

    return numero


# =====================================================
# LER CSV
# =====================================================

def ler_csv():

    if not ARQUIVO_CSV.exists():
        raise FileNotFoundError(
            f"CSV não encontrado:\n{ARQUIVO_CSV}"
        )

    ultimo_erro = None

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

            if not cabecalhos:
                raise ValueError(
                    "O CSV não possui cabeçalho."
                )

            return (
                cabecalhos,
                linhas,
                dialeto,
                encoding
            )

        except UnicodeDecodeError as erro:
            ultimo_erro = erro

    raise ValueError(
        f"Não foi possível identificar a codificação do CSV: "
        f"{ultimo_erro}"
    )

# =====================================================
# SALVAR CSV SEM BACKUP
# =====================================================

def salvar_csv(cabecalhos, linhas, dialeto, encoding):

    with open(
        ARQUIVO_CSV,
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

    print("[CSV] Arquivo atualizado.")
# =====================================================
# CARREGAR CONTATOS PENDENTES
# =====================================================

def carregar_contatos():

    try:
        cabecalhos, linhas, _, _ = ler_csv()

    except Exception as erro:
        messagebox.showerror(
            "Erro ao ler CSV",
            str(erro)
        )
        return []

    cnpj_col = encontrar_coluna(
        cabecalhos,
        "cnpj"
    )

    contato1_col = encontrar_coluna(
        cabecalhos,
        "CONTATO 1"
    )

    status1_col = encontrar_coluna(
        cabecalhos,
        "STATUS CONTATO 1"
    )

    contato2_col = encontrar_coluna(
        cabecalhos,
        "CONTATO 2"
    )

    status2_col = encontrar_coluna(
        cabecalhos,
        "STATUS CONTATO 2"
    )

    nome_col = (
        encontrar_coluna(cabecalhos, "nome_fantasia")
        or encontrar_coluna(cabecalhos, "razao_social")
    )

    faltando = []

    for nome, coluna in (
        ("cnpj", cnpj_col),
        ("CONTATO 1", contato1_col),
        ("STATUS CONTATO 1", status1_col),
        ("CONTATO 2", contato2_col),
        ("STATUS CONTATO 2", status2_col),
    ):

        if not coluna:
            faltando.append(nome)

    if faltando:
        messagebox.showerror(
            "Colunas ausentes",
            "Não encontrei estas colunas no CSV:\n\n"
            + "\n".join(faltando)
            + "\n\nConfira os nomes do cabeçalho."
        )
        return []

    contatos = []

    for indice, linha in enumerate(linhas):

        cnpj = str(
            linha.get(cnpj_col, "") or ""
        ).strip()

        nome = (
            str(linha.get(nome_col, "") or "").strip()
            if nome_col
            else ""
        )

        # Verifica os dois telefones separadamente
        for numero_col, status_col in (
            (contato1_col, status1_col),
            (contato2_col, status2_col),
        ):

            numero = normalizar_numero(
                linha.get(numero_col, "")
            )

            status = str(
                linha.get(status_col, "") or ""
            ).strip().upper()

            if not numero:
                continue

            # Pula os números já classificados
            if status in (
                STATUS_DISPONIVEL,
                STATUS_INDISPONIVEL
            ):
                continue

            contatos.append({
                "indice": indice,
                "cnpj": cnpj,
                "nome": nome,
                "numero": numero,
                "numero_col": numero_col,
                "status_col": status_col,
                "status": status,
            })

    return contatos


# =====================================================
# ATUALIZAR STATUS NO CSV
# =====================================================

def atualizar_status_csv(contato, novo_status):

    try:
        (
            cabecalhos,
            linhas,
            dialeto,
            encoding
        ) = ler_csv()

        cnpj_col = encontrar_coluna(
            cabecalhos,
            "cnpj"
        )

        numero_col = encontrar_coluna(
            cabecalhos,
            contato["numero_col"]
        )

        status_col = encontrar_coluna(
            cabecalhos,
            contato["status_col"]
        )

        if not numero_col or not status_col:
            print(
                "[ERRO CSV] Não encontrei a coluna "
                "do telefone ou do status."
            )
            return False

        numero_alvo = normalizar_numero(
            contato["numero"]
        )

        cnpj_alvo = str(
            contato.get("cnpj", "")
        ).strip()

        indice_alvo = contato.get("indice")
        atualizado = False

        # Primeiro tenta encontrar a linha pela posição
        if (
            isinstance(indice_alvo, int)
            and 0 <= indice_alvo < len(linhas)
        ):

            linha = linhas[indice_alvo]

            mesmo_cnpj = (
                not cnpj_col
                or str(
                    linha.get(cnpj_col, "") or ""
                ).strip() == cnpj_alvo
            )

            mesmo_telefone = (
                normalizar_numero(
                    linha.get(numero_col, "")
                ) == numero_alvo
            )

            if mesmo_cnpj and mesmo_telefone:
                linha[status_col] = novo_status
                atualizado = True

        # Se a linha mudou de posição, procura novamente
        if not atualizado:

            for linha in linhas:

                mesmo_cnpj = (
                    not cnpj_col
                    or str(
                        linha.get(cnpj_col, "") or ""
                    ).strip() == cnpj_alvo
                )

                mesmo_telefone = (
                    normalizar_numero(
                        linha.get(numero_col, "")
                    ) == numero_alvo
                )

                if mesmo_cnpj and mesmo_telefone:
                    linha[status_col] = novo_status
                    atualizado = True
                    break

        if not atualizado:
            print(
                f"[AVISO CSV] Não encontrei o telefone "
                f"{numero_alvo} na coluna {numero_col}."
            )
            return False

        salvar_csv(
            cabecalhos,
            linhas,
            dialeto,
            encoding
        )

        return True

    except Exception as erro:
        print(f"[ERRO CSV] {erro}")
        return False


# =====================================================
# VERIFICAR SE O WHATSAPP RECONHECE O NÚMERO
# =====================================================

def verificar_whatsapp(page, timeout=60):

    """
    Retorna:
    False = apareceu mensagem explícita de número inválido.
    True  = o campo de mensagem da conversa ficou visível.
    None  = não foi possível confirmar.
    """

    inicio = time.time()

    seletores_compose = [
        'footer [contenteditable="true"][role="textbox"]',
        'footer [contenteditable="true"]',
        '[data-testid="conversation-compose-box-input"]',
        'div[aria-label="Digite uma mensagem"][contenteditable="true"]',
        'div[aria-label="Type a message"][contenteditable="true"]',
    ]

    mensagens_invalidas = (
        "o número de telefone compartilhado através de url é inválido",
        "phone number shared via url is invalid",
        "não está no whatsapp",
        "isn't on whatsapp",
        "não está usando o whatsapp",
        "not on whatsapp",
    )

    # =====================================================
    # AGUARDAR O POP-UP "INICIANDO CONVERSA"
    # =====================================================

    print("[AGUARDANDO] WhatsApp iniciando conversa...")

    popup_iniciando = page.get_by_text(
        "Iniciando conversa",
        exact=False
    )

    popup_detectado = False

    while time.time() - inicio < timeout:

        try:
            if popup_iniciando.count() > 0 and popup_iniciando.first.is_visible():
                popup_detectado = True
                time.sleep(0.5)
                continue

            # Se o pop-up já apareceu e desapareceu, podemos prosseguir.
            if popup_detectado:
                print("[OK] Pop-up encerrado. Verificando o resultado...")
                break

            # Caso ainda não tenha aparecido, continua aguardando
            # sem presumir que o número já está disponível.
            time.sleep(0.5)

        except Exception:
            time.sleep(0.5)

    # =====================================================
    # VERIFICAR O RESULTADO DA CONVERSA
    # =====================================================

    while time.time() - inicio < timeout:

        try:
            texto = page.locator("body").inner_text(
                timeout=2000
            ).lower()

            # Verifica primeiro se o WhatsApp informou
            # explicitamente que o número é inválido.
            if any(
                mensagem in texto
                for mensagem in mensagens_invalidas
            ):
                print("[RESULTADO] Número não está no WhatsApp.")
                return False

            # Só considera disponível quando o campo
            # de mensagem estiver visível.
            for seletor in seletores_compose:

                campo = page.locator(seletor).first

                if campo.is_visible():
                    print("[RESULTADO] Campo de mensagem encontrado.")
                    return True

        except Exception as erro:
            print(f"[AGUARDANDO CONVERSA] {erro}")

        time.sleep(0.5)

    print("[NÃO CONFIRMADO] Tempo de espera esgotado.")
    return None

# =====================================================
# ABRIR WHATSAPP WEB PELO PLAYWRIGHT
# =====================================================

def abrir_chrome_whatsapp():

    playwright = sync_playwright().start()

    print("Abrindo WhatsApp Web pelo Playwright...")
    print(f"Perfil da sessão: {PERFIL_CHROME}")

    try:
        navegador = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PERFIL_CHROME),
            executable_path=str(CHROME),
            headless=False,
            no_viewport=True,
            args=[
                "--start-maximized",
                "--disable-notifications",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        if navegador.pages:
            page = navegador.pages[0]
        else:
            page = navegador.new_page()

        page.goto(
            "https://web.whatsapp.com",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        return playwright, navegador, page

    except Exception:
        playwright.stop()
        raise
# =====================================================
# PROCESSAR CONTATOS
# =====================================================

def processar_contatos(page):

    while True:

        contatos = carregar_contatos()

        if not contatos:
            print(
                "Nenhum contato pendente. "
                "Nova verificação em 60 segundos."
            )

            time.sleep(60)
            continue

        print(
            f"\nContatos pendentes nesta rodada: "
            f"{len(contatos)}"
        )

        for contato in contatos:

            numero = contato["numero"]

            print(
                f"\nVerificando {numero}"
                f" | CNPJ: {contato['cnpj']}"
                f" | Empresa: {contato['nome'] or '(sem nome)'}"
                f" | Coluna: {contato['numero_col']}"
            )

            url = (
                "https://web.whatsapp.com/send"
                f"?phone=55{numero}"
            )

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

            except Exception as erro:
                print(
                    f"[ERRO AO ABRIR] {erro}"
                )
                time.sleep(3)
                continue
            # =====================================================
            # VERIFICAR CONTATO COM NOVAS TENTATIVAS
            # =====================================================

            MAX_TENTATIVAS = 3
            resultado = None

            for tentativa in range(1, MAX_TENTATIVAS + 1):

                print(
                    f"\n[TENTATIVA {tentativa}/{MAX_TENTATIVAS}] "
                    f"Verificando: {numero}"
                )

                # Verifica o contato e aguarda o retorno da função
                resultado = verificar_whatsapp(page, timeout=60)

                # Se confirmou, encerra as tentativas
                if resultado is not None:
                    break

                # Só repete se não conseguiu confirmar
                if tentativa < MAX_TENTATIVAS:

                    print(
                        f"[NÃO CONFIRMADO] {numero} — "
                        "aguardando 3 segundos para tentar novamente."
                    )

                    time.sleep(3)

                    try:
                        page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=60000
                        )

                        page.wait_for_timeout(2000)

                    except Exception as erro:
                        print(f"[ERRO AO REABRIR] {numero}: {erro}")

            # =====================================================
            # SALVAR RESULTADO
            # =====================================================

            if resultado is False:

                atualizado = atualizar_status_csv(
                    contato,
                    STATUS_INDISPONIVEL
                )

                if atualizado:
                    print(f"[INDISPONÍVEL] {numero}")

            elif resultado is True:

                atualizado = atualizar_status_csv(
                    contato,
                    STATUS_DISPONIVEL
                )

                if atualizado:
                    print(f"[DISPONÍVEL] {numero}")

            else:

                print(
                    f"[NÃO CONFIRMADO] {numero} — "
                    "3 tentativas realizadas; status mantido."
                )

            time.sleep(2)
   

        print(
            "\nRodada concluída. "
            "Nova rodada em 60 segundos."
        )

        time.sleep(60)


# =====================================================
# INICIAR
# =====================================================

if __name__ == "__main__":

    playwright = None
    navegador = None

    try:
        (
            playwright,
            navegador,
            page
        ) = abrir_chrome_whatsapp()

        input(
            "\nSe precisar fazer login, faça agora.\n"
            "Quando o WhatsApp estiver pronto, "
            "pressione ENTER..."
        )

        processar_contatos(page)

    except KeyboardInterrupt:
        print(
            "\nPrograma encerrado."
        )

    except Exception as erro:
        print(
            f"\nERRO: {erro}"
        )

        try:
            messagebox.showerror(
                "Erro",
                str(erro)
            )
        except Exception:
            pass

    finally:

        if navegador:
            navegador.close()

        if playwright:
            playwright.stop()