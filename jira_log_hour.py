import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from queue import Queue

from PyQt5 import uic
from PyQt5.QtCore import (Qt, QSettings)
from PyQt5.QtGui import QCloseEvent, QColor
from PyQt5.QtWidgets import (QApplication, QTableWidgetItem,
                             QMainWindow, QTableWidget, QPushButton)
from dateutil import parser
from jira import JIRA, JIRAError

from basic_functions import error_message
from cell_widget import CellWidget
from jira_thread import JiraThread
from login import ValidateCredentials

USERNAME = "username"
PASSWORD = "password"
DONE = 'Done'
JIRA_SERVER = 'https://jira-xxxxxxxxx-xxxx-xxx'
WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LOGGER = logging.getLogger(__file__)


class JiraTool(QMainWindow):
    jira_task_list_table: QTableWidget
    next_btn: QPushButton
    prev_btn: QPushButton
    auth_btn: QPushButton
    refresh_btn: QPushButton
    username: str = ""
    password: str = ""
    
    def __init__(self):
        super(JiraTool, self).__init__()
        uic.loadUi('gui/jira_tool.ui', self)  # Load the .ui file
        for i in range(9):
            item = self.jira_task_list_table.horizontalHeaderItem(i)
            item.setBackground(QColor(0, 0, 255))
        self.today = datetime.now().date()
        self.week = 0
        self.date_list = []
        self.work_log_details = defaultdict(dict)
        self.jira = None
        self.task_queue = Queue()  # Queue each cell changes and update
        self.jira_thread = JiraThread(self.task_queue)  # Thread for log hour
        self.jira_thread.start()

        self.issues = list()
        style = "QHeaderView::section {""background-color: lightblue; border-bottom: 1px solid gray;}"
        self.jira_task_list_table.horizontalHeader().setStyleSheet(style)
        self.jira_task_list_table.setColumnWidth(0, 200)
        self.jira_task_list_table.setColumnWidth(8, 200)
        self.next_btn.clicked.connect(lambda: self.populate_date(1))
        self.prev_btn.clicked.connect(lambda: self.populate_date(-1))
        self.auth_btn.clicked.connect(self.check_credentials)
        self.refresh_btn.clicked.connect(self.refresh_issues)

        self.previous_value = 0
        self.jira_task_list_table.blockSignals(True)
        self.jira_task_list_table.setShowGrid(True)
        self.save_credentials()
        self.populate_date(0)
        # self.test_with_dummy()
        self.jira_task_list_table.blockSignals(False)

    def populate_date(self, btn_number):
        """
        Common function for prev and next button
        :param btn_number: prev == -1 and next == 1
        :return:
        """
        self.jira_task_list_table.blockSignals(True)
        self.date_list.clear()
        self.week += btn_number
        new_date = self.today + timedelta(self.today.weekday(), weeks=self.week)
        today = new_date
        start = today - timedelta(days=today.weekday())

        # Create a date_list for particular week
        for i in range(1, 8):
            item = self.jira_task_list_table.horizontalHeaderItem(i)
            name = WEEK[i - 1]
            if i == 1:
                item.setText(f"{name} {start.day}")
                self.date_list.append(start)
            else:
                next_day = start + timedelta(days=i - 1)
                item.setText(f"{name} {next_day.day}")
                self.date_list.append(next_day)

        self.update_table()  # update values in the TableWidget
        self.jira_task_list_table.blockSignals(False)

    def refresh_issues(self, first_time=True):
        """
        Refresh jira issues by searching again
        :return:
        """
        # uic05031
        self.issues.clear()
        issues = self.jira.search_issues(f"assignee={self.username}")
        for issue in issues:
            status = str(issue.fields.status)
            if status != "Done" and status != "Canceled":
                self.issues.append(issue)

        for row, issue in enumerate(self.issues, start=0):
            self.set_work_log_in_row(issue, row)

        if not first_time:
            self.update_table()

    def search_assign_tickets(self):
        """
        :return:
        """
        self.refresh_issues(first_time=True)
        self.jira_task_list_table.setRowCount(len(self.issues))
        self.update_table()
        self.set_total_time_spent()

    def set_title(self, issue, row):
        """
        Set title by setting column zero
        :param issue: JIRA issue
        :param row: row number
        :return: None
        """
        title = str(issue.key)
        item = QTableWidgetItem(title)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        item.setToolTip(str(issue.fields.summary))
        item.setTextAlignment(Qt.AlignCenter)
        self.jira_task_list_table.setItem(row, 0, item)

    def set_status(self, issue, row):
        """
        Set status by setting column 8
        :param issue: JIRA ISSUE
        :param row: row number
        :return: None
        """
        status = str(issue.fields.status)
        item = QTableWidgetItem(str(status))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.jira_task_list_table.setItem(row, 8, item)

    def update_table(self, ):
        for row, issue in enumerate(self.issues):
            self.set_title(issue, row)
            details = self.work_log_details.get(row, {})
            for col, date_ in enumerate(self.date_list, start=1):
                time_spent = details.get(date_, (0, 0))[0]
                cell_widget = CellWidget(self)
                cell_widget.setText(str(time_spent))
                cell_widget.cell_widget_signal.connect(self.cell_value_changed)
                cell_widget.row = row
                cell_widget.col = col
                self.jira_task_list_table.setCellWidget(row, col, cell_widget)
                if time_spent:
                    cell_widget.change_color()

                # to get story points of the issue
                if issue.fields.customfield_10006 is None:
                    story_points = str(0)
                else:
                    story_points_in_hours = issue.fields.customfield_10006 * 8
                    story_points = str(issue.fields.customfield_10006) + " (" + str(story_points_in_hours) + "hrs)"
                item = QTableWidgetItem(story_points)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self.jira_task_list_table.setItem(row, 9, item)
            self.set_status(issue, row)

    def set_work_log_in_row(self, issue, row):
        work_logs = self.jira.worklogs(issue.id)
        for work_log in work_logs:
            started_date = parser.isoparse(work_log.started)
            time_spent = work_log.timeSpentSeconds / (60 * 60)
            self.work_log_details[row][started_date.date()] = (time_spent, work_log)

    def set_total_time_spent(self):
        for row in self.work_log_details:
            values = self.work_log_details[row].values()
            total_time_spent = sum([value[0] for value in values])
            item = QTableWidgetItem(str(total_time_spent))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.jira_task_list_table.setItem(row, 10, item)  # Total time spent

    def check_credentials(self):
        if not self.username:
            login_window = ValidateCredentials(self)
            login_window.send_credentials.connect(self.authenticate)
            login_window.exec_()

    def authenticate(self, username, password, read_local=None):
        try:
            self.jira: JIRA = JIRA(options={"server": JIRA_SERVER},
                                   basic_auth=(username, password))
            self.username = username
            self.password = password
            if not read_local:
                self.save_credentials(username, password)
            self.auth_btn.hide()

            self.jira_task_list_table.blockSignals(True)
            self.search_assign_tickets()
            self.jira_task_list_table.blockSignals(False)
        except JIRAError:
            error_message("Wrong Credentials or Unable to access JIRA")
            self.auth_btn.show()

    def save_credentials(self, username=None, password=None):
        """
        Save credentials to local 'C:/Users/uicxxxx/AppData/Roaming/Continental/JiraTool.ini'
        :param username: username
        :param password: password
        :return:
        """
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "Continental", "JiraTool")
        settings.beginGroup("Credential")
        if username and password:
            settings.setValue(USERNAME, username)
            settings.setValue(PASSWORD, password)
        else:
            self.username = settings.value(USERNAME, None)
            self.password = settings.value(PASSWORD, None)
            if self.username:
                self.authenticate(self.username, self.password, True)

    def cell_value_changed(self, value, row, col):
        """
        Function to put value in JIRA Thread Queue
        :param value: edited cell value
        :param row: row
        :param col: col
        :return: update in JIRA
        """
        try:
            booking_date = self.date_list[col - 1]
            booked_hour = value
        except Exception as err:
            LOGGER.error(err)
            return

        issue = self.issues[row]
        log_details = self.work_log_details.get(row, {})
        work_log = log_details.get(booking_date, (0, 0))[1]
        log_details[booking_date] = (float(booked_hour), work_log)
        self.task_queue.put((self.jira, issue, booking_date, booked_hour, work_log))
        self.set_total_time_spent()

    def closeEvent(self, a0: QCloseEvent) -> None:
        """
        Close JiraThread
        :param a0: close-event
        :return:
        """
        self.task_queue.put("END")
        self.jira_thread.join()
        self.task_queue.join()

    def test_with_dummy(self):
        import random
        issues = ["CEM200-24033", "CEM200-24032", "CEM200-24034"]
        self.jira_task_list_table.setRowCount(len(issues))

        for row, issue in enumerate(issues):
            self.jira_task_list_table.insertRow(row)
            for col in range(9):
                if not col:
                    time_spent = issue
                else:
                    time_spent = random.randint(1, 9)
                item = QTableWidgetItem(str(time_spent))
                self.jira_task_list_table.setItem(row, col, item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JiraTool()
    window.show()
    app.exec_()
