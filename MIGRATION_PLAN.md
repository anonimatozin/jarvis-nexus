# Plano de Migração - JARVIS Dashboard

## Fase 1: Railway (ATUAL - $5 crédito)
- **URL:** https://jarvis-nexus.up.railway.app
- **Login:** jarvis2026
- **Duração estimada:** 7-30 dias (depende do uso)
- **Status:** ✅ Ativo

---

## Fase 2: Render (QUANDO ACABAR CRÉDITO)
- **Custo:** GRATUITO (750 horas/mês)
- **URL:** https://jarvis-nexus.onrender.com
- **Tempo de resposta:** Cold start ~30s após 15min inativo

### Passos para migrar:
1. Acessar https://render.com
2. Criar conta gratuita
3. "New Web Service" → Conectar GitHub
4. Selecionar repo `jarvis-nexus`
5. Configurações:
   - **Name:** jarvis-nexus
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements_web.txt`
   - **Start Command:** `gunicorn dashboard.app:app --bind 0.0.0.0:$PORT`
   - **Plan:** Free
6. Adicionar variáveis de ambiente (se necessário)
7. Deploy

---

## Fase 3: Netlify (SE RENDER TAMBÉM FALHAR)
- **Custo:** GRATUITO
- **Limitação:** Só arquivos estáticos (login visual sem backend)

### Necessário:
- Transformar login em client-side (localStorage)
- API limitada via Netlify Functions
- Funcionalidades reduzidas

---

## Checklist de Migração

### Arquivos para atualizar:
- [ ] `railway.json` → manter como backup
- [ ] Criar `render.yaml` (opcional, para IaC)
- [ ] Atualizar README.md com nova URL
- [ ] Testar todas as rotas da API
- [ ] Verificar login funciona
- [ ] Verificar chat funciona

### Variáveis de ambiente (se usar API keys):
```
AI_PROVIDER=groq
AI_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=sua_chave_aqui
```

---

## Comandos Úteis

### Verificar status do deploy:
```bash
# Railway
railway status

# Render (após deploy)
curl https://jarvis-nexus.onrender.com/api/health
```

### Testar localmente antes de migrar:
```bash
cd C:\Users\Administrator\Desktop\JARVIS
pip install -r requirements_web.txt
gunicorn dashboard.app:app --bind 0.0.0.0:8080
```

---

## Notas Importantes

1. **Dados:** O Railway/Render não salvam dados entre reinicializações
2. **Login:** A senha `jarvis2026` é recriada se o arquivo `auth_config.json` perder
3. **Chat:** O chat precisa de API keys (GROQ, Gemini) para funcionar com IA
4. **Cold Start:** Render desliga após 15min - primeira requisição demora ~30s

---

**Última atualização:** $(date)
**Próxima revisão:** Quando crédito Railway acabar