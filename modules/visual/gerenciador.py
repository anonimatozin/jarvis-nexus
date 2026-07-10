"""
Gerenciador da memoria visual - thread de captura + auto-limpeza.
"""
import os
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

from modules.visual.captura import (
    capturar_tela, rodar_ocr, criptografar_e_salvar,
    get_janela_ativa, calcular_pontuacao, descriptografar
)
from modules.visual.pendrive import (
    pendrive_conectado, sincronizar_cache_para_pendrive,
    criar_info_pendrive, get_espaco_livre_mb,
    get_espaco_usado_jarvis_mb, listar_cache
)
from modules.visual.database import get_db


INTERVALO_CAPTURA = 120  # 2 minutos
INTERVALO_LIMPEZA = 1800  # 30 minutos
INTERVALO_SINCRONIA_CHECK = 30  # 30s pra checar pendrive
ESPACO_MINIMO_MB = 500  # libera espaco se < 500MB livres


class MemoriaVisual:
    def __init__(self, callback_voz=None):
        self.callback_voz = callback_voz  # pra falar avisos
        self.running = False
        self.pausada = False
        self.thread_captura = None
        self.thread_limpeza = None
        self.thread_pendrive = None

        self._ultimo_pendrive_estado = pendrive_conectado()
        self._capturas_no_cache = 0

        self.db = get_db()

        if pendrive_conectado():
            criar_info_pendrive()

    def iniciar(self):
        if self.running:
            return
        self.running = True

        self.thread_captura = threading.Thread(
            target=self._loop_captura, daemon=True, name="visual_captura"
        )
        self.thread_captura.start()

        self.thread_limpeza = threading.Thread(
            target=self._loop_limpeza, daemon=True, name="visual_limpeza"
        )
        self.thread_limpeza.start()

        self.thread_pendrive = threading.Thread(
            target=self._loop_pendrive, daemon=True, name="visual_pendrive"
        )
        self.thread_pendrive.start()

        print("[VISUAL] Iniciado (captura a cada 2min)")

    def parar(self):
        self.running = False
        try:
            self.db.close()
        except:
            pass

    def pausar(self):
        self.pausada = True
        print("[VISUAL] Pausado")

    def retomar(self):
        self.pausada = False
        print("[VISUAL] Retomado")

    def status(self):
        stats = self.db.estatisticas()
        return {
            "rodando": self.running,
            "pausada": self.pausada,
            "pendrive_conectado": pendrive_conectado(),
            "cache_pendente": len(listar_cache()),
            "espaco_livre_mb": round(get_espaco_livre_mb()),
            "espaco_usado_mb": round(get_espaco_usado_jarvis_mb()),
            "total_capturas": stats.get("total", 0),
            "tamanho_total_mb": round(stats.get("tamanho_mb", 0), 1),
        }

    # ════════ LOOPS ════════

    def _loop_captura(self):
        time.sleep(10)  # delay inicial
        while self.running:
            try:
                if not self.pausada:
                    self._fazer_captura()
            except Exception as e:
                print(f"[VISUAL CAPTURA] {e}")

            # Espera intervalo (verifica running a cada 1s)
            for _ in range(INTERVALO_CAPTURA):
                if not self.running:
                    return
                time.sleep(1)

    def _fazer_captura(self):
        agora = datetime.now()

        # 1. Screenshot
        img_bytes = capturar_tela()
        if not img_bytes:
            return

        # 2. App ativo
        app, titulo = get_janela_ativa()

        # 3. OCR
        ocr = rodar_ocr(img_bytes)

        # 4. Pontuacao
        score = calcular_pontuacao(ocr, app, titulo)

        # Se score muito baixo, nem salva
        if score < 15:
            print(f"[VISUAL] Skip (score {score}): {app}")
            return

        # 5. Criptografa e salva
        path, tamanho_kb = criptografar_e_salvar(img_bytes, agora)
        if not path:
            return

        # 6. Salva no banco
        self.db.adicionar_captura(
            timestamp=agora.isoformat(),
            arquivo_path=path,
            app_ativo=app,
            janela_titulo=titulo,
            ocr_texto=ocr,
            pontuacao=score,
            tamanho_kb=int(tamanho_kb),
        )

        destino = "PENDRIVE" if pendrive_conectado() else "CACHE"
        print(f"[VISUAL] +{destino} score={score} {app[:20]} ({tamanho_kb:.0f}KB)")

    def _loop_pendrive(self):
        time.sleep(5)
        while self.running:
            try:
                conectado_agora = pendrive_conectado()

                # Detectou conexao
                if conectado_agora and not self._ultimo_pendrive_estado:
                    pendentes = len(listar_cache())
                    if pendentes > 0:
                        movidos = sincronizar_cache_para_pendrive()
                        print(f"[VISUAL] Pendrive conectado! Sincronizado {movidos}")
                        # Reconecta DB no pendrive
                        self.db.reconectar()
                        if self.callback_voz:
                            self.callback_voz(
                                f"Pendrive reconectado. {movidos} capturas sincronizadas, Sir."
                            )
                    else:
                        if self.callback_voz:
                            self.callback_voz("Pendrive reconectado, Sir.")
                        self.db.reconectar()

                # Detectou desconexao
                elif not conectado_agora and self._ultimo_pendrive_estado:
                    print("[VISUAL] Pendrive REMOVIDO - modo cache")
                    self.db.reconectar()  # vai pro cache
                    if self.callback_voz:
                        self.callback_voz(
                            "Sir, pendrive removido. Modo cache ativo."
                        )

                self._ultimo_pendrive_estado = conectado_agora

            except Exception as e:
                print(f"[VISUAL PENDRIVE] {e}")

            for _ in range(INTERVALO_SINCRONIA_CHECK):
                if not self.running:
                    return
                time.sleep(1)

    def _loop_limpeza(self):
        time.sleep(60)  # espera 1min pra primeira limpeza
        while self.running:
            try:
                self._fazer_limpeza()
            except Exception as e:
                print(f"[VISUAL LIMPEZA] {e}")

            for _ in range(INTERVALO_LIMPEZA):
                if not self.running:
                    return
                time.sleep(1)

    def _fazer_limpeza(self):
        """Auto-limpeza baseada em pontuacao + espaco."""
        # 1. Pega candidatos com score baixo
        candidatos = self.db.candidatos_para_apagar(dias=7)

        if not candidatos:
            return

        # 2. Se espaco ta apertado, agressivo
        livre = get_espaco_livre_mb()
        agressivo = livre < ESPACO_MINIMO_MB

        apagados = 0
        for cap_id, path, score, ts in candidatos:
            try:
                # Apaga arquivo do disco
                p = Path(path)
                if p.exists():
                    p.unlink()
                # Marca no banco
                self.db.marcar_apagada(cap_id)
                apagados += 1

                # Se nao ta agressivo, para depois de 20
                if not agressivo and apagados >= 20:
                    break
            except Exception as e:
                print(f"[VISUAL LIMPEZA] erro apagar {path}: {e}")

        if apagados > 0:
            print(f"[VISUAL] Limpeza: {apagados} capturas apagadas")

    # ════════ BUSCA (chamado pelo engine) ════════

    def buscar_horario(self, hora_str, dia_offset=0):
        """
        hora_str ex: '14:30' (so hora) ou '18/06 14:30' (dia+hora)
        dia_offset: 0=hoje, -1=ontem, -2=anteontem, etc
        """
        try:
            from datetime import timedelta
            base = datetime.now() + timedelta(days=dia_offset)

            if " " in hora_str:
                quando = datetime.strptime(f"{base.year} {hora_str}", "%Y %d/%m %H:%M")
            else:
                h, m = hora_str.split(":")
                quando = base.replace(hour=int(h), minute=int(m), second=0, microsecond=0)

            print(f"[VISUAL BUSCA] Buscando em {quando.isoformat()} (offset {dia_offset})")
            return self.db.buscar_por_horario(quando.isoformat(), tolerancia_min=30)
        except Exception as e:
            print(f"[VISUAL] erro buscar horario: {e}")
            return []

    def buscar_dia_inteiro(self, dia_offset=0):
        """Lista TODAS capturas de um dia."""
        try:
            from datetime import timedelta
            base = datetime.now() + timedelta(days=dia_offset)
            inicio = base.replace(hour=0, minute=0, second=0).isoformat()
            fim = base.replace(hour=23, minute=59, second=59).isoformat()
            cur = self.db.conn.cursor()
            cur.execute("""
                SELECT * FROM capturas
                WHERE timestamp BETWEEN ? AND ?
                AND apagado=0
                ORDER BY timestamp
            """, (inicio, fim))
            return [self.db._row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[VISUAL] erro dia inteiro: {e}")
            return []

    def buscar_texto(self, termo):
        return self.db.buscar_por_texto(termo, limite=10)

    def buscar_app(self, app, dias=1):
        return self.db.buscar_por_app(app, ultimos_dias=dias)

    def descrever_captura(self, captura_id, brain=None):
        """
        Pega 1 captura, descriptografa, manda pra IA descrever.
        So usa IA se brain fornecido.
        """
        try:
            cur = self.db.conn.cursor()
            cur.execute("SELECT * FROM capturas WHERE id=?", (captura_id,))
            row = cur.fetchone()
            if not row:
                return None
            cap = self.db._row_to_dict(row)

            if cap.get("descricao_ia"):
                return cap["descricao_ia"]

            # Tem brain? Usa IA
            if brain:
                ocr = cap.get("ocr_texto", "")[:1500]
                app = cap.get("app_ativo", "")
                titulo = cap.get("janela_titulo", "")
                prompt = (
                    f"Resumo curto do que o usuario fazia nesta tela:\n"
                    f"App: {app}\nJanela: {titulo}\n"
                    f"Texto visivel (OCR):\n{ocr}\n\n"
                    f"Responda em 1-2 frases."
                )
                desc = brain.think(prompt)
                if desc:
                    self.db.adicionar_descricao_ia(captura_id, desc)
                    return desc

            # Fallback sem IA
            return f"{cap.get('app_ativo', '?')} - {cap.get('janela_titulo', '?')[:80]}"
        except Exception as e:
            return None


# Singleton
_instance = None

def get_memoria_visual(callback_voz=None):
    global _instance
    if _instance is None:
        _instance = MemoriaVisual(callback_voz=callback_voz)
    return _instance
