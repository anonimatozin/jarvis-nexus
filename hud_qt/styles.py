"""QSS - Stark Reactor Pro Theme v3.0"""
from . import config as cfg

def get_stylesheet():
    p = cfg.PALETA
    return f"""
    QWidget#mainBackground {{
        background-color: {p['bg_main']};
    }}

    QWidget#miniOrbBg {{
        background-color: {p['bg_main']};
        border: 1px solid {p['border']};
        border-radius: 18px;
    }}

    QWidget#titleBar {{
        background-color: {p['bg_panel']};
        border-bottom: 1px solid {p['border']};
    }}

    QLabel#brandLabel {{
        color: {p['accent_glow']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 4px;
        padding-left: 16px;
    }}

    QPushButton#titleBtn {{
        background-color: transparent;
        border: none;
        color: {p['text_dim']};
        font-size: 13px;
        font-family: 'Segoe UI', sans-serif;
        min-width: 42px; max-width: 42px;
        min-height: 36px; max-height: 36px;
    }}
    QPushButton#titleBtn:hover {{
        background-color: {p['bg_elevated']};
        color: {p['text_bright']};
    }}
    QPushButton#titleBtnClose:hover {{
        background-color: {p['danger']};
        color: white;
    }}

    QPushButton#controlBtn {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 28px;
        color: {p['text_main']};
        font-size: 20px;
        min-width: 56px; max-width: 56px;
        min-height: 56px; max-height: 56px;
    }}
    QPushButton#controlBtn:hover {{
        background-color: {p['bg_elevated']};
        border-color: {p['accent']};
        color: {p['text_bright']};
    }}
    QPushButton#controlBtn[muted="true"] {{
        background-color: {p['danger']};
        border-color: {p['danger']};
        color: white;
    }}

    QLabel#statusLabel {{
        color: {p['accent_glow']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 10px;
        letter-spacing: 2px;
        font-weight: 600;
    }}

    QWidget#configPanel {{
        background-color: {p['bg_panel']};
        border-left: 1px solid {p['border']};
    }}

    QLabel#configTitle {{
        color: {p['accent_glow']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 3px;
        padding: 18px 22px 10px 22px;
    }}

    QPushButton#panelCloseBtn {{
        background-color: transparent;
        border: none;
        color: {p['text_dim']};
        font-size: 14px;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
    }}
    QPushButton#panelCloseBtn:hover {{
        background-color: {p['danger']};
        color: white;
    }}

    QListWidget#tabList {{
        background-color: transparent;
        border: none;
        color: {p['text_main']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        outline: 0;
    }}
    QListWidget#tabList::item {{
        padding: 12px 22px;
        border: none;
    }}
    QListWidget#tabList::item:hover {{
        background-color: {p['bg_elevated']};
        color: {p['text_bright']};
    }}
    QListWidget#tabList::item:selected {{
        background-color: {p['accent_bg']};
        color: {p['accent_glow']};
        border-left: 2px solid {p['accent']};
    }}

    QWidget#tabContent {{
        background-color: {p['bg_main']};
    }}

    QLabel#tabHeader {{
        color: {p['text_bright']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 15px;
        font-weight: 700;
        padding: 20px 24px 8px 24px;
    }}

    QLabel#tabSection {{
        color: {p['accent_glow']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        padding: 18px 24px 6px 24px;
    }}

    QLabel#fieldLabel {{
        color: {p['text_main']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        padding: 4px 0;
    }}

    QLabel#fieldHint {{
        color: {p['text_dim']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 10px;
        padding: 0 0 8px 0;
    }}

    QCheckBox {{
        color: {p['text_main']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        spacing: 8px;
        padding: 4px 0;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px;
        border: 1px solid {p['border']};
        background-color: {p['bg_elevated']};
        border-radius: 3px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {p['accent']};
        border-color: {p['accent']};
    }}

    QComboBox {{
        background-color: {p['bg_elevated']};
        border: 1px solid {p['border']};
        color: {p['text_bright']};
        padding: 6px 10px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {p['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p['bg_panel']};
        color: {p['text_main']};
        border: 1px solid {p['border']};
        selection-background-color: {p['accent_bg']};
        selection-color: {p['accent_glow']};
    }}

    QSpinBox {{
        background-color: {p['bg_elevated']};
        border: 1px solid {p['border']};
        color: {p['text_bright']};
        padding: 4px 8px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        min-height: 22px;
    }}

    QSlider::groove:horizontal {{
        background-color: {p['bg_elevated']};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background-color: {p['accent']};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background-color: {p['accent']};
        border-radius: 2px;
    }}

    QPushButton#configBtn {{
        background-color: {p['bg_elevated']};
        border: 1px solid {p['border']};
        color: {p['text_main']};
        padding: 8px 16px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        min-height: 28px;
    }}
    QPushButton#configBtn:hover {{
        background-color: {p['accent_bg']};
        color: {p['accent_glow']};
        border-color: {p['accent']};
    }}
    QPushButton#dangerBtn {{
        background-color: transparent;
        border: 1px solid {p['danger']};
        color: {p['danger']};
        padding: 8px 16px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QPushButton#dangerBtn:hover {{
        background-color: {p['danger']};
        color: white;
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background-color: {p['bg_main']};
        width: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {p['border']};
        border-radius: 4px;
        min-height: 20px;
    }}

    QToolTip {{
        background-color: {p['bg_elevated']};
        color: {p['text_main']};
        border: 1px solid {p['accent']};
        padding: 6px 10px;
        font-size: 11px;
    }}
    """
