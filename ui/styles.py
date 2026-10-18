APP_STYLE = """
QWidget { background: #071019; color: #d9eaf4; font-family: 'Segoe UI'; font-size: 10pt; }
QMainWindow { background: #050b12; }
QFrame#card { background: #0b1722; border: 1px solid #173348; border-radius: 14px; }
QFrame#softCard { background: #0a141e; border: 1px solid #142a3a; border-radius: 11px; }
QLabel#muted { color: #8299a9; }
QLabel#cyan { color: #44ddff; font-weight: 600; }
QLabel#heading { color: #e9f8ff; font-size: 14pt; font-weight: 600; }
QLabel#brand { color: #e8faff; font-size: 19pt; font-weight: 700; letter-spacing: 4px; }
QLabel#status { color: #52dcff; font-size: 11pt; font-weight: 600; letter-spacing: 2px; }
QPushButton { background: #102333; border: 1px solid #1d4861; border-radius: 9px; padding: 9px 13px; color: #c9eefa; }
QPushButton:hover { background: #15364b; border-color: #3acff2; }
QPushButton:pressed { background: #1a5268; }
QPushButton:disabled { color: #587080; background: #0b1620; border-color: #122838; }
QPushButton#primary { background: #07394a; border: 1px solid #18b9dc; color: #dffaff; font-weight: 600; }
QPushButton#danger { border-color: #613b45; color: #ffc3cb; }
QLineEdit, QTextEdit, QComboBox { background: #08131d; border: 1px solid #1c3a4e; border-radius: 9px; padding: 10px; selection-background-color: #137a96; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #25c9ee; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #071019; width: 8px; margin: 3px; }
QScrollBar::handle:vertical { background: #1b526a; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSlider::groove:horizontal { height: 4px; background: #20394a; border-radius: 2px; }
QSlider::handle:horizontal { width: 13px; margin: -5px 0; border-radius: 6px; background: #46dfff; }
QCheckBox { spacing: 8px; color: #a9c0ce; }
QCheckBox::indicator { width: 16px; height: 16px; }
QCheckBox::indicator:unchecked { background: #101e29; border: 1px solid #31536a; border-radius: 4px; }
QCheckBox::indicator:checked { background: #12a8c7; border: 1px solid #60e9ff; border-radius: 4px; }
QDialog { background: #071019; }
QListWidget { background: #08131d; border: 1px solid #1c3a4e; border-radius: 9px; }
"""
