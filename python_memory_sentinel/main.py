import sys
import psutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHeaderView, QHBoxLayout, QMessageBox,
    QSplitter, QStyle
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, Qt, QThread
from pyqtgraph import PlotWidget, mkPen
from collections import deque
from settings import SettingsWindow
from core import get_python_processes
from worker import SentinelWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_worker_thread()
        self.setWindowTitle("Python Memory Sentinel")
        self.setGeometry(100, 100, 1000, 700)

        # Main layout and widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(splitter)

        # Top widget for the table
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        splitter.addWidget(top_widget)

        # Bottom widget for the graph
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        splitter.addWidget(bottom_widget)

        # Create table for processes
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Memory (MB)", "CPU (%)", "Command Line"])
        top_layout.addWidget(self.process_table)

        self.process_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.process_table.itemSelectionChanged.connect(self.on_process_selected)

        # Create a layout for the buttons
        button_layout = QHBoxLayout()
        top_layout.addLayout(button_layout)

        # Create buttons
        style = self.style()
        self.refresh_button = QPushButton(" Refresh")
        self.refresh_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.terminate_button = QPushButton(" Terminate")
        self.terminate_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.restart_button = QPushButton(" Restart")
        self.restart_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.settings_button = QPushButton(" Settings")
        self.settings_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.terminate_button)
        button_layout.addWidget(self.restart_button)
        button_layout.addStretch()
        button_layout.addWidget(self.settings_button)

        # Connect button signals
        self.refresh_button.clicked.connect(self.populate_process_list)
        self.terminate_button.clicked.connect(self.terminate_process)
        self.restart_button.clicked.connect(self.restart_process)
        self.settings_button.clicked.connect(self.open_settings)

        # Graph setup
        self.graph_widget = PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Memory Usage (MB)", color="k", size="12pt")
        self.graph_widget.setLabel('left', 'Memory (MB)', color='k')
        self.graph_widget.setLabel('bottom', 'Time (s)', color='k')
        self.graph_widget.showGrid(x=True, y=True)
        bottom_layout.addWidget(self.graph_widget)

        # Graphing data and timer
        self.selected_pid = None
        self.time_counter = 0
        self.memory_data = deque(maxlen=60) # Store last 60 points
        self.time_data = deque(maxlen=60)
        self.graph_timer = QTimer()
        self.graph_timer.setInterval(1000) # 1 second
        self.graph_timer.timeout.connect(self.update_graph)
        self.data_line = self.graph_widget.plot(self.time_data, self.memory_data, pen=mkPen(color=(255, 0, 0), width=2))

        # Populate the list on startup
        self.populate_process_list()

    def setup_worker_thread(self):
        self.worker_thread = QThread()
        self.worker = SentinelWorker()
        self.worker.moveToThread(self.worker_thread)

        self.worker.notification_signal.connect(self.show_notification)
        self.worker.terminate_signal.connect(self.force_terminate)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def show_notification(self, title, message):
        QMessageBox.information(self, title, message)

    def force_terminate(self, pid):
        try:
            process = psutil.Process(pid)
            process.kill()
            self.show_notification("Process Terminated by Sentinel", f"Process {pid} was automatically terminated.")
        except psutil.NoSuchProcess:
            pass # Process already gone
        except psutil.AccessDenied:
            self.show_notification("Sentinel Error", f"Could not terminate process {pid}: Access Denied.")
        finally:
            self.populate_process_list()

    def populate_process_list(self):
        """
        Fetches the list of Python processes and populates the table.
        """
        selected_pid_before_refresh = self.get_selected_pid()
        self.process_table.setRowCount(0)
        processes = list(get_python_processes())

        for row, process_data in enumerate(processes):
            self.process_table.insertRow(row)
            pid_item = QTableWidgetItem(str(process_data['pid']))
            self.process_table.setItem(row, 0, pid_item)
            self.process_table.setItem(row, 1, QTableWidgetItem(process_data['memory_mb']))
            self.process_table.setItem(row, 2, QTableWidgetItem(str(process_data['cpu_percent'])))
            self.process_table.setItem(row, 3, QTableWidgetItem(process_data['cmdline']))

            if process_data['pid'] == selected_pid_before_refresh:
                self.process_table.selectRow(row)

    def on_process_selected(self):
        """
        Handles the selection of a new process in the table.
        """
        pid = self.get_selected_pid()
        if pid is None:
            self.graph_timer.stop()
            self.selected_pid = None
            return

        if pid != self.selected_pid:
            self.selected_pid = pid
            self.graph_widget.setTitle(f"Memory Usage for PID: {pid}", color="k", size="12pt")
            # Reset graph data
            self.memory_data.clear()
            self.time_data.clear()
            self.time_counter = 0
            self.graph_timer.start()

    def update_graph(self):
        """
        Called by the QTimer to update the memory graph.
        """
        if self.selected_pid is None:
            return

        try:
            process = psutil.Process(self.selected_pid)
            memory_mb = process.memory_info().rss / (1024 * 1024)

            self.time_counter += 1
            self.time_data.append(self.time_counter)
            self.memory_data.append(memory_mb)

            self.data_line.setData(list(self.time_data), list(self.memory_data))

        except psutil.NoSuchProcess:
            self.graph_timer.stop()
            self.selected_pid = None
            QMessageBox.warning(self, "Process Ended", "The selected process has ended.")
            self.populate_process_list()

    def get_selected_pid(self):
        """Returns the PID of the selected process."""
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            return None
        return int(self.process_table.item(selected_items[0].row(), 0).text())

    def terminate_process(self):
        """Terminates the selected process."""
        pid = self.get_selected_pid()
        if pid is None:
            QMessageBox.warning(self, "No Process Selected", "Please select a process to terminate.")
            return

        reply = QMessageBox.question(self, "Confirm Termination",
                                     f"Are you sure you want to terminate process {pid}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                process = psutil.Process(pid)
                process.kill()
                QMessageBox.information(self, "Process Terminated", f"Process {pid} has been terminated.")
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "Error", f"Process {pid} no longer exists.")
            except psutil.AccessDenied:
                QMessageBox.critical(self, "Access Denied", f"Could not terminate process {pid}. Access denied.")
            finally:
                self.populate_process_list()

    def restart_process(self):
        """Restarts the selected process."""
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Process Selected", "Please select a process to restart.")
            return

        pid = int(selected_items[0].text())
        cmdline = self.process_table.item(selected_items[0].row(), 3).text()

        try:
            process = psutil.Process(pid)
            process.kill()
            subprocess.Popen(cmdline.split())
            QMessageBox.information(self, "Process Restarted", f"Process {pid} has been restarted.")
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "Error", f"Process {pid} no longer exists.")
        except psutil.AccessDenied:
            QMessageBox.critical(self, "Access Denied", f"Could not restart process {pid}. Access denied.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restart process: {e}")
        finally:
            self.populate_process_list()

    def open_settings(self):
        """Opens the settings dialog."""
        dialog = SettingsWindow(self)
        dialog.exec()
        self.worker.load_rules() # Reload rules after settings are changed

    def closeEvent(self, event):
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
