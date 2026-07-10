# GUIA DE DEPLOY - JARVIS DASHBOARD

## 1. Enviar para o GitHub

### 1.1 Login no GitHub CLI
```powershell
cd C:\Users\Administrator\Desktop\JARVIS
gh auth login --web -p https
```
- Abre um link no navegador
- Copia o codigo mostrado no terminal
- Autoriza no GitHub
- Volta ao terminal

### 1.2 Criar repositorio e fazer push
```powershell
git init
git add .
git commit -m "JARVIS Control Center v2.0"
gh repo create jarvis-nexus --public --source=. --remote=origin --push
```

Pronto! O codigo esta no GitHub em: `https://github.com/SEU_USUARIO/jarvis-nexus`

---

## 2. Conectar ao Netlify (auto-deploy)

### 2.1 Metodo 1: Via Site Netlify
1. Acesse https://app.netlify.com
2. Clique em **"Add new site"** → **"Import an existing project"**
3. Escolha **GitHub** e autorize
4. Selecione o repo `jarvis-nexus`
5. Configuracoes (ja preenchidas pelo `netlify.toml`):
   - **Build command:** `pip install -r netlify/functions/requirements.txt`
   - **Publish directory:** `dashboard/static`
   - **Functions directory:** `netlify/functions`
6. Clique em **"Deploy site"**

### 2.2 Metodo 2: Via Netlify CLI
```powershell
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

### Auto-Update
**Toda vez que voce fizer `git push` pro GitHub, o Netlify atualiza automaticamente.** Nao precisa fazer nada manualmente.

---

## 3. URL do site
Apos o deploy, o site fica em:
```
https://jarvis-nexus.netlify.app
```
(Voce pode configurar um dominio personalizado em **Domain settings** no Netlify)

---

## 4. Importante: Variaveis de Ambiente
No Netlify, va em **Site settings** → **Environment variables** e adicione:
```
GROQ_API_KEY=sua_chave
GEMINI_API_KEY=sua_chave
DISCORD_TOKEN=seu_token
```
(Elas estao no seu `.env` local, que NAO sobe pro GitHub - protegido pelo `.gitignore`)

---

## 5. Rodar Localmente (testar antes do deploy)
```powershell
cd C:\Users\Administrator\Desktop\JARVIS
.\venv\Scripts\python dashboard\app.py
```
Depois abrir: http://localhost:8080
