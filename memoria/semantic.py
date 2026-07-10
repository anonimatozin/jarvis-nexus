"""
NEXUS - Memoria Semantica v2.0 (cosine distance)
Busca por significado REAL agora.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_OK = True
except ImportError:
    CHROMA_OK = False

try:
    from sentence_transformers import SentenceTransformer
    ST_OK = True
except ImportError:
    ST_OK = False


class MemoriaSemantica:
    def __init__(self, persist_dir="data/memoria_semantica"):
        self.disponivel = CHROMA_OK and ST_OK
        if not self.disponivel:
            return
        
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.persist_dir = persist_dir
        
        print("[MEMORIA] Carregando modelo de embeddings (primeira vez demora)...")
        try:
            self.modelo = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2"
            )
            print("[MEMORIA] Modelo de embeddings carregado.")
        except Exception as e:
            print(f"[MEMORIA] Erro carregando modelo: {e}")
            self.disponivel = False
            return
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # ★ COSINE SIMILARITY (correto pra texto)
            self.colecoes = {}
            for cat in ["fatos", "preferencias", "eventos", "pessoas", "geral"]:
                self.colecoes[cat] = self.client.get_or_create_collection(
                    name=f"jarvis_{cat}",
                    metadata={
                        "description": f"Memorias - {cat}",
                        "hnsw:space": "cosine"  # ★ MUDANCA CRITICA
                    }
                )
            
            total = sum(c.count() for c in self.colecoes.values())
            print(f"[MEMORIA] ChromaDB pronto. {total} memorias carregadas.")
        except Exception as e:
            print(f"[MEMORIA] Erro ChromaDB: {e}")
            self.disponivel = False
    
    def lembrar(self, texto, categoria="geral", metadata=None):
        if not self.disponivel:
            return False
        if categoria not in self.colecoes:
            categoria = "geral"
        try:
            embedding = self.modelo.encode(texto, normalize_embeddings=True).tolist()
            meta = metadata or {}
            meta["timestamp"] = datetime.now().isoformat()
            meta["data_legivel"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            doc_id = f"{categoria}_{int(time.time() * 1000)}"
            self.colecoes[categoria].add(
                ids=[doc_id],
                documents=[texto],
                embeddings=[embedding],
                metadatas=[meta],
            )
            return True
        except Exception as e:
            print(f"[MEMORIA] Erro ao salvar: {e}")
            return False
    
    def buscar(self, consulta, categoria=None, top_k=5, threshold=0.3):
        """
        Busca por significado usando cosine similarity.
        threshold: 0.3 = razoavelmente similar
                   0.5 = bem similar
                   0.7 = muito similar
        """
        if not self.disponivel:
            return []
        
        try:
            embedding = self.modelo.encode(
                consulta, normalize_embeddings=True
            ).tolist()
            
            colecoes_busca = (
                [self.colecoes[categoria]] 
                if categoria and categoria in self.colecoes
                else list(self.colecoes.values())
            )
            
            todos_resultados = []
            
            for col in colecoes_busca:
                if col.count() == 0:
                    continue
                
                resultado = col.query(
                    query_embeddings=[embedding],
                    n_results=min(top_k, col.count()),
                )
                
                docs = resultado.get("documents", [[]])[0]
                metas = resultado.get("metadatas", [[]])[0]
                distancias = resultado.get("distances", [[]])[0]
                
                for doc, meta, dist in zip(docs, metas, distancias):
                    # ★ COSINE: distancia 0 = identico, 2 = oposto
                    # similaridade = 1 - (distancia / 2)
                    similaridade = max(0.0, 1.0 - (dist / 2.0))
                    
                    if similaridade >= threshold:
                        todos_resultados.append({
                            "texto": doc,
                            "similaridade": round(similaridade, 3),
                            "metadata": meta,
                            "categoria": col.name.replace("jarvis_", ""),
                        })
            
            todos_resultados.sort(
                key=lambda x: x["similaridade"], reverse=True
            )
            return todos_resultados[:top_k]
        except Exception as e:
            print(f"[MEMORIA] Erro ao buscar: {e}")
            return []
    
    def detectar_categoria(self, texto):
        txt = texto.lower()
        if any(p in txt for p in ["gosto", "gosta", "prefiro", "adoro", "amo",
                                   "odeio", "favorito", "preferido"]):
            return "preferencias"
        if any(p in txt for p in ["aniversário", "aniversario", "consulta",
                                   "reuniao", "reunião", "compromisso", "evento",
                                   "amanhã", "amanha"]):
            return "eventos"
        if any(p in txt for p in ["meu amigo", "meu irmão", "meu irmao",
                                   "minha mãe", "minha mae", "meu pai",
                                   "minha namorada", "meu namorado"]):
            return "pessoas"
        if any(p in txt for p in ["meu nome", "eu sou", "meu cpf",
                                   "meu telefone", "meu endereço", "moro em",
                                   "trabalho em", "estudo"]):
            return "fatos"
        return "geral"
    
    def estatisticas(self):
        if not self.disponivel:
            return {"disponivel": False}
        stats = {"disponivel": True, "categorias": {}}
        total = 0
        for nome, col in self.colecoes.items():
            count = col.count()
            stats["categorias"][nome.replace("jarvis_", "")] = count
            total += count
        stats["total"] = total
        return stats
    
    def listar_recentes(self, n=5):
        if not self.disponivel:
            return []
        todas = []
        for nome, col in self.colecoes.items():
            if col.count() == 0:
                continue
            try:
                resultado = col.get(limit=col.count())
                for doc, meta in zip(
                    resultado.get("documents", []),
                    resultado.get("metadatas", []),
                ):
                    todas.append({
                        "texto": doc,
                        "metadata": meta,
                        "categoria": nome.replace("jarvis_", ""),
                    })
            except Exception:
                pass
        todas.sort(
            key=lambda x: x["metadata"].get("timestamp", ""),
            reverse=True
        )
        return todas[:n]
    
    def esquecer(self, categoria=None):
        if not self.disponivel:
            return False
        try:
            if categoria and categoria in self.colecoes:
                self.client.delete_collection(f"jarvis_{categoria}")
                self.colecoes[categoria] = self.client.get_or_create_collection(
                    name=f"jarvis_{categoria}",
                    metadata={"hnsw:space": "cosine"}
                )
                return True
            for cat in list(self.colecoes.keys()):
                self.client.delete_collection(f"jarvis_{cat}")
                self.colecoes[cat] = self.client.get_or_create_collection(
                    name=f"jarvis_{cat}",
                    metadata={"hnsw:space": "cosine"}
                )
            return True
        except Exception as e:
            print(f"[MEMORIA] Erro ao esquecer: {e}")
            return False
