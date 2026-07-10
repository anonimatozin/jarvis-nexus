# -*- coding: utf-8 -*-
"""Mostra diferenca entre versoes de arquivo."""

import difflib


def gerar_diff(antigo, novo, nome_arquivo="arquivo"):
    """Retorna diff legivel pro usuario."""
    linhas_antigo = antigo.splitlines()
    linhas_novo = novo.splitlines()

    diff = list(difflib.unified_diff(
        linhas_antigo, linhas_novo,
        fromfile=f"{nome_arquivo} (antes)",
        tofile=f"{nome_arquivo} (depois)",
        lineterm="", n=2,
    ))

    if not diff:
        return "Nenhuma mudanca detectada."

    # Conta mudancas
    add = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    rem = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

    resumo = f"{add} linhas adicionadas, {rem} removidas."
    detalhes = "\n".join(diff[:30])
    if len(diff) > 30:
        detalhes += f"\n... e mais {len(diff)-30} linhas de diff"

    return f"{resumo}\n\n{detalhes}"


def resumir_diff_voz(antigo, novo):
    """Resumo curto pra voz."""
    linhas_antigo = antigo.splitlines()
    linhas_novo = novo.splitlines()
    diff = list(difflib.unified_diff(linhas_antigo, linhas_novo, lineterm="", n=0))
    add = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    rem = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    if add == 0 and rem == 0:
        return "Sem mudancas"
    return f"{add} linha(s) adicionada(s), {rem} removida(s)"
