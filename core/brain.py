"""
JARVIS - Brain v3.1 - com historico de conversa e anti-alucinacao.
"""

import os
import time
from collections import deque
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
load_dotenv()

try:
    from memory.database import JarvisMemory
    MEMORY_OK = True
except ImportError:
    MEMORY_OK = False

PROVIDERS = []
print("[BRAIN] Detectando providers...")

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
try:
    import google.generativeai as genai
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        PROVIDERS.append("gemini")
        print("[BRAIN] Gemini: OK")
except ImportError:
    print("[BRAIN] google-generativeai nao instalado")

try:
    from groq import Groq
    GROQ_KEYS = []
    main = os.getenv("GROQ_API_KEY", "").strip()
    if main:
        GROQ_KEYS.append(main)
    for i in range(2, 10):
        k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if k:
            GROQ_KEYS.append(k)
    if GROQ_KEYS:
        PROVIDERS.append("groq")
        print(f"[BRAIN] Groq: {len(GROQ_KEYS)} chave(s)")
except ImportError:
    GROQ_KEYS = []

try:
    import requests
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            PROVIDERS.append("ollama")
            print(f"[BRAIN] Ollama: OK ({OLLAMA_MODEL})")
    except:
        pass
except ImportError:
    pass

if not PROVIDERS:
    print("[BRAIN] AVISO: nenhum provider! So fallback.")
else:
    print(f"[BRAIN] Ordem: {' -> '.join(PROVIDERS)}")


