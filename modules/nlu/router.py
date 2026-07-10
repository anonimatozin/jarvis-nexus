# -*- coding: utf-8 -*-
"""
Router NLU v4 - Arquitetura de Fluxo Unificado
- Multi-comando Paralelo (Threading)
- Whitelist de intents rapidos expandida
- Pre-processadores prioritarios
- Backup automatico
"""

import os
import re
import sys
import time
import shutil
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Backups
def _fazer_backup(caminho):
    try:
        p = Path(caminho)
        if not p.exists(): return
        bkp_dir = p.parent / "backups_nlu"
        bkp_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(str(p), str(bkp_dir / f"{p.name}.{ts}.bak"))
    except Exception as e:
        print(f"[BACKUP ERROR] {e}")

_fazer_backup(__file__)

from modules.nlu.intent_classifier import (
    classificar, separar_multi_comando
)
from modules.nlu.composer import compor_respostas
from utils.logger import print_error

# ═══ NIVEIS DE SEGURANCA ═══
# Nivel 1: INFORMAR - so informa o que encontrou
# Nivel 2: SUGERIR - pergunta antes de executar
# Nivel 3: EXECUTAR - executa direto (requer confirmacao pra acoes destrutivas)

# Operacoes que REQUEREM confirmacao (nivel 2)
OPERACOES_PERIGOSAS = {
    "deletar", "excluir", "apagar", "remover",
    "formatar", "reiniciar", "desligar", "encerrar",
    "fechar_processo", "matar_processo",
}

# Operacoes que sao somente leitura (nivel 1)
OPERACOES_SEGURAS = {
    "status", "clima", "hora", "data", "pesquisar",
    "listar", "mostrar", "ver", "ler", "analisar",
    "horas", "atividade", "resumo", "memoria",
}

def nivel_seguranca(texto):
    """Determina nivel de seguranca de um comando."""
    tl = texto.lower().strip()
    for op in OPERACOES_PERIGOSAS:
        if op in tl:
            return 2  # requer confirmacao
    for op in OPERACOES_SEGURAS:
        if op in tl:
            return 1  # somente leitura
    return 1  # default: seguro

# Whitelist de intents que NUNCA devem ir para o Brain (execucao imediata)
INTENTS_RAPIDOS = [
    'hora_atual', 'data_atual', 'clima_atual', 'clima_chover', 'clima_amanha', 
    'clima_cidade', 'localizacao_minha', 'localizacao_atualizar', 'localizacao_mudar', 
    'luz_ligar', 'luz_desligar', 'luz_cor', 'luz_brilho', 'cena_dormir', 
    'cena_acordar', 'cena_cinema', 'cena_iron_man', 'mc_iniciar', 'mc_parar', 
    'mc_status', 'mc_comando', 'mc_server_iniciar', 'mc_server_parar', 
    'mc_server_status', 'legiao_criar', 'legiao_adicionar', 'legiao_status', 
    'legiao_seguir', 'legiao_parar', 'legiao_defender', 'legiao_atacar', 
    'legiao_voltar', 'legiao_resetar', 'legiao_proteger', 'legiao_dispersar', 
    'esp32_status', 'palmas_ativar', 'palmas_desativar', 'musica_proxima', 
    'musica_pausar', 'musica_anterior', 'musica_tocar', 'lembrete_agendar', 
    'lembrete_listar', 'pomodoro', 'volume_set', 'brilho_set', 'bloquear_tela', 
    'status_pc', 'visao_ler_tela', 'visao_foto', 'camera_mostrar', 'camera_todas', 
    'camera_scan', 'camera_listar', 'pesquisa_web', 'pesquisa_youtube',
    'app_abrir', 'app_fechar', 'jarvis_encerrar', 'jarvis_reiniciar', 'jarvis_saudacao',
    'turbo_ativar', 'turbo_desativar', 'turbo_status', 'turbo_analise',
    'turbo_rotina', 'turbo_historico',
    'calcular', 'timer', 'listar_timers', 'lembrete', 'listar_lembretes',
    'info_sistema', 'top_processos', 'limpar_tela', 'limpar_terminal',
    'mostrar_agenda', 'mostrar_historico',
    'desligar_pc', 'cancelar_desligamento',
    'abrir_explorer', 'fechar_tudo',
    'prod_relatorio_dia', 'prod_resumo_dia', 'prod_resumo_semana',
    'prod_exportar_memorias', 'prod_tempo_focado',
    'prod_gasto_adicionar', 'prod_gasto_listar', 'prod_planilha_gastos',
    'prod_listar_relatorios',
    'cel_status', 'cel_notificacoes', 'cel_abrir_app', 'cel_listar_apps',
    'cel_fechar_app', 'cel_bateria', 'cel_volume', 'cel_wifi',
    'cel_bluetooth', 'cel_screenshot', 'cel_localizar',
    'cel_sms_enviar', 'cel_sms_ler', 'cel_transferir',
    'tv_ligar', 'tv_desligar', 'tv_volume', 'tv_mutar', 'tv_canal',
    'tv_input', 'tv_status', 'tv_play', 'tv_pause', 'tv_home', 'tv_navegar',
    'seg_senha_definir', 'seg_desbloquear', 'seg_status', 'seg_logs',
    'seg_rede', 'seg_portas',
    'entre_jogo', 'entre_adivinhar', 'entre_quiz', 'entre_responder',
    'entre_piada', 'entre_curiosidade', 'entre_filme', 'entre_frase',
]

