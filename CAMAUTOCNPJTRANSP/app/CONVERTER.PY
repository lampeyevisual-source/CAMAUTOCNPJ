
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import shutil

# ==========================================
# CAMINHOS DOS ARQUIVOS
# ==========================================

ENTRADA = Path(
    r"data\CONTATOSGRUPOS.CSV"
)

SAIDA = Path(
    r"data\motoristas_convertidos.csv"
)

# ==========================================
# ESTRUTURA FINAL DO CSV
# ==========================================

COLUNAS = [
    "cnpj",
    "identificador_matriz_filial",
    "nome_fantasia",
    "situacao_cadastral_codigo",
    "situacao_cadastral",
    "cnae_principal_codigo",
    "cnae_principal",
    "cnae_secundario_codigo",
    "cnae_secundario",
    "tipo_logradouro",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "uf",
    "codigo_municipio",
    "CONTATO 1",
    "STATUS CONTATO 1",
    "CONTATO 2",
    "STATUS CONTATO 2",
    "ddd_1",
    "telefone_1",
    "ddd_2",
    "telefone_2",
    "email",
    "razao_social",
    "natureza_juridica",
    "qualificacao_responsavel",
    "capital_social",
    "porte_empresa",
    "ente_federativo_responsavel",
    "identificador_socio",
    "nome_socio",
    "cpf_cnpj_socio",
    "qualificacao_socio",
    "data_entrada_sociedade",
    "data_saida_sociedade",
    "cpf_representante_legal",
    "nome_representante_legal",
    "qualificacao_representante_legal",
    "faixa_etaria",
]

# ==========================================
# DDD -> UF
# ==========================================

DDD_UF = {
    "11": "SP", "12": "SP", "13": "SP", "14": "SP",
    "15": "SP", "16": "SP", "17": "SP", "18": "SP",
    "19": "SP",

    "21": "RJ", "22": "RJ", "24": "RJ",
    "27": "ES", "28": "ES",

    "31": "MG", "32": "MG", "33": "MG",
    "34": "MG", "35": "MG", "37": "MG", "38": "MG",

    "41": "PR", "42": "PR", "43": "PR",
    "44": "PR", "45": "PR", "46": "PR",

    "47": "SC", "48": "SC", "49": "SC",

    "51": "RS", "53": "RS", "54": "RS", "55": "RS",

    "61": "DF", "62": "GO", "64": "GO",
    "63": "TO",

    "65": "MT", "66": "MT",
    "67": "MS",

    "68": "AC", "69": "RO",

    "71": "BA", "73": "BA", "74": "BA",
    "75": "BA", "77": "BA",

    "79": "SE",

    "81": "PE", "87": "PE",
    "82": "AL", "83": "PB", "84": "RN",
    "85": "CE", "88": "CE",
    "86": "PI", "89": "PI",

    "91": "PA", "93": "PA", "94": "PA",
    "92": "AM", "97": "AM",
    "95": "RR", "96": "AP",
    "98": "MA", "99": "MA",

    "101": "",  # Não é um DDD válido; ignorado na validação
}

# ==========================================
# EXTRAIR E NORMALIZAR TELEFONE
# ==========================================

def normalizar_telefone(texto):
    texto = str(texto).strip()

    if not texto:
        return None

    # Extrai os dígitos, removendo espaços e pontuação.
    numero = re.sub(r"\D", "", texto)

    # Remove o código do Brasil, se presente.
    if numero.startswith("55") and len(numero) in (12, 13):
        numero = numero[2:]

    # O número nacional deve ter DDD + telefone.
    if len(numero) not in (10, 11):
        return None

    ddd = numero[:2]
    telefone = numero[2:]

    if ddd not in DDD_UF:
        return None

    return {
        "numero": numero,
        "ddd": ddd,
        "telefone": telefone,
        "uf": DDD_UF[ddd],
    }

# ==========================================
# LER CSV SIMPLES DE TELEFONES
# ==========================================

def ler_telefones(caminho):
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            texto = caminho.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Não foi possível ler o arquivo.")

    telefones = []

    for linha in texto.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        # Permite CSV com um número por linha,
        # inclusive quando há separadores extras.
        telefones.append(linha)

    return telefones

# ==========================================
# CONVERTER PARA A ESTRUTURA DE EMPRESAS
# ==========================================

def converter():

    if not ENTRADA.exists():
        print("Arquivo de entrada não encontrado:")
        print(ENTRADA)
        return

    print("\nLendo telefones...")

    try:
        linhas = ler_telefones(ENTRADA)
    except Exception as erro:
        print("Erro na leitura:", erro)
        return

    registros = []
    numeros_encontrados = set()

    invalidos = 0
    duplicados = 0

    for linha in linhas:

        contato = normalizar_telefone(linha)

        if contato is None:
            invalidos += 1
            print("Telefone inválido:", linha)
            continue

        numero = contato["numero"]

        if numero in numeros_encontrados:
            duplicados += 1
            continue

        numeros_encontrados.add(numero)

        # Todas as colunas começam vazias.
        registro = {coluna: "" for coluna in COLUNAS}

        # Dados que podem ser obtidos do telefone.
        registro["situacao_cadastral"] = "ATIVA"
        registro["uf"] = contato["uf"]

        registro["CONTATO 1"] = contato["numero"]
        registro["STATUS CONTATO 1"] = "DISPONÍVEL"

        registro["ddd_1"] = contato["ddd"]
        registro["telefone_1"] = contato["telefone"]

        # Demais campos permanecem vazios.
        registros.append(registro)

    df = pd.DataFrame(registros, columns=COLUNAS)

    # ==========================================
    # CRIAR DIRETÓRIO DE SAÍDA
    # ==========================================

    try:
        SAIDA.parent.mkdir(parents=True, exist_ok=True)

        # Se a saída já existir, preservar backup.
        if SAIDA.exists():
            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")

            backup = SAIDA.with_name(
                f"{SAIDA.stem}_BACKUP_{data_hora}{SAIDA.suffix}"
            )

            shutil.copy2(SAIDA, backup)
            print("Backup anterior:", backup)

        # ==========================================
        # SALVAR CSV
        # ==========================================

        df.to_csv(
            SAIDA,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        # Conferir o arquivo gerado.
        conferido = pd.read_csv(
            SAIDA,
            sep=";",
            dtype=str,
            encoding="utf-8-sig",
            keep_default_na=False
        )

        if len(conferido) != len(df):
            print("ERRO: quantidade de registros não confere.")
            return

        if list(conferido.columns) != COLUNAS:
            print("ERRO: as colunas não correspondem à estrutura.")
            return

    except Exception as erro:
        print("Erro ao salvar o arquivo:", erro)
        return

    # ==========================================
    # RELATÓRIO FINAL
    # ==========================================

    print("\n====================================")
    print("CONVERSÃO CONCLUÍDA")
    print("====================================")
    print("Linhas lidas:", len(linhas))
    print("Telefones convertidos:", len(df))
    print("Duplicados ignorados:", duplicados)
    print("Telefones inválidos:", invalidos)
    print("Contatos disponíveis:", (df["STATUS CONTATO 1"] == "DISPONÍVEL").sum())
    print("Arquivo gerado:", SAIDA)
    print("Registros conferidos:", len(conferido))

# ==========================================
# EXECUTAR
# ==========================================

if __name__ == "__main__":
    converter()
