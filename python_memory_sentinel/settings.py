import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QFormLayout, QLabel, QSpinBox
)

class RuleDialog(QDialog):
    """
    A dialog for adding or editing a rule.
    """
    def __init__(self, rule=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Rule")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(rule.get('name', '') if rule else '')
        self.process_name_input = QLineEdit(rule.get('process_name', '') if rule else '')
        self.memory_threshold_input = QSpinBox()
        self.memory_threshold_input.setRange(1, 100000)
        self.memory_threshold_input.setValue(rule.get('memory_threshold_mb', 1024) if rule else 1024)
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 3600)
        self.duration_input.setValue(rule.get('duration_seconds', 60) if rule else 60)
        self.action_input = QComboBox()
        self.action_input.addItems(['notify', 'terminate'])
        if rule:
            self.action_input.setCurrentText(rule.get('action', 'notify'))

        form_layout.addRow(QLabel("Rule Name:"), self.name_input)
        form_layout.addRow(QLabel("Process Name (contains):"), self.process_name_input)
        form_layout.addRow(QLabel("Memory Threshold (MB):"), self.memory_threshold_input)
        form_layout.addRow(QLabel("Duration (seconds):"), self.duration_input)
        form_layout.addRow(QLabel("Action:"), self.action_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def get_rule(self):
        return {
            "name": self.name_input.text(),
            "process_name": self.process_name_input.text(),
            "memory_threshold_mb": self.memory_threshold_input.value(),
            "duration_seconds": self.duration_input.value(),
            "action": self.action_input.currentText()
        }


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sentinel Rules")
        self.setGeometry(150, 150, 600, 400)

        self.layout = QVBoxLayout(self)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(5)
        self.rules_table.setHorizontalHeaderLabels(["Name", "Process", "Memory (MB)", "Duration (s)", "Action"])
        self.layout.addWidget(self.rules_table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Rule")
        self.edit_button = QPushButton("Edit Rule")
        self.delete_button = QPushButton("Delete Rule")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        self.layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.add_rule)
        self.edit_button.clicked.connect(self.edit_rule)
        self.delete_button.clicked.connect(self.delete_rule)

        self.load_rules()

    def load_rules(self):
        try:
            with open("python_memory_sentinel/rules.json", "r") as f:
                self.rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.rules = []

        self.rules_table.setRowCount(0)
        for row, rule in enumerate(self.rules):
            self.rules_table.insertRow(row)
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.get("name", "")))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.get("process_name", "")))
            self.rules_table.setItem(row, 2, QTableWidgetItem(str(rule.get("memory_threshold_mb", ""))))
            self.rules_table.setItem(row, 3, QTableWidgetItem(str(rule.get("duration_seconds", ""))))
            self.rules_table.setItem(row, 4, QTableWidgetItem(rule.get("action", "")))

    def save_rules(self):
        with open("python_memory_sentinel/rules.json", "w") as f:
            json.dump(self.rules, f, indent=4)
        self.load_rules()

    def add_rule(self):
        dialog = RuleDialog(parent=self)
        if dialog.exec():
            self.rules.append(dialog.get_rule())
            self.save_rules()

    def edit_rule(self):
        current_row = self.rules_table.currentRow()
        if current_row < 0:
            return

        rule = self.rules[current_row]
        dialog = RuleDialog(rule, self)
        if dialog.exec():
            self.rules[current_row] = dialog.get_rule()
            self.save_rules()

    def delete_rule(self):
        current_row = self.rules_table.currentRow()
        if current_row < 0:
            return

        del self.rules[current_row]
        self.save_rules()
