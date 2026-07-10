import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, db_path: str = "data/audit_log.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._init_database()

    def _ensure_directory(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    module TEXT,
                    action TEXT,
                    user_input TEXT,
                    system_output TEXT,
                    threat_level INTEGER,
                    threats_detected TEXT,
                    approved INTEGER,
                    reason TEXT,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT,
                    details TEXT,
                    blocked INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    allowed INTEGER,
                    reason TEXT
                )
            ''')

            conn.commit()

    def log_event(self, event_type: str, module: str = None, action: str = None,
                  user_input: str = None, system_output: str = None,
                  threat_level: int = 0, threats_detected: List[str] = None,
                  approved: bool = True, reason: str = None, metadata: Dict = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log
                    (timestamp, event_type, module, action, user_input, system_output,
                     threat_level, threats_detected, approved, reason, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    event_type,
                    module,
                    action,
                    user_input[:1000] if user_input else None,
                    system_output[:2000] if system_output else None,
                    threat_level,
                    json.dumps(threats_detected or []),
                    1 if approved else 0,
                    reason,
                    json.dumps(metadata or {})
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar evento: {e}")

    def log_security_event(self, event_type: str, severity: str, source: str,
                           details: str, blocked: bool = True):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO security_events
                    (timestamp, event_type, severity, source, details, blocked)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    event_type,
                    severity,
                    source,
                    details,
                    1 if blocked else 0
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar evento de segurança: {e}")

    def log_file_access(self, file_path: str, access_type: str, allowed: bool,
                        reason: str = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO file_access_log
                    (timestamp, file_path, access_type, allowed, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    file_path,
                    access_type,
                    1 if allowed else 0,
                    reason
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar acesso a arquivo: {e}")

    def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                since = (datetime.now() - timedelta(hours=hours)).isoformat()

                cursor.execute('''
                    SELECT timestamp, event_type, module, action, threat_level, approved
                    FROM audit_log
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (since, limit))

                return [
                    {
                        "timestamp": row[0],
                        "event_type": row[1],
                        "module": row[2],
                        "action": row[3],
                        "threat_level": row[4],
                        "approved": bool(row[5])
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Erro ao buscar eventos: {e}")
            return []

    def get_security_events(self, hours: int = 24) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                since = (datetime.now() - timedelta(hours=hours)).isoformat()

                cursor.execute('''
                    SELECT timestamp, event_type, severity, source, blocked
                    FROM security_events
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (since,))

                return [
                    {
                        "timestamp": row[0],
                        "event_type": row[1],
                        "severity": row[2],
                        "source": row[3],
                        "blocked": bool(row[4])
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Erro ao buscar eventos de segurança: {e}")
            return []

    def get_threat_summary(self, hours: int = 24) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                since = (datetime.now() - timedelta(hours=hours)).isoformat()

                cursor.execute('''
                    SELECT COUNT(*) FROM audit_log
                    WHERE threat_level > 0 AND timestamp > ?
                ''', (since,))
                threats_detected = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*) FROM audit_log
                    WHERE approved = 0 AND timestamp > ?
                ''', (since,))
                actions_blocked = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*) FROM security_events
                    WHERE blocked = 1 AND timestamp > ?
                ''', (since,))
                security_blocks = cursor.fetchone()[0]

                return {
                    "period_hours": hours,
                    "threats_detected": threats_detected,
                    "actions_blocked": actions_blocked,
                    "security_blocks": security_blocks,
                    "total_events": threats_detected + actions_blocked + security_blocks
                }
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return {}

    def export_log(self, days: int = 7, format: str = "json") -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                since = (datetime.now() - timedelta(days=days)).isoformat()

                cursor.execute('''
                    SELECT * FROM audit_log
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (since,))

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                data = [dict(zip(columns, row)) for row in rows]

                output_path = f"data/audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                return output_path
        except Exception as e:
            logger.error(f"Erro ao exportar log: {e}")
            return ""
