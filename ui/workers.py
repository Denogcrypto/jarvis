from PySide6.QtCore import QThread, Signal

from assistant.core import AssistantCore


class ChatWorker(QThread):
    status = Signal(str)
    completed = Signal(str)

    def __init__(self, core: AssistantCore, text: str, attachment_text: str = ""):
        super().__init__()
        self.core = core
        self.text = text
        self.attachment_text = attachment_text

    def run(self) -> None:
        answer = self.core.handle(self.text, self.attachment_text, self.status.emit)
        self.completed.emit(answer)
