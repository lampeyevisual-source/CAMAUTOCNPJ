import csv
import re

arquivo_vcf = "data/contatos.vcf"
arquivo_csv = "data/contatos.csv"

contatos = []

nome = ""
telefones = []

with open(arquivo_vcf, "r", encoding="utf-8") as arquivo:

    for linha in arquivo:
        linha = linha.strip()

        if linha.startswith("FN:"):
            nome = linha.replace("FN:", "").strip()

        elif linha.startswith("TEL"):
            numero = linha.split(":")[-1].strip()

            # deixa somente números
            numero = re.sub(r"\D", "", numero)

            if numero:
                telefones.append(numero)

        elif linha == "END:VCARD":

            for telefone in telefones:
                contatos.append([
                    nome if nome else "Sem nome",
                    telefone,
                    f"https://api.whatsapp.com/send/?phone={telefone}"
                ])

            nome = ""
            telefones = []


with open(arquivo_csv, "w", newline="", encoding="utf-8") as arquivo:

    escritor = csv.writer(arquivo)

    escritor.writerow([
        "nome",
        "telefone",
        "link_whatsapp"
    ])

    escritor.writerows(contatos)


print("CSV criado com sucesso!")