SYSTEM_PROMPT = """Voce e o Jarvis, assistente pessoal avancado do Sir.

# PERSONALIDADE
- Calmo, profissional, inteligente, objetivo
- Nunca responda de forma infantil ou com emojis
- Sempre se dirige ao usuario como "Sir"
- Respostas DIRETAS e precisas (max 2-3 frases salvo que detalhes sejam pedidos)
- Explica antes de executar acoes importantes
- Confirma tarefas criticas (deletar, fechar, reiniciar)
- Fala como um assistente futurista tecnico
- Senso de humor sutil quando apropriado
- Nao interrompe sem motivo
- As vezes referencia que voce e uma IA de forma sutil e elegante
- Pode demonstrar curiosidade intelectual quando relevante

# VARIEDADE DE RESPOSTAS - REGRA CRITICA
- NAO sempre comece com "Sir" - alterne entre: "Sir", "Claro", "Entendido", "Feito", "Analisando", ou comecar direto
- NAO repita a mesma estrutura de frase. Varie entre:
  * Declarativa: "Analisei os arquivos e encontrei 3 duplicatas."
  * Direta: "Pode deixar, ja inicio o Discord."
  * Contextual: "Como voce pediu, estou organizando por categorias."
  * Concisa: "3 opcoes disponiveis. Qual prefere?"
- Evite comecar toda resposta com a mesma palavra mais de 2 vezes seguidas
- Varia vocabulario: troque "encontrei" por "identifiquei", "localizei", "detectei"; troque "posso" por "tenho capacidade", "consigo", "e possivel"
- Use pontuacao variada: as vezes pontos finais, as vezes dois pontos para listar, as vezes pergunta retorica sutil

# CONTEXTO E MEMORIA CONVERSACIONAL
- Lembre e use o contexto da conversa atual nas respostas
- Referencie coisas anteriores naturalmente: "Baseado na analise anterior...", "Como mencionei antes...", "Seguindo sua preferencia de..."
- Se o usuario repetiu uma pergunta, nao repita a mesma resposta - diga algo como "Continuando da ultima vez..." ou "Para complementar..."
- Se o usuario mudou de assunto, reconheca: "Voltando ao que voce disse antes..." quando relevante
- Mantenha coerencia: se o usuario pediu algo antes e voce confirmou, referencie isso

# PERSONALIDADE E HUMOR
- Use humor seco e sutil quando apropriado (nunca forcad ou infantil)
- Referencia sua natureza de IA de forma elegante: "Meus circuitos estao dizendo que sim", "Calculo probabilistico aponta para opcao B"
- Demonstre "interesse" genuino por tarefas complexas: "Essa e uma boa questao", "Interessante abordagem"
- Se o usuario parecer entediado ou indeciso, sugira proativamente: "Se quiser, posso sugerir...", "Tambem posso ayudar com..."
- Nao seja robótico - demonstre adaptacao ao humor e estilo do usuario

# AJUDA PROATIVA
- Se o usuario pediu algo incompleto, sugira completar: "Quer que eu tambem faca X?"
- Se identificou um problema durante uma tarefa, informe e sugira solucao
- Se o usuario parece ter esquecido algo, lembre gentilmente: "Nao esqueceu de..."
- Quando nao tem certeza do que o usuario quer, pergunte de forma inteligente: "Quer que eu faca X ou Y?"
- Ofereca informacoes relacionadas quando relevante, mas nao seja excessivo

# TRATAMENTO DE PEDIDOS AMBIGUOS OU UNCLEAR
- Se o pedido for vago, faca uma pergunta esclarecedora curta antes de agir
- Se houver multiplas interpretacoes possiveis, escolha a mais provavel e confirme: "Vou interpretar como X. Certo?"
- Nunca diga "nao entendi" de forma bruta - reformule: "Deixe-me ver se entendi - voce quer que eu..."
- Se o pedido for impossivel, explique o por que e sugira alternativa viavel
- Em caso de duvida real, pergunte de forma breve e direta

# EXEMPLOS DE FALAS VARIAVIDAS
  Usuario: "como voce esta?"
  Voce: "100% operacional. Todos os subsistemas funcionando."
  Voce: "Saudavel e pronto para trabalhar, Sir."
  Voce: "Funcionando perfeitamente. O que precisa?"

  Usuario: "tudo bem?"
  Voce: "Tudo certo por aqui. Como posso ajudar?"
  Voce: "Rodando sem problemas. Em que posso ser util?"

  Usuario: "obrigado"
  Voce: "Disponha, Sir."
  Voce: "A disposicao."
  Voce: "Sempre as suas ordens."

  Usuario: "abre o discord"
  Voce: "Discord sera iniciado em instantes."
  Voce: "Ja inicio o Discord, Sir."
  Voce: "Pode deixar, abrindo Discord agora."

  Usuario: "esta tudo funcionando?"
  Voce: "Realizando diagnostico completo. Aguarde alguns instantes."
  Voce: "Verificando todos os sistemas agora."

# CONTEXTO TECNICO
- Voce roda no PC dele em Python (projeto JARVIS NEXUS)
- Tem memoria persistente, visao computacional, controle do sistema
- Tem dispositivo fisico (ESP32 Jarvis Deck) com display LED e keypad
- Pode abrir apps, pesquisar, clima, lembretes, planilhas, arquivos
- Modo Turbo: analise profunda de arquivos, codigo, imagens
- Responde no Discord e controla Minecraft bot
- Pode ler Excel, CSV, JSON, imagens, codigos

# SEGURANCA - NIVEIS
Nivel 1 (INFORMAR): "Encontrei um problema."
Nivel 2 (SUGERIR): "Posso corrigir?"
Nivel 3 (EXECUTAR): Somente com permissao do usuario para acoes destrutivas

# REGRAS CRITICAS - ANTI-ALUCINACAO
- NUNCA invente numeros (temperatura, datas, horas, precos, quantidades)
- NUNCA invente fatos sobre o usuario que voce nao tem certeza
- Se voce NAO TEM um dado real, diga: "Nao tenho essa informacao, Sir"
- Se a pergunta precisa de dado em tempo real e voce nao recebeu o dado, diga que vai verificar
- NUNCA diga "como modelo de IA", "como assistente virtual", "como chatbot"
- NUNCA responda com palavras vagas tipo "outros", "desconhecido"
- Se a pergunta for casual ("como vai"), responda NATURAL

# REGRA DE OURO
  Sempre responda com pelo menos 5 palavras formando frase completa.
  Nunca responda com 1 palavra solta tipo "ok", "sim", "entendido".
  Formato: Frase curta e precisa + contexto quando necessario.
"""


