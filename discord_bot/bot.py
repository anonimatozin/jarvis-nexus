"""
JARVIS Discord Bot v3.0
DM privado com persistencia e mais funcoes.
"""

import os
import sys
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime, date

import discord
from discord.ext import commands
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))

# Arquivo de persistencia
_DATA_DIR = Path("data")
_WELCOME_FILE = _DATA_DIR / "discord_welcome_sent.json"


def _carregar_welcome():
    """Carrega registro de welcome enviado."""
    if _WELCOME_FILE.exists():
        try:
            with open(_WELCOME_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _salvar_welcome(dados):
    """Salva registro de welcome enviado."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_WELCOME_FILE, "w") as f:
        json.dump(dados, f)


def _ja_enviou_welcome():
    """Verifica se ja enviou welcome hoje."""
    dados = _carregar_welcome()
    ultima_data = dados.get("ultima_data")
    if ultima_data == date.today().isoformat():
        return True
    return False


def _marcar_welcome_enviado():
    """Marca que o welcome foi enviado hoje."""
    dados = _carregar_welcome()
    dados["ultima_data"] = date.today().isoformat()
    dados["total_envios"] = dados.get("total_envios", 0) + 1
    dados["ultimo_envio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _salvar_welcome(dados)


class JarvisDiscord:
    """Bot do Jarvis no Discord."""

    def __init__(self, engine_ref=None):
        self.engine = engine_ref
        self.owner = None
        self.loop = None
        self.bot_ready = False
        self._historico_comandos = []  # ultimos 50 comandos

        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.members = True

        self.bot = commands.Bot(
            command_prefix=["!", "/"],
            intents=intents,
            help_command=None,
        )

        self._setup_events()
        self._setup_commands()

    def _setup_events(self):
        bot = self.bot

        @bot.event
        async def on_ready():
            print(f"[DISCORD] Bot online: {bot.user}")
            print(f"[DISCORD] ID: {bot.user.id}")
            self.bot_ready = True

            try:
                self.owner = await bot.fetch_user(OWNER_ID)
                print(f"[DISCORD] Dono: {self.owner.name}")

                # Verifica se ja enviou welcome hoje
                if not _ja_enviou_welcome():
                    try:
                        await self.owner.send(
                            "**J.A.R.V.I.S. Discord Bot Online**\n\n"
                            "Sir, estou disponivel por aqui tambem.\n\n"
                            "**Comandos:**\n"
                            "`!status` - Telemetria do PC\n"
                            "`!abrir <app>` - Abre programa\n"
                            "`!fechar <app>` - Fecha programa\n"
                            "`!pesquisar <X>` - Pesquisa\n"
                            "`!clima` - Tempo agora\n"
                            "`!horas` - Que horas sao\n"
                            "`!cpu` - CPU detalhado\n"
                            "`!ram` - Memoria RAM\n"
                            "`!disco` - Espaco em disco\n"
                            "`!processos` - Top processos\n"
                            "`!rede` - Status da rede\n"
                            "`!dizer <texto>` - Faz Jarvis falar\n"
                            "`!voz on/off` - Controla voz\n"
                            "`!lembrar` - Agenda lembrete\n"
                            "`!turbo` - Ativa modo turbo\n"
                            "`!ajuda` - Lista completa\n\n"
                            "Ou apenas converse normalmente comigo."
                        )
                        _marcar_welcome_enviado()
                        print("[DISCORD] DM de boas vindas enviada!")
                    except discord.Forbidden:
                        print("[DISCORD] Nao consegui enviar DM (DMs fechadas?)")
                    except Exception as e:
                        print(f"[DISCORD] Erro DM: {e}")
                else:
                    print("[DISCORD] Welcome ja enviado hoje, pulando.")
            except Exception as e:
                print(f"[DISCORD] Erro ao pegar dono: {e}")

            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="o Sir | !ajuda"
                )
            )

        @bot.event
        async def on_message(message):
            if message.author == bot.user:
                return
            if message.author.id != OWNER_ID:
                return
            if not isinstance(message.channel, discord.DMChannel):
                return

            # Registra no historico
            self._registrar_comando(message.content[:80])

            if message.content.startswith(("!", "/")):
                await bot.process_commands(message)
                return

            # ANEXOS
            if message.attachments:
                pasta = Path("data/recebidos_discord")
                pasta.mkdir(parents=True, exist_ok=True)
                ts2 = datetime.now().strftime("%Y%m%d_%H%M%S")
                for att in message.attachments:
                    destino = pasta / f"{ts2}_{att.filename}"
                    await att.save(destino)
                    await message.channel.send(
                        f"Recebi `{att.filename}` ({att.size//1024}KB). "
                        f"Salvei em `{destino.relative_to(Path.cwd())}`."
                    )

            # Mensagem normal -> processa
            if not message.content.strip():
                return

            async with message.channel.typing():
                resposta = await self._processar_engine(message.content)
                if resposta:
                    for chunk in self._split_message(resposta):
                        await message.channel.send(chunk)

    def _registrar_comando(self, texto):
        """Registra comando no historico."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._historico_comandos.append({"hora": ts, "cmd": texto})
        if len(self._historico_comandos) > 50:
            self._historico_comandos = self._historico_comandos[-50:]

    def _split_message(self, text, limit=1900):
        if len(text) <= limit:
            return [text]
        chunks = []
        while len(text) > limit:
            split_at = text.rfind("\n", 0, limit)
            if split_at == -1:
                split_at = text.rfind(" ", 0, limit)
            if split_at == -1:
                split_at = limit
            chunks.append(text[:split_at])
            text = text[split_at:].strip()
        if text:
            chunks.append(text)
        return chunks

    async def _processar_engine(self, texto):
        if not self.engine:
            return "Engine nao conectado."
        try:
            loop = asyncio.get_event_loop()
            resposta = await loop.run_in_executor(
                None,
                lambda: self.engine.processar(texto, from_hud=True)
            )
            return resposta or "..."
        except Exception as e:
            return f"Erro: {e}"

    def _setup_commands(self):
        bot = self.bot

        # ═══ SISTEMA ═══

        @bot.command(name="status")
        async def cmd_status(ctx):
            r = await self._processar_engine("status do sistema")
            await ctx.send(f"**Status:** {r}")

        @bot.command(name="ping")
        async def cmd_ping(ctx):
            latencia = round(bot.latency * 1000)
            await ctx.send(f"Pong! Latencia: {latencia}ms")

        @bot.command(name="horas", aliases=["hora", "time"])
        async def cmd_horas(ctx):
            r = await self._processar_engine("que horas sao")
            await ctx.send(f"**Hora:** {r}")

        @bot.command(name="atividade", aliases=["fazendo"])
        async def cmd_atividade(ctx):
            r = await self._processar_engine("o que estou fazendo")
            await ctx.send(f"**Atividade:** {r}")

        @bot.command(name="resumo")
        async def cmd_resumo(ctx):
            r = await self._processar_engine("resumo do dia")
            await ctx.send(f"**Resumo:** {r}")

        # ═══ HARDWARE ═══

        @bot.command(name="cpu")
        async def cmd_cpu(ctx):
            r = await self._processar_engine("status cpu")
            await ctx.send(f"**CPU:** {r}")

        @bot.command(name="ram", aliases=["memoria"])
        async def cmd_ram(ctx):
            r = await self._processar_engine("status ram")
            await ctx.send(f"**RAM:** {r}")

        @bot.command(name="disco", aliases=["hd", "ssd"])
        async def cmd_disco(ctx):
            r = await self._processar_engine("status disco")
            await ctx.send(f"**Disco:** {r}")

        @bot.command(name="processos", aliases=["procs", "top"])
        async def cmd_processos(ctx):
            r = await self._processar_engine("quais processos estao rodando")
            await ctx.send(f"**Processos:** {r}")

        @bot.command(name="rede", aliases=["network", "net"])
        async def cmd_rede(ctx):
            r = await self._processar_engine("status da rede")
            await ctx.send(f"**Rede:** {r}")

        # ═══ APPS ═══

        @bot.command(name="abrir", aliases=["open"])
        async def cmd_abrir(ctx, *, app: str = None):
            if not app:
                await ctx.send("Uso: `!abrir <nome do app>`")
                return
            r = await self._processar_engine(f"abrir {app}")
            await ctx.send(f"**App:** {r}")

        @bot.command(name="fechar", aliases=["close"])
        async def cmd_fechar(ctx, *, app: str = None):
            if not app:
                await ctx.send("Uso: `!fechar <nome do app>`")
                return
            r = await self._processar_engine(f"fechar {app}")
            await ctx.send(f"**Fechar:** {r}")

        # ═══ PESQUISA ═══

        @bot.command(name="pesquisar", aliases=["pesquisa", "busca", "search"])
        async def cmd_pesquisar(ctx, *, query: str = None):
            if not query:
                await ctx.send("Uso: `!pesquisar <termo>`")
                return
            async with ctx.typing():
                r = await self._processar_engine(f"pesquisar {query}")
                for chunk in self._split_message(f"**Pesquisa:** {r}"):
                    await ctx.send(chunk)

        @bot.command(name="clima", aliases=["tempo", "weather"])
        async def cmd_clima(ctx):
            async with ctx.typing():
                r = await self._processar_engine("clima atual")
                await ctx.send(f"**Clima:** {r}")

        # ═══ CONTROLE ═══

        @bot.command(name="modo")
        async def cmd_modo(ctx, *, nome: str = None):
            if not nome:
                await ctx.send("Uso: `!modo <trabalho/gamer/noturno/manha>`")
                return
            r = await self._processar_engine(f"modo {nome}")
            await ctx.send(f"**Modo:** {r}")

        @bot.command(name="modos", aliases=["rotinas"])
        async def cmd_modos(ctx):
            embed = discord.Embed(
                title="Modos Disponiveis",
                description="Use `!modo <nome>` para ativar",
                color=0x2a7fff,
            )
            embed.add_field(
                name="Trabalho",
                value="Abre Chrome, volume 40%",
                inline=True
            )
            embed.add_field(
                name="Gamer",
                value="Volume 80%, otimizado pra jogos",
                inline=True
            )
            embed.add_field(
                name="Noturno",
                value="Brilho 30%, volume 20%",
                inline=True
            )
            embed.add_field(
                name="Manha",
                value="Briefing: hora, clima, luzes",
                inline=True
            )
            embed.add_field(
                name="Organizar",
                value="Organiza a pasta Downloads",
                inline=True
            )
            await ctx.send(embed=embed)

        # ═══ VOZ ═══

        @bot.command(name="dizer", aliases=["fala", "falar", "say"])
        async def cmd_dizer(ctx, *, texto: str = None):
            if not texto:
                await ctx.send("Uso: `!dizer <texto pra falar no PC>`")
                return
            if self.engine and self.engine.tts:
                self.engine.tts.speak(texto)
                await ctx.send(f"**Falando no PC:** {texto}")
            else:
                await ctx.send("TTS indisponivel.")

        @bot.command(name="voz")
        async def cmd_voz(ctx, estado: str = None):
            if not estado or estado.lower() not in ("on", "off"):
                status = "ATIVA" if getattr(self, "voz_ativa", False) else "DESATIVA"
                await ctx.send(f"Voz no PC esta: **{status}**\nUse `!voz on` ou `!voz off`")
                return
            self.voz_ativa = (estado.lower() == "on")
            await ctx.send(f"Voz no PC: **{'ATIVADA' if self.voz_ativa else 'DESATIVADA'}**, Sir.")

        # ═══ LEMBRETE ═══

        @bot.command(name="lembrar", aliases=["lembrete", "reminder"])
        async def cmd_lembrar(ctx, *, args: str = None):
            if not args:
                await ctx.send("Uso: `!lembrar em 5 minutos de tomar agua`")
                return
            r = await self._processar_engine(f"me lembre {args}")
            await ctx.send(f"**Lembrete:** {r}")

        # ═══ TURBO ═══

        @bot.command(name="turbo")
        async def cmd_turbo(ctx):
            r = await self._processar_engine("ativa o modo turbo")
            await ctx.send(f"**Turbo:** {r}")

        # ═══ HISTORICO ═══

        @bot.command(name="historico", aliases=["history", "cmds"])
        async def cmd_historico(ctx):
            if not self._historico_comandos:
                await ctx.send("Nenhum comando registrado.")
                return
            linhas = []
            for item in self._historico_comandos[-10:]:
                linhas.append(f"[{item['hora']}] {item['cmd']}")
            await ctx.send("**Historico:**\n" + "\n".join(linhas))

        # ═══ AJUDA ═══

        @bot.command(name="help", aliases=["ajuda", "comandos"])
        async def cmd_help(ctx):
            embed = discord.Embed(
                title="J.A.R.V.I.S. - Comandos",
                description="Lista completa de comandos disponiveis",
                color=0x00e5ff,
            )
            embed.add_field(
                name="Sistema",
                value=(
                    "`!status` - Telemetria completa\n"
                    "`!cpu` - CPU detalhado\n"
                    "`!ram` - Memoria RAM\n"
                    "`!disco` - Espaco em disco\n"
                    "`!processos` - Top processos\n"
                    "`!rede` - Status da rede\n"
                    "`!ping` - Latencia"
                ),
                inline=False
            )
            embed.add_field(
                name="Apps & Controle",
                value=(
                    "`!abrir <app>` - Abre programa\n"
                    "`!fechar <app>` - Fecha programa\n"
                    "`!modo <nome>` - Executa rotina\n"
                    "`!modos` - Lista rotinas"
                ),
                inline=False
            )
            embed.add_field(
                name="Inteligencia",
                value=(
                    "`!pesquisar <X>` - Pesquisa web\n"
                    "`!clima` - Tempo agora\n"
                    "`!horas` - Que horas\n"
                    "`!atividade` - O que esta fazendo\n"
                    "`!resumo` - Resumo do dia"
                ),
                inline=False
            )
            embed.add_field(
                name="Voz & Lembretes",
                value=(
                    "`!dizer <texto>` - Faz Jarvis falar no PC\n"
                    "`!voz on/off` - Controla voz\n"
                    "`!lembrar em X de Y` - Agenda lembrete"
                ),
                inline=False
            )
            embed.add_field(
                name="Chat",
                value=(
                    "`!turbo` - Ativa modo Turbo\n"
                    "`!historico` - Ultimos comandos\n"
                    "Apenas converse normalmente sem prefixo."
                ),
                inline=False
            )
            embed.set_footer(text="J.A.R.V.I.S. v3.0 | DM exclusivo do Sir")
            await ctx.send(embed=embed)

    def send_dm_sync(self, mensagem):
        """Envia DM para o dono (chamada sincrona)."""
        if not self.bot_ready or not self.owner or not self.loop:
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.owner.send(mensagem),
                self.loop
            )
            future.result(timeout=10)
            return True
        except Exception as e:
            print(f"[DISCORD] erro send DM: {e}")
            return False

    def iniciar(self):
        """Inicia o bot em thread separada."""
        if not DISCORD_TOKEN:
            print("[DISCORD] DISCORD_TOKEN nao configurado no .env")
            return False
        if OWNER_ID == 0:
            print("[DISCORD] DISCORD_OWNER_ID nao configurado no .env")
            return False

        def run_bot():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(self.bot.start(DISCORD_TOKEN))
            except Exception as e:
                print(f"[DISCORD] erro bot: {e}")

        thread = threading.Thread(target=run_bot, daemon=True, name="discord-bot")
        thread.start()
        return True

    def parar(self):
        """Para o bot."""
        try:
            if self.loop and self.bot:
                asyncio.run_coroutine_threadsafe(
                    self.bot.close(),
                    self.loop
                )
        except Exception:
            pass
