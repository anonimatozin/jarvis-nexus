# perception/sentiment.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.logger import print_success

class SentimentAnalyzer:
    def __init__(self):
        print_success("Analisador de sentimento carregado.")
    def analyze_text(self, text: str) -> dict:
        return {"sentiment": "neutral", "confidence": 0.5}
