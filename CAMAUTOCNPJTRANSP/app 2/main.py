from fretebras import abrir_fretebras, capturar_fretes
from whatsapp_contatos import extrair_ddd, pegar_estado, salvar_contato_whatsapp

import random
import time
import re


ARQUIVO_PROCESSADOS = "data/processados.txt"


# =========================
# TIMER
# =========================

def iniciar_timer():

    return time.time()


def finalizar_timer(
    nome_acao,
    inicio
):

    tempo = round(
        time.time() - inicio,
        2
    )

    print(
        f"[TEMPO] {nome_acao}: {tempo}s"
    )


# =========================
# CARREGA PROCESSADOS
# =========================

def carregar_processados():

    try:

        with open(
            ARQUIVO_PROCESSADOS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return set(
                linha.strip()
                for linha in arquivo.readlines()
            )

    except:

        return set()


# =========================
# SALVA PROCESSADO
# =========================

def salvar_processado(
    link,
    nome,
    transportadora
):

    with open(
        ARQUIVO_PROCESSADOS,
        "a",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            f"{link} | "
            f"{nome} | "
            f"{transportadora}\n"
        )


# =========================
# LIMPA LINK
# =========================

def limpar_link(link):

    if "&text=" in link:

        return link.split("&text=")[0]

    return link


# =========================
# ESTADO
# =========================

estado = input(
    "\nDigite o estado (MT, GO, SP, PR...): "
).strip().lower()

# =========================
# ABRE FRETEBRAS
# =========================

inicio_sistema = iniciar_timer()

playwright, context, page = abrir_fretebras(
    estado
)

finalizar_timer(
    "Abrir Fretebras",
    inicio_sistema
)

# Variável global do ciclo
pagina_atual = 1
total_paginas = 1

indice_card = 0

# =========================
# LOOP PRINCIPAL
# =========================

while True:

    ciclo_inicio = iniciar_timer()

    try:

        print("\n===================================")
        print("NOVO CICLO")
        print("===================================\n")

        etapa_inicio = iniciar_timer()

        # =========================
        # DEFINE URL
        # =========================

        if pagina_atual == 1:

            url = (
                f"https://www.fretebras.com.br/fretes/carga-de-{estado}/carroceria-cacamba"
            )

        else:

            url = (
                f"https://www.fretebras.com.br/fretes/carga-de-{estado}/carroceria-cacamba/{pagina_atual}"
            )

        print(
            f"Página atual: {pagina_atual}"
        )

        # =========================
        # ACESSA PÁGINA
        # =========================

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        try:

            elemento = page.locator("p").filter(
                has_text="páginas"
            ).first

            print(
                "Quantidade encontrada:",
                elemento.count()
            )

            texto_paginas = elemento.inner_text()

            match = re.search(
                r"de\s+(\d+)\s+páginas",
                texto_paginas
            )

            

            if match:

                total_paginas = int(
                    match.group(1)
                )

                print(
                    f"Total de páginas: {total_paginas}"
                )

        except Exception as e:

            print(
                f"Erro ao capturar total de páginas: {e}"
            )
            
        finalizar_timer(
            "Atualizar fretes",
            etapa_inicio
        )

        # =========================
        # PROCESSADOS
        # =========================

        processados = carregar_processados()

        # =========================
        # TOTAL DE FRETES
        # =========================

        cards = page.locator(
            "section"
        ).all()

        total_cards = len(cards)

        print(
            f"\nTotal de cards na página: "
            f"{total_cards}"
        )

        if indice_card >= total_cards:

            print(
                "\nTodos os fretes da página foram analisados."
            )

            indice_card = 0

            page.reload()
            
            page.wait_for_timeout(3000)

            print("URL após voltar:")
            print(page.url)

            page.wait_for_timeout(5000)

            continue
        
        while indice_card < total_cards:

            # =========================
            # CAPTURA FRETE
            # =========================

            try:
                etapa_inicio = iniciar_timer()

                dados = capturar_fretes(page,indice_card)

                if dados == "IGNORADO":

                    indice_card += 1

                    print(
                    f"Próximo card: {indice_card}"
                    )
                    
                    finalizar_timer(
                        "Capturar frete",
                        etapa_inicio
                    )
                    
                    page.go_back()

                    page.wait_for_timeout(3000)

                    print("URL após voltar:")
                    print(page.url)

                    page.wait_for_timeout(3000)
                    
                    dados= None

                # =========================
                # SEM DADOS
                # =========================

                if not dados:

                    print(
                        "\nNenhum WhatsApp encontrado."
                    )

                    espera = random.randint(
                        5000,
                        10000
                    )

                    print(
                        f"Aguardando "
                        f"{espera/1000:.0f}s..."
                    )

                    page.wait_for_timeout(
                        espera
                    )

                    continue

                # =========================
                # RECEBE DADOS
                # =========================

                link = dados["link"]

                nome = dados["nome"]

                transportadora = dados[
                    "transportadora"
                ]

                # =========================
                # LIMPA LINK
                # =========================

                link_limpo = limpar_link(link)

                    
                # =========================
                # LOGS
                # =========================

                print("\n==================")
                print("NOVO CONTATO")
                print("====================")

                print(
                    f"Nome: "
                    f"{nome}"
                )

                print(
                    f"Transportadora: "
                    f"{transportadora}"
                )

                print(
                    f"WhatsApp: "
                    f"{link_limpo}"
                )

                # =========================
                # CHAVE CONTATO
                # =========================

                chave_contato = (
                    f"{link_limpo.strip()} | "
                    f"{nome.strip()} | "
                    f"{transportadora.strip()}"
                )

                # =========================
                # VERIFICA PROCESSADO
                # =========================

                processado = any(

                    " ".join(
                        chave_contato.lower().split()
                    )

                    ==

                    " ".join(
                        linha.lower().split()
                    )

                    for linha in processados

                )

                if processado:

                    print(
                        "\nContato já processado."
                    )

                    print(
                        f"Registro: {chave_contato}"
                    )

                    indice_card += 1

                    print(
                        f"Próximo card: {indice_card}"
                    )

                    page.wait_for_timeout(
                        random.randint(
                            3000,
                            7000
                        )
                    )

                    print(
                        "\nVoltando para lista de fretes..."
                    )

                    page.go_back()

                    page.wait_for_timeout(3000)

                    print("URL após voltar:")
                    print(page.url)

                    page.wait_for_timeout(3000)

                    continue

                else:

                    print(
                        "\nContato novo."
                    )

                    print(
                        f"Registro: {chave_contato}"
                    )

                # =========================
                # EXTRAI NÚMERO
                # =========================

                numero = (
                    link
                    .replace("tel:", "")
                    .replace(
                        "https://api.whatsapp.com/send/?phone=",
                        ""
                    )
                    .strip()
                )

                if not numero.startswith("55"):

                    numero = "55" + numero

                # =========================
                # LINK WHATSAPP
                # =========================

                link_whatsapp = (
                    "https://web.whatsapp.com/send?"
                    f"phone={numero}"
                )

                # =========================
                # ABRE WHATSAPP
                # =========================

                etapa_inicio = iniciar_timer()

                pagina_whatsapp = context.new_page()

                print(
                    "\nAbrindo WhatsApp..."
                )

                pagina_whatsapp.goto(
                    link_whatsapp,
                    wait_until="domcontentloaded",
                    timeout=80000
                )

                pagina_whatsapp.locator(
                    "header h2"
                ).wait_for(
                    state="visible",
                    timeout=80000
                )
                
                print("Head Encontrado...")
            
                finalizar_timer(
                    "Abrir WhatsApp",
                    etapa_inicio
                )

                # =========================
                # TEMPO TOTAL
                # =========================

                tempo_ate_whatsapp = round(
                    time.time() - ciclo_inicio,
                    2
                )

                print(
                    f"\n[TEMPO TOTAL "
                    f"ATÉ WHATSAPP]: "
                    f"{tempo_ate_whatsapp}s"
                )
                    
                # =========================
                # TEMPO HUMANO
                # =========================

                tempo_total_whatsapp = (
                random.randint(100, 130)
                )

                print(
                    f"Tempo humano definido: {tempo_total_whatsapp} segundos"
                )

            
                inicio_whatsapp = time.time()

                # =========================
                # FOCA CAMPO
                # =========================

                print(
                    "Focando campo..."
                )   

                caixa = pagina_whatsapp.locator(
                    'footer div[contenteditable="true"]'
                ).first

                caixa.focus()

                pagina_whatsapp.wait_for_timeout(
                    tempo_total_whatsapp * 1000
                )

                # =========================
                # ENVIA
                # =========================

                envio_inicio = iniciar_timer()

                print(
                    "\nEnviando mensagem..."
                )

                pagina_whatsapp.keyboard.press(
                    "Enter"
                )

                finalizar_timer(
                    "Enviar mensagem",
                    envio_inicio
                )

                print(
                    "\nMensagem enviada!"
                )


                # =========================
                # PÓS ENVIO
                # =========================

                tempo_pos = random.randint(
                    30,
                    60
                )

                print(
                    f"\nAguardando pós envio "
                    f"({tempo_pos}s)..."
                )

                pagina_whatsapp.wait_for_timeout(
                    tempo_pos * 1000
                )

                # =========================
                # SALVA PROCESSADO
                # =========================

                salvar_processado(
                    link_limpo,
                    nome,
                    transportadora
                )

                print(
                    "\nContato salvo "
                    "em processados.txt"
                )

                
                # =========================
                # SALVA CONTATO WHATSAPP
                # =========================

                salvar_inicio = iniciar_timer()

                print(
                    "\nSalvando contato..."
                    )

                salvar_contato_whatsapp(    pagina_whatsapp,
                    nome, 
                    transportadora
                    )

                finalizar_timer(
                    "Salvar contato",
                    salvar_inicio
                    )
                
            

                # =========================
                # FECHA ABA
                # =========================

                if not pagina_whatsapp.is_closed():

                    print("Fechando aba WhatsApp...")

                    pagina_whatsapp.close()

                    print("Aba WhatsApp fechada.")

            except Exception as e:

                print(
                    f"Erro no card {indice_card}"
                )

                print(e)

                indice_card += 1

                page.go_back()

                page.wait_for_timeout(3000)

                continue
                    
            # =========================
            # PRÓXIMO CICLO
            # =========================

            tempo_proximo = random.randint(
                10,
                25
            )

            print(
                f"\nPróximo ciclo em "
                f"{tempo_proximo}s..."
            )

            indice_card += 1 
            print(
                f"Próximo card: {indice_card}"
            )

            page.wait_for_timeout(
                tempo_proximo * 1000
            )

            finalizar_timer(
                "TEMPO TOTAL DO CICLO",
                ciclo_inicio
            )
            
        print(
        "\nTodos os cards da página foram analisados."
        )

        indice_card = 0

        if pagina_atual < total_paginas:

            pagina_atual += 1

            print(
                f"Indo para página {pagina_atual}"
            )

        else:

            pagina_atual = 1

            print(
                "Voltando para página 1"
            )

        continue

    except Exception as e:

        print("\nErro no sistema:")
        print(e)

        finalizar_timer(
            "Ciclo com erro",
            ciclo_inicio
        )

        tempo_erro = random.randint(
            5,
            12
        )

        print(
            f"\nTentando novamente "
            f"em {tempo_erro}s..."
        )

        page.wait_for_timeout(
            tempo_erro * 1000
        )