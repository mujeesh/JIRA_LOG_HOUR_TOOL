from PyQt5.QtWidgets import QMessageBox


def error_message(message):
    msg = QMessageBox()
    msg.resize(500, 2000)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Error")
    msg.setText(message)
    msg.exec_()


def info_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Info")
    msg.setText(message)
    msg.exec_()
