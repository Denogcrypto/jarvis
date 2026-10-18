from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QInputDialog, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSlider, QSplitter, QVBoxLayout, QWidget,
)

from assistant.core import AssistantCore
from config.settings import Settings, save_settings
from memory.store import MemoryStore
from ui.styles import APP_STYLE
from ui.workers import ChatWorker
from voice.engine import ListenWorker, SpeechWorker


def card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    return frame


class CoreWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.phase = "idle"
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(45)
        self.setMinimumSize(250, 280)

    def set_phase(self, phase: str) -> None:
        self.phase = phase
        self.update()

    def _tick(self) -> None:
        self.angle = (self.angle + (4 if self.phase != "idle" else 1)) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) * 0.34
        colors = {"listening": (44, 228, 255), "speaking": (87, 174, 255), "thinking": (84, 125, 255), "executing": (70, 240, 198), "idle": (40, 199, 235)}
        color = QColor(*colors.get(self.phase, colors["idle"]))
        glow = QRadialGradient(center, radius * 1.4)
        glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 45))
        glow.setColorAt(0.55, QColor(color.red(), color.green(), color.blue(), 15))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, int(radius * 1.4), int(radius * 1.4))
        for index, scale in enumerate((1.0, 0.78, 0.57)):
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 85 - index * 15), 1.3 if index else 1.7)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, int(radius * scale), int(radius * scale))
        painter.save()
        painter.translate(center)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor(117, 239, 255, 190), 2))
        painter.drawArc(int(-radius), int(-radius), int(radius * 2), int(radius * 2), 12 * 16, 65 * 16)
        painter.drawArc(int(-radius * .78), int(-radius * .78), int(radius * 1.56), int(radius * 1.56), 160 * 16, 52 * 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(193, 248, 255))
        painter.drawEllipse(int(radius * .95), -4, 8, 8)
        painter.restore()
        inner = QRadialGradient(center, radius * .45)
        inner.setColorAt(0, QColor(123, 235, 255, 205))
        inner.setColorAt(.35, QColor(29, 149, 193, 155))
        inner.setColorAt(1, QColor(8, 50, 79, 65))
        painter.setPen(QPen(QColor(105, 232, 255, 200), 1))
        painter.setBrush(inner)
        painter.drawEllipse(center, int(radius * .34), int(radius * .34))
        painter.setPen(QColor(229, 251, 255))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "J")


class WaveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.active = False
        self.tick = 0
        self.setFixedHeight(46)
        timer = QTimer(self)
        timer.timeout.connect(self.animate)
        timer.start(70)

    def animate(self) -> None:
        self.tick += 1
        self.update()

    def set_active(self, active: bool) -> None:
        self.active = active
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        count = 32
        center_y = self.height() / 2
        gap = self.width() / (count + 1)
        for index in range(count):
            wave = abs(((index * 13 + self.tick * 3) % 29) - 14) / 14
            amplitude = (5 + wave * 13) if self.active else (3 + wave * 5)
            height = amplitude * (0.8 + 0.2 * abs((index - count / 2) / (count / 2)))
            color = QColor(53, 218, 246, 180 if self.active else 85)
            painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            x = (index + 1) * gap
            painter.drawLine(int(x), int(center_y - height), int(x), int(center_y + height))


