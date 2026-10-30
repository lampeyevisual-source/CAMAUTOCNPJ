from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    # =========================
    # PERFIL PERSISTENTE
    # =========================

    context = p.chromium.launch_persistent_context(
        user_data_dir="whatsapp_perfil",
        headless=False,

        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ],

        no_viewport=True
    )

    # =========================
    # PEGA ABA EXISTENTE
    # =========================

    page = context.pages[0] if context.pages else context.new_page()

    # =========================
    # ABRE WHATSAPP WEB
    # =========================

    page.goto(
        "https://web.whatsapp.com",
        wait_until="domcontentloaded",
        timeout=120000
    )

    # =========================
    # LOGIN
    # =========================

    print("\n===================================")
    print("ESCANEIE O QR CODE")
    print("ESPERE O WHATSAPP ABRIR")
    print("NÃO FECHE A JANELA")
    print("===================================\n")

    # =========================
    # ESPERA LOGIN
    # =========================

    input("Depois que carregar totalmente, aperte ENTER...\n")

    # =========================
    # GARANTE SALVAMENTO
    # =========================

    page.wait_for_timeout(10000)

    print("\n===================================")
    print("SESSÃO WHATSAPP SALVA COM SUCESSO")
    print("PASTA UTILIZADA: whatsapp_perfil")
    print("A JANELA VAI PERMANECER ABERTA")
    print("===================================\n")

    # =========================
    # MANTÉM JANELA ABERTA
    # =========================

    input("Pressione ENTER apenas quando quiser fechar tudo...\n")

    # =========================
    # FECHA MANUALMENTE
    # =========================

    context.close()