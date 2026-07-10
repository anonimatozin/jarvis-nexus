# core/multi_api.py
import os
import requests
from pathlib import Path
import json

class MultiAPI:
    def __init__(self):
        self.apis = []
        self.current_index = 0
        self.cache = {}
        self._load_apis()
        self._load_cache()
    
    def _load_apis(self):
        """Carrega até 7 chaves do Groq"""
        for i in range(1, 8):
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key:
                self.apis.append({
                    "name": f"Groq-{i}",
                    "key": key,
                    "fails": 0
                })
        
        # Fallback para chave padrão
        default_key = os.getenv("GROQ_API_KEY")
        if default_key and default_key not in [a["key"] for a in self.apis]:
            self.apis.append({
                "name": "Groq-Default",
                "key": default_key,
                "fails": 0
            })
        
        if self.apis:
            print(f"✅ Carregadas {len(self.apis)} chaves do Groq")
        else:
            print("⚠️ Nenhuma chave do Groq encontrada!")
    
    def _load_cache(self):
        cache_file = Path("data/cache.json")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
    
    def _save_cache(self):
        cache_file = Path("data/cache.json")
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _call_groq(self, api, prompt):
        """Chama API do Groq"""
        headers = {
            "Authorization": f"Bearer {api['key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Você é o Jarvis, assistente IA elegante e inteligente. Responda em português brasileiro de forma natural."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        raise Exception(f"HTTP {response.status_code}")
    
    def think(self, prompt):
        """Tenta todas as chaves até uma funcionar"""
        
        # Verifica cache
        cache_key = prompt[:100]
        if cache_key in self.cache:
            pass  # cache print removido
            return self.cache[cache_key]
        
        for i, api in enumerate(self.apis):
            try:
                print(f"🔄 Tentando {api['name']}...")
                resposta = self._call_groq(api, prompt)
                
                # Salva no cache
                self.cache[cache_key] = resposta
                self._save_cache()
                
                print(f"✅ {api['name']} respondeu")
                
                # Move esta chave para o topo
                self.apis.insert(0, self.apis.pop(i))
                
                return resposta
                
            except Exception as e:
                print(f"❌ {api['name']} falhou: {str(e)[:50]}")
                api["fails"] += 1
                continue
        
        return "Desculpe, todas as chaves do Groq estão com limite excedido. Tente novamente mais tarde."
    
    def get_stats(self):
        return [{"name": a["name"], "fails": a["fails"]} for a in self.apis]