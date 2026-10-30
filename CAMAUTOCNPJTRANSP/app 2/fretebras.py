from playwright.sync_api import sync_playwright


from playwright.sync_api import sync_playwright


def abrir_fretebras(
    estado
):


    # =========================
    # URL
    # =========================

    url = (
        f"https://www.fretebras.com.br/fretes/"
        f"carga-de-{estado}/"
        f"carroceria-cacamba"
    )

    print(f"\nURL gerada: {url}")

    print(
        f"\nBuscando fretes de {estado.upper()}"
    )

    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir="perfil",
        headless=False,

        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled"
        ],

        no_viewport=True
    )

    page = (
        context.pages[0]
        if context.pages
        else context.new_page()
    )

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=120000
    )

    page.wait_for_timeout(5000)

    print(
        f"\nFretebras carregado para {estado.upper()}!"
    )

    return playwright, context, page

def extrair_transportadora(url_frete):

    """
    EXEMPLO URL:

    https://www.fretebras.com.br/frete/
    cerro-azul-transportes/
    carga-de-sao-jose...

    A TRANSPORTADORA SEMPRE FICA
    ENTRE:

    /frete/
    E A PRÓXIMA "/"
    """

    try:

        if "/frete/" not in url_frete:

            return "N/A"

        # =====================================
        # PEGA TEXTO APÓS /frete/
        # =====================================

        parte = url_frete.split(
            "/frete/"
        )[1]

        # =====================================
        # PEGA SOMENTE A PRIMEIRA PARTE
        # =====================================

        slug_transportadora = (
            parte.split("/")[0]
        )

        # =====================================
        # FORMATA TEXTO
        # =====================================

        transportadora = (
            slug_transportadora
            .replace("-", " ")
            .title()
            .strip()
        )

        return transportadora

    except Exception as erro:

        print(
            "\nErro ao extrair transportadora:"
        )

        print(erro)

        return "N/A"


def capturar_fretes(page,indice_card):



    # =====================================
    # CAPTURA CARDS
    # =====================================

    cards = page.locator(
        "section"
    ).all()

    print(
        f"\nFretes encontrados: "
        f"{len(cards)}"
    )


    # =====================================
    # LISTA FRETES
    # =====================================

    for card in cards[:5]:

        try:

            cidades = card.locator(
                "h2"
            ).all_text_contents()

            preco = card.locator(   
                '[data-testid="payment-price"]'
            ).text_content()

            tags = card.locator(
                '[data-testid="chips"]'
            ).all_text_contents()

            print("\n====================")

            if len(cidades) >= 2:

                print(
                    "Origem:",
                    cidades[0]
                )

                print(
                    "Destino:",
                    cidades[1]
                )

            print("Preço:", preco)

            print("Tags:", tags)

        except Exception as e:

            print(
                "\nErro ao capturar frete:"
            )

            print(e)


    # =====================================
    # ABRE FRETE
    # =====================================

    print(
        f"\nAbrindo frete índice {indice_card}..."
    )

    cards[indice_card].click(
        force=True
    )

    page.wait_for_timeout(5000)

    # =====================================
    # VALIDA ESPÉCIE DO FRETE
    # =====================================

    page.wait_for_timeout(2000)

    try:

        especie = page.locator(
            'span.frete-dados.frete-especie'
        ).first.text_content().strip()

        print(
            f"Espécie encontrada: {especie}"
        )

        if especie != "GRANEL":

            print(
                "\nFrete ignorado "
                "(não é GRANEL)."
            )
            return "IGNORADO"
        
    except Exception as e:

        print(
            "\nErro ao validar espécie:"
        )

        print(e)


    # =====================================
    # URL DO FRETE
    # =====================================

    url_frete = page.url

    print("\nURL atual:")

    print(url_frete)

    # =====================================
    # TRANSPORTADORA
    # =====================================

    transportadora = (
        extrair_transportadora(
            url_frete
        )
    )

    print("\nTRANSPORTADORA:")

    print(transportadora)

    # =====================================
    # ABRE CONTATOS
    # =====================================

    print("\nAbrindo contatos...")

    page.locator(
        ".btn-ver-contatos"
    ).click()

    page.wait_for_timeout(3000)

    contatos = page.locator(
        "#contacts-whatsapp > div"
    )

    total = contatos.count()

    print(
        f"\nContatos encontrados: "
        f"{total}"
    )

    for i in range(total):

        try:

            contato = contatos.nth(i)

            # =========================
            # LINK WHATSAPP
            # =========================

            link = contato.locator(
                "a"
            ).get_attribute(
                "href"
            )

            # =========================
            # NOME CONTATO
            # =========================

            nome = "N/A"

            try:

                nome_elemento = contato.locator(
                    ".modal-contacts__name"
                )

                if nome_elemento.count() > 0:

                    nome = (
                        nome_elemento
                        .text_content()
                        .strip()
                    )

            except:
                pass

            # =========================
            # VALIDA LINK
            # =========================

            if (
                link
                and "whatsapp" in link
            ):

                print(
                    "\n===================="
                )

                print(
                    "NOME:"
                )

                print(nome)

                print(
                    "\nTRANSPORTADORA:"
                )

                print(
                    transportadora
                )

                print(
                    "\nLINK WHATSAPP:"
                )

                print(link)

                # =====================
                # RETORNA AO MAIN
                # =====================

                return {
                    "link": link,
                    "nome": nome,
                    "transportadora": transportadora,
                    "url_frete": url_frete
                }

        except Exception as e:

            print("\nErro contato:")

            print(e)

            pass

    return None