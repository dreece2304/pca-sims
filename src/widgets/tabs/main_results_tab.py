"""
Main Results Tab

Main PCA visualization tab with interactive matplotlib plots.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from widgets.plotting import PCAPlotCanvas


class MainResultsTab(QWidget):
    """Main results tab widget with PCA plot canvas"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the main results tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create matplotlib canvas with DPI awareness
        self.plot_canvas = PCAPlotCanvas(self, width=12, height=8)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self)

        layout.addWidget(self.plot_toolbar)
        layout.addWidget(self.plot_canvas)

    def get_canvas(self):
        """Get the plot canvas

        Returns:
            PCAPlotCanvas: The matplotlib plot canvas
        """
        return self.plot_canvas
