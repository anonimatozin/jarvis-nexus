import sqlite3
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self, db_path: str = "data/knowledge_base.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._init_database()

    def _ensure_directory(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS module_cache (
                    module_name TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    params TEXT DEFAULT '{}',
                    result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def store(self, category: str, key: str, content: str,
              metadata: Dict = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO knowledge
                    (category, key, content, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (category, key, content, json.dumps(metadata or {}),
                      datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erro ao armazenar conhecimento: {e}")
            return False

    def retrieve(self, category: str, key: str) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content, metadata, created_at, updated_at
                    FROM knowledge
                    WHERE category = ? AND key = ?
                ''', (category, key))

                row = cursor.fetchone()
                if row:
                    return {
                        "content": row[0],
                        "metadata": json.loads(row[1]),
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                return None
        except Exception as e:
            logger.error(f"Erro ao recuperar conhecimento: {e}")
            return None

    def search(self, query: str, category: str = None,
               limit: int = 10) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute('''
                        SELECT category, key, content, metadata
                        FROM knowledge
                        WHERE category = ? AND content LIKE ?
                        LIMIT ?
                    ''', (category, f"%{query}%", limit))
                else:
                    cursor.execute('''
                        SELECT category, key, content, metadata
                        FROM knowledge
                        WHERE content LIKE ?
                        LIMIT ?
                    ''', (f"%{query}%", limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "category": row[0],
                        "key": row[1],
                        "content": row[2],
                        "metadata": json.loads(row[3])
                    })
                return results
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento: {e}")
            return []

    def cache_module_data(self, module_name: str, data: Any,
                          expires_in_minutes: int = 30) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                expires_at = datetime.now().timestamp() + (expires_in_minutes * 60)

                cursor.execute('''
                    INSERT OR REPLACE INTO module_cache
                    (module_name, data, expires_at)
                    VALUES (?, ?, ?)
                ''', (module_name, json.dumps(data),
                      datetime.fromtimestamp(expires_at).isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erro ao cache módulo: {e}")
            return False

    def get_cached_module_data(self, module_name: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT data, expires_at
                    FROM module_cache
                    WHERE module_name = ?
                ''', (module_name,))

                row = cursor.fetchone()
                if row:
                    expires_at = datetime.fromisoformat(row[1])
                    if datetime.now() < expires_at:
                        return json.loads(row[0])
                    else:
                        cursor.execute('''
                            DELETE FROM module_cache
                            WHERE module_name = ?
                        ''', (module_name,))
                        conn.commit()
                return None
        except Exception as e:
            logger.error(f"Erro ao recuperar cache: {e}")
            return None

    def log_action(self, module_name: str, action: str,
                   params: Dict = None, result: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO action_log
                    (module_name, action, params, result)
                    VALUES (?, ?, ?, ?)
                ''', (module_name, action, json.dumps(params or {}), result))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erro ao registrar ação: {e}")
            return False

    def get_action_log(self, module_name: str = None,
                       limit: int = 100) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if module_name:
                    cursor.execute('''
                        SELECT module_name, action, params, result, timestamp
                        FROM action_log
                        WHERE module_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (module_name, limit))
                else:
                    cursor.execute('''
                        SELECT module_name, action, params, result, timestamp
                        FROM action_log
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (limit,))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "module_name": row[0],
                        "action": row[1],
                        "params": json.loads(row[2]),
                        "result": row[3],
                        "timestamp": row[4]
                    })
                return results
        except Exception as e:
            logger.error(f"Erro ao buscar log: {e}")
            return []

    def get_stats(self) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM knowledge')
                knowledge_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM module_cache')
                cache_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM action_log')
                log_count = cursor.fetchone()[0]

                return {
                    "knowledge_entries": knowledge_count,
                    "cached_modules": cache_count,
                    "total_actions": log_count
                }
        except Exception as e:
            logger.error(f"Erro ao buscar stats: {e}")
            return {}
