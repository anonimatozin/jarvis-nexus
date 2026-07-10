# memory/database.py
"""
J.A.R.V.I.S. - Sistema de Memória Persistente v1.2
Agora com suporte a perfil de personalidade adaptativa.

Tabelas:
  conversations       → histórico completo de mensagens
  preferences         → preferências do usuário
  learned_facts       → fatos aprendidos sobre o usuário
  command_log         → auditoria de comandos executados
  personality_profile → perfil comportamental do usuário (NOVO)
  feedback_log        → feedbacks explícitos do usuário (NOVO)
  interaction_patterns→ padrões de interação detectados (NOVO)
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_PATH
from utils.logger import setup_logger

logger = setup_logger("memory")


class JarvisMemory:
    """Gerenciador completo de memória persistente do Jarvis."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path   = db_path
        self.connection = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        # Melhora performance
        self.cursor.execute("PRAGMA journal_mode=WAL")
        self.cursor.execute("PRAGMA foreign_keys=ON")

        self._create_tables()
        logger.info(f"Memória inicializada: {db_path}")

    # ──────────────────────────────────────────────────────────────────────
    #  CRIAÇÃO DE TABELAS
    # ──────────────────────────────────────────────────────────────────────

    def _create_tables(self):
        """Cria todas as tabelas necessárias."""

        # Histórico de conversas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT NOT NULL,
                role       TEXT NOT NULL,
                message    TEXT NOT NULL,
                intent     TEXT,
                session_id TEXT
            )
        """)

        # Preferências do usuário
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT UNIQUE NOT NULL,
                value      TEXT NOT NULL,
                category   TEXT,
                updated_at TEXT NOT NULL
            )
        """)

        # Fatos aprendidos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_facts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                fact             TEXT NOT NULL,
                source           TEXT,
                confidence       REAL DEFAULT 1.0,
                created_at       TEXT NOT NULL,
                times_referenced INTEGER DEFAULT 0
            )
        """)

        # Log de comandos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command   TEXT NOT NULL,
                module    TEXT,
                success   INTEGER DEFAULT 1,
                details   TEXT
            )
        """)

        # ── NOVO: Perfil de personalidade ─────────────────────────────────
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_profile (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT UNIQUE NOT NULL,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes      TEXT
            )
        """)

        # ── NOVO: Log de feedbacks explícitos ─────────────────────────────
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                description  TEXT NOT NULL,
                context      TEXT,
                applied      INTEGER DEFAULT 0
            )
        """)

        # ── NOVO: Padrões de interação detectados ─────────────────────────
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_patterns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern     TEXT NOT NULL,
                category    TEXT NOT NULL,
                occurrences INTEGER DEFAULT 1,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                examples    TEXT
            )
        """)

        self.connection.commit()

    # ──────────────────────────────────────────────────────────────────────
    #  CONVERSAS
    # ──────────────────────────────────────────────────────────────────────

    def save_message(
        self,
        role: str,
        message: str,
        intent: str = None,
        session_id: str = None,
    ):
        """Salva uma mensagem no histórico."""
        self.cursor.execute("""
            INSERT INTO conversations
                (timestamp, role, message, intent, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), role, message, intent, session_id))
        self.connection.commit()

    def get_recent_messages(self, limit: int = 20) -> list:
        """Retorna as N mensagens mais recentes em ordem cronológica."""
        self.cursor.execute("""
            SELECT role, message FROM conversations
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = self.cursor.fetchall()
        return [
            {"role": r["role"], "content": r["message"]}
            for r in reversed(rows)
        ]

    def get_conversation_count(self) -> int:
        """Retorna total de mensagens armazenadas."""
        self.cursor.execute(
            "SELECT COUNT(*) as c FROM conversations"
        )
        return self.cursor.fetchone()["c"]

    # ──────────────────────────────────────────────────────────────────────
    #  PREFERÊNCIAS
    # ──────────────────────────────────────────────────────────────────────

    def set_preference(
        self,
        key: str,
        value: str,
        category: str = "general",
    ):
        """Salva ou atualiza uma preferência."""
        self.cursor.execute("""
            INSERT INTO preferences (key, value, category, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                category   = excluded.category,
                updated_at = excluded.updated_at
        """, (key, value, category, datetime.now().isoformat()))
        self.connection.commit()

    def get_preference(self, key: str) -> Optional[str]:
        """Busca uma preferência pelo nome."""
        self.cursor.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        )
        row = self.cursor.fetchone()
        return row["value"] if row else None

    def get_all_preferences(self) -> dict:
        """Retorna todas as preferências como dicionário."""
        self.cursor.execute("SELECT key, value FROM preferences")
        return {r["key"]: r["value"] for r in self.cursor.fetchall()}

    # ──────────────────────────────────────────────────────────────────────
    #  FATOS APRENDIDOS
    # ──────────────────────────────────────────────────────────────────────

    def learn_fact(
        self,
        fact: str,
        source: str = "conversation",
        confidence: float = 1.0,
    ):
        """Armazena um fato aprendido."""
        self.cursor.execute("""
            INSERT INTO learned_facts
                (fact, source, confidence, created_at)
            VALUES (?, ?, ?, ?)
        """, (fact, source, confidence, datetime.now().isoformat()))
        self.connection.commit()

    def search_facts(self, keyword: str) -> list:
        """Busca fatos que contenham a palavra-chave."""
        self.cursor.execute("""
            SELECT fact, confidence, created_at FROM learned_facts
            WHERE fact LIKE ? ORDER BY confidence DESC
        """, (f"%{keyword}%",))
        return [dict(r) for r in self.cursor.fetchall()]

    # ──────────────────────────────────────────────────────────────────────
    #  PERFIL DE PERSONALIDADE (NOVO)
    # ──────────────────────────────────────────────────────────────────────

    def set_personality_trait(
        self,
        key: str,
        value: str,
        notes: str = None,
    ):
        """
        Define ou atualiza um traço do perfil de personalidade.

        Exemplos de keys:
            humor_level       → "alto" / "moderado" / "baixo"
            communication_style → "direto" / "elaborado"
            sarcasm_tolerance → "alto" / "moderado" / "baixo"
            formality_level   → "informal" / "semi-formal" / "formal"
            preferred_tone    → "seco" / "zoeiro" / "técnico"
            feedback_frequency → "alta" / "baixa"
        """
        self.cursor.execute("""
            INSERT INTO personality_profile (key, value, updated_at, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                updated_at = excluded.updated_at,
                notes      = excluded.notes
        """, (key, value, datetime.now().isoformat(), notes))
        self.connection.commit()

    def get_personality_trait(self, key: str) -> Optional[str]:
        """Retorna um traço específico do perfil."""
        self.cursor.execute(
            "SELECT value FROM personality_profile WHERE key = ?", (key,)
        )
        row = self.cursor.fetchone()
        return row["value"] if row else None

    def get_full_personality_profile(self) -> dict:
        """Retorna o perfil completo de personalidade."""
        self.cursor.execute(
            "SELECT key, value, notes FROM personality_profile"
        )
        return {
            r["key"]: {"value": r["value"], "notes": r["notes"]}
            for r in self.cursor.fetchall()
        }

    # ──────────────────────────────────────────────────────────────────────
    #  FEEDBACK EXPLÍCITO (NOVO)
    # ──────────────────────────────────────────────────────────────────────

    def log_feedback(
        self,
        feedback_type: str,
        description: str,
        context: str = None,
    ):
        """
        Registra um feedback explícito do usuário.

        Args:
            feedback_type: 'tom', 'humor', 'resposta', 'comportamento'
            description  : O que o usuário disse/pediu
            context      : Contexto da conversa onde surgiu
        """
        self.cursor.execute("""
            INSERT INTO feedback_log
                (timestamp, feedback_type, description, context, applied)
            VALUES (?, ?, ?, ?, 0)
        """, (datetime.now().isoformat(), feedback_type, description, context))
        self.connection.commit()
        logger.info(f"Feedback registrado: [{feedback_type}] {description}")

    def get_recent_feedbacks(self, limit: int = 10) -> list:
        """Retorna os feedbacks mais recentes."""
        self.cursor.execute("""
            SELECT feedback_type, description, context, timestamp
            FROM feedback_log
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in self.cursor.fetchall()]

    # ──────────────────────────────────────────────────────────────────────
    #  PADRÕES DE INTERAÇÃO (NOVO)
    # ──────────────────────────────────────────────────────────────────────

    def record_pattern(
        self,
        pattern: str,
        category: str,
        example: str = None,
    ):
        """
        Registra ou incrementa um padrão de interação observado.

        Categorias: 'humor', 'vocabulario', 'tom', 'preferencia', 'giria'
        """
        now = datetime.now().isoformat()
        existing = self.cursor.execute(
            "SELECT id, occurrences, examples FROM interaction_patterns "
            "WHERE pattern = ? AND category = ?",
            (pattern, category)
        ).fetchone()

        if existing:
            examples = existing["examples"] or ""
            if example and example not in examples:
                examples = f"{examples}|{example}" if examples else example

            self.cursor.execute("""
                UPDATE interaction_patterns
                SET occurrences = occurrences + 1,
                    last_seen   = ?,
                    examples    = ?
                WHERE id = ?
            """, (now, examples[:500], existing["id"]))
        else:
            self.cursor.execute("""
                INSERT INTO interaction_patterns
                    (pattern, category, occurrences, first_seen, last_seen, examples)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (pattern, category, now, now, example or ""))

        self.connection.commit()

    def get_top_patterns(self, category: str = None, limit: int = 10) -> list:
        """Retorna os padrões mais frequentes."""
        if category:
            self.cursor.execute("""
                SELECT pattern, category, occurrences, examples
                FROM interaction_patterns
                WHERE category = ?
                ORDER BY occurrences DESC LIMIT ?
            """, (category, limit))
        else:
            self.cursor.execute("""
                SELECT pattern, category, occurrences, examples
                FROM interaction_patterns
                ORDER BY occurrences DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in self.cursor.fetchall()]

    # ──────────────────────────────────────────────────────────────────────
    #  LOG DE COMANDOS
    # ──────────────────────────────────────────────────────────────────────

    def log_command(
        self,
        command: str,
        module: str = None,
        success: bool = True,
        details: str = None,
    ):
        """Registra um comando executado para auditoria."""
        self.cursor.execute("""
            INSERT INTO command_log
                (timestamp, command, module, success, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            command, module, int(success), details,
        ))
        self.connection.commit()

    # ──────────────────────────────────────────────────────────────────────
    #  ESTATÍSTICAS
    # ──────────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Retorna estatísticas gerais da memória."""
        stats = {}
        tables = {
            "total_messages"  : "conversations",
            "total_preferences": "preferences",
            "total_facts"     : "learned_facts",
            "total_commands"  : "command_log",
            "total_feedbacks" : "feedback_log",
            "total_patterns"  : "interaction_patterns",
        }
        for key, table in tables.items():
            self.cursor.execute(f"SELECT COUNT(*) as c FROM {table}")
            stats[key] = self.cursor.fetchone()["c"]
        return stats

    # ──────────────────────────────────────────────────────────────────────
    #  LIFECYCLE
    # ──────────────────────────────────────────────────────────────────────

    def close(self):
        """Fecha a conexão com segurança."""
        try:
            self.connection.close()
            logger.info("Memória fechada com segurança.")
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()