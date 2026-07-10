"""
Composer - junta multiplas respostas de multi-comando em uma so.
"""

def compor_respostas(respostas):
    """
    respostas: lista de strings (cada uma e a resposta de 1 intent)
    Retorna: string unica concatenada de forma natural
    """
    respostas = [r for r in respostas if r and r.strip()]
    if not respostas:
        return ""

    if len(respostas) == 1:
        return respostas[0]

    # Junta com conectores naturais
    if len(respostas) == 2:
        return f"{respostas[0]} Tambem: {respostas[1]}"

    # 3 ou mais
    partes = [respostas[0]]
    for i, r in enumerate(respostas[1:], 1):
        if i == len(respostas) - 1:
            partes.append(f"Por fim: {r}")
        else:
            partes.append(f"Depois: {r}")
    return " ".join(partes)
