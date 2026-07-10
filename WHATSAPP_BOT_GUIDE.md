# Guia Completo: Bot no WhatsApp com JARVIS

## Visão Geral

Existem 3 formas de criar um bot no WhatsApp:

| Método | Dificuldade | Custo | Melhor para |
|--------|-------------|-------|-------------|
| **WhatsApp Business API (Meta)** | Média | Pago por mensagem | Produção, empresas |
| **Whapi.Cloud** | Fácil | Free tier disponível | Testes, projetos pessoais |
| **Baileys** | Difícil | Grátis | Não oficiais, arriscado |

**Recomendação:** Use a **WhatsApp Business API (Meta)** para algo sério, ou **Whapi.Cloud** para testar rápido.

---

## Opção 1: WhatsApp Business API (Meta) - RECOMENDADA

### Pré-requisitos

1. Conta Facebook Business Manager verificada
2. Número de telefone não usado no WhatsApp pessoal
3. Documentos de empresa (CNPJ, etc.)

### Passo 1: Criar App no Meta Developer

1. Acesse [developers.facebook.com](https://developers.facebook.com/)
2. Clique em "Meus Apps" → "Criar App"
3. Escolha "Business" → Próximo
4. Nome: "JARVIS Bot" → Criar App
5. No painel, adicione o produto **WhatsApp**

### Passo 2: Configurar WhatsApp

1. Vá em **WhatsApp** → **Configuração da API**
2. Selecione ou adicione um número de telefone
3. Copie o **Phone Number ID**
4. Gere um **Access Token** (para teste, use o temporário de 24h)

### Passo 3: Configurar Webhook

O webhook é para **receber mensagens**. Você precisa de um servidor público.

```python
# webhook.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == WHATSAPP_VERIFY_TOKEN:
        return challenge
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get('object') == 'whatsapp_business_account':
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if 'messages' in change.get('value', {}):
                    for message in change['value']['messages']:
                        handle_message(message)

    return jsonify({'status': 'ok'})

def handle_message(message):
    from_number = message['from']
    msg_type = message['type']

    if msg_type == 'text':
        text = message['text']['body']
        print(f"Mensagem de {from_number}: {text}")

        # Processar com JARVIS
        from core.universal_knowledge import UniversalKnowledge
        jarvis = UniversalKnowledge()
        result = jarvis.process(text)

        if result['success']:
            reply = str(result['result'])
        else:
            reply = result.get('message', 'Erro ao processar')

        send_message(from_number, reply)

def send_message(to, text):
    import requests

    url = f"https://graph.facebook.com/v22.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"

    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"Resposta enviada: {response.json()}")

if __name__ == '__main__':
    app.run(port=5000)
```

### Passo 4: Expor o Webhook (para teste local)

Use **ngrok** para expor seu servidor local:

```bash
# Instalar ngrok
# Baixe em https://ngrok.com/download

# Expor porta 5000
ngrok http 5000

# Copie a URL (ex: https://abc123.ngrok.io)
# Configure no Meta Developer:
# Webhook URL: https://abc123.ngrok.io/webhook
# Verify Token: seu_verify_token
```

### Passo 5: Variáveis de Ambiente

Adicione ao seu `.env`:

```env
WHATSAPP_ACCESS_TOKEN=seu_token
WHATSAPP_PHONE_NUMBER_ID=seu_phone_id
WHATSAPP_VERIFY_TOKEN=seu_verify_token
```

### Passo 6: Testar

1. Envie uma mensagem para o número do bot
2. O webhook deve receber a mensagem
3. O JARVIS processa e responde

---

## Opção 2: Whapi.Cloud (MAIS FÁCIL)

### Vantagens
- Não precisa de empresa verificada
- Free tier generoso
- Setup em 5 minutos
- API simples

### Passo 1: Criar Conta

1. Acesse [panel.whapi.cloud/register](https://panel.whapi.cloud/register)
2. Crie uma conta gratuita
3. Copie seu **API Token**

### Passo 2: Conectar Número

1. No painel, vá em **Channels**
2. Escaneie o QR Code com seu WhatsApp
3. Pronto! Seu número está conectado

### Passo 3: Configurar Webhook

No painel do Whapi:
1. Vá em **Settings** → **Webhooks**
2. Adicione sua URL (pode ser ngrok)
3. Selecione os eventos: `messages`, `message_status`

### Passo 4: Código Python

```python
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

WHAPI_TOKEN = "seu_token_whapi"
WHAPI_URL = "https://gate.whapi.cloud"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if 'messages' in data:
        for msg in data['messages']:
            handle_message(msg)

    return jsonify({'status': 'ok'})

def handle_message(message):
    from_number = message['from']
    text = message.get('text', {}).get('body', '')

    # Processar com JARVIS
    from core.universal_knowledge import UniversalKnowledge
    jarvis = UniversalKnowledge()
    result = jarvis.process(text)

    reply = str(result.get('result', result.get('message', 'Erro')))

    send_message(from_number, reply)

def send_message(to, text):
    url = f"{WHAPI_URL}/messages/text"

    headers = {
        "Authorization": f"Bearer {WHAPI_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": to,
        "text": text
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"Enviado: {response.json()}")

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Opção 3: Integração com LLM (ChatGPT/Gemini)

Para o bot responder com IA de verdade:

```python
import openai

def get_ai_response(user_message, conversation_history=[]):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
        {"role": "system", "content": "Você é JARVIS, um assistente AI inteligente e prestativo."}
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500
    )

    return response.choices[0].message.content
```

---

## Fluxo Completo

```
Usuário manda mensagem no WhatsApp
        ↓
WhatsApp Cloud API recebe
        ↓
Webhook notifica seu servidor
        ↓
JARVIS processa (UniversalKnowledge)
        ↓
Resposta enviada de volta
        ↓
Usuário recebe no WhatsApp
```

---

## Custos

### Meta Cloud API
- Primeiras 1,000 mensagens/mês: **Grátis**
- Após: $0.005-0.01 por mensagem (varia por país)
- Mensagens de template: $0.02-0.10

### Whapi.Cloud
- Free tier: 500 mensagens/mês
- Planos pagos a partir de $9/mês

---

## Checklist

- [ ] Criar conta no Meta Developer
- [ ] Criar app com produto WhatsApp
- [ ] Configurar número de telefone
- [ ] Gerar Access Token
- [ ] Configurar webhook (ngrok para teste)
- [ ] Adicionar variáveis de ambiente no .env
- [ ] Testar envio e recebimento
- [ ] Integrar com UniversalKnowledge
- [ ] Deploy em servidor (para produção)

---

## Links Úteis

- [Documentação Meta WhatsApp](https://developers.facebook.com/docs/whatsapp)
- [Whapi.Cloud](https://whapi.cloud)
- [Ngrok](https://ngrok.com)
- [Exemplo Python WhatsApp Bot](https://github.com/daveebbelaar/python-whatsapp-bot)
