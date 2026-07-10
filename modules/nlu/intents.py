"""Intents v3 - blockers ultra rigidos."""
import re


INTENTS = {
    # ═══ AJUDA (prioridade max) ═══
    "ajuda_completa": {
        "exemplos": [
            "o que voce pode fazer", "lista de comandos",
            "suas capacidades", "todos comandos",
            "tudo que voce faz", "me mostra tudo",
            "que comandos voce tem", "voce pode fazer o que",
        ],
        "keywords": ["o que voce pode fazer", "o que voce faz",
                      "lista de comandos", "suas capacidades",
                      "todos comandos", "tudo que voce faz",
                      "que comandos"],
        "blockers": [],
    },

    # ═══ TEMPO ═══
    "hora_atual": {
        "exemplos": [
            "que horas sao", "qual a hora", "que hora e",
            "me diz a hora", "que horario sao", "horas",
        ],
        "keywords": ["que hora", "que horas", "qual a hora",
                      "que horario", "horas sao"],
        "blockers": ["lembre", "lembra", "lembrete", "agenda",
                      "em ", "daqui", "minutos", "minuto",
                      "fazia as", "fiz as", "via as"],
    },
    "data_atual": {
        "exemplos": [
            "que dia e hoje", "qual a data", "que data e hoje",
            "data atual", "dia da semana",
        ],
        "keywords": ["que dia", "que data", "qual a data"],
        "blockers": ["chover", "clima", "tempo", "amanha", "ontem"],
    },

    # ═══ CLIMA (super blockers) ═══
    "clima_atual": {
        "exemplos": [
            "qual o clima", "como ta o tempo", "qual a temperatura",
            "ta calor", "ta frio", "ta quente", "clima",
            "como esta o tempo agora",
        ],
        "keywords": ["qual o clima", "como ta o tempo",
                      "esta o tempo", "qual a temperatura"],
        "blockers": [
            "amanha", "ontem", "previsao", "chover",
            "lembre", "lembrete", "abra", "abrir",
            "minutos", "minuto", "agua", "tomar",
            "remedio", "comer", "comprar",
        ],
    },
    "clima_chover": {
        "exemplos": [
            "vai chover", "vai chover hoje", "ta chovendo",
            "vai molhar hoje", "tem chuva hoje", "chuva hoje",
        ],
        "keywords": ["vai chover", "ta chovendo", "tem chuva",
                      "chuva hoje", "vai molhar"],
        "blockers": [
            "amanha", "lembre", "minutos", "minuto",
            "abra", "abrir", "agua", "tomar",
            "pao", "comida", "bolo",
        ],
    },
    "clima_amanha": {
        "exemplos": [
            "vai chover amanha", "como vai estar amanha",
            "clima amanha", "previsao amanha", "tempo amanha",
            "amanha vai chover", "qual a previsao pra amanha",
            "previsao do tempo amanha", "amanha vai dar chuva",
        ],
        "keywords": ["amanha", "amanhã"],
        "blockers": ["abra", "abrir", "lembre"],
    },
    "clima_cidade": {
        "exemplos": [
            "clima em paris", "temperatura em tokyo",
            "tempo em sao paulo", "qual o clima de curitiba",
            "como esta o clima em londres",
        ],
        "keywords": ["clima em", "clima de", "temperatura em",
                      "tempo em", "tempo de"],
        "blockers": [
            "lembre", "lembrete", "minutos", "minuto",
            "abra", "abrir", "tomar", "agua",
            "remedio", "comer",
        ],
        "extractor": r"(?:em|de|na|no)\s+([A-Za-zãáéíóúçâêôà\s]+?)(?:$|\?|\.|,)",
    },

    # ═══ LOCALIZACAO ═══
    "localizacao_minha": {
        "exemplos": [
            "qual minha cidade", "onde eu estou", "minha localizacao",
        ],
        "keywords": ["minha cidade", "minha localizacao",
                      "onde eu estou", "onde estou"],
        "blockers": ["clima", "tempo", "previsao"],
    },
    "localizacao_atualizar": {
        "exemplos": ["atualiza localizacao", "redetectar localizacao"],
        "keywords": ["atualiza localizacao", "redetectar",
                      "detectar localizacao", "atualizar cidade"],
    },
    "localizacao_mudar": {
        "exemplos": ["minha cidade e curitiba", "agora moro em sao paulo"],
        "keywords": ["minha cidade e", "mudar cidade", "moro em"],
        "extractor": r"(?:cidade e|cidade para|moro em)\s+([A-Za-z\s]+)",
    },

    # ═══ MEMORIA VISUAL ═══
    "visual_status": {
        "exemplos": [
            "status do pendrive", "espaco do pendrive",
            "status da memoria visual", "memoria visual",
            "quantas capturas tenho", "status pen drive",
            "pendrive status", "memoria visual status",
        ],
        "keywords": ["pendrive", "pen drive", "memoria visual",
                      "quantas capturas"],
        "blockers": [],
    },
    "visual_buscar_horario": {
        "exemplos": [
            "o que eu fazia as 14 horas", "o que eu fiz as 10",
            "o que eu via as 15", "estava fazendo as 12",
            "me mostra as 16 horas", "o que eu fiz ontem as 15",
            "o que eu fiz dia 19 as 19", "o que eu fazia ontem",
            "memoria visual de ontem", "captura de ontem",
        ],
        "keywords": ["fazia as", "fiz as", "via as",
                      "estava fazendo as", "mostra as",
                      "fiz ontem", "fazia ontem", "vi ontem",
                      "captura de", "memoria de"],
        "blockers": ["pesquisar", "pesquise", "buscar", "google"],
        "extractor": r"(?:as|às)\s+(\d{1,2})(?::(\d{2}))?",
    },
    "visual_buscar_texto": {
        "exemplos": [
            "achei aquele tutorial", "qual aquele site",
            "lembra daquele video", "memoria visual sobre python",
        ],
        "keywords": ["achei aquele", "qual aquele",
                      "lembra daquele", "memoria visual sobre"],
        "blockers": ["pendrive", "pen drive", "horas"],
    },
    "visual_pausar": {
        "exemplos": [
            "pausa captura", "pausar captura", "para de gravar",
        ],
        "keywords": ["pausa captura", "pausar captura",
                      "para de gravar", "para de capturar"],
    },
    "visual_retomar": {
        "exemplos": ["retoma captura", "retomar captura", "volta a gravar"],
        "keywords": ["retoma captura", "retomar captura",
                      "volta captura", "ativa captura"],
    },

    # ═══ PESQUISA ═══
    "pesquisa_web": {
        "exemplos": [
            "pesquisar python tutorial", "me fala sobre einstein",
            "procura sobre cachorro", "o que e blockchain",
            "buscar receita de bolo",
        ],
        "keywords": ["pesquisar", "pesquisa", "procurar", "buscar",
                      "me fala sobre", "me conta sobre",
                      "o que e", "o que sabe sobre"],
        "blockers": ["youtube", "spotify", "lembre", "abra",
                      "horas", "amanha", "ontem", "fiz", "fazia",
                      "minha", "meu", "estava"],
    },
    "pesquisa_youtube": {
        "exemplos": [
            "youtube musica relax", "video de minecraft no youtube",
            "busca no youtube",
        ],
        "keywords": ["youtube"],
    },

    # ═══ CONTROLE PC ═══
    "app_abrir": {
        "exemplos": [
            "abrir spotify", "abre o chrome", "iniciar discord",
            "abrir notepad",
        ],
        "keywords": ["abrir", "abre", "abra", "iniciar", "executar",
                      "inicia", "roda"],
        "blockers": ["captura", "modo", "rotina", "tela", "olho"],
        "extractor": r"(?:abrir|abre|abra|iniciar|inicia|executar|roda)\s+(?:o |a |os |as )?(.+)",
    },
    "app_fechar": {
        "exemplos": ["fechar chrome", "encerrar discord"],
        "keywords": ["fechar", "fecha", "feche"],
        "blockers": ["jarvis", "tudo", "captura"],
    },
    "volume_set": {
        "exemplos": ["volume 50", "aumenta volume"],
        "keywords": ["volume", "muta", "mute"],
        "blockers": ["lembre"],
        "extractor": r"volume\s+(\d+)",
    },
    "brilho_set": {
        "exemplos": ["brilho 80", "aumenta brilho"],
        "keywords": ["brilho"],
        "extractor": r"brilho\s+(\d+)",
    },
    "bloquear_tela": {
        "exemplos": ["bloquear tela", "bloquear pc"],
        "keywords": ["bloquear tela", "bloquear pc", "trava o pc"],
    },
    "status_pc": {
        "exemplos": [
            "status do pc", "status do computador", "como esta o pc",
            "uso de cpu", "diagnostico", "uso de ram",
        ],
        "keywords": ["status do pc", "status computador",
                      "diagnostico", "uso de cpu", "uso de ram",
                      "status sistema"],
        "blockers": ["pendrive", "pen drive", "visual", "captura",
                      "memoria"],
    },

    # ═══ LEMBRETES ═══
    "lembrete_agendar": {
        "exemplos": [
            "me lembre em 5 minutos de tomar agua",
            "me avise em 10 minutos",
            "lembrete pra daqui 1 hora",
        ],
        "keywords": ["me lembre", "me lembra", "me avise", "lembrete"],
        "blockers": ["meus lembretes", "lista", "quantos"],
        "extractor": r"(?:em|daqui)\s+(\d+)\s*(segundo|minuto|hora)s?\s+(?:de|para|que)?\s*(.+)",
    },
    "lembrete_listar": {
        "exemplos": [
            "meus lembretes", "lista de lembretes", "agendamentos",
            "meus lembre", "quais meus lembretes",
        ],
        "keywords": ["meus lembretes", "meus lembre",
                      "lista lembretes", "agendamentos",
                      "quais meus lembretes"],
    },
    "pomodoro": {
        "exemplos": ["pomodoro", "inicia pomodoro"],
        "keywords": ["pomodoro"],
    },

    # ═══ MODOS ═══
    "modo_executar": {
        "exemplos": [
            "vou jogar minecraft", "vou dormir", "preparar pc",
            "modo trabalho", "preciso focar", "vou gravar",
        ],
        "keywords": ["vou jogar", "vou dormir", "vou gravar",
                      "preparar pc", "preciso focar"],
        "blockers": [],
    },
    "modos_listar": {
        "exemplos": ["lista de modos", "quais modos"],
        "keywords": ["lista de modos", "quais modos",
                      "modos disponiveis"],
    },

    # ═══ VISAO ═══
    "visao_ler_tela": {
        "exemplos": [
            "o que tem na tela", "le a tela", "o que ta escrito",
            "leia a tela pra mim", "descreve a tela",
        ],
        "keywords": ["o que tem na tela", "le a tela",
                      "leia a tela", "o que ta escrito",
                      "descreve a tela", "descreva a tela"],
    },
    "visao_foto": {
        "exemplos": ["tira uma foto", "fotografa"],
        "keywords": ["tira foto", "tirar foto", "fotografa",
                      "tira uma foto"],
    },

    # ═══ CONTEXTO ═══
    "contexto_atividade": {
        "exemplos": [
            "o que estou fazendo", "qual app to usando",
            "atividade atual",
        ],
        "keywords": ["o que estou fazendo", "qual app",
                      "atividade atual"],
    },
    "contexto_top_apps": {
        "exemplos": ["app mais usado", "top apps"],
        "keywords": ["app mais usado", "top apps",
                      "apps mais usados"],
    },
    "contexto_resumo": {
        "exemplos": ["resumo do dia", "como foi meu dia"],
        "keywords": ["resumo do dia", "como foi meu dia",
                      "o que fiz hoje"],
    },

    # ═══ MEMORIA EXPLICITA ═══
    "memoria_lembrar": {
        "exemplos": [
            "lembre disso meu aniversario e 10 de maio",
            "guarde isso senha do wifi e 1234",
        ],
        "keywords": ["lembre disso", "guarde isso", "anote isso",
                      "memoriza isso", "salva isso"],
    },
    "memoria_stats": {
        "exemplos": ["quantas memorias voce tem", "quantas memorias"],
        "keywords": ["quantas memorias", "tamanho da memoria"],
    },

    # ═══ MUSICA ═══
    "musica_tocar": {
        "exemplos": ["toca uma musica", "coloca uma musica"],
        "keywords": ["toca musica", "toca uma musica",
                      "coloca musica", "bota musica"],
        "blockers": ["abrir", "abre", "abra"],
    },


    # ═══ MINECRAFT BOT ═══
    "mc_iniciar": {
        "exemplos": [
            "entra no minecraft", "entra no meu mundo",
            "bota o jarvis no jogo", "vai jogar minecraft comigo",
            "se conecta no mine",
        ],
        "keywords": ["entra no minecraft", "entra no mundo",
                      "no minecraft jarvis", "conecta no mine",
                      "joga minecraft comigo"],
        "blockers": ["sai", "para"],
    },
    "mc_parar": {
        "exemplos": [
            "sai do minecraft", "para de jogar",
            "desconecta do mine",
        ],
        "keywords": ["sai do minecraft", "desconecta minecraft",
                      "para de jogar"],
    },
    "mc_status": {
        "exemplos": [
            "status do bot", "como ta o jarvis no jogo",
            "vida do bot", "onde voce ta no mine",
        ],
        "keywords": ["status do bot", "vida do bot", "como ta no mine",
                      "onde voce ta no jogo"],
    },
    "mc_comando": {
        "exemplos": [
            "vem aqui no jogo", "me segue no mine",
            "cava aqui", "para de andar", "pula no jogo",
            "o que tem no inventario", "coordenadas suas",
        ],
        "keywords": ["vem aqui", "me segue no mine", "cava aqui",
                      "pula no jogo", "no inventario",
                      "suas coordenadas no jogo"],
    },


    "esp32_status": {
        "exemplos": [
            "status do esp", "status do esp32", "status do deck",
            "esp conectado", "esp32 online", "deck conectado",
            "ip do esp",
        ],
        "keywords": ["status do esp", "esp32", "status deck",
                      "deck conectado", "ip do esp"],
    },


    "musica_proxima": {
        "exemplos": ["proxima musica", "pula musica", "next"],
        "keywords": ["proxima musica", "pula musica", "musica seguinte"],
    },
    "musica_pausar": {
        "exemplos": ["pausa musica", "pausar musica"],
        "keywords": ["pausa musica", "pausar musica"],
    },
    "musica_anterior": {
        "exemplos": ["musica anterior", "volta musica"],
        "keywords": ["musica anterior", "volta musica", "musica passada"],
    },


    "palmas_desativar": {
        "exemplos": [
            "desativa palmas", "desliga palmas", "para de ouvir palmas",
            "ignora palmas", "palmas off",
        ],
        "keywords": ["desativa palmas", "desliga palmas",
                      "ignora palmas", "palmas off",
                      "para de ouvir palmas"],
    },
    "palmas_ativar": {
        "exemplos": [
            "ativa palmas", "liga palmas", "volta a ouvir palmas",
            "palmas on",
        ],
        "keywords": ["ativa palmas", "liga palmas",
                      "palmas on", "volta a ouvir palmas"],
    },


    "visual_lista_dia": {
        "exemplos": [
            "lista capturas de ontem", "tudo que fiz ontem",
            "todas capturas de ontem", "o que fiz hoje",
            "capturas de hoje", "tudo de ontem",
        ],
        "keywords": ["tudo que fiz", "todas capturas", "lista capturas",
                      "capturas de", "tudo de ontem", "tudo de hoje"],
        "blockers": ["as ", "às "],
    },


    # ═══ LEGIAO DE FERRO ═══
    "legiao_criar": {
        "exemplos": [
            "cria legiao de 10", "criar legiao de ferro 15",
            "spawna 10 soldados", "monta legiao de 5",
            "invoca legiao de ferro 20",
        ],
        "keywords": ["cria legiao", "criar legiao", "monta legiao",
                      "spawna legiao", "invoca legiao",
                      "spawna soldados", "criar soldados",
                      "chama tropa", "monta tropa", "cria tropa",
                      "chama exercito", "invoca exercito",
                      "manda soldados", "spawna bots",
                      "cria legiao de ferro"],
        "extractor": r"(?:de\s+)?(\d+)",
    },
    "legiao_adicionar": {
        "exemplos": [
            "adiciona 5 na legiao", "manda mais 10 soldados",
            "reforco de 5", "envia reforco de 10",
        ],
        "keywords": ["adiciona", "manda mais", "reforco",
                      "mais soldados", "envia mais"],
        "extractor": r"(\d+)",
    },
    "legiao_status": {
        "exemplos": [
            "status da legiao", "como ta a legiao",
            "quantos soldados", "legiao status",
        ],
        "keywords": ["status da legiao", "como ta a legiao",
                      "quantos soldados", "legiao status",
                      "vida da legiao", "estado da legiao"],
    },
    "legiao_seguir": {
        "exemplos": [
            "legiao me segue", "legiao segue", "soldados sigam",
            "tropa segue",
        ],
        "keywords": ["legiao segue", "legiao me segue",
                      "soldados sigam", "tropa segue"],
    },
    "legiao_parar": {
        "exemplos": [
            "legiao parar", "legiao para", "soldados parem",
            "tropa congela",
        ],
        "keywords": ["legiao parar", "legiao para",
                      "soldados parem", "tropa congela",
                      "legiao congela"],
    },
    "legiao_defender": {
        "exemplos": [
            "legiao defender", "legiao defende",
            "formacao defensiva", "soldados em formacao",
        ],
        "keywords": ["legiao defender", "legiao defende",
                      "formacao defensiva", "soldados em formacao",
                      "legiao protege"],
    },
    "legiao_atacar": {
        "exemplos": [
            "legiao atacar steve", "legiao ataca BlockMC",
            "soldados matem joao", "tropa eliminar pedro",
        ],
        "keywords": ["legiao atacar", "legiao ataca",
                      "soldados matem", "tropa eliminar",
                      "legiao mata"],
        "extractor": r"(?:atacar|ataca|matem|eliminar|mata)\s+(\w+)",
    },
    "legiao_voltar": {
        "exemplos": [
            "legiao voltar", "legiao volta pra mim",
            "soldados voltem", "tropa recuar",
        ],
        "keywords": ["legiao voltar", "legiao volta",
                      "soldados voltem", "tropa recuar",
                      "legiao recua"],
    },
    "legiao_resetar": {
        "exemplos": [
            "reseta legiao", "resetar legiao",
            "limpa legiao", "limpar legiao",
            "zera legiao",
        ],
        "keywords": ["reseta legiao", "resetar legiao",
                      "limpa legiao", "limpar legiao",
                      "zera legiao", "zerar legiao"],
    },

    "legiao_proteger": {
        "exemplos": [
            "legiao protege BlockMC387", "protege amigo",
            "legiao proteger fulano",
        ],
        "keywords": ["legiao protege", "legiao proteger",
                      "protege amigo", "proteger amigo"],
        "extractor": r"proteger?\s+(\w+)",
    },

    "legiao_dispersar": {
        "exemplos": [
            "legiao dispersar", "dispersa a legiao",
            "manda legiao embora", "encerra legiao",
        ],
        "keywords": ["legiao dispersar", "dispersa legiao",
                      "manda legiao embora", "encerra legiao",
                      "fim da legiao"],
    },


    # ═══ MC SERVER LOCAL ═══
    "mc_server_iniciar": {
        "exemplos": [
            "liga servidor", "liga o servidor",
            "ligar servidor minecraft", "ligar o servidor",
            "inicia servidor", "inicia o servidor",
            "abre servidor", "abre o servidor",
            "sobe servidor mc", "sobe o servidor",
            "abrir servidor", "iniciar servidor",
            "ativa servidor", "ativar o servidor",
            "liga servidor mc", "liga o mc",
        ],
        "keywords": ["liga servidor", "liga o servidor",
                      "ligar servidor", "ligar o servidor",
                      "inicia servidor", "inicia o servidor",
                      "iniciar servidor",
                      "abre servidor", "abre o servidor",
                      "abrir servidor",
                      "sobe servidor", "sobe o servidor",
                      "subir servidor",
                      "ativa servidor", "ativar servidor",
                      "liga mc", "liga o mc",
                      "starta servidor", "start servidor"],
        "blockers": ["desliga", "desligar", "para servidor",
                      "parar servidor", "encerra", "fecha"],
    },
    "mc_server_parar": {
        "exemplos": [
            "desliga servidor", "desliga o servidor",
            "para servidor", "para o servidor",
            "encerra servidor minecraft",
            "fecha servidor", "fecha o servidor",
            "desligar servidor", "parar o servidor",
        ],
        "keywords": ["desliga servidor", "desliga o servidor",
                      "desligar servidor",
                      "para servidor", "para o servidor",
                      "parar servidor",
                      "encerra servidor", "encerrar servidor",
                      "fecha servidor", "fechar servidor"],
        "blockers": ["liga ", "ligar ", "inicia ", "iniciar ",
                      "abre ", "abrir ", "sobe ", "subir ",
                      "ativa", "ativar"],
    },
    "mc_server_status": {
        "exemplos": [
            "status do servidor", "servidor ta online",
            "quantos players no servidor",
        ],
        "keywords": ["status do servidor", "status servidor",
                      "servidor ta online", "servidor online",
                      "quantos players", "jogadores online"],
    },


    # ═══ CAMERAS IP ═══
    "camera_mostrar": {
        "exemplos": [
            "mostra camera sala", "mostra camera quintal",
            "abre camera sala", "ver camera",
            "camera do quintal", "camera da sala",
        ],
        "keywords": ["mostra camera", "abre camera",
                      "ver camera", "camera do",
                      "camera da", "ve a camera"],
        "blockers": ["fechar", "fecha", "todas"],
        "extractor": r"camera\s+(?:do|da|de)?\s*(\w+)",
    },
    "camera_todas": {
        "exemplos": [
            "mostra todas as cameras", "todas cameras",
            "ver todas as cameras", "abre todas cameras",
        ],
        "keywords": ["todas as cameras", "todas cameras",
                      "ver todas cameras", "abrir todas cameras"],
    },
    "camera_scan": {
        "exemplos": [
            "procura cameras", "scan de cameras",
            "buscar cameras na rede",
        ],
        "keywords": ["procura cameras", "scan cameras",
                      "buscar cameras", "achar cameras"],
    },
    "camera_listar": {
        "exemplos": [
            "lista de cameras", "quais cameras",
            "cameras configuradas",
        ],
        "keywords": ["lista cameras", "quais cameras",
                      "cameras configuradas", "minhas cameras"],
    },


    # ═══ LUZES TUYA ═══
    "luz_ligar": {
        "exemplos": [
            "acende a luz", "liga a luz", "acende a lampada",
            "acende luz do quarto", "liga luz da mae",
        ],
        "keywords": ["acende", "acender", "liga a luz", "liga luz",
                      "ligar luz", "ligar lampada"],
        "blockers": ["servidor", "minecraft", "esp32", "deck"],
        "extractor": r"(?:acende|acender|liga|ligar)\s+(?:a\s+)?(?:luz|lampada)?\s*(?:do|da)?\s*(\w+)?",
    },
    "luz_desligar": {
        "exemplos": [
            "apaga a luz", "desliga a luz", "apaga lampada",
            "apaga luz do quarto", "desliga luz mae",
        ],
        "keywords": ["apaga", "apagar", "desliga a luz",
                      "desligar luz", "apagar luz"],
        "blockers": ["servidor", "minecraft", "esp32"],
        "extractor": r"(?:apaga|apagar|desliga|desligar)\s+(?:a\s+)?(?:luz|lampada)?\s*(?:do|da)?\s*(\w+)?",
    },
    "luz_cor": {
        "exemplos": [
            "luz vermelha", "lampada azul", "muda a cor pra verde",
            "luz roxa", "cor amarela",
        ],
        "keywords": ["luz vermelha", "luz azul", "luz verde",
                      "luz roxa", "luz amarela", "luz rosa",
                      "luz branca", "luz laranja", "muda a cor",
                      "muda cor", "cor da luz", "lampada vermelha",
                      "lampada azul", "lampada verde", "lampada rosa"],
        "extractor": r"(?:luz|lampada|cor)\s*(?:pra|para)?\s*(\w+)",
    },
    "luz_brilho": {
        "exemplos": [
            "brilho 50", "luz 80 por cento", "lampada brilho 30",
        ],
        "keywords": ["brilho da luz", "brilho da lampada",
                      "luz brilho", "lampada brilho"],
        "extractor": r"(\d+)",
    },
    "cena_dormir": {
        "exemplos": [
            "modo dormir", "boa noite", "apaga tudo",
            "vou dormir luzes",
        ],
        "keywords": ["modo dormir", "boa noite luzes",
                      "apaga tudo", "apagar tudo",
                      "vou dormir"],
        "blockers": ["minecraft"],
    },
    "cena_acordar": {
        "exemplos": [
            "modo acordar", "bom dia luzes", "liga tudo",
        ],
        "keywords": ["modo acordar", "bom dia luzes",
                      "liga tudo", "ligar tudo"],
    },
    "cena_cinema": {
        "exemplos": [
            "modo cinema", "modo filme", "luz cinema",
        ],
        "keywords": ["modo cinema", "modo filme", "luz cinema"],
    },
    "cena_iron_man": {
        "exemplos": [
            "modo iron man", "modo stark",
        ],
        "keywords": ["modo iron man", "modo stark", "iron man"],
    },

    # ═══ SISTEMA ═══
    "jarvis_encerrar": {
        "exemplos": [
            "encerrar jarvis", "desligar jarvis", "tchau jarvis",
        ],
        "keywords": ["encerrar jarvis", "desligar jarvis",
                      "tchau jarvis", "fechar jarvis"],
    },
    "jarvis_reiniciar": {
        "exemplos": [
            "reinicia jarvis", "reiniciar jarvis", "reinicia",
            "reinicia ele", "reinicie", "reboot", "reiniciar sistema",
        ],
        "keywords": ["reiniciar jarvis", "reinicia jarvis", "reinicia",
                      "reinicie", "reboot", "reiniciar sistema"],
        "blockers": ["minecraft", "servidor", "bot"],
    },
    "jarvis_pausar_fala": {
        "exemplos": ["para de falar", "cala boca", "silencio"],
        "keywords": ["para de falar", "cala", "silencio",
                      "fica quieto"],
    },
    "jarvis_saudacao": {
        "exemplos": [
            "oi jarvis", "ola jarvis", "bom dia",
        ],
        "keywords": ["oi", "ola", "bom dia", "boa tarde",
                      "boa noite"],
        "blockers": ["abra", "abrir", "clima", "hora", "lembre"],
    },

    # ═══ DEV AGENT - ARQUIVOS E CODIGO ═══
    "dev_listar_pasta": {
        "exemplos": [
            "lista a pasta downloads", "o que tem nos downloads",
            "mostra a pasta documentos", "lista o desktop",
            "o que tem no pendrive", "lista a pasta jarvis",
            "abre a pasta videos", "explora downloads",
            "o que tem na pasta musicas",
        ],
        "keywords": [
            "lista a pasta", "lista o", "lista os",
            "o que tem na pasta", "o que tem nos",
            "o que tem no", "mostra a pasta",
            "explora pasta", "abre a pasta",
            "o que tem no desktop", "o que tem no pendrive",
        ],
        "blockers": ["mostra camera", "abre camera", "ver camera"],
        "extractor": r"(?:pasta|o que tem no?s?|lista o?s?|mostra a?|explora)\s+(\w+)",
    },

    "dev_ler_arquivo": {
        "exemplos": [
            "le o arquivo engine.py", "leia o brain.py",
            "mostra o conteudo do config.py",
            "abre o arquivo readme", "le o requirements.txt",
        ],
        "keywords": [
            "le o arquivo", "leia o arquivo",
            "mostra o conteudo", "abre o arquivo",
            "ler arquivo", "le o",
        ],
        "blockers": ["pasta", "downloads", "musicas"],
        "extractor": r"(?:le o|leia o|mostra o conteudo do?|abre o arquivo)\s+(\S+)",
    },

    "dev_mover_arquivo": {
        "exemplos": [
            "move o arquivo X para downloads",
            "mover foto para imagens",
            "transfere o video para o pendrive",
            "move os downloads pra pasta videos",
        ],
        "keywords": [
            "move o", "mover o", "mova o",
            "transfere o", "transferir o",
            "move arquivo", "mover arquivo",
        ],
        "blockers": [],
        "extractor": r"(?:move|mover|mova|transfere|transferir)\s+(?:o\s+)?(.+?)\s+(?:para|pra|pro)\s+(.+)",
    },

    "dev_organizar_downloads": {
        "exemplos": [
            "organiza os downloads", "organizar pasta downloads",
            "arruma os downloads", "organiza o download",
            "limpa os downloads", "organiza meus arquivos",
        ],
        "keywords": [
            "organiza os downloads", "organizar downloads",
            "arruma os downloads", "organiza downloads",
            "limpa downloads", "organiza arquivos",
        ],
        "blockers": [],
    },

    "dev_espaco_disco": {
        "exemplos": [
            "espaco no disco", "quanto tem no hd",
            "espaco livre no c", "quanto tem no pendrive",
            "espaco no drive e", "hd livre",
            "espaco no computador",
        ],
        "keywords": [
            "espaco no disco", "espaco livre",
            "quanto tem no hd", "espaco no hd",
            "hd livre", "espaco no drive",
            "espaco no computador", "espaco no pendrive",
        ],
        "blockers": ["pendrive jarvis", "memoria visual"],
        "extractor": r"(?:drive|disco|hd|pendrive)?\s*([a-eA-E])(?::|\\)?",
    },

    "dev_criar_modulo": {
        "exemplos": [
            "cria um modulo de notificacoes",
            "cria modulo de backup automatico",
            "faz um modulo de traducao",
            "cria um modulo novo de clima melhorado",
        ],
        "keywords": [
            "cria um modulo", "cria modulo",
            "faz um modulo", "novo modulo",
            "criar modulo",
        ],
        "blockers": [],
        "extractor": r"modulo\s+(?:de\s+)?(.+)",
    },

    "dev_tarefa_agente": {
        "exemplos": [
            "usa o openclaude pra organizar meu projeto",
            "pede pro agente melhorar o brain.py",
            "agente cria um bot do discord melhorado",
            "openclaude faz um servidor web simples",
            "usa o agente pra refatorar o router",
        ],
        "keywords": [
            "usa o openclaude", "openclaude",
            "pede pro agente", "usa o agente",
            "agente cria", "agente faz",
            "agente melhora",
        ],
        "blockers": [],
        "extractor": r"(?:openclaude|agente)\s+(?:pra|para|faz|cria|melhora)?\s*(.+)",
    },

    "dev_analisar_codigo": {
        "exemplos": [
            "analisa o engine.py", "analisa o brain.py",
            "melhora o router.py", "o que pode melhorar no brain",
            "analisa meu codigo", "revisa o codigo do engine",
        ],
        "keywords": [
            "analisa o", "analisar o",
            "melhora o", "melhorar o",
            "revisa o codigo", "o que pode melhorar",
        ],
        "blockers": ["modulo"],
        "extractor": r"(?:analisa o|analisar o|melhora o|melhorar o|revisa o codigo do?)\s+(\S+)",
    },

    "dev_drives": {
        "exemplos": [
            "quais drives tenho", "lista os drives",
            "drives disponiveis", "quais hds tenho",
            "quantos drives tem",
        ],
        "keywords": [
            "quais drives", "lista drives",
            "drives disponiveis", "quais hds",
            "quantos drives",
        ],
        "blockers": [],
    },

    # ═══ TURBO - CENTRAL DE COMANDO ═══
    "turbo_ativar": {
        "exemplos": [
            "ativa o modo turbo", "modo turbo", "turbo on",
            "ativar turbo", "entre no modo turbo",
        ],
        "keywords": ["modo turbo", "ativa turbo", "turbo on", "ativar turbo"],
        "blockers": [],
    },
    "turbo_desativar": {
        "exemplos": [
            "desativa o modo turbo", "turbo off", "sair do turbo",
        ],
        "keywords": ["desativa turbo", "turbo off", "sair do turbo", "modo normal"],
        "blockers": [],
    },
    "turbo_status": {
        "exemplos": [
            "status do sistema", "como ta o pc", "status completo",
            "informacoes do sistema", "relatorio do sistema",
        ],
        "keywords": ["status do sistema", "status completo", "relatorio", "como ta o pc"],
        "blockers": ["minecraft", "bot", "legiao"],
    },
    "turbo_analise": {
        "exemplos": [
            "analisa minha pasta projetos", "ver o que tem na pasta downloads",
            "olha essa pasta", "analisa o desktop", "analise de arquivos",
        ],
        "keywords": ["analisa", "analise", "olha a pasta", "ver pasta", "analisar pasta"],
        "blockers": ["minecraft", "bot"],
        "extractor": r"analise(?:r)?\s+(?:a\s+)?(?:pasta\s+)?(.+)",
    },
    "turbo_rotina": {
        "exemplos": [
            "ativa modo trabalho", "rotina de manha", "modo gamer",
            "modo noturno", "organiza tudo",
        ],
        "keywords": ["modo trabalho", "modo gamer", "modo noturno", "rotina", "organizar tudo"],
        "blockers": [],
        "extractor": r"(?:modo|rotina)\s+(\w+)",
    },
    "turbo_historico": {
        "exemplos": [
            "o que voce fez hoje", "historico de acoes", "ultimas acoes",
            "o que voce ja fez",
        ],
        "keywords": ["historico", "ultimas acoes", "o que fez", "o que voce fez"],
        "blockers": [],
    },

    # ═══ PRODUTIVIDADE ═══
    "prod_relatorio_dia": {
        "exemplos": [
            "criar relatório do dia", "gerar relatório diario",
            "relatório de hoje", "planilha do dia",
            "exportar atividades de hoje",
        ],
        "keywords": ["relatório do dia", "relatório diario", "planilha do dia",
                      "criar relatório", "gerar relatório"],
        "blockers": ["semana", "semanal", "gastos", "memória", "memorias"],
    },
    "prod_resumo_dia": {
        "exemplos": [
            "resumo do dia", "o que fiz hoje", "minha produtividade",
            "como foi meu dia", "resumo diario",
        ],
        "keywords": ["resumo do dia", "resumo diario", "o que fiz hoje",
                      "minha produtividade", "como foi meu dia"],
        "blockers": ["semana", "semanal", "relatório"],
    },
    "prod_resumo_semana": {
        "exemplos": [
            "resumo da semana", "resumo semanal", "minha semana",
            "como foi minha semana", "produção da semana",
        ],
        "keywords": ["resumo da semana", "resumo semanal", "minha semana",
                      "como foi minha semana", "produção da semana"],
        "blockers": ["dia", "diario", "hoje"],
    },
    "prod_exportar_memorias": {
        "exemplos": [
            "exportar memórias", "exportar memorias",
            "salvar memórias em planilha", "memórias em csv",
        ],
        "keywords": ["exportar memórias", "exportar memorias",
                      "memórias em planilha", "memórias em csv"],
        "blockers": [],
    },
    "prod_tempo_focado": {
        "exemplos": [
            "tempo focado hoje", "quanto tempo foquei",
            "horas produtivas", "meu foco hoje",
        ],
        "keywords": ["tempo focado", "horas produtivas", "meu foco",
                      "quanto tempo foquei"],
        "blockers": [],
    },
    "prod_gasto_adicionar": {
        "exemplos": [
            "adicionar gasto almoço 25", "gasto uber 15 reais",
            "registra gasto mercado 80", "anota gasto lanche 10",
            "gasto de 50 no shop",
        ],
        "keywords": ["adicionar gasto", "gasto", "registra gasto",
                      "anota gasto", "gasto de"],
        "blockers": ["listar", "mostrar", "planilha", "relatório"],
        "extractor": r"(?:adicionar gasto|gasto|registra gasto|anota gasto)\s+(.+?)(?:\s+(\d+(?:[.,]\d+)?)\s*(?:reais|R\$?)?)?$",
    },
    "prod_gasto_listar": {
        "exemplos": [
            "listar gastos", "mostrar gastos", "meus gastos",
            "quanto gastei", "gastos recentes",
        ],
        "keywords": ["listar gastos", "mostrar gastos", "meus gastos",
                      "quanto gastei", "gastos recentes"],
        "blockers": ["adicionar", "registrar", "planilha"],
    },
    "prod_planilha_gastos": {
        "exemplos": [
            "planilha de gastos", "gerar planilha de gastos",
            "excel de gastos", "exportar gastos",
        ],
        "keywords": ["planilha de gastos", "gerar planilha de gastos",
                      "excel de gastos", "exportar gastos"],
        "blockers": ["adicionar", "listar"],
    },
    "prod_listar_relatorios": {
        "exemplos": [
            "listar relatórios", "mostrar relatórios",
            "quais relatórios tenho", "relatórios salvos",
        ],
        "keywords": ["listar relatórios", "mostrar relatórios",
                      "relatórios salvos", "quais relatórios"],
        "blockers": ["criar", "gerar"],
    },

    # ═══ CELULAR ═══
    "cel_status": {
        "exemplos": [
            "status do celular", "informações do celular",
            "que celular tenho", "modelo do celular",
        ],
        "keywords": ["status do celular", "informações do celular",
                      "modelo do celular", "que celular"],
        "blockers": ["bateria", "notificação", "sms"],
    },
    "cel_notificacoes": {
        "exemplos": [
            "ler notificações do celular", "notificações do celular",
            "o que tem no celular", "notificações",
        ],
        "keywords": ["notificações do celular", "ler notificações",
                      "notificações"],
        "blockers": ["sms", "bateria"],
    },
    "cel_abrir_app": {
        "exemplos": [
            "abrir instagram no celular", "abre o whatsapp",
            "abrir youtube no celular", "abrir app",
        ],
        "keywords": ["abrir", "abre", "abrir no celular", "abre no celular"],
        "blockers": ["fechar", "status", "bateria", "listar"],
        "extractor": r"(?:abrir|abre)\s+(?:o\s+|a\s+)?(\w+)(?:\s+no\s+celular)?",
    },
    "cel_listar_apps": {
        "exemplos": [
            "listar apps do celular", "quais apps tenho",
            "apps instalados", "lista de apps",
        ],
        "keywords": ["listar apps", "quais apps", "apps instalados", "lista de apps"],
        "blockers": ["abrir", "fechar"],
    },
    "cel_fechar_app": {
        "exemplos": [
            "fechar instagram no celular", "fecha o whatsapp",
            "fechar app no celular",
        ],
        "keywords": ["fechar app", "fecha o", "fechar no celular"],
        "blockers": ["abrir", "listar"],
        "extractor": r"(?:fechar|fecha)\s+(?:o\s+|a\s+)?(\w+)(?:\s+no\s+celular)?",
    },
    "cel_bateria": {
        "exemplos": [
            "bateria do celular", "quanto de bateria",
            "nível da bateria", "bateria",
        ],
        "keywords": ["bateria do celular", "bateria", "quanto de bateria"],
        "blockers": ["notificação", "sms", "status"],
    },
    "cel_volume": {
        "exemplos": [
            "volume do celular 10", "volume do celular",
            "aumentar volume do celular", "diminuir volume",
        ],
        "keywords": ["volume do celular", "volume", "aumentar volume", "diminuir volume"],
        "blockers": ["notificação", "bateria"],
        "extractor": r"volume(?:\s+do\s+celular)?\s*(\d+|[+\-])?",
    },
    "cel_wifi": {
        "exemplos": [
            "wi-fi do celular", "ligar wi-fi do celular",
            "desligar wi-fi", "status do wi-fi",
        ],
        "keywords": ["wi-fi do celular", "wifi", "ligar wi-fi", "desligar wi-fi"],
        "blockers": ["notificação", "bateria", "bluetooth"],
    },
    "cel_bluetooth": {
        "exemplos": [
            "bluetooth do celular", "ligar bluetooth",
            "desligar bluetooth", "status bluetooth",
        ],
        "keywords": ["bluetooth do celular", "bluetooth", "ligar bluetooth"],
        "blockers": ["notificação", "bateria", "wi-fi"],
    },
    "cel_screenshot": {
        "exemplos": [
            "tirar screenshot do celular", "captura de tela do celular",
            "print do celular", "screenshot",
        ],
        "keywords": ["screenshot", "captura de tela", "print do celular"],
        "blockers": [],
    },
    "cel_localizar": {
        "exemplos": [
            "onde tá meu celular", "procurar celular",
            "faz meu celular tocar", "localizar celular",
        ],
        "keywords": ["onde tá meu celular", "procurar celular", "localizar celular",
                      "faz tocar"],
        "blockers": [],
    },
    "cel_sms_enviar": {
        "exemplos": [
            "enviar sms para 123456789 oi tudo bem",
            "mandar sms 999999999 olá",
            "sms para 111111111 teste",
        ],
        "keywords": ["enviar sms", "mandar sms", "sms para"],
        "blockers": ["ler", "ler sms"],
        "extractor": r"(?:enviar sms|mandar sms|sms\s+para)\s+(\d+)\s+(.+)",
    },
    "cel_sms_ler": {
        "exemplos": [
            "ler sms recentes", "ler mensagens",
            "sms recebidos", "ver sms",
        ],
        "keywords": ["ler sms", "sms recentes", "mensagens", "sms recebidos"],
        "blockers": ["enviar", "mandar"],
    },
    "cel_transferir": {
        "exemplos": [
            "transferir arquivo para o celular",
            "enviar arquivo para celular",
            "copiar para o celular",
        ],
        "keywords": ["transferir arquivo", "enviar arquivo", "copiar para celular"],
        "blockers": ["receber", "baixar"],
        "extractor": r"(?:transferir|enviar|copiar)\s+arquivo\s+(.+?)(?:\s+para\s+(?:o\s+)?celular)?$",
    },

    # ═══ TV SAMSUNG ═══
    "tv_ligar": {
        "exemplos": [
            "ligar a tv", "ligar televisão", "liga a tv",
            "ligar samsung", "liga a televisão",
        ],
        "keywords": ["ligar a tv", "liga a tv", "ligar televisão", "ligar samsung"],
        "blockers": ["desligar", "volume", "canal"],
    },
    "tv_desligar": {
        "exemplos": [
            "desligar a tv", "desligar televisão", "desliga a tv",
            "desligar samsung",
        ],
        "keywords": ["desligar a tv", "desliga a tv", "desligar televisão"],
        "blockers": ["ligar", "volume", "canal"],
    },
    "tv_volume": {
        "exemplos": [
            "volume da tv 20", "volume da televisão",
            "aumentar volume da tv", "diminuir volume da tv",
        ],
        "keywords": ["volume da tv", "volume da televisão", "volume da samsung"],
        "blockers": ["canal", "ligar", "desligar"],
        "extractor": r"volume(?:\s+da\s+(?:tv|televisão|samsung))?\s*(\d+|[+\-])?",
    },
    "tv_mutar": {
        "exemplos": [
            "mutar a tv", "mudo da tv", "mutar televisão",
        ],
        "keywords": ["mutar a tv", "mudo da tv", "mutar televisão"],
        "blockers": ["volume", "canal"],
    },
    "tv_canal": {
        "exemplos": [
            "canal 5", "mudar para o canal 10", "canal da tv",
            "próximo canal", "canal anterior",
        ],
        "keywords": ["canal", "mudar canal", "próximo canal", "canal anterior"],
        "blockers": ["volume", "ligar", "desligar", "hdmi"],
        "extractor": r"(?:canal|频道)\s*(\d+)?",
    },
    "tv_input": {
        "exemplos": [
            "mudar para hdmi1", "entrada hdmi2", "tv input",
            "mudar para tv", "fonte de entrada",
        ],
        "keywords": ["hdmi", "entrada", "input", "fonte", "mudar para hdmi"],
        "blockers": ["volume", "canal", "ligar"],
    },
    "tv_status": {
        "exemplos": [
            "status da tv", "tv ligada", "está ligada a tv",
        ],
        "keywords": ["status da tv", "tv ligada", "está ligada"],
        "blockers": ["volume", "canal", "ligar", "desligar"],
    },
    "tv_play": {
        "exemplos": [
            "play da tv", "play tv", "iniciar tv",
        ],
        "keywords": ["play da tv", "play tv", "iniciar tv"],
        "blockers": ["pause", "stop"],
    },
    "tv_pause": {
        "exemplos": [
            "pause da tv", "pausar tv", "pause tv",
        ],
        "keywords": ["pause da tv", "pausar tv", "pause tv"],
        "blockers": ["play", "stop"],
    },
    "tv_home": {
        "exemplos": [
            "home da tv", "menu da tv", "home samsung",
        ],
        "keywords": ["home da tv", "menu da tv", "home samsung"],
        "blockers": ["volume", "canal"],
    },
    "tv_navegar": {
        "exemplos": [
            "seta da tv pra cima", "navegar na tv",
            "seta pra direita na tv", "confirmar na tv",
        ],
        "keywords": ["seta da tv", "navegar na tv", "confirmar na tv"],
        "blockers": ["volume", "canal"],
        "extractor": r"(?:seta|navegar)\s+(?:da\s+tv\s+)?(?:pra\s+|para\s+)?(cima|baixo|esquerda|direita|ok|enter|confirmar)",
    },

    # ═══ SEGURANCA ═══
    "seg_senha_definir": {
        "exemplos": [
            "definir senha 1234", "criar senha",
            "definir senha do jarvis", "nova senha",
        ],
        "keywords": ["definir senha", "criar senha", "nova senha"],
        "blockers": ["desbloquear", "verificar"],
        "extractor": r"(?:definir|criar|nova)\s+senha\s+(.+)",
    },
    "seg_desbloquear": {
        "exemplos": [
            "desbloquear 1234", "desbloquear jarvis",
            "desbloquear sistema",
        ],
        "keywords": ["desbloquear"],
        "blockers": ["definir", "criar"],
        "extractor": r"desbloquear\s+(.+)",
    },
    "seg_status": {
        "exemplos": [
            "status de segurança", "segurança do sistema",
            "status segurança",
        ],
        "keywords": ["status de segurança", "segurança"],
        "blockers": ["desbloquear", "definir"],
    },
    "seg_logs": {
        "exemplos": [
            "quem usou o pc", "listar logs",
            "log de acessos", "historico de uso",
        ],
        "keywords": ["quem usou", "listar logs", "log de acessos", "historico de uso"],
        "blockers": ["definir", "desbloquear"],
    },
    "seg_rede": {
        "exemplos": [
            "dispositivos na rede", "scan de rede",
            "quem ta na minha rede",
        ],
        "keywords": ["dispositivos na rede", "scan de rede", "quem ta na rede"],
        "blockers": ["portas"],
    },
    "seg_portas": {
        "exemplos": [
            "verificar portas", "portas abertas",
            "quais portas abertas",
        ],
        "keywords": ["verificar portas", "portas abertas"],
        "blockers": ["rede"],
    },

    # ═══ ENTRETENIMENTO ═══
    "entre_jogo": {
        "exemplos": [
            "jogar adivinha", "iniciar jogo",
            "jogo da adivinhação",
        ],
        "keywords": ["jogar", "iniciar jogo", "jogo da adivinhação"],
        "blockers": ["adivinhar", "responder"],
    },
    "entre_adivinhar": {
        "exemplos": [
            "adivinhar 50", "chute 25",
            "meu palpite é 75",
        ],
        "keywords": ["adivinhar", "chute", "palpite"],
        "blockers": ["jogar", "iniciar"],
        "extractor": r"(?:adivinhar|chute|palpite\s+(?:e|é)?)\s*(\d+)",
    },
    "entre_quiz": {
        "exemplos": [
            "quiz", "pergunta",
            "jogo de perguntas",
        ],
        "keywords": ["quiz", "pergunta", "jogo de perguntas"],
        "blockers": ["responder", "adivinhar"],
    },
    "entre_responder": {
        "exemplos": [
            "responder paris", "minha resposta é 42",
        ],
        "keywords": ["responder", "minha resposta"],
        "blockers": ["quiz", "pergunta"],
        "extractor": r"(?:responder|minha\s+resposta\s+(?:e|é)?)\s+(.+)",
    },
    "entre_piada": {
        "exemplos": [
            "me conta uma piada", "piada",
            "conta uma piada", "me faz rir",
        ],
        "keywords": ["piada", "conta uma piada", "me faz rir"],
        "blockers": ["quiz", "jogo"],
    },
    "entre_curiosidade": {
        "exemplos": [
            "curiosidade", "fato curioso",
            "me conta um fato",
        ],
        "keywords": ["curiosidade", "fato curioso", "me conta um fato"],
        "blockers": ["piada", "quiz"],
    },
    "entre_filme": {
        "exemplos": [
            "recomendar filme", "o que assistir",
            "me indica um filme",
        ],
        "keywords": ["recomendar filme", "o que assistir", "me indica"],
        "blockers": ["piada", "quiz"],
        "extractor": r"(?:recomendar|indicar|assistir)\s+(?:um\s+)?(?:filme\s+)?(?:de\s+)?(\w+)?",
    },
    "entre_frase": {
        "exemplos": [
            "frase famosa", "frase motivacional",
            "me inspira",
        ],
        "keywords": ["frase famosa", "frase motivacional", "me inspira"],
        "blockers": ["piada", "quiz"],
    },
}


def get_todos_exemplos():
    out = []
    for nome, dados in INTENTS.items():
        for ex in dados.get("exemplos", []):
            out.append((nome, ex))
    return out


def get_intent(nome):
    return INTENTS.get(nome)


def get_keywords(nome):
    intent = INTENTS.get(nome, {})
    return intent.get("keywords", []) + intent.get("extra_keywords", [])


def get_blockers(nome):
    return INTENTS.get(nome, {}).get("blockers", [])


def extrair_parametro(nome, texto):
    intent = INTENTS.get(nome)
    if not intent or "extractor" not in intent:
        return None
    m = re.search(intent["extractor"], texto, re.IGNORECASE)
    if m:
        return m.groups() if m.groups() else m.group(0)
    return None

