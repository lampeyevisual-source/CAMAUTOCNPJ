def enviar_whatsapp(page, link):

    print("\n===================================")
    print("ABRINDO CONVERSA")
    print("===================================\n")

    # ===================================
    # CONVERTE TEL:
    # ===================================

    if link.startswith("tel:"):

        numero = link.replace("tel:", "")

        if not numero.startswith("55"):
            numero = "55" + numero

        link = f"https://web.whatsapp.com/send?phone={numero}"

    # ===================================
    # ABRE LINK
    # ===================================

    page.goto(
        link,
        wait_until="domcontentloaded",
        timeout=4000
    )

    page.wait_for_timeout(8000)

    # ===================================
    # BOTÃO CONTINUAR
    # ===================================

    try:

        print("Procurando botão continuar...")

        botao_continuar = page.locator(
            'a:has-text("Continuar para o WhatsApp Web")'
        ).first

        if botao_continuar.count() > 0:

            print("Clicando em continuar...")

            botao_continuar.click(force=True)

            page.wait_for_timeout(10000)

    except Exception as e:

        print("Botão continuar não apareceu:")
        print(e)

    # ===================================
    # ESPERA CHAT CARREGAR
    # ===================================

    try:

        print("\nEsperando conversa carregar...")

        page.wait_for_selector(
            'footer div[contenteditable="true"]',
            timeout=4000
        )

        print("Chat carregado!")

    except Exception as e:

        print("Erro ao carregar conversa:")
        print(e)
        return

        # ===================================
    # ENVIA MENSAGEM
    # ===================================

    try:

        print("Procurando caixa de mensagem...")

        caixa = page.locator(
            'footer div[contenteditable="true"]'
        ).first

        caixa.wait_for(timeout=60000)

        print("Caixa encontrada!")

        # GARANTE FOCO
        caixa.focus()

        page.wait_for_timeout(1000)

        print("Enviando ENTER...")

        page.keyboard.down("Enter")
        page.keyboard.up("Enter")

        print("\nMensagem enviada com sucesso!")

        page.wait_for_timeout(5000)

    except Exception as e:

        print("\nErro ao enviar mensagem:")
        print(e)