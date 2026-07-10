"""
Database SQLite da memoria visual.
Roda no pendrive (ou cache se removido).
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from modules.visual.pendrive import get_database_path


class VisualDB:
    def __init__(self):
        self.db_path = None
        self.conn = None
        self._connect()

    def _connect(self):
        try:
            self.db_path = get_database_path()
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._init_schema()
        except Exception as e:
            print(f"[VISUAL DB] erro connect: {e}")

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS capturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            arquivo_path TEXT NOT NULL,
            app_ativo TEXT,
            janela_titulo TEXT,
            ocr_texto TEXT,
            descricao_ia TEXT,
            pontuacao INTEGER DEFAULT 50,
            tamanho_kb INTEGER,
            apagado INTEGER DEFAULT 0,
            arquivado INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_timestamp ON capturas(timestamp);
        CREATE INDEX IF NOT EXISTS idx_app ON capturas(app_ativo);
        CREATE INDEX IF NOT EXISTS idx_pontuacao ON capturas(pontuacao);
        CREATE INDEX IF NOT EXISTS idx_apagado ON capturas(apagado);

        CREATE TABLE IF NOT EXISTS arquivos_pessoais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nome TEXT NOT NULL,
            conteudo TEXT,
            timestamp TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def reconectar(self):
        """Reconecta no pendrive (apos sincronia)."""
        try:
            if self.conn:
                self.conn.close()
        except:
            pass
        self._connect()

    def adicionar_captura(self, timestamp, arquivo_path, app_ativo="",
                          janela_titulo="", ocr_texto="", pontuacao=50,
                          tamanho_kb=0):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO capturas
                (timestamp, arquivo_path, app_ativo, janela_titulo,
                 ocr_texto, pontuacao, tamanho_kb)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, str(arquivo_path), app_ativo, janela_titulo,
                  ocr_texto, pontuacao, tamanho_kb))
            self.conn.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"[VISUAL DB] erro add: {e}")
            return None

    def adicionar_descricao_ia(self, captura_id, descricao):
        try:
            self.conn.execute(
                "UPDATE capturas SET descricao_ia=? WHERE id=?",
                (descricao, captura_id)
            )
            self.conn.commit()
        except Exception as e:
            print(f"[VISUAL DB] erro desc IA: {e}")

    def buscar_por_horario(self, quando_str, tolerancia_min=30):
        """quando_str ex: '2026-06-18 14:00:00'."""
        try:
            quando = datetime.fromisoformat(quando_str)
            inicio = (quando - timedelta(minutes=tolerancia_min)).isoformat()
            fim = (quando + timedelta(minutes=tolerancia_min)).isoformat()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM capturas
                WHERE timestamp BETWEEN ? AND ?
                AND apagado=0
                ORDER BY timestamp
            """, (inicio, fim))
            return [self._row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[VISUAL DB] erro buscar horario: {e}")
            return []

    def buscar_por_texto(self, termo, limite=10):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM capturas
                WHERE (ocr_texto LIKE ? OR descricao_ia LIKE ?
                       OR janela_titulo LIKE ? OR app_ativo LIKE ?)
                AND apagado=0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{termo}%", f"%{termo}%", f"%{termo}%", f"%{termo}%", limite))
            return [self._row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[VISUAL DB] erro buscar texto: {e}")
            return []

    def buscar_por_app(self, app, ultimos_dias=1):
        try:
            inicio = (datetime.now() - timedelta(days=ultimos_dias)).isoformat()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM capturas
                WHERE app_ativo LIKE ?
                AND timestamp >= ?
                AND apagado=0
                ORDER BY timestamp
            """, (f"%{app}%", inicio))
            return [self._row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[VISUAL DB] erro buscar app: {e}")
            return []

    def estatisticas(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM capturas WHERE apagado=0")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM capturas WHERE apagado=1")
            apagadas = cur.fetchone()[0]
            cur.execute("SELECT SUM(tamanho_kb) FROM capturas WHERE apagado=0")
            tamanho = cur.fetchone()[0] or 0
            cur.execute("""
                SELECT app_ativo, COUNT(*) as c, SUM(tamanho_kb) as t
                FROM capturas WHERE apagado=0 AND app_ativo != ''
                GROUP BY app_ativo
                ORDER BY c DESC LIMIT 5
            """)
            top_apps = [(r[0], r[1], r[2] or 0) for r in cur.fetchall()]
            return {
                "total": total,
                "apagadas": apagadas,
                "tamanho_mb": tamanho / 1024,
                "top_apps": top_apps,
            }
        except Exception as e:
            return {"erro": str(e)}

    def candidatos_para_apagar(self, dias=7):
        """
        Retorna capturas com score baixo ou antigas.
        Decide o que pode apagar pra liberar espaco.
        """
        try:
            limite = (datetime.now() - timedelta(days=dias)).isoformat()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT id, arquivo_path, pontuacao, timestamp
                FROM capturas
                WHERE apagado=0
                AND (
                    pontuacao < 20
                    OR (pontuacao < 40 AND timestamp < ?)
                    OR (pontuacao < 60 AND timestamp < ?)
                )
                ORDER BY pontuacao ASC, timestamp ASC
                LIMIT 100
            """, (
                (datetime.now() - timedelta(days=1)).isoformat(),
                (datetime.now() - timedelta(days=3)).isoformat(),
            ))
            return [(r[0], r[1], r[2], r[3]) for r in cur.fetchall()]
        except Exception as e:
            print(f"[VISUAL DB] erro candidatos: {e}")
            return []

    def marcar_apagada(self, captura_id):
        try:
            self.conn.execute("UPDATE capturas SET apagado=1 WHERE id=?", (captura_id,))
            self.conn.commit()
        except Exception as e:
            print(f"[VISUAL DB] erro marcar: {e}")

    def _row_to_dict(self, row):
        if not row:
            return None
        cols = ["id", "timestamp", "arquivo_path", "app_ativo",
                "janela_titulo", "ocr_texto", "descricao_ia",
                "pontuacao", "tamanho_kb", "apagado", "arquivado"]
        return dict(zip(cols, row))

    def close(self):
        try:
            self.conn.close()
        except:
            pass


_instance = None

def get_db():
    global _instance
    if _instance is None:
        _instance = VisualDB()
    return _instance
