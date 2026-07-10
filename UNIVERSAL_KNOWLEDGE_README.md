# JARVIS Universal Knowledge System

Sistema de conhecimento universal com lazy activation para o JARVIS.

## O que é?

Um sistema onde o JARVIS **já sabe tudo** mas fica "dormindo" e só ativa a parte específica quando requisitada.

## Arquitetura

```
UniversalKnowledge
├── ModuleFactory (Lazy Loading)
│   ├── Gmail Module [DORMINDO]
│   ├── Calendar Module [DORMINDO]
│   ├── GitHub Module [ATIVO] ← quando você fala de código
│   ├── System Module [DORMINDO]
│   └── Web Module [DORMINDO]
├── KnowledgeBase (SQLite)
│   ├── knowledge (dados persistentes)
│   ├── module_cache (cache temporário)
│   └── action_log (histórico de ações)
└── IntentDetector (Keywords + Semântica)
    ├── Layer 1: Keywords (rápido)
    └── Layer 2: Semântica (inteligente)
```

## Como funciona?

1. **Usuário fala algo** → "Ver meus emails"
2. **IntentDetector** identifica módulo → `gmail`
3. **ModuleFactory** ativa módulo sob demanda
4. **Módulo executa** ação
5. **Volta a dormir** após 5 minutos de inatividade

## Módulos Disponíveis

| Módulo | Descrição | Keywords |
|--------|-----------|----------|
| gmail | Emails via Gmail | email, gmail, enviar, ler |
| calendar | Google Calendar | calendário, evento, reunião |
| github | GitHub CLI | github, repo, issue, pr |
| system | Sistema/Arquivos | arquivo, cpu, memória, processo |
| web | Navegação/Busca | web, buscar, clima, download |

## Uso

### Básico

```python
from core.universal_knowledge import UniversalKnowledge

jarvis = UniversalKnowledge()

# Processar comando
result = jarvis.process("Ver meus emails")

# Resultado
{
    "success": True,
    "module": "gmail",
    "action": "list",
    "result": [...]
}
```

### Com JARVIS

```python
from jarvis_knowledge_demo import JARVISWithKnowledge

jarvis = JARVISWithKnowledge()
response = jarvis.process_command("Ver clima em São Paulo")
print(response)
```

### Teste

```bash
python test_universal_knowledge.py
```

## Estrutura de Diretórios

```
core/universal_knowledge/
├── __init__.py
├── base_module.py          # Classe base dos módulos
├── module_factory.py       # Factory Pattern + Lazy Loading
├── knowledge_base.py       # SQLite para dados
├── intent_detector.py      # Detecção de intenção
├── universal_knowledge.py  # Classe principal
└── modules/
    ├── __init__.py
    ├── gmail.py
    ├── calendar.py
    ├── github.py
    ├── system.py
    └── web.py
```

## Adicionar Novo Módulo

1. Crie arquivo em `modules/nome_modulo.py`

```python
from ..base_module import BaseModule

class MeuModulo(BaseModule):
    def __init__(self):
        super().__init__(
            name="meu_modulo",
            description="Descrição do módulo"
        )

    def _load_resources(self):
        # Carregar APIs, credenciais, etc.
        pass

    def _unload_resources(self):
        # Liberar memória
        pass

    def execute(self, action: str, **kwargs):
        # Implementar ações
        pass
```

2. Registre em `universal_knowledge.py`

```python
from .modules import MeuModulo

# Adicionar em _register_modules()
{
    "name": "meu_modulo",
    "class": MeuModulo,
    "description": "Descrição",
    "keywords": ["keyword1", "keyword2"]
}
```

## Lazy Loading

Módulos ficam em estado `SLEEPING` até serem chamados:

```python
# Módulo não está carregado
module = factory.get("gmail")  # ← aqui cria e ativa

# ... usar módulo ...

# Após 5 minutos sem uso, volta a dormir automaticamente
```

## Intent Detection

Sistema híbrido de 2 camadas:

1. **Keywords** → Rápido, zero custo
2. **Semântica** → Mais inteligente, usa similaridade de palavras

```python
# Exemplo
detector.detect_intent("enviar email para boss")
# → [("gmail", 0.95), ("web", 0.2)]
```

## Performance

- Ativação: < 150ms
- Idle: < 300MB RAM
- Cleanup automático após 5 minutos

## Segurança

- Credenciais devem ser criptografadas (SQLCipher)
- Cada módulo com permissões mínimas
- Log de todas as ações

## Próximos Passos

- [ ] Implementar OAuth2 para Gmail/Calendar
- [ ] Adicionar FAISS para busca semântica vetorial
- [ ] Criar módulos: WhatsApp, Telegram, Slack, Notion
- [ ] Interface web para gerenciar módulos
- [ ] Dashboard de uso e performance