class NLURouter:
    def __init__(self, engine):
        self.engine = engine

    def rotear(self, texto):
        if not texto: return ""

        # PRIMEIRO: separa multi-comando
        partes = separar_multi_comando(texto)
        if len(partes) > 1:
            print(f"[NLU] Multi-comando: {len(partes)} partes")
            return self._executar_multi_paralelo(partes)

        # Comando unico: pre-processadores
        res_pre = self._rodar_pre_processadores(texto)
        if res_pre: return res_pre

        return self._processar_parte(texto)

    def _rodar_pre_processadores(self, texto):
        """Roda os matchers de regex prioritarios."""
        for func in [self._pre_luz, self._pre_app, self._pre_executar, self._pre_bot_mc, self._pre_servidor, self._pre_legiao]:
            try:
                res = func(texto)
                if res: return res
            except Exception as e:
                print(f"[PRE-PROC ERROR] {e}")
        return None

    def _executar_multi_paralelo(self, partes):
        """Executa comandos em paralelo com timeout."""
        respostas = []
        partes_validas = [p.strip() for p in partes if p.strip()]
        if not partes_validas:
            return ""

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(partes_validas), 4)) as executor:
                future_to_part = {executor.submit(self._processar_parte_safe, p): p for p in partes_validas}

                for future in concurrent.futures.as_completed(future_to_part, timeout=30):
                    p = future_to_part[future]
                    try:
                        res = future.result(timeout=25)
                        if res:
                            respostas.append(res)
                    except concurrent.futures.TimeoutError:
                        print(f"[MULTI-PART TIMEOUT] '{p}'")
                        respostas.append(f"'{p}': tempo esgotado.")
                    except Exception as e:
                        print(f"[MULTI-PART ERROR] '{p}': {e}")
                        respostas.append(f"Erro em '{p}'.")
        except Exception as e:
            print(f"[MULTI EXEC ERROR] {e}")
            return "Tive um problema processando os comandos, Sir."

        return compor_respostas(respostas)

    def _processar_parte_safe(self, texto):
        """Wrapper seguro que nunca levanta excessão."""
        try:
            return self._processar_parte(texto)
        except Exception as e:
            print(f"[PART ERROR] '{texto}': {e}")
            return f"Erro ao processar '{texto}'."

    def _processar_parte(self, texto):
        """Processa uma unica intencao decidindo entre NLU Rapido ou ToolExecutor."""
        # Tenta pre-processador na parte especifica (ex: "acende a luz" dentro de um multi)
        pre = self._rodar_pre_processadores(texto)
        if pre: return pre

        # Classifica intent via Semantic/Keywords
        cls = classificar(texto, brain=self.engine.brain)
        intent = cls.get("intent", "outros")
        conf = cls.get("confidence", 0)

        # Decisao de Rota
        if intent in INTENTS_RAPIDOS and conf >= 0.45:
            print(f"[NLU RAPIDO] {intent} ({conf:.2f})")
            return self._executar_intent(cls, texto)
        
        # Fallback para Tool Executor (IA decide JSON)
        print(f"[NLU FALLBACK] Enviando para ToolExecutor: '{texto[:30]}...'")
        return self._fallback(texto)

    def _fallback(self, texto):
        """Chama ToolExecutor. Se falhar, conversa SEM fingir execucao."""
        e = self.engine

        # Tool Executor primeiro
        if hasattr(e, "tool_executor") and e.tool_executor:
            try:
                return e.tool_executor.processar(texto)
            except Exception as ex:
                print_error(f"[TOOL EXEC ERROR] {ex}")

        # Brain como fallback - mas avisado que nao pode executar
        if e.brain:
            VERBOS_ACAO = [
                "cria", "criar", "faz", "fazer", "abre", "abrir",
                "salva", "salvar", "executa", "executar", "instala",
                "deleta", "move", "organiza", "manda", "envia",
            ]
            tl = texto.lower()
            eh_acao = any(v in tl for v in VERBOS_ACAO)

            if eh_acao and hasattr(e.brain, "think_acao"):
                return e.brain.think_acao(texto)
            return e.brain.think(texto)

        return "Nao entendi, Sir."

    # --- MATCHERS DE REGEX (PRE-PROCESSADORES) ---

    def _pre_luz(self, texto):
        tl = texto.lower().strip()
        e = self.engine
        if not hasattr(e, "luzes") or not e.luzes: return None

        # Cenas
        if re.search(r"modo dormir|boa noite|apaga tudo", tl): return e.luzes.cena_dormir()
        if re.search(r"modo acordar|bom dia luzes|liga tudo", tl): return e.luzes.cena_acordar()
        if re.search(r"modo cinema|modo filme", tl): return e.luzes.cena_cinema()

        # Basico Ligar/Desligar/Cor
        if any(x in tl for x in ["luz", "lampada", "led", "abajur"]):
            # Ligar
            if re.search(r"\b(acend\w*|liga\w*)\b", tl):
                alvo = "quarto"
                if "mae" in tl: alvo = "mae"
                elif "rgb" in tl or "led" in tl: alvo = "lampada"
                ok, msg = e.luzes.ligar(alvo)
                return msg
            # Desligar
            if re.search(r"\b(apag\w*|desliga\w*)\b", tl):
                alvo = "quarto"
                if "mae" in tl: alvo = "mae"
                elif "rgb" in tl or "led" in tl: alvo = "lampada"
                ok, msg = e.luzes.desligar(alvo)
                return msg
        return None

    def _pre_bot_mc(self, texto):
        tl = texto.lower().strip()
        if "servidor" in tl: return None # Deixa pro pre_servidor
        if re.search(r"\b(entra|joga|inicia)\b.*\b(minecraft|mine|mc|jogo)\b", tl):
            return self._executar_intent({"intent": "mc_iniciar"}, texto)
        if re.search(r"\b(sai|parar|tira|fecha)\b.*\b(minecraft|mine|mc|bot)\b", tl):
            return self._executar_intent({"intent": "mc_parar"}, texto)
        return None

    def _pre_servidor(self, texto):
        tl = texto.lower().strip()
        if not "servidor" in tl and not "server" in tl: return None
        if re.search(r"\b(liga|inicia|abre|start)\b", tl):
            return self._executar_intent({"intent": "mc_server_iniciar"}, texto)
        if re.search(r"\b(desliga|para|fecha|encerra)\b", tl):
            return self._executar_intent({"intent": "mc_server_parar"}, texto)
        return None

    def _pre_legiao(self, texto):
        tl = texto.lower()
        if "legi" not in tl: return None
        m = re.search(r"de\s+(\d+)", tl)
        if m and "cria" in tl:
            return self._executar_intent({"intent": "legiao_criar", "parametros": m.group(1)}, texto)
        return None

    def _pre_app(self, texto):
        """Captura comandos de abrir app antes do classificador."""
        tl = texto.lower().strip()
        e = self.engine

        APPS_DIRETOS = {
            "spotify":    "spotify",
            "discord":    "discord",
            "chrome":     "chrome",
            "firefox":    "firefox",
            "notepad":    "notepad",
            "bloco de notas": "notepad",
            "calculadora": "calc",
            "steam":      "steam",
            "vscode":     "code",
            "vs code":    "code",
            "youtube":    "youtube",
            "netflix":    "netflix",
        }

        tem_verbo = re.search(
            r"\b(abre|abrir|abra|lanca|abre o|abre a|executa|inicia|starta)\b", tl
        )
        if not tem_verbo:
            return None

        for palavra, app in APPS_DIRETOS.items():
            if palavra in tl:
                print(f"[PRE-APP] Abrindo {app}")
                if not hasattr(e, "app_launcher") or not e.app_launcher:
                    import webbrowser
                    if app == "spotify":
                        webbrowser.open("https://open.spotify.com")
                        return "Abrindo Spotify, Sir."
                    return f"Launcher indisponivel, Sir."
                r = e.app_launcher.abrir(app)
                if r is True:
                    return f"Abrindo {app}, Sir."
                elif isinstance(r, str):
                    return r
                if app == "spotify":
                    import webbrowser
                    webbrowser.open("https://open.spotify.com")
                    return "Abrindo Spotify, Sir."
                return f"Tentando abrir {app}, Sir."

        return None

    def _pre_executar(self, texto):
        """Captura 'executa/roda esse script/o ultimo' antes do classificador."""
        tl = texto.lower().strip()
        e = self.engine

        # Verbos de executar
        if not re.search(r"\b(executa|execute|executar|roda|rodar|rode)\b", tl):
            return None

        # Se mencionou app especifico (spotify, chrome) - nao eh isso
        APPS = ["spotify", "chrome", "discord", "firefox", "steam"]
        if any(a in tl for a in APPS):
            return None

        # Executa ultimo / esse / o script
        if re.search(r"\b(ultimo|esse|este|o script|aquele|agora)\b", tl) or len(tl.split()) <= 3:
            if hasattr(e, "tool_executor") and e.tool_executor:
                print("[PRE-EXEC] executar_ultimo")
                return e.tool_executor._t_executar_ultimo({}, texto)

        return None

    # --- HANDLERS DE INTENTS (LOGICA DE EXECUCAO) ---

    def _executar_intent(self, cls, texto):
        intent = cls["intent"]
        params = cls.get("parametros")
        e = self.engine

        try:
            # HORA E DATA
            if intent == "hora_atual": return f"Sao {datetime.now().strftime('%H:%M')}, Sir."
            if intent == "data_atual": return f"Hoje e {datetime.now().strftime('%d/%m/%Y')}."

            # APPS
            if intent == "app_abrir":
                if not e.app_launcher: return "Launcher offline."
                nome = params if isinstance(params, str) else (params[0] if params else "")
                if not nome: 
                    m = re.search(r"(?:abre|abrir|executa)\s+(?:o\s+|a\s+)?(\w+)", texto.lower())
                    nome = m.group(1) if m else ""
                if nome:
                    r = e.app_launcher.abrir(nome)
                    return f"Abrindo {nome}, Sir." if r is True else (r if r else f"Nao achei {nome}.")
                return "O que abrir?"

            if intent == "app_fechar":
                nome = params if isinstance(params, str) else ""
                if not nome:
                    m = re.search(r"(?:fecha|fechar|mata|encerra|fecha o|fecha a)\s+(?:o\s+|a\s+)?(\w+)", texto.lower())
                    nome = m.group(1) if m else ""
                if nome:
                    import subprocess
                    # Mapeia nomes comuns pra executáveis corretos
                    MAPA_EXE = {
                        "discord": "Discord.exe",
                        "spotify": "Spotify.exe",
                        "chrome": "chrome.exe",
                        "firefox": "firefox.exe",
                        "steam": "steam.exe",
                        "obs": "obs64.exe",
                        "code": "Code.exe",
                        "vscode": "Code.exe",
                        "telegram": "telegram.exe",
                        "notepad": "notepad.exe",
                    }
                    exe = MAPA_EXE.get(nome.lower(), f"{nome}.exe")
                    try:
                        subprocess.run(
                            f"taskkill /f /im {exe}",
                            shell=True, capture_output=True, timeout=10
                        )
                    except subprocess.TimeoutExpired:
                        pass
                    return f"Fechando {nome}, Sir."
                return "Qual fechar?"

            # MUSICA
            if intent == "musica_tocar":
                import webbrowser
                webbrowser.open("https://open.spotify.com")
                return "Abrindo Spotify, Sir."
            
            if intent in ["musica_proxima", "musica_pausar", "musica_anterior"]:
                keys = {"musica_proxima": 176, "musica_pausar": 179, "musica_anterior": 177}
                import subprocess
                subprocess.run(["powershell", f"(New-Object -ComObject WScript.Shell).SendKeys([char]{keys[intent]})"], capture_output=True)
                return "Feito, Sir."

            # CLIMA (Simplificado para o Router)
            if "clima" in intent:
                from modules.clima import get_clima_atual, falar_clima_atual, extrair_cidade
                cidade = extrair_cidade(texto)
                msg = falar_clima_atual(cidade)
                # Trigger popup com dados estruturados
                try:
                    dados = get_clima_atual(cidade)
                    if not dados.get("erro"):
                        e._show_popup("clima", dados=dados)
                except Exception:
                    pass
                return msg

            # MINECRAFT
            if intent == "mc_iniciar":
                if e.minecraft: 
                    ok, msg = e.minecraft.iniciar_bot()
                    return "Conectando bot no Minecraft, Sir." if ok else msg
            if intent == "mc_parar":
                if e.minecraft: return "Bot desconectado." if e.minecraft.parar_bot() else "Ja estava offline."

            # SERVIDOR MC
            if intent == "mc_server_iniciar":
                if e.mc_server: 
                    e.mc_server.iniciar()
                    return "Ligando servidor de Minecraft, Sir."
            if intent == "mc_server_parar":
                if e.mc_server:
                    e.mc_server.parar()
                    return "Desligando servidor, Sir."

            # LEGIAO
            if intent == "legiao_criar":
                if e.legion:
                    qtd = int(params) if params else 10
                    e.legion.criar_legiao(qtd)
                    return f"Iniciando legiao com {qtd} soldados."

            # PESQUISA
            if intent == "pesquisa_web":
                query = texto.lower().replace("pesquisa", "").replace("sobre", "").strip()
                if e.pesquisa:
                    r = e.pesquisa.pesquisar(query, com_resumo=True)
                    resumo = r.get("resumo", "Pesquisei sobre isso, Sir.")
                    links = r.get("links", [])
                    # Trigger popup
                    try:
                        e._show_popup("pesquisa", query=query, resumo=resumo, links=links)
                    except Exception:
                        pass
                    return resumo
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Buscando {query} no Google."

            # STATUS PC
            if intent == "status_pc":
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                disco = psutil.disk_usage("C:\\").percent
                # Trigger popup
                try:
                    e._show_popup("status", info={
                        "cpu_percent": cpu,
                        "ram_used_percent": ram,
                        "disk_used_percent": disco,
                    })
                except Exception:
                    pass
                return f"CPU: {cpu}%, RAM: {ram}%, Disco: {disco}%"

            # VOLUME / BRILHO
            if intent == "volume_set":
                if e.system_control:
                    m = re.search(r"(\d+)", texto)
                    vol = int(m.group(1)) if m else 50
                    e.system_control.set_volume(vol)
                    return f"Volume em {vol}%, Sir."
                return "Controle de volume indisponivel."
            if intent == "brilho_set":
                if e.system_control:
                    m = re.search(r"(\d+)", texto)
                    brilho = int(m.group(1)) if m else 80
                    e.system_control.set_brightness(brilho)
                    return f"Brilho em {brilho}%, Sir."
                return "Controle de brilho indisponivel."

            # BLOQUEAR TELA
            if intent == "bloquear_tela":
                if e.system_control:
                    e.system_control.lock_screen()
                    return "Tela bloqueada, Sir."
                import subprocess
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
                return "Tela bloqueada, Sir."

            # CAMERAS
            if intent in ("camera_mostrar", "camera_todas"):
                if e.cameras:
                    cams = e.cameras.listar()
                    if cams:
                        nomes = [c.get("nome", "?") for c in cams[:5]]
                        return f"Cameras disponiveis: {', '.join(nomes)}."
                    return "Nenhuma camera configurada."
                return "Modulo de cameras offline."
            if intent == "camera_scan":
                if e.cameras:
                    return "Escaneando rede por cameras..."
                return "Modulo de cameras offline."
            if intent == "camera_listar":
                if e.cameras:
                    cams = e.cameras.listar()
                    return f"{len(cams)} cameras configuradas." if cams else "Nenhuma camera."
                return "Modulo offline."

            # VISAO
            if intent == "visao_ler_tela":
                if e.visao:
                    return e.visao.ler_tela()
                return "Visao indisponivel."
            if intent == "visao_foto":
                if e.visao:
                    return e.visao.tirar_foto()
                return "Visao indisponivel."

            # LEMBRETE
            if intent == "lembrete_agendar":
                if e.scheduler:
                    m = re.search(r"(?:em|daqui)\s+(\d+)\s+(minuto|hora|segundo)", texto)
                    if m:
                        qtd = int(m.group(1))
                        unidade = m.group(2)
                        if "hora" in unidade:
                            secs = qtd * 3600
                        elif "minuto" in unidade:
                            secs = qtd * 60
                        else:
                            secs = qtd
                        msg = texto.split("que")[-1].strip() if "que" in texto else "Lembrete"
                        e.scheduler.agendar_unico(secs, msg)
                        return f"Lembrete em {qtd} {unidade}(s), Sir."
                    return "Como assim, Sir? Ex: 'em 5 minutos de tomar agua'"
                return "Scheduler offline."
            if intent == "lembrete_listar":
                if e.scheduler:
                    lembretes = e.scheduler.listar()
                    if lembretes:
                        return f"{len(lembretes)} lembretes ativos."
                    return "Nenhum lembrete ativo."
                return "Scheduler offline."

            # POMODORO
            if intent == "pomodoro":
                if e.scheduler:
                    e.scheduler.pomodoro()
                    return "Pomodoro iniciado: 25min foco, 5min pausa."
                return "Scheduler offline."

            # MINECRAFT STATUS
            if intent == "mc_status":
                if e.minecraft:
                    return e.minecraft.status()
                return "Bot Minecraft offline."
            if intent == "mc_comando":
                cmd = texto.lower().replace("comando", "").replace("minecraft", "").strip()
                if e.minecraft and cmd:
                    return e.minecraft.enviar_comando(cmd)
                return "Comando vazio."

            # ESP32
            if intent == "esp32_status":
                if e.esp32:
                    return "ESP32 conectado." if e.esp32.conectado else "ESP32 offline."
                return "Modulo ESP32 offline."

            # LEGIAO (handlers faltantes)
            if intent == "legiao_status":
                if e.legion:
                    return e.legion.status()
                return "Legiao offline."
            if intent == "legiao_parar":
                if e.legion:
                    e.legion.parar_tudo()
                    return "Legiao desativada."
                return "Legiao offline."
            if intent in ("legiao_seguir", "legiao_voltar"):
                if e.legion:
                    e.legion.seguir_master()
                    return "Soldados seguindo o mestre."
                return "Legiao offline."
            if intent in ("legiao_defender", "legiao_proteger"):
                if e.legion:
                    e.legion.defender()
                    return "Legiao em modo defesa."
                return "Legiao offline."
            if intent in ("legiao_atacar",):
                if e.legion:
                    e.legion.atacar()
                    return "Legiao atacando!"
                return "Legiao offline."
            if intent == "legiao_dispersar":
                if e.legion:
                    e.legion.dispersar()
                    return "Legiao dispersada."
                return "Legiao offline."
            if intent == "legiao_resetar":
                if e.legion:
                    e.legion.resetar()
                    return "Legiao resetada."
                return "Legiao offline."
            if intent == "legiao_adicionar":
                if e.legion:
                    qtd = int(params) if params else 1
                    e.legion.adicionar_soldados(qtd)
                    return f"+{qtd} soldados adicionados."
                return "Legiao offline."

            # JARVIS
            if intent == "jarvis_encerrar":
                e.shutdown()
                os._exit(0)
            
            if intent == "jarvis_reiniciar":
                e.shutdown()
                import subprocess
                import sys
                python = sys.executable
                subprocess.Popen([python] + sys.argv,
                                 cwd=str(Path(__file__).resolve().parent.parent.parent))
                os._exit(0)
            
            if intent == "jarvis_saudacao":
                return "Sim, Sir? No que posso ajudar?"

            # ═══ TURBO ═══
            if intent == "turbo_ativar":
                if e.turbo:
                    resultado = e.turbo.ativar()
                    # Abre a janela Turbo via HUD (thread-safe)
                    if e.hud:
                        try:
                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(0, lambda: e.hud.turbo_mode(True))
                        except Exception:
                            pass
                    return resultado
                return "Modo Turbo indisponivel."
            if intent == "turbo_desativar":
                if e.turbo:
                    resultado = e.turbo.desativar()
                    # Fecha a janela Turbo (thread-safe)
                    if e.hud:
                        try:
                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(0, lambda: e.hud.turbo_mode(False))
                        except Exception:
                            pass
                    return resultado
                return "Modo Turbo indisponivel."
            if intent == "turbo_status":
                if e.turbo:
                    return e.turbo.formatar_status()
                return "Modo Turbo indisponivel."
            if intent == "turbo_analise":
                if e.turbo:
                    m = re.search(r"(?:analise|analisa|ver|olha|le|leia|abre|abra)\s+(.+)", texto.lower())
                    if m:
                        caminho = m.group(1).strip()
                        # Detecta se e arquivo ou pasta
                        cam = Path(caminho)
                        if cam.is_file():
                            dados = e.turbo.ler_arquivo(caminho)
                            return e.turbo.formatar_leitura(dados)
                        elif cam.is_dir():
                            dados = e.turbo.analisar_pasta(caminho)
                            return e.turbo.formatar_analise(dados)
                        else:
                            # Tenta resolver relativo ao Desktop
                            desktop = Path.home() / "Desktop"
                            tentativa = desktop / caminho
                            if tentativa.is_file():
                                dados = e.turbo.ler_arquivo(str(tentativa))
                                return e.turbo.formatar_leitura(dados)
                            elif tentativa.is_dir():
                                dados = e.turbo.analisar_pasta(str(tentativa))
                                return e.turbo.formatar_analise(dados)
                            return f"Nao encontrei: {caminho}"
                    return "Qual arquivo ou pasta analisar?"
                return "Modo Turbo indisponivel."
            if intent == "turbo_rotina":
                if e.turbo:
                    m = re.search(r"(?:rotina|modo)\s+(\w+)", texto.lower())
                    if m:
                        return e.turbo.executar_rotina(m.group(1))
                    return "Qual rotina? (trabalho, gamer, noturno, manha, organizar)"
                return "Modo Turbo indisponivel."
            if intent == "turbo_historico":
                if e.turbo:
                    return e.turbo.formatar_historico()
                return "Modo Turbo indisponivel."

            # ═══ PRODUTIVIDADE ═══
            if intent == "prod_relatorio_dia":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.criar_relatorio_dia()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_resumo_dia":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.resumo_dia()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_resumo_semana":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.resumo_semanal()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_exportar_memorias":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.exportar_memorias()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_tempo_focado":
                if hasattr(e, 'produtividade') and e.produtividade:
                    tempo = e.produtividade.tempo_focado_hoje()
                    return f"Tempo focado hoje: {tempo}, Sir."
                return "Modulo de produtividade indisponivel."

            if intent == "prod_gasto_adicionar":
                if hasattr(e, 'produtividade') and e.produtividade:
                    m = re.search(r"(?:gasto|registra gasto|anota gasto)\s+(.+?)(?:\s+(\d+(?:[.,]\d+)?)\s*(?:reais|R\$?)?)?$", texto.lower())
                    if m:
                        descricao = m.group(1).strip()
                        valor_str = m.group(2) if m.group(2) else "0"
                        valor = float(valor_str.replace(",", "."))
                        return e.produtividade.adicionar_gasto(descricao, valor)
                    return "Qual gasto devo registrar, Sir? Ex: gasto almoço 25"
                return "Modulo de produtividade indisponivel."

            if intent == "prod_gasto_listar":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.listar_gastos()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_planilha_gastos":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.planilha_gastos()
                return "Modulo de produtividade indisponivel."

            if intent == "prod_listar_relatorios":
                if hasattr(e, 'produtividade') and e.produtividade:
                    return e.produtividade.listar_relatorios()
                return "Modulo de produtividade indisponivel."

            # ═══ CELULAR ═══
            if intent == "cel_status":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.status_completo()
                return "Modulo celular indisponivel. Instale ADB e conecte o celular."

            if intent == "cel_notificacoes":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.ler_notificacoes()
                return "Modulo celular indisponivel."

            if intent == "cel_abrir_app":
                if hasattr(e, 'celular') and e.celular:
                    m = re.search(r"(?:abrir|abre)\s+(?:o\s+|a\s+)?(\w+)", texto.lower())
                    if m:
                        app = m.group(1)
                        return e.celular.abrir_app(app)
                    return "Qual app devo abrir, Sir?"
                return "Modulo celular indisponivel."

            if intent == "cel_listar_apps":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.listar_apps()
                return "Modulo celular indisponivel."

            if intent == "cel_fechar_app":
                if hasattr(e, 'celular') and e.celular:
                    m = re.search(r"(?:fechar|fecha)\s+(?:o\s+|a\s+)?(\w+)", texto.lower())
                    if m:
                        app = m.group(1)
                        return e.celular.fechar_app(app)
                    return "Qual app devo fechar, Sir?"
                return "Modulo celular indisponivel."

            if intent == "cel_bateria":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.status_bateria()
                return "Modulo celular indisponivel."

            if intent == "cel_volume":
                if hasattr(e, 'celular') and e.celular:
                    m = re.search(r"volume(?:\s+do\s+celular)?\s*(\d+|[+\-])?", texto.lower())
                    if m:
                        val = m.group(1)
                        if val and val.isdigit():
                            return e.celular.volume(nivel=int(val))
                        elif val == "+":
                            return e.celular.volume(direcao="up")
                        elif val == "-":
                            return e.celular.volume(direcao="down")
                    return e.celular.volume(direcao="up")
                return "Modulo celular indisponivel."

            if intent == "cel_wifi":
                if hasattr(e, 'celular') and e.celular:
                    if "ligar" in texto.lower():
                        return e.celular.wifi(True)
                    elif "desligar" in texto.lower():
                        return e.celular.wifi(False)
                    return e.celular.wifi()
                return "Modulo celular indisponivel."

            if intent == "cel_bluetooth":
                if hasattr(e, 'celular') and e.celular:
                    if "ligar" in texto.lower():
                        return e.celular.bluetooth(True)
                    elif "desligar" in texto.lower():
                        return e.celular.bluetooth(False)
                    return e.celular.bluetooth()
                return "Modulo celular indisponivel."

            if intent == "cel_screenshot":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.screenshot()
                return "Modulo celular indisponivel."

            if intent == "cel_localizar":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.localizar()
                return "Modulo celular indisponivel."

            if intent == "cel_sms_enviar":
                if hasattr(e, 'celular') and e.celular:
                    m = re.search(r"(?:enviar sms|mandar sms|sms\s+para)\s+(\d+)\s+(.+)", texto.lower())
                    if m:
                        numero = m.group(1)
                        msg = m.group(2)
                        return e.celular.enviar_sms(numero, msg)
                    return "Para quem e qual mensagem, Sir? Ex: enviar sms 123456789 oi"
                return "Modulo celular indisponivel."

            if intent == "cel_sms_ler":
                if hasattr(e, 'celular') and e.celular:
                    return e.celular.ler_sms_recentes()
                return "Modulo celular indisponivel."

            if intent == "cel_transferir":
                if hasattr(e, 'celular') and e.celular:
                    m = re.search(r"(?:transferir|enviar|copiar)\s+arquivo\s+(.+?)(?:\s+para\s+(?:o\s+)?celular)?$", texto.lower())
                    if m:
                        caminho = m.group(1).strip()
                        return e.celular.transferir_arquivo(caminho)
                    return "Qual arquivo transferir, Sir?"
                return "Modulo celular indisponivel."

            # ═══ TV SAMSUNG ═══
            if intent == "tv_ligar":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.ligar()
                return "Modulo TV indisponivel."

            if intent == "tv_desligar":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.desligar()
                return "Modulo TV indisponivel."

            if intent == "tv_volume":
                if hasattr(e, 'tv') and e.tv:
                    m = re.search(r"volume(?:\s+da\s+(?:tv|televisão|samsung))?\s*(\d+|[+\-])?", texto.lower())
                    if m:
                        val = m.group(1)
                        if val and val.isdigit():
                            return e.tv.volume(nivel=int(val))
                        elif val == "+":
                            return e.tv.volume(direcao="up")
                        elif val == "-":
                            return e.tv.volume(direcao="down")
                    return e.tv.volume(direcao="up")
                return "Modulo TV indisponivel."

            if intent == "tv_mutar":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.mutar()
                return "Modulo TV indisponivel."

            if intent == "tv_canal":
                if hasattr(e, 'tv') and e.tv:
                    m = re.search(r"(?:canal|频道)\s*(\d+)?", texto.lower())
                    if m and m.group(1):
                        return e.tv.canal(int(m.group(1)))
                    if "próximo" in texto.lower() or "proximo" in texto.lower():
                        return e.tv.canal_proximo()
                    if "anterior" in texto.lower():
                        return e.tv.canal_anterior()
                    return "Qual canal, Sir?"
                return "Modulo TV indisponivel."

            if intent == "tv_input":
                if hasattr(e, 'tv') and e.tv:
                    if "hdmi1" in texto.lower():
                        return e.tv.hdmi1()
                    elif "hdmi2" in texto.lower():
                        return e.tv.hdmi2()
                    elif "tv" in texto.lower() and "input" not in texto.lower():
                        return e.tv.tv_input()
                    return e.tv.listar_fontes()
                return "Modulo TV indisponivel."

            if intent == "tv_status":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.status()
                return "Modulo TV indisponivel."

            if intent == "tv_play":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.play()
                return "Modulo TV indisponivel."

            if intent == "tv_pause":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.pause()
                return "Modulo TV indisponivel."

            if intent == "tv_home":
                if hasattr(e, 'tv') and e.tv:
                    return e.tv.home()
                return "Modulo TV indisponivel."

            if intent == "tv_navegar":
                if hasattr(e, 'tv') and e.tv:
                    m = re.search(r"(?:seta|navegar)\s+(?:da\s+tv\s+)?(?:pra\s+|para\s+)?(cima|baixo|esquerda|direita|ok|enter|confirmar)", texto.lower())
                    if m:
                        direcao = m.group(1)
                        if direcao in ("ok", "enter", "confirmar"):
                            return e.tv.confirmar()
                        return e.tv.seta(direcao)
                    return "Pra onde navegar, Sir? (cima, baixo, esquerda, direita, ok)"
                return "Modulo TV indisponivel."

            # ═══ SEGURANCA ═══
            if intent == "seg_senha_definir":
                if hasattr(e, 'seguranca') and e.seguranca:
                    m = re.search(r"(?:definir|criar|nova)\s+senha\s+(.+)", texto.lower())
                    if m:
                        senha = m.group(1).strip()
                        return e.seguranca.definir_senha(senha)
                    return "Qual senha definir, Sir?"
                return "Modulo segurança indisponivel."

            if intent == "seg_desbloquear":
                if hasattr(e, 'seguranca') and e.seguranca:
                    m = re.search(r"desbloquear\s+(.+)", texto.lower())
                    if m:
                        senha = m.group(1).strip()
                        return e.seguranca.desbloquear(senha)
                    return "Qual a senha, Sir?"
                return "Modulo segurança indisponivel."

            if intent == "seg_status":
                if hasattr(e, 'seguranca') and e.seguranca:
                    return e.seguranca.status_seguranca()
                return "Modulo segurança indisponivel."

            if intent == "seg_logs":
                if hasattr(e, 'seguranca') and e.seguranca:
                    return e.seguranca.listar_logs()
                return "Modulo segurança indisponivel."

            if intent == "seg_rede":
                if hasattr(e, 'seguranca') and e.seguranca:
                    return e.seguranca.scan_rede()
                return "Modulo segurança indisponivel."

            if intent == "seg_portas":
                if hasattr(e, 'seguranca') and e.seguranca:
                    return e.seguranca.portas_abertas()
                return "Modulo segurança indisponivel."

            # ═══ ENTRETENIMENTO ═══
            if intent == "entre_jogo":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    return e.entretenimento.iniciar_jogo()
                return "Modulo entretenimento indisponivel."

            if intent == "entre_adivinhar":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    m = re.search(r"(?:adivinhar|chute|palpite\s+(?:e|é)?)\s*(\d+)", texto.lower())
                    if m:
                        numero = int(m.group(1))
                        return e.entretenimento.adivinhar(numero)
                    return "Qual número, Sir?"
                return "Modulo entretenimento indisponivel."

            if intent == "entre_quiz":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    return e.entretenimento.proxima_pergunta()
                return "Modulo entretenimento indisponivel."

            if intent == "entre_responder":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    m = re.search(r"(?:responder|minha\s+resposta\s+(?:e|é)?)\s+(.+)", texto.lower())
                    if m:
                        resposta = m.group(1).strip()
                        return e.entretenimento.verificar_resposta(resposta)
                    return "Qual sua resposta, Sir?"
                return "Modulo entretenimento indisponivel."

            if intent == "entre_piada":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    return e.entretenimento.piada()
                return "Modulo entretenimento indisponivel."

            if intent == "entre_curiosidade":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    return e.entretenimento.curiosidade()
                return "Modulo entretenimento indisponivel."

            if intent == "entre_filme":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    m = re.search(r"(?:recomendar|indicar|assistir)\s+(?:um\s+)?(?:filme\s+)?(?:de\s+)?(\w+)?", texto.lower())
                    genero = m.group(1) if m and m.group(1) else None
                    return e.entretenimento.recomendar_filme(genero)
                return "Modulo entretenimento indisponivel."

            if intent == "entre_frase":
                if hasattr(e, 'entretenimento') and e.entretenimento:
                    return e.entretenimento.falar_frase_famous()
                return "Modulo entretenimento indisponivel."

            # ═══ EXTRAS ═══
            if intent == "calcular":
                from modules.extras import get_calculadora
                calc = get_calculadora()
                m = re.search(r"(?:calc(?:ular)?|quanto[eé]\s*|qual\s+(?:e|eh)\s*)(.+)", texto.lower())
                if m:
                    expr = m.group(1).strip()
                    return calc.calcular(expr)
                return "O que devo calcular, Sir?"

            if intent == "timer":
                from modules.extras import get_timer_manager
                tm = get_timer_manager()
                m = re.search(r"(?:timer|alarme|avise(?:me)?|lembre(?:me)?)\s+(?:em|daqui|nos?)?\s*(\d+)\s*(minuto|hora|segundo)", texto.lower())
                if m:
                    valor = int(m.group(1))
                    unidade = m.group(2)
                    if "hora" in unidade:
                        segundos = valor * 3600
                    elif "minuto" in unidade:
                        segundos = valor * 60
                    else:
                        segundos = valor
                    tid = tm.criar_timer(segundos)
                    return f"Timer de {valor} {unidade} criado, Sir."
                return "Para quanto tempo devo colocar o timer, Sir?"

            if intent == "listar_timers":
                from modules.extras import get_timer_manager
                tm = get_timer_manager()
                timers = tm.listar_timers()
                if not timers:
                    return "Nenhum timer ativo, Sir."
                partes = [f"Timer {t['id']}: {t['restante_seg']} segundos restantes" for t in timers]
                return ", ".join(partes) + "."

            if intent == "lembrete":
                from modules.extras import get_lembretes
                lm = get_lembretes()
                m = re.search(r"(?:lembre(?:te)?|avise(?:me)?)\s+(?:me\s+)?(?:de\s+)?(.+)", texto.lower())
                if m:
                    texto_lembrete = m.group(1).strip()
                    lid = lm.adicionar(texto_lembrete)
                    return f"Lembrete criado, Sir. ID: {lid}."
                return "Do que devo lembrar, Sir?"

            if intent == "listar_lembretes":
                from modules.extras import get_lembretes
                lm = get_lembretes()
                lembretes = lm.listar()
                if not lembretes:
                    return "Nenhum lembrete ativo, Sir."
                partes = [f"{l['id']}: {l['texto']}" for l in lembretes]
                return "Lembretes: " + ", ".join(partes) + "."

            if intent == "info_sistema":
                from modules.extras import SistemaInfo
                return SistemaInfo.info_formatada()

            if intent == "top_processos":
                from modules.extras import MonitorProcessos
                return MonitorProcessos.formatar_top()

            if intent == "limpar_tela" or intent == "limpar_terminal":
                os.system("cls" if os.name == "nt" else "clear")
                return "Tela limpa, Sir."

            if intent == "mostrar_agenda":
                if e.scheduler:
                    try:
                        return e.scheduler.listar_tarefas()
                    except:
                        pass
                return "Agenda indisponivel, Sir."

            if intent == "mostrar_historico":
                if hasattr(e, 'historico_comandos'):
                    historico = e.historico_comandos[-10:]  # ultimos 10
                    if historico:
                        return "Ultimos comandos: " + "; ".join(historico) + "."
                return "Historico vazio, Sir."

            if intent == "reiniciar_jarvis":
                return "__REINICIAR__"

            if intent == "desligar_pc":
                import platform
                if platform.system() == "Windows":
                    os.system("shutdown /s /t 60")
                    return "Desligando o computador em 60 segundos, Sir."
                return "Comando disponivel apenas no Windows, Sir."

            if intent == "cancelar_desligamento":
                os.system("shutdown /a")
                return "Desligamento cancelado, Sir."

            if intent == "abrir_explorer":
                import subprocess
                subprocess.Popen(["explorer.exe"])
                return "Explorador de arquivos aberto, Sir."

            if intent == "fechar_tudo":
                import psutil
                fechados = 0
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] in ['chrome.exe', 'firefox.exe', 'msedge.exe']:
                            proc.kill()
                            fechados += 1
                    except:
                        pass
                return f"Navegadores fechados, Sir. {fechados} processos encerrados."

        except Exception as ex:
            print(f"[EXEC INTENT ERROR] {intent}: {ex}")
            return self._fallback(texto)

        return self._fallback(texto)