#!/usr/bin/env python3
"""Separa um TXT exportado do WhatsApp em um arquivo por remetente.

Uso pelo terminal:
    python separar_mensagens_por_pessoa.py "Conversa do WhatsApp.txt"

Se nenhum arquivo for informado, o programa abre uma janela para selecioná-lo.
Os arquivos gerados ficam na mesma pasta do TXT original.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import OrderedDict
from pathlib import Path


# Formato Android: 03/11/2023 00:19 - Nome: mensagem
PADRAO_ANDROID = re.compile(
    r"^[\u200e\ufeff]?"
    r"(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s+-\s+"
    r"(?P<conteudo>.*)$"
)

# Formato iPhone: [03/11/2023, 00:19:00] Nome: mensagem
PADRAO_IPHONE = re.compile(
    r"^[\u200e\ufeff]?\["
    r"(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)"
    r"\]\s+(?P<conteudo>.*)$"
)

PADRAO_REMETENTE = re.compile(r"^(?P<nome>[^:]+?):\s?(?P<mensagem>.*)$")
CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
NOMES_RESERVADOS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{numero}" for numero in range(1, 10)),
    *(f"LPT{numero}" for numero in range(1, 10)),
}


def ler_texto(caminho: Path) -> str:
    """Lê o arquivo tentando codificações comuns de exportações do WhatsApp."""
    ultimo_erro: UnicodeDecodeError | None = None
    for codificacao in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return caminho.read_text(encoding=codificacao)
        except UnicodeDecodeError as erro:
            ultimo_erro = erro

    if ultimo_erro is not None:
        raise ultimo_erro
    raise OSError(f"Não foi possível ler o arquivo: {caminho}")


def separar_mensagens(texto: str) -> OrderedDict[str, list[dict[str, str]]]:
    """Agrupa as mensagens pelo nome do remetente."""
    mensagens: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    mensagem_atual: dict[str, str] | None = None

    for linha in texto.splitlines():
        inicio = PADRAO_ANDROID.match(linha) or PADRAO_IPHONE.match(linha)

        if inicio:
            remetente = PADRAO_REMETENTE.match(inicio.group("conteudo"))

            # Linhas de sistema do WhatsApp não possuem "Nome: mensagem".
            if not remetente:
                mensagem_atual = None
                continue

            nome = remetente.group("nome").strip()
            mensagem_atual = {
                "data": inicio.group("data"),
                "hora": inicio.group("hora").strip(),
                "texto": remetente.group("mensagem"),
            }
            mensagens.setdefault(nome, []).append(mensagem_atual)
            continue

        # Continuações pertencem à última mensagem encontrada.
        if mensagem_atual is not None:
            mensagem_atual["texto"] += "\n" + linha

    return mensagens


def nome_de_arquivo_seguro(nome: str) -> str:
    """Remove caracteres que não podem ser usados em nomes de arquivos no Windows."""
    nome_limpo = CARACTERES_INVALIDOS.sub("_", nome).strip().rstrip(". ")
    if not nome_limpo:
        nome_limpo = "Sem nome"
    if nome_limpo.upper() in NOMES_RESERVADOS:
        nome_limpo += "_contato"
    return nome_limpo[:180]


def criar_arquivos(
    mensagens: OrderedDict[str, list[dict[str, str]]], caminho_origem: Path
) -> list[tuple[str, Path, int]]:
    """Cria um TXT por pessoa na mesma pasta do arquivo de origem."""
    resultados: list[tuple[str, Path, int]] = []
    nomes_usados: set[str] = {caminho_origem.name.casefold()}

    for pessoa, itens in mensagens.items():
        base = nome_de_arquivo_seguro(pessoa)
        nome_saida = f"{base}.txt"
        contador = 2

        while nome_saida.casefold() in nomes_usados:
            nome_saida = f"{base} ({contador}).txt"
            contador += 1

        nomes_usados.add(nome_saida.casefold())
        caminho_saida = caminho_origem.parent / nome_saida

        blocos = [
            f"[{item['data']} {item['hora']}] {item['texto']}" for item in itens
        ]
        caminho_saida.write_text("\n".join(blocos) + "\n", encoding="utf-8-sig")
        resultados.append((pessoa, caminho_saida, len(itens)))

    return resultados


def escolher_arquivo() -> Path | None:
    """Abre uma janela de seleção; usa entrada digitada se Tkinter não existir."""
    try:
        from tkinter import Tk, filedialog

        janela = Tk()
        janela.withdraw()
        janela.attributes("-topmost", True)
        selecionado = filedialog.askopenfilename(
            title="Selecione o TXT exportado do WhatsApp",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        janela.destroy()
        return Path(selecionado) if selecionado else None
    except (ImportError, RuntimeError):
        digitado = input("Cole o caminho do TXT exportado do WhatsApp: ").strip().strip('"')
        return Path(digitado) if digitado else None


def executar(caminho: Path) -> list[tuple[str, Path, int]]:
    caminho = caminho.expanduser().resolve()
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    mensagens = separar_mensagens(ler_texto(caminho))
    if not mensagens:
        raise ValueError(
            "Nenhuma mensagem foi reconhecida. Confira se o TXT foi exportado pelo WhatsApp."
        )

    return criar_arquivos(mensagens, caminho)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Separa uma conversa exportada do WhatsApp em um TXT por remetente."
    )
    parser.add_argument(
        "arquivo",
        nargs="?",
        type=Path,
        help="caminho do TXT exportado do WhatsApp",
    )
    argumentos = parser.parse_args()
    caminho = argumentos.arquivo or escolher_arquivo()

    if caminho is None:
        print("Nenhum arquivo foi selecionado.")
        return 1

    try:
        resultados = executar(caminho)
    except (OSError, UnicodeError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    total = sum(quantidade for _, _, quantidade in resultados)
    print(f"\nPronto: {total} mensagens de {len(resultados)} pessoas foram separadas.\n")
    for pessoa, arquivo, quantidade in resultados:
        print(f"- {pessoa}: {quantidade} mensagens -> {arquivo.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
