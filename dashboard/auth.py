import os
import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class LoginSystem:
    def __init__(self, db_path: str = "data/login.db"):
        self.db_path = db_path
        self._sessions: Dict[str, Dict] = {}
        self._attempts: Dict[str, list] = {}
        self._blocked_ips: Dict[str, datetime] = {}

        # Senha padrão: "jarvis2026" (fácil de digitar, difícil de adivinhar)
        self._default_password_hash = self._hash_password("jarvis2026")
        self._secret_key = secrets.token_hex(32)

        self._load_or_create_password()

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # 100k iterações
        )
        return f"{salt}:{pwd_hash.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, hash_hex = stored_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            )
            return pwd_hash.hex() == hash_hex
        except Exception:
            return False

    def _load_or_create_password(self):
        config_file = os.path.join(os.path.dirname(self.db_path), "auth_config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self._default_password_hash = config.get("password_hash", self._default_password_hash)
            except Exception:
                pass
        else:
            with open(config_file, 'w') as f:
                json.dump({"password_hash": self._default_password_hash}, f)

    def _check_rate_limit(self, ip: str) -> Tuple[bool, int]:
        now = datetime.now()

        if ip in self._blocked_ips:
            if now < self._blocked_ips[ip]:
                remaining = (self._blocked_ips[ip] - now).seconds
                return False, remaining
            else:
                del self._blocked_ips[ip]

        if ip not in self._attempts:
            self._attempts[ip] = []

        self._attempts[ip] = [t for t in self._attempts[ip] if now - t < timedelta(minutes=5)]

        if len(self._attempts[ip]) >= 3:
            delay = min(300, 2 ** len(self._attempts[ip]) * 30)
            self._blocked_ips[ip] = now + timedelta(seconds=delay)
            return False, delay

        return True, 0

    def _record_attempt(self, ip: str):
        if ip not in self._attempts:
            self._attempts[ip] = []
        self._attempts[ip].append(datetime.now())

    def login(self, password: str, ip: str = "unknown") -> Tuple[bool, str, Optional[str]]:
        is_allowed, wait_time = self._check_rate_limit(ip)

        if not is_allowed:
            logger.warning(f"Rate limit atingido para IP: {ip}")
            return False, f"Muitas tentativas. Aguarde {wait_time} segundos.", None

        if self._verify_password(password, self._default_password_hash):
            session_token = secrets.token_hex(32)
            self._sessions[session_token] = {
                "ip": ip,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24),
                "last_activity": datetime.now()
            }

            if ip in self._attempts:
                del self._attempts[ip]

            logger.info(f"Login bem-sucedido de {ip}")
            return True, "Login realizado com sucesso!", session_token
        else:
            self._record_attempt(ip)
            logger.warning(f"Senha incorreta de {ip}")
            return False, "Senha incorreta.", None

    def validate_session(self, token: str) -> bool:
        if not token or token not in self._sessions:
            return False

        session = self._sessions[token]

        if datetime.now() > session["expires_at"]:
            del self._sessions[token]
            return False

        session["last_activity"] = datetime.now()
        return True

    def logout(self, token: str):
        if token in self._sessions:
            del self._sessions[token]

    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        if self._verify_password(old_password, self._default_password_hash):
            if len(new_password) < 8:
                return False, "Nova senha deve ter pelo menos 8 caracteres."

            self._default_password_hash = self._hash_password(new_password)

            config_file = os.path.join(os.path.dirname(self.db_path), "auth_config.json")
            with open(config_file, 'w') as f:
                json.dump({"password_hash": self._default_password_hash}, f)

            self._sessions.clear()
            return True, "Senha alterada com sucesso!"
        else:
            return False, "Senha atual incorreta."

    def get_login_page(self) -> str:
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0a0a0f;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 40px;
            background: rgba(15, 25, 35, 0.9);
            border-radius: 20px;
            border: 1px solid rgba(0, 200, 255, 0.2);
            box-shadow: 0 0 60px rgba(0, 200, 255, 0.1);
            position: relative;
            z-index: 10;
        }
        .logo {
            text-align: center;
            margin-bottom: 40px;
        }
        .arc-reactor {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            border-radius: 50%;
            background: radial-gradient(circle, #00c8ff 0%, transparent 70%);
            animation: pulse 2s infinite;
            box-shadow: 0 0 40px rgba(0, 200, 255, 0.5);
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.1); opacity: 1; }
        }
        h1 {
            color: #00c8ff;
            text-align: center;
            font-size: 28px;
            text-shadow: 0 0 20px rgba(0, 200, 255, 0.5);
        }
        .subtitle {
            color: #5a6a7a;
            text-align: center;
            margin-top: 5px;
            font-size: 12px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            color: #7a8a9a;
            margin-bottom: 8px;
            font-size: 14px;
        }
        input[type="password"] {
            width: 100%;
            padding: 15px 20px;
            background: rgba(0, 20, 40, 0.5);
            border: 1px solid rgba(0, 200, 255, 0.3);
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }
        input[type="password"]:focus {
            border-color: #00c8ff;
            box-shadow: 0 0 20px rgba(0, 200, 255, 0.2);
        }
        .btn-login {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #00c8ff, #0080ff);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 200, 255, 0.3);
        }
        .btn-login:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .error-message {
            color: #ff4444;
            text-align: center;
            margin-top: 15px;
            font-size: 14px;
            min-height: 20px;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 15px;
        }
        .loading-spinner {
            width: 30px;
            height: 30px;
            border: 3px solid rgba(0, 200, 255, 0.2);
            border-top-color: #00c8ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        .security-notice {
            margin-top: 20px;
            padding: 10px;
            background: rgba(255, 200, 0, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(255, 200, 0, 0.3);
        }
        .security-notice p {
            color: #ffcc00;
            font-size: 11px;
            text-align: center;
        }
    </style>
</head>
<body>
    <canvas class="particles" id="particles"></canvas>
    
    <div class="login-container">
        <div class="logo">
            <div class="arc-reactor"></div>
            <h1>J.A.R.V.I.S.</h1>
            <p class="subtitle">Just A Rather Very Intelligent System</p>
        </div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="password">Senha de Acesso</label>
                <input type="password" id="password" name="password" 
                       placeholder="Digite sua senha..." autocomplete="current-password" required>
            </div>
            
            <button type="submit" class="btn-login" id="btnLogin">
                Acessar Sistema
            </button>
            
            <div class="error-message" id="errorMsg"></div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <p style="color: #00c8ff; margin-top: 10px;">Autenticando...</p>
            </div>
        </form>
        
        <div class="security-notice">
            <p>🔒 Sistema protegido contra ataques de força bruta</p>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('particles');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particles = [];
        for (let i = 0; i < 50; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1
            });
        }

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0, 200, 255, 0.3)';
                ctx.fill();
            });
            requestAnimationFrame(animate);
        }
        animate();

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            const loading = document.getElementById('loading');
            const btn = document.getElementById('btnLogin');
            
            errorMsg.textContent = '';
            loading.style.display = 'block';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    localStorage.setItem('jarvis_token', data.token);
                    window.location.href = '/';
                } else {
                    errorMsg.textContent = data.message;
                    loading.style.display = 'none';
                    btn.disabled = false;
                }
            } catch (error) {
                errorMsg.textContent = 'Erro de conexão';
                loading.style.display = 'none';
                btn.disabled = false;
            }
        });

        document.getElementById('password').focus();
    </script>
</body>
</html>'''


login_system = LoginSystem()
