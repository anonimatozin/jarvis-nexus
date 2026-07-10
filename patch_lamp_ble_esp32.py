# patch_lamp_ble_esp32.py
"""
Atualiza modules/luzes.py pra mandar lampada via ESP32 BLE
ao inves de tinytuya direto.
"""
import shutil, ast
from pathlib import Path
from datetime import datetime

ts = datetime.now().strftime('%H%M%S')
BASE = Path("C:/Users/Administrator/Desktop/JARVIS")

# Patch no luzes.py - adiciona metodo _cmd_ble e usa no cor/ligar/desligar
lp = BASE / "modules/luzes.py"
shutil.copy(lp, f"{lp}.bak_{ts}")

METODO_BLE = '''
    def _cmd_ble(self, tipo, **kwargs):
        """Manda comando pra lampada via ESP32 BLE bridge."""
        try:
            import json as _json
            # Pega referencia do ESP32 manager via engine
            # O engine_callback nao existe aqui, usa arquivo de socket direto
            import socket as _sock
            payload = {"tipo": tipo, **kwargs}
            # Usa WebSocket client simples via TCP
            # ESP32 server ta em ws://192.168.0.109:8766
            # Mas o SERVER ta no PC, ESP32 e o CLIENT
            # Entao mandamos via o server do ESP32 que ja ta no engine
            # Salva em arquivo de fila que o esp32_manager le
            from pathlib import Path as _P
            fila = _P("data/esp32_queue.json")
            fila.parent.mkdir(exist_ok=True)
            import threading
            # Thread-safe append
            import time
            entry = _json.dumps(payload)
            with open(str(fila), "a", encoding="utf-8") as f:
                f.write(entry + "\\n")
            return True
        except Exception as e:
            print(f"[LUZ-BLE] erro cmd: {e}")
            return False

'''

with open(lp, "r", encoding="utf-8") as f:
    luz = f.read()

# Adiciona metodo BLE
if "_cmd_ble" not in luz:
    luz = luz.replace(
        "    def ligar(self, nome):",
        METODO_BLE + "    def ligar(self, nome):",
        1
    )

# Patch ligar/desligar/cor pra usar BLE na lampada
LIGAR_NOVO = '''    def ligar(self, nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        # Lampada BLE -> via ESP32
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_on")
            return True, f"Lampada ligada"
        # Switch normal -> tinytuya
        d = self._get_device(nome)
        if not d:
            return False, "Device indisponivel"
        try:
            d.turn_on()
            return True, f"Luz {nome} ligada"
        except Exception as e:
            return False, f"Erro: {e}"
'''

DESLIGAR_NOVO = '''    def desligar(self, nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_off")
            return True, f"Lampada desligada"
        d = self._get_device(nome)
        if not d:
            return False, "Device indisponivel"
        try:
            d.turn_off()
            return True, f"Luz {nome} desligada"
        except Exception as e:
            return False, f"Erro: {e}"
'''

COR_NOVO = '''    def cor(self, nome, cor_nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_cor", cor=cor_nome.lower().strip())
            return True, f"Cor {cor_nome}"
        return False, f"{nome} nao tem cor"
'''

BRILHO_NOVO = '''    def brilho(self, nome, percent):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            v = int(max(0, min(1000, percent * 10)))
            self._cmd_ble("lamp_brilho", valor=v)
            return True, f"Brilho {percent}%"
        d = self._get_device(nome)
        if not d:
            return False, "Indisponivel"
        try:
            v = int(max(10, min(1000, percent * 10)))
            if hasattr(d, "set_brightness"):
                d.set_brightness(v)
            return True, f"Brilho {percent}%"
        except Exception as e:
            return False, f"Erro: {e}"
'''

# Substitui os metodos antigos
import re

def replace_method(src, method_name, novo):
    # Acha def method_name ate o proximo def no mesmo nivel
    pattern = rf'(    def {method_name}\(self[^)]*\):.*?)(?=\n    def |\nclass |\Z)'
    return re.sub(pattern, novo.rstrip(), src, count=1, flags=re.DOTALL)

luz = replace_method(luz, "ligar", LIGAR_NOVO)
luz = replace_method(luz, "desligar", DESLIGAR_NOVO)
luz = replace_method(luz, "cor", COR_NOVO)
luz = replace_method(luz, "brilho", BRILHO_NOVO)

try:
    ast.parse(luz)
    lp.write_text(luz, encoding="utf-8")
    print("✔ luzes.py atualizado com BLE bridge")
except SyntaxError as e:
    print(f"✖ SyntaxError: {e}")
    shutil.copy(f"{lp}.bak_{ts}", lp)

# ══════════════════════════════════════════════
# Patch ESP32 manager pra ler fila e enviar
# ══════════════════════════════════════════════
esp_path = BASE / "modules/esp32_manager.py"
with open(esp_path, "r", encoding="utf-8") as f:
    esp = f.read()

FILA_LOOP = '''
    def _fila_loop(self):
        """Le fila de comandos BLE e envia pro ESP32."""
        import json, time
        from pathlib import Path
        fila = Path("data/esp32_queue.json")
        while True:
            try:
                if fila.exists() and fila.stat().st_size > 0:
                    with open(str(fila), "r", encoding="utf-8") as f:
                        linhas = f.readlines()
                    fila.write_text("", encoding="utf-8")  # limpa
                    for linha in linhas:
                        linha = linha.strip()
                        if not linha:
                            continue
                        try:
                            self.enviar(json.loads(linha))
                            time.sleep(0.05)
                        except Exception as e:
                            print(f"[ESP32-FILA] erro: {e}")
            except Exception as e:
                print(f"[ESP32-FILA] loop erro: {e}")
            time.sleep(0.1)

'''

if "_fila_loop" not in esp:
    # Insere antes do ultimo metodo ou no final da classe
    if "def enviar(self" in esp:
        esp = esp.replace(
            "    def enviar(self",
            FILA_LOOP + "    def enviar(self",
            1
        )
    # Inicia thread no __init__ ou start
    esp = esp.replace(
        "self._ws_thread.start()",
        """self._ws_thread.start()
        import threading
        self._fila_thread = threading.Thread(
            target=self._fila_loop, daemon=True, name="ESP32Fila"
        )
        self._fila_thread.start()
        print("[ESP32] Fila BLE ativa")""",
        1
    )
    try:
        ast.parse(esp)
        shutil.copy(esp_path, f"{esp_path}.bak_{ts}")
        esp_path.write_text(esp, encoding="utf-8")
        print("✔ esp32_manager.py com fila BLE")
    except SyntaxError as e:
        print(f"✖ esp32_manager erro: {e}")

print("""
══════════════════════════════════════
PROXIMO PASSO:
1. Grava jarvis_deck_v4_ble.ino no ESP32
   (Arduino IDE - mesmas libs de antes + BLE)

2. Libs necessarias no Arduino IDE:
   - ArduinoJson
   - WebSockets (Markus Sattler)
   - TM1637Display
   - Keypad
   - ESP32 BLE Arduino (ja vem com ESP32 board)

3. python main.py --mode hybrid

4. Testa:
   'jarvis acende a lampada'
   'jarvis luz vermelha'
   'jarvis modo iron man'
══════════════════════════════════════
""")