class MessageBubble(QFrame):
    def __init__(self, role: str, text: str):
        super().__init__()
        self.setObjectName("softCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        who = QLabel("TÚ" if role == "user" else "JARVIS")
        who.setObjectName("cyan" if role == "assistant" else "muted")
        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(who)
        layout.addWidget(body)


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Configuración de JARVIS")
        self.resize(520, 380)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Proveedor compatible con OpenAI"))
        self.endpoint = QLineEdit(settings.base_url)
        self.model = QLineEdit(settings.model)
        layout.addWidget(QLabel("URL base (local por defecto: Ollama)"))
        layout.addWidget(self.endpoint)
        layout.addWidget(QLabel("Modelo"))
        layout.addWidget(self.model)
        self.key_status = QLabel("Clave API: " + ("configurada en JARVIS_API_KEY" if settings.api_key else "no configurada (no necesaria para Ollama local)"))
        self.key_status.setObjectName("muted")
        layout.addWidget(self.key_status)
        layout.addWidget(QLabel("Volumen de voz"))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(round(settings.voice_volume * 100))
        layout.addWidget(self.volume)
        layout.addWidget(QLabel("Velocidad de voz"))
        self.rate = QSlider(Qt.Orientation.Horizontal)
        self.rate.setRange(120, 250)
        self.rate.setValue(settings.voice_rate)
        layout.addWidget(self.rate)
        self.auto_speak = QCheckBox("Leer automáticamente las respuestas (TTS local)")
        self.auto_speak.setChecked(settings.auto_speak)
        layout.addWidget(self.auto_speak)
        note = QLabel("Las claves nunca se guardan en settings.json ni se muestran. Define JARVIS_API_KEY en Windows para servicios en la nube.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        base = self.endpoint.text().strip().rstrip("/")
        model = self.model.text().strip()
        if not base.startswith(("http://", "https://")) or not model:
            QMessageBox.warning(self, "Configuración incompleta", "Indica una URL http(s) y el nombre del modelo.")
            return
        self.settings.base_url = base
        self.settings.model = model
        self.settings.voice_volume = self.volume.value() / 100
        self.settings.voice_rate = self.rate.value()
        self.settings.auto_speak = self.auto_speak.isChecked()
        save_settings(self.settings)
        super().accept()


class MemoryDialog(QDialog):
    def __init__(self, store: MemoryStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Memoria local")
        self.resize(620, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("JARVIS solo guarda recuerdos cuando se lo pides. Puedes editar o eliminar cada elemento."))
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        row = QHBoxLayout()
        self.new_text = QLineEdit()
        self.new_text.setPlaceholderText("Agregar un recuerdo…")
        add = QPushButton("Agregar")
        add.clicked.connect(self.add_memory)
        edit = QPushButton("Editar seleccionado")
        edit.clicked.connect(self.edit_memory)
        delete = QPushButton("Eliminar seleccionado")
        delete.setObjectName("danger")
        delete.clicked.connect(self.delete_memory)
        row.addWidget(self.new_text, 1)
        row.addWidget(add)
        layout.addLayout(row)
        controls = QHBoxLayout()
        controls.addWidget(edit)
        controls.addWidget(delete)
        clear_all = QPushButton("Borrar toda la memoria")
        clear_all.setObjectName("danger")
        clear_all.clicked.connect(self.clear_all)
        controls.addWidget(clear_all)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for memory in self.store.memories():
            item = QListWidgetItem(f"[{memory['category']}]  {memory['content']}")
            item.setData(Qt.ItemDataRole.UserRole, memory["id"])
            self.list.addItem(item)

    def add_memory(self) -> None:
        value = self.new_text.text().strip()
        if value:
            if any(word in value.casefold() for word in ("contraseña", "password", "api key", "token", "tarjeta de crédito")):
                QMessageBox.warning(self, "Dato sensible", "No guardo contraseñas, credenciales ni datos financieros.")
                return
            try:
                self.store.add_memory(value)
            except ValueError as exc:
                QMessageBox.warning(self, "Recuerdo no válido", str(exc))
                return
            self.new_text.clear()
            self.refresh()

    def edit_memory(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        value, ok = QInputDialog.getText(self, "Editar recuerdo", "Contenido:", text=item.text().split("  ", 1)[-1])
        if ok and value.strip():
            try:
                self.store.update_memory(item.data(Qt.ItemDataRole.UserRole), value)
            except ValueError as exc:
                QMessageBox.warning(self, "Recuerdo no válido", str(exc))
                return
            self.refresh()

    def delete_memory(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Eliminar recuerdo", "¿Eliminar este recuerdo de forma permanente?") == QMessageBox.StandardButton.Yes:
            self.store.delete_memory(item.data(Qt.ItemDataRole.UserRole))
            self.refresh()

    def clear_all(self) -> None:
        if not self.store.memories():
            return
        if QMessageBox.question(self, "Borrar toda la memoria", "¿Eliminar permanentemente todos los recuerdos guardados?") == QMessageBox.StandardButton.Yes:
            self.store.clear_memories()
            self.refresh()


class ActivityDialog(QDialog):
    def __init__(self, store: MemoryStore, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro local de actividad")
        self.resize(700, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Registro de solicitudes enviadas a herramientas locales y su resultado."))
        listing = QListWidget()
        layout.addWidget(listing, 1)
        for action in store.actions():
            text = f"{action['created_at']}\n{action['request']}\n→ {action['result']}"
            listing.addItem(QListWidgetItem(text))
        if listing.count() == 0:
            listing.addItem("Todavía no hay acciones registradas.")


class JarvisWindow(QMainWindow):
    def __init__(self, settings: Settings, store: MemoryStore):
        super().__init__()
        self.settings = settings
        self.store = store
        self.core = AssistantCore(settings, store)
        self.chat_worker: ChatWorker | None = None
        self.listen_worker: ListenWorker | None = None
        self.speech_worker: SpeechWorker | None = None
        self.mic_enabled = False
        self.attachment_text = ""
        self.attachment_label = ""
        self.action_id_before_send = 0
        self.setWindowTitle("JARVIS · Asistente personal")
        self.setMinimumSize(980, 680)
        self.resize(1500, 940)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._load_history()
        self._update_clock()
        timer = QTimer(self)
        timer.timeout.connect(self._update_clock)
        timer.start(1000)
        self._update_system()
        system_timer = QTimer(self)
        system_timer.timeout.connect(self._update_system)
        system_timer.start(4000)

    def _build_ui(self) -> None:
        base = QWidget()
        root = QVBoxLayout(base)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)
        header = QHBoxLayout()
        brand = QLabel("JARVIS")
        brand.setObjectName("brand")
        subtitle = QLabel("SISTEMA DE INTELIGENCIA PERSONAL")
        subtitle.setObjectName("muted")
        head_text = QVBoxLayout()
        head_text.addWidget(brand)
        head_text.addWidget(subtitle)
        header.addLayout(head_text)
        header.addStretch(1)
        self.connection_label = QLabel("●  LOCAL · OLLAMA")
        self.connection_label.setText("○  CONEXIÓN SIN COMPROBAR")
        self.connection_label.setObjectName("cyan")
        header.addWidget(self.connection_label)
        memory_button = QPushButton("Memoria")
        memory_button.clicked.connect(self._show_memory)
        activity_button = QPushButton("Actividad")
        activity_button.clicked.connect(lambda: ActivityDialog(self.store, self).exec())
        settings_button = QPushButton("Ajustes")
        settings_button.clicked.connect(self._show_settings)
        clear_button = QPushButton("Borrar historial")
        clear_button.setObjectName("danger")
        clear_button.clicked.connect(self._clear_history)
        header.addWidget(memory_button)
        header.addWidget(activity_button)
        header.addWidget(settings_button)
        header.addWidget(clear_button)
        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        left = self._build_side_panel()
        middle = self._build_core_panel()
        right = self._build_chat_panel()
        splitter.addWidget(left)
        splitter.addWidget(middle)
        splitter.addWidget(right)
        splitter.setSizes([260, 420, 600])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        root.addWidget(splitter, 1)
        self.setCentralWidget(base)

    def _build_side_panel(self) -> QWidget:
        side = QWidget()
        side.setMinimumWidth(220)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 8, 0)
        status_card = card()
        s = QVBoxLayout(status_card)
        title = QLabel("ESTADO DEL SISTEMA")
        title.setObjectName("muted")
        s.addWidget(title)
        self.clock_label = QLabel("--:--")
        self.clock_label.setStyleSheet("font-size: 29pt; color: #e4faff; font-weight: 300;")
        self.date_label = QLabel("--")
        self.date_label.setObjectName("muted")
        s.addWidget(self.clock_label)
        s.addWidget(self.date_label)
        s.addSpacing(12)
        self.cpu_label = QLabel("CPU  ···")
        self.ram_label = QLabel("RAM  ···")
        self.battery_label = QLabel("BATERÍA  ···")
        for label in (self.cpu_label, self.ram_label, self.battery_label):
            label.setObjectName("cyan")
            s.addWidget(label)
        layout.addWidget(status_card)

        audio_card = card()
        a = QVBoxLayout(audio_card)
        audio_title = QLabel("AUDIO Y PRIVACIDAD")
        audio_title.setObjectName("muted")
        a.addWidget(audio_title)
        self.mic_button = QPushButton("Activar micrófono")
        self.mic_button.clicked.connect(self._toggle_mic)
        a.addWidget(self.mic_button)
        self.listen_button = QPushButton("●  Pulsar para hablar")
        self.listen_button.setObjectName("primary")
        self.listen_button.clicked.connect(self._listen)
        a.addWidget(self.listen_button)
        self.voice_check = QCheckBox("Leer respuestas en voz alta")
        self.voice_check.setChecked(self.settings.auto_speak)
        self.voice_check.toggled.connect(self._toggle_auto_speak)
        a.addWidget(self.voice_check)
        self.stop_speech_button = QPushButton("Detener voz")
        self.stop_speech_button.clicked.connect(self._stop_speech)
        a.addWidget(self.stop_speech_button)
        layout.addWidget(audio_card)

        tools_card = card()
        t = QVBoxLayout(tools_card)
        t.addWidget(QLabel("HERRAMIENTAS ACTIVAS"))
        tools_text = QLabel("Aplicaciones permitidas\nBúsqueda web en navegador\nNotas locales\nArchivos por nombre\nMemoria SQLite\nEstado del equipo")
        tools_text.setObjectName("muted")
        tools_text.setWordWrap(True)
        t.addWidget(tools_text)
        layout.addWidget(tools_card)
        layout.addStretch(1)
        return side

    def _build_core_panel(self) -> QWidget:
        panel = card()
        panel.setMinimumWidth(260)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        self.state_label = QLabel("ESPERANDO")
        self.state_label.setObjectName("status")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.state_label)
        self.core_widget = CoreWidget()
        layout.addWidget(self.core_widget, 0, Qt.AlignmentFlag.AlignCenter)
        self.wave = WaveWidget()
        layout.addWidget(self.wave)
        self.core_hint = QLabel("Listo cuando tú lo estés.")
        self.core_hint.setObjectName("muted")
        self.core_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.core_hint)
        layout.addStretch(1)
        return panel

    def _build_chat_panel(self) -> QWidget:
        panel = card()
        panel.setMinimumWidth(340)
        layout = QVBoxLayout(panel)
        top = QHBoxLayout()
        title = QLabel("Conversación")
        title.setObjectName("heading")
        top.addWidget(title)
        top.addStretch(1)
        self.attachment_status = QLabel("")
        self.attachment_status.setObjectName("muted")
        top.addWidget(self.attachment_status)
        layout.addLayout(top)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.message_host = QWidget()
        self.messages = QVBoxLayout(self.message_host)
        self.messages.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages.setSpacing(9)
        self.scroll.setWidget(self.message_host)
        layout.addWidget(self.scroll, 1)
        controls = QHBoxLayout()
        attach = QPushButton("Adjuntar texto")
        attach.clicked.connect(self._attach_document)
        controls.addWidget(attach)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Escribe un mensaje para JARVIS…")
        self.input.returnPressed.connect(self._send)
        send = QPushButton("Enviar")
        send.setObjectName("primary")
        send.clicked.connect(self._send)
        controls.addWidget(self.input, 1)
        controls.addWidget(send)
        layout.addLayout(controls)
        return panel

    def _append_message(self, role: str, text: str) -> None:
        self.messages.addWidget(MessageBubble(role, text))
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def _load_history(self) -> None:
        history = self.store.conversation(100)
        if not history:
            self._append_message("assistant", "Buenas. Soy JARVIS. Puedo responder preguntas y realizar las tareas disponibles en el panel de herramientas.")
            return
        for item in history:
            self._append_message(item["role"], item["content"])

    def _send(self) -> None:
        text = self.input.text().strip()
        if not text or (self.chat_worker and self.chat_worker.isRunning()):
            return
        self.input.clear()
        self._append_message("user", text)
        self.input.setEnabled(False)
        self._set_phase("thinking")
        latest_actions = self.store.actions(1)
        self.action_id_before_send = latest_actions[0]["id"] if latest_actions else 0
        attachment = self.attachment_text
        self.attachment_text = ""
        self.attachment_label = ""
        self.attachment_status.clear()
        self.chat_worker = ChatWorker(self.core, text, attachment)
        self.chat_worker.status.connect(self._set_phase)
        self.chat_worker.completed.connect(self._chat_completed)
        self.chat_worker.start()

    def _chat_completed(self, answer: str) -> None:
        self._append_message("assistant", answer)
        self.input.setEnabled(True)
        self.input.setFocus()
        if answer.startswith("No pude obtener una respuesta del modelo:"):
            self.connection_label.setText("●  PROVEEDOR SIN CONEXIÓN")
        latest_actions = self.store.actions(1)
        action_was_run = bool(latest_actions and latest_actions[0]["id"] > self.action_id_before_send)
        if not action_was_run and not answer.startswith(("Por privacidad", "No pude completar la solicitud", "No pude obtener una respuesta del modelo:")):
            if "localhost" in self.settings.base_url or "127.0.0.1" in self.settings.base_url:
                self.connection_label.setText("●  OLLAMA RESPONDIÓ")
            else:
                self.connection_label.setText("●  PROVEEDOR RESPONDIÓ")
        if self.settings.auto_speak:
            self._speak(answer)
        else:
            self._set_phase("idle")

    def _attach_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona texto para resumir", str(Path.home()), "Texto (*.txt *.md)")
        if not path:
            return
        try:
            file_path = Path(path)
            if file_path.stat().st_size > 1_000_000:
                QMessageBox.warning(self, "Archivo grande", "Por seguridad, solo admito archivos de hasta 1 MB.")
                return
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            QMessageBox.warning(self, "No se pudo leer", str(exc))
            return
        self.attachment_text = text[:30000]
        self.attachment_label = file_path.name
        self.attachment_status.setText(f"Adjunto: {file_path.name}")
        if not self.input.text():
            self.input.setText("Resume este documento")

    def _toggle_mic(self) -> None:
        self.mic_enabled = not self.mic_enabled
        if self.mic_enabled:
            self.mic_button.setText("Desactivar micrófono")
            self.mic_button.setStyleSheet("border-color: #24d7b8; color: #8fffe9;")
            self.core_hint.setText("Micrófono habilitado · captura solo al pulsar el botón de voz.")
        else:
            self.mic_button.setText("Activar micrófono")
            self.mic_button.setStyleSheet("")
            self.core_hint.setText("Micrófono desactivado.")
            if self.listen_worker and self.listen_worker.isRunning():
                self.listen_worker.stop_capture()
        self._update_mic_indicator()

    def _update_mic_indicator(self) -> None:
        self.listen_button.setText("●  Pulsar para hablar" if self.mic_enabled else "Micrófono desactivado")
        self.listen_button.setEnabled(self.mic_enabled and not (self.listen_worker and self.listen_worker.isRunning()))

    def _listen(self) -> None:
        if not self.mic_enabled:
            return
        if self.listen_worker and self.listen_worker.isRunning():
            return
        self.listen_worker = ListenWorker(self.settings.stt_mode, self.settings.vosk_model_path)
        self.listen_worker.status.connect(self._listening_status)
        self.listen_worker.transcript.connect(self._recognized)
        self.listen_worker.error.connect(self._voice_error)
        self.listen_worker.finished.connect(self._update_mic_indicator)
        self._set_phase("listening")
        self._update_mic_indicator()
        self.listen_worker.start()

    def _listening_status(self, message: str) -> None:
        self.core_hint.setText(message)
        self.wave.set_active("Escuchando" in message)

    def _recognized(self, text: str) -> None:
        if not self.mic_enabled:
            return
        self.core_hint.setText(f"Reconocido: {text}")
        self.input.setText(text)
        self._send()

    def _voice_error(self, message: str) -> None:
        self._set_phase("idle")
        self.core_hint.setText("Voz no disponible.")
        QMessageBox.warning(self, "Entrada de voz", message)

    def _speak(self, text: str) -> None:
        if self.speech_worker and self.speech_worker.isRunning():
            self.speech_worker.stop_speaking()
            self.speech_worker.wait(900)
        self.speech_worker = SpeechWorker(text, self.settings.voice_volume, self.settings.voice_rate)
        self.speech_worker.failed.connect(self._voice_error)
        self.speech_worker.finished.connect(lambda: self._set_phase("idle"))
        self._set_phase("speaking")
        self.speech_worker.start()

    def _stop_speech(self) -> None:
        if self.speech_worker and self.speech_worker.isRunning():
            self.speech_worker.stop_speaking()
            self._set_phase("idle")

    def _toggle_auto_speak(self, enabled: bool) -> None:
        self.settings.auto_speak = enabled
        save_settings(self.settings)

    def _set_phase(self, phase: str) -> None:
        labels = {"idle": "ESPERANDO", "listening": "ESCUCHANDO", "thinking": "PENSANDO", "speaking": "HABLANDO", "executing": "EJECUTANDO TAREA"}
        self.state_label.setText(labels.get(phase, "ESPERANDO"))
        self.core_widget.set_phase(phase)
        self.wave.set_active(phase in {"listening", "speaking"})
        if phase == "idle":
            self.core_hint.setText("Listo cuando tú lo estés.")

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.voice_check.setChecked(self.settings.auto_speak)
            self.core.client.settings = self.settings
            self.connection_label.setText("●  LOCAL · OLLAMA" if "localhost" in self.settings.base_url or "127.0.0.1" in self.settings.base_url else "●  PROVEEDOR CONFIGURADO")

    def _show_memory(self) -> None:
        MemoryDialog(self.store, self).exec()

    def _clear_history(self) -> None:
        answer = QMessageBox.question(self, "Borrar historial", "¿Eliminar conversaciones y registro de actividad? Los recuerdos se conservan. Esta acción no se puede deshacer.")
        if answer == QMessageBox.StandardButton.Yes:
            self.store.clear_history()
            while self.messages.count():
                item = self.messages.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._append_message("assistant", "Historial eliminado. La memoria guardada se mantiene y puede administrarse por separado.")

    def _update_clock(self) -> None:
        now = __import__("datetime").datetime.now().astimezone()
        self.clock_label.setText(now.strftime("%H:%M:%S"))
        weekdays = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
        months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        self.date_label.setText(f"{weekdays[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year}".upper())

    def _update_system(self) -> None:
        try:
            import psutil
            self.cpu_label.setText(f"CPU   {psutil.cpu_percent(interval=None):.0f}%")
            memory = psutil.virtual_memory()
            self.ram_label.setText(f"RAM   {memory.percent:.0f}%")
            battery = psutil.sensors_battery()
            self.battery_label.setText(f"BATERÍA   {battery.percent:.0f}%" if battery else "BATERÍA   NO DISPONIBLE")
        except (ImportError, OSError, AttributeError):
            self.cpu_label.setText("CPU   n/d")
            self.ram_label.setText("RAM   n/d")
            self.battery_label.setText("BATERÍA   n/d")

    def closeEvent(self, event) -> None:
        workers = [worker for worker in (self.listen_worker, self.speech_worker, self.chat_worker) if worker and worker.isRunning()]
        if workers:
            event.ignore()
            self.core_hint.setText("Cerrando después de detener la tarea activa…")
            for worker in workers:
                if isinstance(worker, SpeechWorker):
                    worker.stop_speaking()
                elif isinstance(worker, ListenWorker):
                    worker.stop_capture()
                worker.finished.connect(self._close_when_workers_finish)
            return
        event.accept()

    def _close_when_workers_finish(self) -> None:
        if not any(worker and worker.isRunning() for worker in (self.listen_worker, self.speech_worker, self.chat_worker)):
            self.close()
