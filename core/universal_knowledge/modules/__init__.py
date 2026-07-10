from .gmail import GmailModule
from .calendar import CalendarModule
from .github import GitHubModule
from .system import SystemModule
from .web import WebModule
from .notion import NotionModule
from .telegram import TelegramModule
from .whatsapp import WhatsAppModule
from .email import EmailModule
from .memory import MemoryModule
from .news import NewsModule

__all__ = [
    'GmailModule', 'CalendarModule', 'GitHubModule', 'SystemModule', 'WebModule',
    'NotionModule', 'TelegramModule', 'WhatsAppModule', 'EmailModule', 'MemoryModule', 'NewsModule'
]
