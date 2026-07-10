"""
Lista organizada de TUDO que o Jarvis pode fazer.
Usado pelo comando "o que voce pode fazer".
"""


CAPACIDADES = {
    "⌚ Tempo e Data": [
        ("Jarvis que horas sao", "Diz a hora atual"),
        ("Jarvis que dia e hoje", "Diz a data"),
    ],

    "🌤️ Clima (3 APIs em consenso)": [
        ("Jarvis qual a temperatura", "Clima atual da sua cidade"),
        ("Jarvis vai chover hoje", "Previsao de hoje"),
        ("Jarvis vai chover amanha", "Previsao de amanha"),
        ("Jarvis clima em Paris", "Clima de outra cidade"),
    ],

    "📍 Localizacao": [
        ("Jarvis qual minha cidade", "Mostra sua cidade salva"),
        ("Jarvis atualiza localizacao", "Detecta de novo via IP"),
        ("Jarvis minha cidade e X", "Muda cidade manualmente"),
    ],

    "🎙️ Pesquisa Web": [
        ("Jarvis pesquisar X", "Busca multi-site"),
        ("Jarvis me fala sobre X", "Pesquisa com resumo"),
        ("Jarvis youtube X", "Abre busca no YouTube"),
    ],

    "💻 Controle do PC": [
        ("Jarvis abrir spotify", "Abre qualquer programa"),
        ("Jarvis fechar X", "Fecha programa"),
        ("Jarvis volume 50", "Muda volume do PC"),
        ("Jarvis brilho 80", "Muda brilho da tela"),
        ("Jarvis bloquear tela", "Bloqueia o Windows"),
        ("Jarvis status", "CPU, RAM, disco"),
    ],

    "🧠 Memoria (de longo prazo)": [
        ("Jarvis lembre disso: X", "Memoriza informacao"),
        ("Jarvis quantas memorias", "Mostra estatisticas"),
    ],

    "📸 Memoria Visual (NOVO!)": [
        ("Jarvis o que eu fazia as 14 horas", "Busca por horario"),
        ("Jarvis achei aquele tutorial de X", "Busca por texto"),
        ("Jarvis quanto tempo no Discord ontem", "Tempo em apps"),
        ("Jarvis pausa captura", "Para de gravar tela"),
        ("Jarvis retoma captura", "Volta a gravar"),
        ("Jarvis status do pendrive", "Espaco, capturas, etc"),
    ],

    "📅 Lembretes e Agenda": [
        ("Jarvis me lembre em 5 minutos de X", "Lembrete rapido"),
        ("Jarvis pomodoro", "Inicia pomodoro de 25min"),
        ("Jarvis meus lembretes", "Lista pendentes"),
    ],

    "🎯 Modos de Trabalho": [
        ("Jarvis vou jogar minecraft", "Abre jogo e Discord"),
        ("Jarvis preparar pc", "Modo trabalho"),
        ("Jarvis vou gravar", "Modo gravacao"),
        ("Jarvis vou dormir", "Fecha tudo"),
        ("Jarvis preciso focar", "Modo foco"),
        ("Jarvis lista de modos", "Mostra todos"),
    ],

    "👁️ Visao e Camera": [
        ("Jarvis o que tem na tela", "Le e descreve a tela"),
        ("Jarvis tira uma foto", "Captura da webcam"),
    ],

    "📊 Contexto e Atividade": [
        ("Jarvis o que estou fazendo", "App ativo"),
        ("Jarvis top apps", "Mais usados hoje"),
        ("Jarvis resumo do dia", "O que voce fez"),
    ],

    "🎵 Musica": [
        ("Jarvis toca uma musica", "Abre Spotify"),
    ],

    "🎮 Minecraft Bot (NOVO!)": [
        ("Jarvis entra no minecraft", "Bot entra em LAN auto"),
        ("Jarvis status do bot", "HP, posicao, objetivo"),
        ("Jarvis vem aqui", "Bot vem ate voce"),
        ("Jarvis cava aqui", "Bot cava o bloco que olha"),
        ("Jarvis pega madeira", "Bot coleta madeira sozinho"),
        ("Jarvis me segue", "Bot segue voce"),
        ("Jarvis sai do minecraft", "Desconecta bot"),
    ],

    "🔌 ESP32 Jarvis Deck (NOVO!)": [
        ("Jarvis status do ESP", "Mostra IP e conexao"),
        ("Tecla 1 no keypad", "Pomodoro"),
        ("Tecla 2/3", "Volume +/-"),
        ("Tecla 7", "Que horas sao"),
        ("Tecla 8", "Status do PC"),
        ("Tecla *", "Bloquear tela"),
        ("Tecla #", "Lista de comandos"),
        ("2 palmas", "Comando especial"),
        ("Passar mao", "Detector IR"),
    ],

    "📱 Controle Celular Android (NOVO!)": [
        ("Jarvis status do celular", "Modelo, Android, bateria"),
        ("Jarvis ler notificações do celular", "Lista notificações"),
        ("Jarvis abrir [app] no celular", "Abre qualquer app"),
        ("Jarvis listar apps do celular", "Lista apps instalados"),
        ("Jarvis fechar [app] no celular", "Fecha um app"),
        ("Jarvis bateria do celular", "Nível da bateria"),
        ("Jarvis volume do celular 10", "Ajusta volume (0-15)"),
        ("Jarvis volume do celular +", "Aumenta volume"),
        ("Jarvis volume do celular -", "Diminui volume"),
        ("Jarvis Wi-Fi do celular", "Status do Wi-Fi"),
        ("Jarvis ligar Wi-Fi do celular", "Liga Wi-Fi"),
        ("Jarvis desligar Wi-Fi do celular", "Desliga Wi-Fi"),
        ("Jarvis Bluetooth do celular", "Status Bluetooth"),
        ("Jarvis tirar screenshot do celular", "Captura de tela"),
        ("Jarvis onde tá meu celular", "Faz tocar (ring)"),
        ("Jarvis enviar SMS [num] [msg]", "Abre SMS pronto"),
        ("Jarvis ler SMS recentes", "Lê SMS do celular"),
        ("Jarvis informações do celular", "Info completa"),
    ],

    "📺 TV Samsung SmartThings (NOVO!)": [
        ("Jarvis ligar a TV", "Liga a TV Samsung"),
        ("Jarvis desligar a TV", "Desliga a TV"),
        ("Jarvis volume da TV 20", "Seta volume específico"),
        ("Jarvis volume da TV +", "Aumenta volume"),
        ("Jarvis volume da TV -", "Diminui volume"),
        ("Jarvis mutar a TV", "Muta/Desmuta"),
        ("Jarvis canal 5", "Muda para canal específico"),
        ("Jarvis próximo canal", "Canal up"),
        ("Jarvis canal anterior", "Canal down"),
        ("Jarvis mudar para HDMI1", "Troca fonte HDMI"),
        ("Jarvis mudar para HDMI2", "Troca fonte HDMI"),
        ("Jarvis status da TV", "Status da TV"),
        ("Jarvis play da TV", "Play mídia"),
        ("Jarvis pause da TV", "Pause mídia"),
        ("Jarvis home da TV", "Volta pra Home"),
        ("Jarvis seta da TV pra cima", "Navega na TV"),
        ("Jarvis confirmar na TV", "Pressiona OK"),
    ],

    "📊 Produtividade e Planilhas": [
        ("Jarvis criar relatório do dia", "Gera planilha Excel com atividades"),
        ("Jarvis resumo do dia", "Mostra resumo de produtividade"),
        ("Jarvis resumo da semana", "Relatório semanal consolidado"),
        ("Jarvis exportar memórias", "Exporta memórias para CSV/Excel"),
        ("Jarvis tempo focado hoje", "Mostra horas produtivas"),
        ("Jarvis planilha de gastos", "Gera planilha de finanças"),
        ("Jarvis adicionar gasto X Y", "Registra gasto (descrição, valor)"),
        ("Jarvis listar gastos", "Mostra gastos recentes"),
        ("Jarvis listar relatorios", "Mostra relatórios salvos"),
    ],

    "🔒 Segurança": [
        ("Jarvis definir senha X", "Define senha por voz"),
        ("Jarvis desbloquear X", "Desbloqueia com senha"),
        ("Jarvis status de segurança", "Mostra status"),
        ("Jarvis quem usou o PC", "Log de acessos"),
        ("Jarvis listar logs", "Logs recentes"),
        ("Jarvis dispositivos na rede", "Scan de rede"),
        ("Jarvis verificar portas", "Portas abertas"),
    ],

    "🎮 Entretenimento": [
        ("Jarvis jogar adivinha", "Jogo da adivinhação"),
        ("Jarvis adivinhar X", "Tenta adivinhar número"),
        ("Jarvis quiz", "Pergunta e resposta"),
        ("Jarvis responder X", "Responde quiz"),
        ("Jarvis me conta uma piada", "Piada aleatória"),
        ("Jarvis curiosidade", "Fato curioso"),
        ("Jarvis recomendar filme", "Recomenda filme"),
        ("Jarvis frase famosa", "Frase motivacional"),
    ],

    "⚙️ Sistema": [
        ("Jarvis encerrar", "Desliga o Jarvis"),
        ("/clear", "Limpa terminal"),
        ("/restart", "Reinicia o Jarvis"),
        ("/limpar conversa", "Esquece historico recente"),
    ],
}


