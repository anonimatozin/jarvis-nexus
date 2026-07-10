# modules/aprendizado.py
import json
from pathlib import Path

class Aprendizado:
    def __init__(self):
        self.arquivo = Path("data/aprendizado.json")
        self.dados = self.carregar()
    
    def carregar(self):
        if self.arquivo.exists():
            with open(self.arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "gostos_musicais": [],
            "generos_preferidos": [],
            "artistas_preferidos": [],
            "palavras_chave": [],
            "interacoes": 0,
            "estilo_comunicacao": "formal",
            "ultimos_assuntos": []
        }
    
    def salvar(self):
        self.arquivo.parent.mkdir(exist_ok=True)
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, indent=2, ensure_ascii=False)
    
    def aprender(self, texto):
        texto_lower = texto.lower()
        self.dados["interacoes"] += 1
        
        # Aprende estilo de comunicação
        if any(p in texto_lower for p in ["cara", "mano", "véi", "tá", "po", "né", "bah", "tchê"]):
            self.dados["estilo_comunicacao"] = "descontraido"
        elif any(p in texto_lower for p in ["senhor", "sir", "comandante", "doutor"]):
            self.dados["estilo_comunicacao"] = "formal"
        
        # Aprende gostos musicais
        palavras_musica = ["música", "música", "banda", "artista", "cantor"]
        for p in palavras_musica:
            if p in texto_lower:
                self.dados["gostos_musicais"].append(texto)
                break
        
        # Aprende gêneros musicais
        generos = ["rock", "pop", "funk", "samba", "eletrônica", "mpb", "rap", "hip hop", "clássica", "jazz", "pagode", "sertanejo", "forró"]
        for g in generos:
            if g in texto_lower and g not in self.dados["generos_preferidos"]:
                self.dados["generos_preferidos"].append(g)
        
        # Aprende tópicos de interesse
        topicos = ["filme", "série", "jogo", "esporte", "programação", "python", "ia", "robô", "tecnologia"]
        for t in topicos:
            if t in texto_lower and t not in self.dados["palavras_chave"]:
                self.dados["palavras_chave"].append(t)
        
        self.salvar()
    
    def sugerir_musica(self):
        if self.dados["generos_preferidos"]:
            genero = self.dados["generos_preferidos"][0]
            return f"Que tal ouvirmos {genero}? Posso abrir o Spotify para você!"
        return "Me conte que tipo de música você gosta, assim posso te fazer boas sugestões!"
    
    def sugerir_conteudo(self):
        if self.dados["palavras_chave"]:
            interesse = self.dados["palavras_chave"][0]
            return f"Percebi que você gosta de {interesse}. Quer que eu pesquise novidades sobre isso?"
        return None
    
    def get_saudacao(self):
        if self.dados["estilo_comunicacao"] == "descontraido":
            return "E aí! Como posso te ajudar hoje?"
        return "Boa noite, Sir. Como posso ajudá-lo?"
    
    def get_personalidade(self):
        if self.dados["interacoes"] < 10:
            return "formal"
        elif self.dados["interacoes"] < 50:
            return "amigavel"
        else:
            return self.dados["estilo_comunicacao"]