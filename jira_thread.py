from threading import Thread


class JiraThread(Thread):
    def __init__(self, task_queue):
        """
        :param task_queue: Task Queue from jira_log_hour
        """
        super(JiraThread, self).__init__()
        self.task_queue = task_queue

    def run(self):
        """
        Check for task in Queue and make request if there is a task
        :return:
        """
        while True:
            next_task = self.task_queue.get()
            if next_task == "END":
                self.task_queue.task_done()
                break
            args = next_task
            self.book_hour(*args)
            self.task_queue.task_done()
        return

    def book_hour(self, jira_instance, issue, time_started, time_spent, work_log):
        """
        :param jira_instance: JIRA instance
        :param issue: JIRA ISSUE
        :param time_started: date
        :param time_spent: logged hour
        :param work_log: work log instance if editing existing hour booking
        :return:
        """
        if work_log:
            work_log.update(timeSpent=time_spent)
        else:
            time_spent = f"{time_spent}h"
            jira_instance.add_worklog(issue, timeSpent=time_spent,
                                      started=time_started)
