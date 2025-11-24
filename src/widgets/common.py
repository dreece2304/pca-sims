"""
Common utility widgets used throughout the application.

Pure UI components with minimal dependencies.
"""

from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts numerically instead of lexicographically"""

    def __lt__(self, other):
        """Override less-than comparison for proper numeric sorting"""
        try:
            # Get numeric values from UserRole data
            self_value = self.data(Qt.UserRole)
            other_value = other.data(Qt.UserRole)

            # Compare numerically if both are numbers
            if self_value is not None and other_value is not None:
                return float(self_value) < float(other_value)
            else:
                # Fall back to string comparison
                return super().__lt__(other)
        except (ValueError, TypeError):
            # Fall back to string comparison if conversion fails
            return super().__lt__(other)
