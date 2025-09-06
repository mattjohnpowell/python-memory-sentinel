import json
import time
import psutil
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

# Define the absolute path to the rules.json file
RULES_FILE_PATH = Path(__file__).parent / "rules.json"

class SentinelWorker(QObject):
    """
    A worker that runs in the background to monitor processes based on rules.
    """
    notification_signal = pyqtSignal(str, str) # title, message
    terminate_signal = pyqtSignal(int) # pid

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.rules = []
        self.breaches = {} # {pid: {rule_name: start_time}}

    def run(self):
        """
        The main loop of the worker.
        """
        self.running = True
        while self.running:
            self.load_rules()
            self.check_processes()
            time.sleep(15) # Check every 15 seconds

    def stop(self):
        self.running = False

    def load_rules(self):
        try:
            if not RULES_FILE_PATH.exists():
                self.rules = []
                return
            with open(RULES_FILE_PATH, "r") as f:
                self.rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            self.rules = []

    def check_processes(self):
        """
        Iterates through running monitored processes and checks them against the rules.
        """
        if not self.rules:
            return

        process_names = {'python.exe', 'pythonw.exe', 'python', 'python3', 'node.exe', 'node'}
        for process in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
            try:
                if process.info['name'].lower() not in process_names:
                    continue

                for rule in self.rules:
                    self.check_rule(process, rule)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def check_rule(self, process, rule):
        """
        Checks a single process against a single rule.
        """
        pid = process.info['pid']
        process_name_match = rule.get('process_name', '') in ' '.join(process.info['cmdline'])

        if not process_name_match:
            return

        memory_mb = process.memory_info().rss / (1024 * 1024)
        memory_threshold = rule.get('memory_threshold_mb', 0)

        if memory_mb > memory_threshold:
            # Memory breach detected
            breach_key = (pid, rule['name'])
            if breach_key not in self.breaches:
                self.breaches[breach_key] = time.time()

            breach_duration = time.time() - self.breaches[breach_key]
            rule_duration = rule.get('duration_seconds', 0)

            if breach_duration >= rule_duration:
                self.trigger_action(process, rule)
                # Reset breach after action
                del self.breaches[breach_key]

        else:
            # No breach, remove from tracking
            breach_key = (pid, rule['name'])
            if breach_key in self.breaches:
                del self.breaches[breach_key]

    def trigger_action(self, process, rule):
        """
        Triggers the action defined in the rule.
        """
        pid = process.info['pid']
        action = rule.get('action', 'notify')

        if action == 'terminate':
            self.terminate_signal.emit(pid)
        else: # notify
            title = f"Sentinel Alert: {rule['name']}"
            message = (f"Process {pid} ('{' '.join(process.info['cmdline'])}') "
                       f"has exceeded {rule['memory_threshold_mb']} MB for "
                       f"{rule['duration_seconds']} seconds.")
            self.notification_signal.emit(title, message)
