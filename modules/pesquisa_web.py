"""
NEXUS - Pesquisa Web Multi-Site v1.0
═══════════════════════════════════════════════════════════
Busca em multiplas fontes em paralelo, resume com IA.
Fontes: DuckDuckGo, Wikipedia, scraping leve.
═══════════════════════════════════════════════════════════
"""

import time
import threading
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Dependencias
try:
    from duckduckgo_search import DDGS
    DDG_OK = True
except ImportError:
    DDG_OK = False
    print("[PESQUISA] duckduckgo-search nao instalado")

try:
    import wikipedia
    wikipedia.set_lang("pt")
    WIKI_OK = True
except ImportError:
    WIKI_OK = False
    print("[PESQUISA] wikipedia nao instalado")

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPE_OK = True
except ImportError:
    SCRAPE_OK = False


class PesquisaWeb:
    """Buscador multi-site com resumo por IA."""
    
    def __init__(self, brain=None):
        """
        Args:
            brain: instancia do JarvisBrain para resumir resultados
        """
        self.brain = brain
        self.disponivel = DDG_OK or WIKI_OK
        
        if self.disponivel:
            print(f"[PESQUISA] Pronta. DDG={DDG_OK} WIKI={WIKI_OK}")
        else:
            print("[PESQUISA] Indisponivel - instale duckduckgo-search e wikipedia")
    
    # ════════════════════════════════════════════════════════
    # FONTES INDIVIDUAIS (rodam em paralelo)
    # ════════════════════════════════════════════════════════
    
    def _buscar_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """Busca no DuckDuckGo."""
        if not DDG_OK:
            return []
        try:
            resultados = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results, region="br-pt"):
                    resultados.append({
                        "titulo": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "fonte": "DuckDuckGo",
                    })
            return resultados
        except Exception as e:
            print(f"[DDG] erro: {e}")
            return []
    
    def _buscar_wikipedia(self, query: str) -> List[Dict]:
        """Busca na Wikipedia."""
        if not WIKI_OK:
            return []
        try:
            resultados = []
            # Pega ate 3 paginas relacionadas
            titulos = wikipedia.search(query, results=3)
            
            for titulo in titulos[:2]:  # so as 2 mais relevantes
                try:
                    pagina = wikipedia.page(titulo, auto_suggest=False)
                    resumo = wikipedia.summary(titulo, sentences=3, auto_suggest=False)
                    resultados.append({
                        "titulo": pagina.title,
                        "url": pagina.url,
                        "snippet": resumo,
                        "fonte": "Wikipedia",
                    })
                except wikipedia.exceptions.DisambiguationError as e:
                    # Pega primeira opcao
                    try:
                        opcao = e.options[0]
                        pagina = wikipedia.page(opcao, auto_suggest=False)
                        resumo = wikipedia.summary(opcao, sentences=2)
                        resultados.append({
                            "titulo": pagina.title,
                            "url": pagina.url,
                            "snippet": resumo,
                            "fonte": "Wikipedia",
                        })
                    except Exception:
                        pass
                except Exception:
                    continue
            
            return resultados
        except Exception as e:
            print(f"[WIKI] erro: {e}")
            return []
    
    def _buscar_noticias(self, query: str) -> List[Dict]:
        """Busca noticias recentes (DDG news)."""
        if not DDG_OK:
            return []
        try:
            resultados = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=3, region="br-pt"):
                    resultados.append({
                        "titulo": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("body", ""),
                        "fonte": f"Noticias ({r.get('source', '?')})",
                        "data": r.get("date", ""),
                    })
            return resultados
        except Exception as e:
            print(f"[NEWS] erro: {e}")
            return []
    
    # ════════════════════════════════════════════════════════
    # BUSCA PARALELA
    # ════════════════════════════════════════════════════════
    
    def buscar_tudo(self, query: str, incluir_noticias: bool = False) -> Dict:
        """
        Busca em todas as fontes em paralelo.
        Returns:
            {
                "query": str,
                "duckduckgo": [...],
                "wikipedia": [...],
                "noticias": [...],
                "total": int,
                "tempo": float,
            }
        """
        if not self.disponivel:
            return {"erro": "Sistema de pesquisa indisponivel"}
        
        inicio = time.time()
        resultado = {
            "query": query,
            "duckduckgo": [],
            "wikipedia": [],
            "noticias": [],
        }
        
        # Roda em paralelo
        with ThreadPoolExecutor(max_workers=3) as executor:
            futuros = {
                executor.submit(self._buscar_duckduckgo, query): "duckduckgo",
                executor.submit(self._buscar_wikipedia, query): "wikipedia",
            }
            
            if incluir_noticias:
                futuros[executor.submit(self._buscar_noticias, query)] = "noticias"
            
            for futuro in as_completed(futuros, timeout=15):
                fonte = futuros[futuro]
                try:
                    resultado[fonte] = futuro.result(timeout=10)
                except Exception as e:
                    print(f"[PESQUISA] {fonte} timeout/erro: {e}")
                    resultado[fonte] = []
        
        tempo = round(time.time() - inicio, 2)
        total = (
            len(resultado["duckduckgo"]) +
            len(resultado["wikipedia"]) +
            len(resultado["noticias"])
        )
        
        resultado["total"] = total
        resultado["tempo"] = tempo
        
        print(f"[PESQUISA] '{query}' - {total} resultados em {tempo}s")
        return resultado
    
    # ════════════════════════════════════════════════════════
    # RESUMO COM IA
    # ════════════════════════════════════════════════════════
    
    def resumir(self, resultados: Dict, max_tokens: int = 300) -> str:
        """Usa IA para resumir todos os resultados."""
        if not self.brain:
            return self._resumo_simples(resultados)
        
        # Monta contexto
        contexto = f"PESQUISA: {resultados.get('query', '?')}\n\n"
        
        for fonte_nome in ["duckduckgo", "wikipedia", "noticias"]:
            items = resultados.get(fonte_nome, [])
            if items:
                contexto += f"=== {fonte_nome.upper()} ===\n"
                for i, item in enumerate(items[:3], 1):
                    contexto += f"{i}. {item['titulo']}\n"
                    contexto += f"   {item['snippet'][:300]}\n"
                    contexto += f"   Fonte: {item['url']}\n\n"
        
        prompt = (
            f"{contexto}\n\n"
            "TAREFA: Resuma em 3-5 frases CURTAS o que voce descobriu sobre "
            "esse assunto. Seja direto e util. Mencione fontes apenas se "
            "for crucial. Responda como Jarvis: elegante e conciso.\n\n"
            "RESPOSTA:"
        )
        
        try:
            resumo = self.brain.think(prompt)
            if resumo and len(resumo) > 20:
                return resumo
        except Exception as e:
            print(f"[PESQUISA] erro resumo IA: {e}")
        
        return self._resumo_simples(resultados)
    
    def _resumo_simples(self, resultados: Dict) -> str:
        """Resumo sem IA (fallback)."""
        partes = []
        
        # Wikipedia primeiro
        if resultados.get("wikipedia"):
            wiki = resultados["wikipedia"][0]
            partes.append(f"{wiki['snippet'][:250]}")
        
        # Depois DDG
        elif resultados.get("duckduckgo"):
            ddg = resultados["duckduckgo"][0]
            partes.append(f"{ddg['snippet'][:250]}")
        
        # Adiciona contagem
        total = resultados.get("total", 0)
        partes.append(f"Encontrei {total} resultados ao todo.")
        
        return " ".join(partes) if partes else "Nao encontrei resultados."
    
    # ════════════════════════════════════════════════════════
    # API SIMPLIFICADA
    # ════════════════════════════════════════════════════════
    
    def pesquisar(self, query: str, com_resumo: bool = True) -> Dict:
        """
        Pesquisa completa: busca + resumo.
        Returns:
            {
                "query": str,
                "resumo": str,
                "resultados": [{fonte, titulo, url, snippet}, ...],
                "total": int,
                "tempo": float,
            }
        """
        # Busca em todas as fontes
        dados = self.buscar_tudo(query, incluir_noticias=False)
        
        if "erro" in dados:
            return {"query": query, "erro": dados["erro"], "resultados": []}
        
        # Junta todos resultados numa lista
        todos = []
        todos.extend(dados.get("wikipedia", []))      # Wiki primeiro
        todos.extend(dados.get("duckduckgo", []))     # DDG depois
        todos.extend(dados.get("noticias", []))       # Noticias por ultimo
        
        # Resumo
        resumo = self.resumir(dados) if com_resumo else None
        
        return {
            "query": query,
            "resumo": resumo,
            "resultados": todos[:10],
            "total": dados["total"],
            "tempo": dados["tempo"],
        }
