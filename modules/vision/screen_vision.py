# modules/vision/screen_vision.py
"""
J.A.R.V.I.S. - Screen Vision Module
Le a tela inteira via OCR, encontra botoes por texto, clica por coordenadas.
Inspirado no PanPenek/JarvisAi.
"""

import time
import subprocess
import sys
from pathlib import Path

class ScreenVision:
    """Leitura de tela via OCR e automacao visual."""
    
    def __init__(self):
        self.ocr_available = False
        self._check_ocr()
    
    def _check_ocr(self):
        """Verifica se Tesseract esta instalado."""
        try:
            import pytesseract
            self.ocr_available = True
            self.pytesseract = pytesseract
        except ImportError:
            try:
                subprocess.run(["tesseract", "--version"], 
                             capture_output=True, timeout=5)
                self.ocr_available = True
            except Exception:
                self.ocr_available = False
    
    def capture_screen(self):
        """Captura a tela inteira."""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            return None
    
    def ocr_screen(self, region=None):
        """Le texto de toda a tela ou de uma regiao especifica."""
        if not self.ocr_available:
            return "OCR nao disponivel. Instale Tesseract."
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot(region=region)
            text = self.pytesseract.image_to_string(screenshot, lang='eng+por')
            return text.strip()
        except Exception as e:
            return f"Erro OCR: {e}"
    
    def find_text_on_screen(self, target_text):
        """Encontra um texto na tela e retorna suas coordenadas."""
        if not self.ocr_available:
            return None
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            data = self.pytesseract.image_to_data(screenshot, output_type=self.pytesseract.Output.DICT)
            
            target_lower = target_text.lower()
            
            for i, text in enumerate(data['text']):
                if target_lower in text.lower():
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    return {
                        'text': text,
                        'x': x,
                        'y': y,
                        'confidence': data['conf'][i]
                    }
            return None
        except Exception as e:
            return None
    
    def click_on_text(self, target_text):
        """Clica em um texto encontrado na tela."""
        location = self.find_text_on_screen(target_text)
        if location:
            try:
                import pyautogui
                pyautogui.click(location['x'], location['y'])
                return f"Cliquei em '{location['text']}' em ({location['x']}, {location['y']})"
            except Exception as e:
                return f"Erro ao clicar: {e}"
        return f"Texto '{target_text}' nao encontrado na tela."
    
    def find_and_click_button(self, button_text):
        """Encontra e clica em um botao por texto."""
        synonyms = {
            'ok': ['ok', 'okay', 'confirmar', 'confirm', 'yes', 'sim'],
            'cancel': ['cancel', 'cancelar', 'no', 'nao', 'fechar', 'close'],
            'save': ['save', 'salvar', 'salvar como', 'save as'],
            'open': ['open', 'abrir'],
            'submit': ['submit', 'enviar', 'send', 'enter'],
        }
        
        texts_to_try = [button_text]
        for key, syns in synonyms.items():
            if button_text.lower() in syns or key == button_text.lower():
                texts_to_try.extend(syns)
        
        for text in texts_to_try:
            result = self.click_on_text(text)
            if "Cliquei" in result:
                return result
        
        return f"Botao '{button_text}' nao encontrado."
    
    def get_screen_elements(self):
        """Retorna todos os elementos visiveis na tela com suas posicoes."""
        if not self.ocr_available:
            return "OCR nao disponivel."
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            data = self.pytesseract.image_to_data(screenshot, output_type=self.pytesseract.Output.DICT)
            
            elements = []
            for i, text in enumerate(data['text']):
                if text.strip() and int(data['conf'][i]) > 30:
                    elements.append({
                        'text': text,
                        'x': data['left'][i] + data['width'][i] // 2,
                        'y': data['top'][i] + data['height'][i] // 2,
                        'confidence': data['conf'][i]
                    })
            return elements
        except Exception as e:
            return f"Erro: {e}"
    
    def describe_screen(self):
        """Descreve o que esta visivel na tela."""
        elements = self.get_screen_elements()
        if isinstance(elements, str):
            return elements
        
        if not elements:
            return "Nenhum texto detectado na tela."
        
        lines = [f"{el['text']} ({el['x']},{el['y']})" for el in elements[:20]]
        return f"Elementos na tela:\n" + "\n".join(lines)


def criar_comandos_vision():
    """Retorna dicionario de comandos de visao para o router."""
    vision = ScreenVision()
    
    comandos = {
        'ocr': lambda: vision.ocr_screen(),
        'ler tela': lambda: vision.ocr_screen(),
        'onde esta [x]': lambda texto: vision.find_text_on_screen(texto.replace('onde esta ', '')),
        'clicar em [x]': lambda texto: vision.click_on_text(texto.replace('clicar em ', '')),
        'clique no botao [x]': lambda texto: vision.find_and_click_button(texto.replace('clique no botao ', '')),
        'o que tem na tela': lambda: vision.describe_screen(),
        'descrever tela': lambda: vision.describe_screen(),
    }
    
    return comandos, vision
