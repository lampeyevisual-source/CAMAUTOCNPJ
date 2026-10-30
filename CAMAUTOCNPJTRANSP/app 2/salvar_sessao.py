from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    # =========================
    # PERFIL PERSISTENTE
    # =========================

    context = p.chromium.launch_persistent_context(
        user_data_dir="perfil",
        headless=False,

        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled"
        ],

        no_viewport=True
    )

    # =========================
    # PEGA ABA EXISTENTE
    # =========================

    page = context.pages[0] if context.pages else context.new_page()

    # =========================
    # ABRE FRETEBRAS
    # =========================

    page.goto(
        "https://www.fretebras.com.br",
        wait_until="domcontentloaded",
        timeout=120000
    )

    print("\n===================================")
    print("FAÇA LOGIN NO FRETEBRAS")
    print("ESPERE ENTRAR NA ÁREA LOGADA")
    print("NÃO FECHE A JANELA")
    print("===================================\n")

    # =========================
    # ESPERA LOGIN
    # =========================

    input("Depois do login completo aperte ENTER...\n")

    # =========================
    # GARANTE SALVAMENTO
    # =========================

    page.wait_for_timeout(10000)

    print("\n===================================")
    print("SESSÃO PERSISTENTE SALVA")
    print("PASTA UTILIZADA: perfil")
    print("A JANELA CONTINUARÁ ABERTA")
    print("===================================\n")

    # =========================
    # MANTÉM JANELA ABERTA
    # =========================

    input("Pressione ENTER apenas quando quiser fechar tudo...\n")

    # =========================
    # FECHA MANUALMENTE
    # =========================

    context.close()