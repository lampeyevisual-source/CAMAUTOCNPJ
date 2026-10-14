
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import shutil

# ==========================================
# CAMINHO DO CSV
# ==========================================

ARQUIVO = Path(
    r"C:\Users\marqu\OneDrive\Desktop\AUTOMACOES LUIZ\CAMAUTOCNPJ - Copia - Copia\data\empresas_cnaes4930202.csv"
)


# ==========================================
# LEITURA DO CSV DA RECEITA
# ==========================================

def ler_csv(caminho):
    for encoding in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            return pd.read_csv(
                caminho,
                dtype=str,
                sep=";",
                encoding=encoding,
                keep_default_na=False
            )
        except UnicodeDecodeError:
            continue

    raise Exception("Não foi possível ler o arquivo CSV.")


# ==========================================
# NORMALIZAR DDD + TELEFONE
# ==========================================

def montar_contato(ddd, telefone):
    ddd = re.sub(r"\D", "", str(ddd))
    telefone = re.sub(r"\D", "", str(telefone))

    if not ddd or not telefone:
        return ""

    # Junta DDD e telefone
    numero = ddd + telefone

    # Remove o código do Brasil somente quando
    # o número completo tiver 12 ou 13 dígitos
    # e começar com 55.
    if numero.startswith("55") and len(numero) in (12, 13):
        numero = numero[2:]

    # O número nacional deve ter 10 ou 11 dígitos
    if len(numero) not in (10, 11):
        return ""

    # Confere o tamanho do DDD e do telefone
    ddd_final = numero[:2]
    telefone_final = numero[2:]

    if len(ddd_final) != 2:
        return ""

    if len(telefone_final) not in (8, 9):
        return ""

    return numero


# ==========================================
# CRIAR CONTATOS E REMOVER DUPLICADOS
# ==========================================

