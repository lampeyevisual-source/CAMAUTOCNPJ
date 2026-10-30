import re


# =========================================
# PEGA DDD
# =========================================

def extrair_ddd(numero):

    numeros = re.sub(
        r"\D",
        "",
        numero
    )

    if numeros.startswith("55"):

        return numeros[2:4]

    return "N/A"


# =========================================
# MAPA DDD
# =========================================

DDD_ESTADOS = {

    "11": "SP",
    "12": "SP",
    "13": "SP",
    "14": "SP",
    "15": "SP",
    "16": "SP",
    "17": "SP",
    "18": "SP",
    "19": "SP",

    "21": "RJ",
    "22": "RJ",
    "24": "RJ",

    "27": "ES",
    "28": "ES",

    "31": "MG",
    "32": "MG",
    "33": "MG",
    "34": "MG",
    "35": "MG",
    "37": "MG",
    "38": "MG",

    "41": "PR",
    "42": "PR",
    "43": "PR",
    "44": "PR",
    "45": "PR",
    "46": "PR",

    "47": "SC",
    "48": "SC",
    "49": "SC",

    "51": "RS",
    "53": "RS",
    "54": "RS",
    "55": "RS",

    "61": "DF",

    "62": "GO",
    "64": "GO",

    "63": "TO",

    "65": "MT",
    "66": "MT",

    "67": "MS",

    "68": "AC",

    "69": "RO",

    "71": "BA",
    "73": "BA",
    "74": "BA",
    "75": "BA",
    "77": "BA",

    "79": "SE",

    "81": "PE",
    "87": "PE",

    "82": "AL",

    "83": "PB",

    "84": "RN",

    "85": "CE",
    "88": "CE",

    "86": "PI",
    "89": "PI",

    "91": "PA",
    "93": "PA",
    "94": "PA",

    "92": "AM",
    "97": "AM",

    "95": "RR",

    "96": "AP",

    "98": "MA",
    "99": "MA"
   
}

   
# =========================================
# PEGA ESTADO
# =========================================

def pegar_estado(ddd):

    return DDD_ESTADOS.get(
        ddd,
        "N/A"
    )


# =========================================
# SALVAR CONTATO
# =========================================

def salvar_contato_whatsapp(
    page,
    nome,
    transportadora
):

    try:

        print("\n===================================")
        print("SALVANDO CONTATO")
        print("===================================\n")

        # =========================================
        # PEGA NÚMERO
        # =========================================

        numero_header = page.locator(
            'span[data-testid="conversation-info-header-chat-title"]'
        ).first

        numero = (
            numero_header
            .text_content()
            .strip()
        )

        print(
            f"Número encontrado: "
            f"{numero}"
        )

        page.wait_for_timeout(3000)

        # =========================================
        # ABRE PERFIL
        # =========================================

        numero_header.click(
            force=True
        )

        page.wait_for_timeout(6000)

        # =========================================
        # DDD / ESTADO
        # =========================================

        ddd = extrair_ddd(
            numero
        )

        estado = pegar_estado(
            ddd
        )

        print(f"DDD: {ddd}")

        print(f"Estado: {estado}")

        # =========================================
        # NOME FINAL
        # =========================================

        nome_contato = (
            f"{nome} | "
            f"{transportadora} | "
            f"{estado}"
        )

        print(
            f"Nome contato: "
            f"{nome_contato}"
        )

        # =========================================
        # CLICA BOTÃO ADICIONAR
        # =========================================

        print(
            "Procurando botão adicionar..."
        )

        botao_adicionar = page.get_by_text(
            "Adicionar",
            exact=True
        ).first

        botao_adicionar.wait_for(
            state="visible",
            timeout=10000
        )

        print(
            "Botão adicionar encontrado!"
        )

        botao_adicionar.click()

        print(
            "Botão adicionar clicado!"
        )

        page.wait_for_timeout(5000)


        # =========================================
        # INPUT NOME
        # =========================================

        campo_nome = page.locator(
                '[aria-label="Nome"]'
            )

        campo_nome.wait_for(
                state="visible",
                timeout=10000
            )

        campo_nome.click()

        page.wait_for_timeout(1000)

        # =========================================
        # LIMPA CAMPO
        # =========================================

        page.keyboard.down("Control")
        page.keyboard.press("A")
        page.keyboard.up("Control")

        page.wait_for_timeout(500)

        page.keyboard.press("Backspace")

        page.wait_for_timeout(500)

        # =========================================
        # DIGITA
        # =========================================

        campo_nome.type(
            nome_contato,
            delay=80
        )

        page.wait_for_timeout(1500)

        # =========================================
        # VAI PARA PRÓXIMO CAMPO
        # =========================================

        page.keyboard.press("Tab")

        page.wait_for_timeout(1000)

        # =========================================
        # LIMPA PRÓXIMO CAMPO
        # =========================================

        page.keyboard.down("Control")

        page.keyboard.press("A")

        page.keyboard.up("Control")

        page.wait_for_timeout(500)

        page.keyboard.press(
            "Backspace"
        )

        page.wait_for_timeout(500)

        # =========================================
        # ENTER PARA SALVAR
        # =========================================

        print(
            "Confirmando contato..."
        )

        page.keyboard.press(
            "Enter"
        )

        page.wait_for_timeout(2500)

        # =========================================
        # SALVAR CONTATO
        # =========================================

        print(
            "Procurando botão salvar..."
        )

        try:

            botao_salvar = page.locator(
                '[data-testid="save-contact-btn"]'
            )

            botao_salvar.wait_for(
                state="visible",
                timeout=10000
            )

            botao_salvar.click()

            print(
                "Botão salvar clicado!"
            )

            page.wait_for_timeout(3000)

            print(
                "Contato salvo com sucesso!"
            )

        except Exception as e:

            print(
                "Erro ao clicar no botão salvar:"
            )

            print(e)

    except Exception as e:

        print(
            "\nErro ao salvar contato:"
        )

        print(e)

print(
    "\nFinalizando bloco..."
)
