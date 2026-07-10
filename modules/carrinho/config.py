"""
Carrinho - Configuracoes
EDITE O IP DO ESP32 AQUI quando souber.
"""

# Wi-Fi do ESP32
ESP32_IP = "192.168.0.150"  # MUDE pra IP do seu ESP32
ESP32_PORT = 80
ESP32_TIMEOUT = 3.0  # segundos

# Comportamento padrao
VELOCIDADE_PADRAO = 180  # 0-255 (PWM)
VELOCIDADE_GIRO = 200
TEMPO_PADRAO_MS = 800   # ms de movimento padrao

# Seguranca
DISTANCIA_SEGURA_CM = 25  # para se obstaculo < 25cm
DISTANCIA_CRITICA_CM = 15  # ré se < 15cm
TIMEOUT_COMANDO_MS = 2000  # auto-stop se sem comando por 2s

# Sensores
HC_SR04_INSTALADO = True
SERVO_INSTALADO = True
SERVO_ANGULO_FRENTE = 90  # graus
SERVO_ANGULO_ESQ = 150
SERVO_ANGULO_DIR = 30

# Modos disponiveis
MODOS_DISPONIVEIS = [
    "manual",           # Controle direto
    "random_walk",      # Anda aleatorio (sem sensor)
    "avoid_obstacles",  # Desvia (precisa HC-SR04)
    "explore",          # Exploracao com sensor
    "patrol",           # Patrulha (vai e volta)
    "follow",           # Segue movimento (futuro)
]
