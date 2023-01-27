import logging

from PyQt5.QtCore import pyqtSignal, QRegExp, Qt
from PyQt5.QtGui import QRegExpValidator, QMouseEvent
from PyQt5.QtWidgets import (QLineEdit)

LOGGER = logging.getLogger(__file__)
REGEX = QRegExp("([1-8](\.\d)?|\.[0-9]{1})")


class CellWidget(QLineEdit):
    """
    CellWidget instance will set in TableWidget each cell (row, col)
    REGEX only will allow to set value in between above 0. and less than 9.
    """
    cell_widget_signal = pyqtSignal(str, int, int)  # Signal to cell value, row, col details to JiraTool class

    def __init__(self, parent):
        super(CellWidget, self).__init__(parent)
        validator = QRegExpValidator(REGEX, self)
        self.col = None
        self.row = None
        self.setValidator(validator)
        self.show()
        self.setAlignment(Qt.AlignCenter)
        self.textEdited.connect(self.cell_value_changed)

    def cell_value_changed(self):
        """
        :return: Send cell value, row, col details to JiraTool class
        """
        try:
            value = float(self.text())
        except ValueError:
            return
        self.cell_widget_signal.emit(value, self.row, self.col)
        self.change_color()

    def change_color(self):
        """
        Function to change the color of value if its not 0
        :return: updated font color
        """
        self.setStyleSheet("color:green; border:1.5px solid green;")

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        """
        allow auto select the cell automatically
        :param a0: pyqt builtin mouseEvent
        :return:
        """
        self.selectAll()
