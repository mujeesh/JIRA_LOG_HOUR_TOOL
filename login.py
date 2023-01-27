from PyQt5 import uic
from PyQt5.QtCore import (pyqtSignal)
from PyQt5.QtWidgets import (QLineEdit,
                             QDialog, QPushButton)

USERNAME = "username"
PASSWORD = "password"


class ValidateCredentials(QDialog):
    username_filed: QLineEdit
    password_field: QLineEdit
    login_btn: QPushButton

    send_credentials = pyqtSignal(str, str)

    def __init__(self, *args, **kwargs):
        super(ValidateCredentials, self).__init__()
        uic.loadUi("gui/login.ui", self)
        self.password_field.setEchoMode(QLineEdit.Password)
        self.login_btn.clicked.connect(self.authenticate_credentials)
        self.show()

    def authenticate_credentials(self):
        username = self.username_filed.text()
        password = self.password_field.text()
        if username and password:
            self.send_credentials.emit(username, password)
        self.close()
