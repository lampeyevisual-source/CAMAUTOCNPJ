import csv

arquivo_txt = "data/processados.txt"
arquivo_csv = "data/contatos transportadoras.csv"

with open(arquivo_txt, "r", encoding="utf-8") as txt:
    linhas = txt.readlines()

with open(arquivo_csv, "w", newline="", encoding="utf-8") as csvfile:

    escritor = csv.writer(csvfile)

    escritor.writerow([
        "link_whatsapp",
        "telefone",
        "nome",
        "empresa"
    ])

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue

        dados = linha.split("|")

        # ignora linhas que não têm 3 partes
        if len(dados) < 3:
            print("Linha ignorada:", linha)
            continue

        link = dados[0].strip()
        nome = dados[1].strip()
        empresa = dados[2].strip()

        telefone = link.replace(
            "https://api.whatsapp.com/send/?phone=",
            ""
        )

        escritor.writerow([
            link,
            telefone,
            nome,
            empresa
        ])

print("CSV criado!")