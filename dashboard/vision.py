import os
import sys
import json
import time
import base64
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionSystem:
    def __init__(self):
        self._frames: List[Dict] = []
        self._is_streaming = False
        self._last_analysis = None
        self._max_frames = 100

    def receive_frame(self, frame_data: str, source: str = "webcam") -> Dict:
        timestamp = datetime.now().isoformat()

        frame_info = {
            "timestamp": timestamp,
            "source": source,
            "data_size": len(frame_data),
            "data": frame_data[:100] + "..." if len(frame_data) > 100 else frame_data
        }

        self._frames.append(frame_info)

        if len(self._frames) > self._max_frames:
            self._frames = self._frames[-self._max_frames:]

        return {
            "received": True,
            "timestamp": timestamp,
            "total_frames": len(self._frames)
        }

    def get_latest_frame(self) -> Optional[Dict]:
        if self._frames:
            return self._frames[-1]
        return None

    def get_frames(self, limit: int = 10) -> List[Dict]:
        return self._frames[-limit:]

    def analyze_frame(self, frame_data: str) -> Dict:
        return {
            "analysis": "Análise de imagem não disponível nesta versão",
            "timestamp": datetime.now().isoformat(),
            "suggestion": "Integre com modelo de visão (GPT-4V, Gemini Vision)"
        }

    def clear_frames(self):
        self._frames.clear()


class WebSocketManager:
    def __init__(self):
        self._connections: Dict[str, any] = {}
        self._message_queue: Dict[str, List] = {}

    def connect(self, client_id: str, connection):
        self._connections[client_id] = connection
        self._message_queue[client_id] = []
        logger.info(f"Cliente conectado: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self._connections:
            del self._connections[client_id]
        if client_id in self._message_queue:
            del self._message_queue[client_id]
        logger.info(f"Cliente desconectado: {client_id}")

    async def send_message(self, client_id: str, message: Dict):
        if client_id in self._connections:
            try:
                await self._connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: Dict):
        for client_id in list(self._connections.keys()):
            await self.send_message(client_id, message)

    def queue_message(self, client_id: str, message: Dict):
        if client_id not in self._message_queue:
            self._message_queue[client_id] = []
        self._message_queue[client_id].append(message)

    def get_queued_messages(self, client_id: str) -> List[Dict]:
        return self._message_queue.pop(client_id, [])


vision_system = VisionSystem()
ws_manager = WebSocketManager()