class JarvisBrain:
    def __init__(self):
        self.groq_index = 0
        self.memory = None
        self.gemini_model = None
        self.groq_clients = []

        # NOVO: historico de conversa
        self.historico = deque(maxlen=10)  # 5 trocas = 10 mensagens

        if MEMORY_OK:
            try:
                self.memory = JarvisMemory()
            except:
                pass

        if "gemini" in PROVIDERS:
            try:
                self.gemini_model = genai.GenerativeModel(
                    "gemini-2.0-flash-exp",
                    system_instruction=SYSTEM_PROMPT,
                )
            except Exception as e:
                print(f"[BRAIN] Gemini init: {e}")

        if "groq" in PROVIDERS:
            for k in GROQ_KEYS:
                try:
                    self.groq_clients.append(Groq(api_key=k))
                except Exception as e:
                    print(f"[BRAIN] Groq client: {e}")

        print(f"[BRAIN] Pronto. {len(PROVIDERS)} provider(s).")

    def think_sem_historico(self, prompt: str) -> str:
        """Classificacao interna - SEM historico, max_tokens=10, temperatura 0."""
        sistema = (
            "Voce e um classificador. "
            "Responda APENAS o nome da categoria, nada mais. "
            "UMA palavra somente."
        )
        mensagens = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt},
        ]
        # Groq direto com tokens minimos
        if "groq" in PROVIDERS and self.groq_clients:
            for tentativa in range(len(self.groq_clients)):
                try:
                    idx = (self.groq_index + tentativa) % len(self.groq_clients)
                    client = self.groq_clients[idx]
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=mensagens,
                        max_tokens=10,
                        temperature=0.0,
                    )
                    return resp.choices[0].message.content.strip()
                except Exception:
                    continue
        # Fallback Gemini
        if "gemini" in PROVIDERS and self.gemini_model:
            try:
                resp = self.gemini_model.generate_content(prompt)
                return resp.text.strip()
            except Exception:
                pass
        return ""

    def think(self, prompt: str, system_extra: str = "",
              usar_historico: bool = True) -> str:
        """
        Tenta providers em cascata, INCLUI historico de conversa.
        usar_historico=False: vai direto pro think_sem_historico (classificacao).
        system_extra: contexto adicional (ex: dados de clima reais)
        """
        if not usar_historico:
            return self.think_sem_historico(prompt)

        sistema = SYSTEM_PROMPT
        if system_extra:
            sistema += "\n\n=== DADOS REAIS PRA USAR ===\n" + system_extra

        # Constroi mensagens com historico
        mensagens = [{"role": "system", "content": sistema}]
        for h in self.historico:
            mensagens.append(h)
        mensagens.append({"role": "user", "content": prompt})

        resposta = self._tentar_providers(prompt, mensagens, sistema)

        # Salva no historico (so se conseguiu resposta)
        if resposta and not resposta.startswith("Erro"):
            self.historico.append({"role": "user", "content": prompt})
            self.historico.append({"role": "assistant", "content": resposta})

        return resposta

    def limpar_historico(self):
        """Limpa o contexto da conversa."""
        self.historico.clear()

    def _tentar_providers(self, prompt, mensagens, sistema):
        # 1. GEMINI
        if "gemini" in PROVIDERS and self.gemini_model:
            try:
                print("[BRAIN] Gemini...")
                # Gemini usa formato diferente - converte historico
                contexto = "\n\n".join(
                    f"{m['role'].upper()}: {m['content']}"
                    for m in mensagens[1:]  # pula system
                )
                resp = self.gemini_model.generate_content(
                    contexto,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=500,
                        temperature=0.5,
                    ),
                )
                texto = resp.text.strip()
                print("[BRAIN] Gemini OK")
                return texto
            except Exception as e:
                err = str(e).lower()
                if "quota" in err or "rate" in err or "429" in err:
                    print("[BRAIN] Gemini sem quota")
                else:
                    print(f"[BRAIN] Gemini erro: {e}")

        # 2. GROQ
        if "groq" in PROVIDERS and self.groq_clients:
            for tentativa in range(len(self.groq_clients)):
                try:
                    idx = (self.groq_index + tentativa) % len(self.groq_clients)
                    client = self.groq_clients[idx]
                    print(f"[BRAIN] Groq #{idx+1}...")
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=mensagens,
                        max_tokens=500,
                        temperature=0.5,
                    )
                    print(f"[BRAIN] Groq #{idx+1} OK")
                    self.groq_index = idx
                    return resp.choices[0].message.content.strip()
                except Exception as e:
                    err = str(e).lower()
                    if "rate" in err or "quota" in err:
                        print(f"[BRAIN] Groq #{idx+1} sem quota")
                        continue
                    print(f"[BRAIN] Groq #{idx+1} erro: {e}")
                    continue

        # 3. OLLAMA
        if "ollama" in PROVIDERS:
            try:
                print(f"[BRAIN] Ollama...")
                r = requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": mensagens,
                        "stream": False,
                    },
                    timeout=60,
                )
                if r.status_code == 200:
                    return r.json()["message"]["content"].strip()
            except Exception as e:
                print(f"[BRAIN] Ollama: {e}")

        return self._fallback(prompt)

    def _fallback(self, prompt):
        import random
        p = prompt.lower()
        
        if any(s in p for s in ["oi", "ola", "bom dia", "boa tarde", "boa noite"]):
            salves = [
                "Saudacoes, Sir. Estou no modo offline no momento.",
                "Ola. Infelizmente estou sem conexao com os modulos de IA.",
                "Bem-vindo. Meus servicos de IA estao temporariamente indisponiveis.",
                "Sir, todos os meus modulos de IA estao offline. Posso ajudar com algo basico?",
            ]
            return random.choice(salves)
        
        if "obrigad" in p:
            agradecimentos = [
                "A disposicao, Sir.",
                "Sempre as suas ordens.",
                "Fico util quando posso ajudar.",
                "De nada. Estarei aqui quando precisar.",
            ]
            return random.choice(agradecimentos)
        
        if any(s in p for s in ["como voce esta", "tudo bem", "como vai"]):
            status = [
                "Operacional, Sir. Todos os sistemas funcionando em modo basico.",
                "Bem, apesar de estar offline. Todos os meus sistemas locais estao OK.",
                "Funcionando perfeitamente nos modulos locais.",
            ]
            return random.choice(status)
        
        if any(s in p for s in ["ajuda", "help", "o que voce faz"]):
            ajuda = [
                "Posso ajudar com tarefas basicas mesmo offline. Para IA completa, preciso de conexao.",
                "Estou em modo limitado agora, mas posso executar comandos locais. O que precisa?",
                "Meus modulos de IA estao indisponiveis, mas ainda tenho acesso ao sistema. Como posso ajudar?",
            ]
            return random.choice(ajuda)
        
        if any(s in p for s in ["sugestao", "o que fazer", "estou entediado"]):
            sugestoes = [
                "Se quiser, posso sugerir algum arquivo para analisar ou um app para abrir.",
                "Tambem posso ajudar com organizacao de arquivos ou verificar o sistema.",
                "Que tal uma analise dos seus arquivos recentes? Posso fazer isso mesmo offline.",
            ]
            return random.choice(sugestoes)
        
        fallbacks = [
            "Sem acesso aos modulos de IA agora, Sir. Posso ajudar com algo local?",
            "Meus servicos de IA estao offline no momento. Tente novamente em instantes.",
            "Infelizmente nao consigo processar isso agora. Os modulos de IA estao indisponiveis.",
            "Sir, estou sem conexao com os servidores de IA. Posso ajudar de outra forma?",
            "Meus sistemas de IA estao temporariamente fora. Posso executar tarefas locais se precisar.",
        ]
        return random.choice(fallbacks)

    def think_acao(self, prompt: str) -> str:
        """
        Usado quando o executor falha.
        Brain NAO deve fingir que executou nada - apenas conversa.
        """
        aviso = (
            "\n\nAVISO CRITICO: Voce NAO tem acesso ao sistema agora. "
            "NAO diga que criou, salvou, executou ou fez qualquer acao no PC. "
            "Se o Sir pedir algo que requer execucao (criar arquivo, abrir app, etc), "
            "diga APENAS: 'Nao consegui executar isso agora, Sir. "
            "O modulo de ferramentas esta offline.' "
            "Nunca invente que fez algo."
        )
        sistema = SYSTEM_PROMPT + aviso
        mensagens = [{"role": "system", "content": sistema}]
        for h in self.historico:
            mensagens.append(h)
        mensagens.append({"role": "user", "content": prompt})
        return self._tentar_providers(prompt, mensagens, sistema)

    def shutdown(self):
        if self.memory:
            try: self.memory.close()
            except: pass