def remover_duplicados():

    if not ARQUIVO.exists():
        print("Arquivo não encontrado:")
        print(ARQUIVO)
        return

    print("\nLendo CSV da Receita Federal...")

    try:
        df = ler_csv(ARQUIVO)
    except Exception as erro:
        print("Erro ao ler o arquivo:", erro)
        return

    df.columns = df.columns.str.strip()

    total_original = len(df)

    # ==========================================
    # VALIDAR COLUNAS OBRIGATÓRIAS
    # ==========================================

    colunas_necessarias = [
        "ddd_1",
        "telefone_1",
        "ddd_2",
        "telefone_2",
        "codigo_municipio"
    ]

    faltantes = [
        coluna
        for coluna in colunas_necessarias
        if coluna not in df.columns
    ]

    if faltantes:
        print("ERRO: faltam colunas obrigatórias:")
        print(faltantes)
        print("Colunas encontradas:", list(df.columns))
        return

    # ==========================================
    # CRIAR BACKUP COM DATA E HORA
    # ==========================================

    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup = ARQUIVO.with_name(
        f"{ARQUIVO.stem}_BACKUP_{data_hora}{ARQUIVO.suffix}"
    )

    try:
        shutil.copy2(ARQUIVO, backup)
        print("Backup criado:", backup)
    except Exception as erro:
        print("ERRO ao criar backup:", erro)
        print("Processamento cancelado por segurança.")
        return

    # ==========================================
    # CRIAR CONTATO 1
    # ==========================================

    df["CONTATO 1"] = df.apply(
        lambda linha: montar_contato(
            linha["ddd_1"],
            linha["telefone_1"]
        ),
        axis=1
    )

    # ==========================================
    # CRIAR CONTATO 2
    # ==========================================

    df["CONTATO 2"] = df.apply(
        lambda linha: montar_contato(
            linha["ddd_2"],
            linha["telefone_2"]
        ),
        axis=1
    )

    # ==========================================
    # POSICIONAR CONTATOS APÓS codigo_municipio
    # ==========================================

    colunas = list(df.columns)

    colunas.remove("CONTATO 1")
    colunas.remove("CONTATO 2")

    posicao = colunas.index("codigo_municipio") + 1

    colunas[posicao:posicao] = [
        "CONTATO 1",
        "CONTATO 2"
    ]

    df = df[colunas]
    
    # ==========================================
    # GARANTIR STATUS CONTATO 1
    # LOGO APÓS CONTATO 1
    # ==========================================

    if "STATUS CONTATO 1" in df.columns:
        status = df.pop("STATUS CONTATO 1")

        posicao = df.columns.get_loc("CONTATO 1") + 1

        df.insert(posicao, "STATUS CONTATO 1", status)

    else:
        posicao = df.columns.get_loc("CONTATO 1") + 1

        df.insert(posicao, "STATUS CONTATO 1", "")


    # ==========================================
    # GARANTIR STATUS CONTATO 2
    # LOGO APÓS CONTATO 2
    # ==========================================

    if "STATUS CONTATO 2" in df.columns:
        status = df.pop("STATUS CONTATO 2")

        posicao = df.columns.get_loc("CONTATO 2") + 1

        df.insert(posicao, "STATUS CONTATO 2", status)

    else:
        posicao = df.columns.get_loc("CONTATO 2") + 1

        df.insert(posicao, "STATUS CONTATO 2", "")
        
    # ==========================================
    # IDENTIFICAR EMPRESAS COM TELEFONES DUPLICADOS
    # ==========================================

    telefones_encontrados = set()
    indices_manter = []

    duplicados_contato_1 = 0
    duplicados_contato_2 = 0

    for indice, linha in df.iterrows():

        contato_1 = linha["CONTATO 1"]
        contato_2 = linha["CONTATO 2"]

        # Ignora contatos vazios.
        # O set evita contar o mesmo número duas vezes
        # dentro da própria empresa.
        contatos_linha = {
            contato
            for contato in (contato_1, contato_2)
            if contato
        }

        # Verifica se algum contato já pertence
        # a uma empresa anterior mantida.
        repetidos = contatos_linha & telefones_encontrados

        if repetidos:

            if contato_1 and contato_1 in repetidos:
                duplicados_contato_1 += 1

            if contato_2 and contato_2 in repetidos:
                duplicados_contato_2 += 1

            # Remove a linha inteira
            continue

        # Mantém a primeira ocorrência da empresa
        indices_manter.append(indice)

        # Registra os contatos somente das linhas mantidas
        telefones_encontrados.update(contatos_linha)

    # ==========================================
    # MANTER SOMENTE AS EMPRESAS NÃO DUPLICADAS
    # ==========================================

    df = df.loc[indices_manter].copy()

    quantidade_removida = total_original - len(df)

    # ==========================================
    # SALVAR O CSV
    # ==========================================

    try:
        df.to_csv(
            ARQUIVO,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        # Reabre o arquivo para conferir a gravação
        df_conferido = ler_csv(ARQUIVO)

        print("\n====================================")
        print("CONFERÊNCIA DA GRAVAÇÃO")
        print("====================================")

        print("Registros esperados:", len(df))
        print("Registros encontrados:", len(df_conferido))
        print("Arquivo:", ARQUIVO)
        print("Tamanho:", ARQUIVO.stat().st_size, "bytes")

        if len(df_conferido) != len(df):
            print("ERRO: a quantidade de registros não confere.")
            print("O backup original permanece disponível.")
            return

        print("GRAVAÇÃO CONFIRMADA.")

    except Exception as erro:
        print("ERRO ao salvar ou conferir o CSV:", erro)
        print("O backup original permanece disponível.")
        return

    # ==========================================
    # RELATÓRIO FINAL
    # ==========================================

    print("\n====================================")
    print("LIMPEZA CONCLUÍDA")
    print("====================================")

    print("Linhas originais:", total_original)
    print("Empresas removidas:", quantidade_removida)
    print("Empresas restantes:", len(df))
    print("Repetições no CONTATO 1:", duplicados_contato_1)
    print("Repetições no CONTATO 2:", duplicados_contato_2)
    print("CONTATO 1 preenchido:", (df["CONTATO 1"] != "").sum())
    print("CONTATO 2 preenchido:", (df["CONTATO 2"] != "").sum())
    print("Backup:", backup)
    print("Arquivo atualizado:", ARQUIVO)


# ==========================================
# EXECUTAR
# ==========================================

if __name__ == "__main__":
    remover_duplicados()