def listar_tudo():
    """Retorna string formatada com TODAS capacidades."""
    linhas = []
    linhas.append("\n" + "=" * 60)
    linhas.append("  J.A.R.V.I.S. - CAPACIDADES COMPLETAS")
    linhas.append("=" * 60)
    total = 0
    for categoria, comandos in CAPACIDADES.items():
        linhas.append(f"\n{categoria}")
        linhas.append("-" * 40)
        for cmd, desc in comandos:
            linhas.append(f"  • \"{cmd}\"")
            linhas.append(f"      {desc}")
            total += 1
    linhas.append("\n" + "=" * 60)
    linhas.append(f"  Total: {total} comandos disponiveis")
    linhas.append("=" * 60 + "\n")
    return "\n".join(linhas)


def falar_resumo():
    """Resumo curto pra falar por voz (categorias)."""
    cats = list(CAPACIDADES.keys())
    qtd_cmds = sum(len(c) for c in CAPACIDADES.values())
    resumo = (
        f"Posso fazer {qtd_cmds} coisas, Sir. As principais categorias sao: "
        f"clima com 3 fontes em consenso, controle do PC, "
        f"memoria visual com print a cada 2 minutos, pesquisa web, "
        f"lembretes, modos de trabalho, e contexto da sua atividade. "
        f"Olhe no console para a lista completa."
    )
    return resumo
