"""Visual identity for JEGEO PAYLOAD.

Centralizes the color palette and the QSS stylesheet so every widget in the
app shares one consistent hologram/terminal look: near-black backgrounds,
cyan primary glow, red alert accents, thin hairline borders instead of
skeuomorphic chrome.
"""

FONT_STACK = '"Fira Code", "JetBrains Mono", "Hack", "Source Code Pro", ' \
             '"DejaVu Sans Mono", "Consolas", monospace'


class Palette:
    bg = "#04070a"
    bg_panel = "#070d12"
    bg_panel_alt = "#0a131a"
    bg_input = "#081119"

    cyan = "#28f5e8"
    cyan_dim = "#0f8f8a"
    cyan_faint = "#123339"

    red = "#ff3355"
    red_dim = "#7a1f2c"

    amber = "#ffb347"
    green = "#5dffa0"

    text = "#cdfbff"
    text_dim = "#5f8b90"
    text_faint = "#33555a"

    border = "#134048"
    border_bright = "#1f6b73"


def stylesheet() -> str:
    p = Palette
    return f"""
    * {{
        font-family: {FONT_STACK};
        outline: none;
    }}

    QWidget {{
        background-color: {p.bg};
        color: {p.text};
        selection-background-color: {p.cyan_dim};
        selection-color: {p.bg};
    }}

    QMainWindow, #rootWindow {{
        background-color: {p.bg};
    }}

    QLabel {{
        background: transparent;
        color: {p.text};
    }}

    QLabel[role="title"] {{
        color: {p.cyan};
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 4px;
    }}

    QLabel[role="subtitle"] {{
        color: {p.text_dim};
        font-size: 11px;
        letter-spacing: 3px;
    }}

    QLabel[role="tagline"] {{
        color: {p.text_dim};
        font-size: 11px;
    }}

    QLabel[role="section"] {{
        color: {p.cyan_dim};
        font-size: 11px;
        letter-spacing: 2px;
        border-bottom: 1px solid {p.border};
        padding-bottom: 4px;
    }}

    QFrame[role="panel"] {{
        background-color: {p.bg_panel};
        border: 1px solid {p.border};
        border-radius: 2px;
    }}

    QFrame[role="hairline"] {{
        background-color: {p.border};
        max-height: 1px;
        min-height: 1px;
    }}

    QPushButton {{
        background-color: {p.bg_panel_alt};
        color: {p.cyan};
        border: 1px solid {p.border_bright};
        border-radius: 2px;
        padding: 7px 16px;
        letter-spacing: 2px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {p.cyan_faint};
        border: 1px solid {p.cyan};
        color: #eafffe;
    }}

    QPushButton:pressed {{
        background-color: {p.cyan_dim};
        color: {p.bg};
    }}

    QPushButton:disabled {{
        color: {p.text_faint};
        border: 1px solid {p.border};
        background-color: {p.bg_panel};
    }}

    QPushButton[role="danger"] {{
        color: {p.red};
        border: 1px solid {p.red_dim};
    }}
    QPushButton[role="danger"]:hover {{
        background-color: #2a0f16;
        border: 1px solid {p.red};
        color: #ffd7dd;
    }}

    QPushButton[role="module"] {{
        text-align: left;
        padding: 10px 12px;
        border: 1px solid {p.border};
        background-color: {p.bg_panel};
        color: {p.text};
        letter-spacing: 1px;
        font-weight: 500;
    }}
    QPushButton[role="module"]:hover {{
        border: 1px solid {p.cyan};
        color: {p.cyan};
        background-color: {p.cyan_faint};
    }}
    QPushButton[role="module"]:checked {{
        border: 1px solid {p.cyan};
        color: {p.bg};
        background-color: {p.cyan};
        font-weight: 700;
    }}

    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
        background-color: {p.bg_input};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 2px;
        padding: 5px 8px;
        selection-background-color: {p.cyan_dim};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border: 1px solid {p.cyan};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p.bg_panel_alt};
        color: {p.text};
        border: 1px solid {p.cyan_dim};
        selection-background-color: {p.cyan_dim};
        selection-color: {p.bg};
    }}

    QCheckBox {{
        color: {p.text};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {p.border_bright};
        background: {p.bg_input};
    }}
    QCheckBox::indicator:checked {{
        background: {p.cyan};
        border: 1px solid {p.cyan};
    }}

    QRadioButton {{
        color: {p.text};
        spacing: 8px;
    }}
    QRadioButton::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 7px;
        border: 1px solid {p.border_bright};
        background: {p.bg_input};
    }}
    QRadioButton::indicator:checked {{
        background: {p.cyan};
        border: 1px solid {p.cyan};
    }}

    QScrollBar:vertical {{
        background: {p.bg_panel};
        width: 9px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border_bright};
        min-height: 24px;
        border-radius: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.cyan_dim};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: {p.bg_panel};
        height: 9px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.border_bright};
        min-width: 24px;
        border-radius: 2px;
    }}

    QProgressBar {{
        background-color: {p.bg_input};
        border: 1px solid {p.border};
        border-radius: 2px;
        text-align: center;
        color: {p.text};
        height: 14px;
    }}
    QProgressBar::chunk {{
        background-color: {p.cyan_dim};
    }}

    QTabWidget::pane {{
        border: 1px solid {p.border};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {p.bg_panel};
        color: {p.text_dim};
        border: 1px solid {p.border};
        padding: 6px 14px;
        letter-spacing: 1px;
    }}
    QTabBar::tab:selected {{
        color: {p.cyan};
        border-bottom: 2px solid {p.cyan};
    }}

    QToolTip {{
        background-color: {p.bg_panel_alt};
        color: {p.cyan};
        border: 1px solid {p.cyan_dim};
        padding: 4px;
    }}

    QSplitter::handle {{
        background-color: {p.border};
    }}

    #consoleOutput {{
        background-color: #030608;
        border: 1px solid {p.border};
        color: {p.cyan};
        font-size: 12px;
        padding: 8px;
    }}
    """
