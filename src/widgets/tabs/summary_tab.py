"""
Summary Tab

Text summary display for PCA variance explained and component statistics.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class SummaryTab(QWidget):
    """Summary tab widget displaying PCA variance statistics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the summary tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)

    def update_summary(self, summary_text: str):
        """Update the summary text

        Args:
            summary_text: Formatted summary text to display
        """
        self.summary_text.setPlainText(summary_text)

    def clear(self):
        """Clear the summary text"""
        self.summary_text.clear()
