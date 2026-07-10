# modules/memory/context_manager.py
"""
J.A.R.V.I.S. - Context Manager Module
Gerenciamento de contexto com sliding window e auto-resumo.
Inspirado no PanPenek/JarvisAi.
"""

import json
from datetime import datetime
from pathlib import Path
from collections import deque

class ContextManager:
    """Gerencia contexto de conversas com sliding window."""
    
    def __init__(self, max_messages=50, summary_threshold=30, data_dir=None):
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.context_file = self.data_dir / "conversation_context.json"
        
        # Sliding window
        self.messages = deque(maxlen=max_messages)
        self.summary = ""
        self.total_messages = 0
        
        self._load_context()
    
    def _load_context(self):
        """Carrega contexto salvo."""
        try:
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.summary = data.get('summary', '')
                    for msg in data.get('messages', []):
                        self.messages.append(msg)
                    self.total_messages = data.get('total_messages', 0)
        except Exception:
            pass
    
    def _save_context(self):
        """Salva contexto em disco."""
        try:
            data = {
                'summary': self.summary,
                'messages': list(self.messages),
                'total_messages': self.total_messages,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def add_message(self, role, content):
        """Adiciona uma mensagem ao contexto."""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.messages.append(message)
        self.total_messages += 1
        
        # Verifica se precisa resumir
        if len(self.messages) >= self.summary_threshold:
            self._auto_summarize()
        
        self._save_context()
    
    def _auto_summarize(self):
        """Gera resumo automatico das mensagens antigas."""
        if len(self.messages) < 10:
            return
        
        # Pega metade das mensagens mais antigas para resumir
        messages_to_summarize = []
        remaining = deque()
        
        half = len(self.messages) // 2
        for i, msg in enumerate(self.messages):
            if i < half:
                messages_to_summarize.append(msg)
            else:
                remaining.append(msg)
        
        # Gera resumo basico
        if messages_to_summarize:
            topics = self._extract_topics(messages_to_summarize)
            new_summary = f"Contexto anterior: {', '.join(topics[:5])}"
            
            if self.summary:
                self.summary = f"{self.summary} | {new_summary}"
            else:
                self.summary = new_summary
            
            # Mantem apenas metade das mensagens
            self.messages = remaining
    
    def _extract_topics(self, messages):
        """Extrai topicos principais das mensagens."""
        # Palavras-chave comuns
        keywords = {
            'programacao': ['python', 'javascript', 'código', 'programa', 'função', 'classe'],
            'arquivos': ['arquivo', 'pasta', 'diretório', 'salvar', 'abrir', 'ler'],
            'sistema': ['computador', 'tela', 'janela', 'processo', 'memória', 'cpu'],
            'internet': ['web', 'site', 'url', 'pesquisar', 'google', 'baixar'],
            'musica': ['música', 'tocar', 'spotify', 'player', 'playlist'],
            'clima': ['clima', 'tempo', 'temperatura', 'previsão'],
            'lembretes': ['lembrete', 'alarme', 'agendar', 'horário', 'tarefa'],
        }
        
        topics = set()
        for msg in messages:
            content = msg.get('content', '').lower()
            for topic, words in keywords.items():
                if any(word in content for word in words):
                    topics.add(topic)
        
        return list(topics) if topics else ['conversa geral']
    
    def get_context_for_llm(self, max_tokens=2000):
        """Retorna contexto formatado para enviar ao LLM."""
        context_parts = []
        
        # Adiciona resumo se existir
        if self.summary:
            context_parts.append(f"[RESUMO] {self.summary}")
        
        # Adiciona mensagens recentes
        for msg in self.messages:
            role = "Usuario" if msg['role'] == 'user' else "Jarvis"
            content = msg['content'][:200]  # Limita tamanho
            context_parts.append(f"{role}: {content}")
        
        context = "\n".join(context_parts)
        
        # Trunca se passar do limite de tokens (aproximado)
        if len(context) > max_tokens * 4:  # ~4 chars por token
            context = context[-(max_tokens * 4):]
            context = f"[...contexto anterior truncado...]\n{context}"
        
        return context
    
    def clear_context(self):
        """Limpa todo o contexto."""
        self.messages.clear()
        self.summary = ""
        self.total_messages = 0
        self._save_context()
        return "Contexto limpo."
    
    def get_stats(self):
        """Retorna estatisticas do contexto."""
        return {
            'total_messages': self.total_messages,
            'current_messages': len(self.messages),
            'max_messages': self.max_messages,
            'has_summary': bool(self.summary),
            'summary_length': len(self.summary),
        }
    
    def search_context(self, query):
        """Busca no contexto por palavra-chave."""
        results = []
        query_lower = query.lower()
        
        # Busca nas mensagens
        for msg in self.messages:
            if query_lower in msg.get('content', '').lower():
                results.append({
                    'role': msg['role'],
                    'content': msg['content'][:100],
                    'timestamp': msg.get('timestamp', '')
                })
        
        # Busca no resumo
        if query_lower in self.summary.lower():
            results.append({
                'role': 'summary',
                'content': self.summary[:200],
                'timestamp': ''
            })
        
        return results
    
    def export_context(self, filename=None):
        """Exporta contexto para arquivo."""
        if filename is None:
            filename = f"context_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.data_dir / filename
        
        data = {
            'summary': self.summary,
            'messages': list(self.messages),
            'stats': self.get_stats(),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return f"Contexto exportado: {filepath}"


def criar_context_manager():
    """Retorna instancia do context manager."""
    return ContextManager()
