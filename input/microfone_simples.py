# input/microfone_simples.py
import sounddevice as sd
import numpy as np
import requests
import io
import wave

class MicrofoneSimples:
    def __init__(self):
        self.sample_rate = 16000
        self.disponivel = True
        
    def ouvir(self, duracao=4):
        print("🎤 Gravando...")
        gravacao = sd.rec(int(duracao * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16')
        sd.wait()
        print("🎤 Processando...")
        
        # Converte para WAV
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(gravacao.tobytes())
        
        # Envia para Google
        url = "https://www.google.com/speech-api/v2/recognize?output=json&lang=pt-BR&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        try:
            resp = requests.post(url, data=buffer.getvalue(), headers={"Content-Type": "audio/l16; rate=16000"}, timeout=10)
            for linha in resp.text.strip().split("\n"):
                import json
                try:
                    dados = json.loads(linha)
                    for resultado in dados.get("result", []):
                        for alt in resultado.get("alternative", []):
                            texto = alt.get("transcript", "")
                            if texto:
                                return texto
                except:
                    pass
        except Exception as e:
            print(f"Erro: {e}")
        return None