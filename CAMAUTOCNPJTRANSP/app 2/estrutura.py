import os

def mostrar_estrutura(pasta, nivel=0):

    ignorar = {
        "__pycache__",
        ".git",
        ".idea",
        ".vscode",
        "node_modules"
    }

    try:
        itens = sorted(os.listdir(pasta))

        for item in itens:

            if item in ignorar:
                continue

            caminho = os.path.join(pasta, item)

            prefixo = "│   " * nivel + "├── "

            print(prefixo + item)

            if os.path.isdir(caminho):
                mostrar_estrutura(caminho, nivel + 1)

    except PermissionError:
        print("Sem permissão:", pasta)


PASTA_ATUAL = os.getcwd()

print("\nESTRUTURA DA AUTOMAÇÃO:\n")

print(PASTA_ATUAL)

mostrar_estrutura(PASTA_ATUAL)