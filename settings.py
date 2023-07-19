import sys
import os
import json
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView, QAbstractItemView, \
    QComboBox, QColorDialog, QToolTip, QTableWidget, QRadioButton, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


class CalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.DEFAULTNAME = "name"
        self.DEFAULTACRONYM = "acronym"
        self.DEFAULTDATABASENAME = "db"
        self.DEFAULTCOLOR = [255, 255, 255]
        self.DEFAULTSEARCHSTR = ["search", "str"]
        self.DEFAULTSTATUS = "日勤"

        self.data = {}
        self.modalities = []
        self.shifts = []
        self.skills = []
        self.modalityConfigHeaders = []
        self.workCountHeaders = []
        self.currentData = []

        self.editCell = None
        self.disableCellValueChangedEvent = True

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Setting Form")
        self.setGeometry(100, 100, 800, 600)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(20, 60, 760, 440)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.tableWidget.setSelectionMode(QAbstractItemView.NoSelection)

         # テーブルのセルを選択したときに編集可能にする
        self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.itemSelectionChanged.connect(self.on_selection_changed)
        # cellDoubleClickedシグナルにスロットを接続
        self.tableWidget.cellDoubleClicked.connect(self.onCellDoubleClicked)

        self.radio_button1 = QRadioButton("Modalities", self)
        self.radio_button1.setGeometry(20, 20, 100, 20)
        self.radio_button1.setChecked(True)
        self.radio_button1.clicked.connect(self.on_radio_button_clicked)

        self.radio_button2 = QRadioButton("Shifts", self)
        self.radio_button2.setGeometry(120, 20, 100, 20)
        self.radio_button2.clicked.connect(self.on_radio_button_clicked)

        self.radio_button3 = QRadioButton("Work Count Header", self)
        self.radio_button3.setGeometry(220, 20, 150, 20)
        self.radio_button3.clicked.connect(self.on_radio_button_clicked)

        self.radio_button4 = QRadioButton("Modality Config Header", self)
        self.radio_button4.setGeometry(370, 20, 180, 20)
        self.radio_button4.clicked.connect(self.on_radio_button_clicked)

        self.radio_button5 = QRadioButton("Skills", self)
        self.radio_button5.setGeometry(550, 20, 100, 20)
        self.radio_button5.clicked.connect(self.on_radio_button_clicked)

        self.label = QLabel(self)
        self.label.setGeometry(20, 520, 760, 20)
        self.label.setAlignment(Qt.AlignCenter)

        self.button1 = QPushButton("Move Up", self)
        self.button1.setGeometry(20, 560, 100, 30)
        self.button1.clicked.connect(self.on_move_up_clicked)

        self.button2 = QPushButton("Move Down", self)
        self.button2.setGeometry(130, 560, 100, 30)
        self.button2.clicked.connect(self.on_move_down_clicked)

        self.button3 = QPushButton("Add Item", self)
        self.button3.setGeometry(240, 560, 100, 30)
        self.button3.clicked.connect(self.on_add_item_clicked)

        self.button4 = QPushButton("Remove Item", self)
        self.button4.setGeometry(350, 560, 100, 30)
        self.button4.clicked.connect(self.on_remove_item_clicked)

        self.load_data_from_json()
        self.set_table_view(self.modalities)

    def load_data_from_json(self):

        root_dir = os.getcwd()

        path = os.path.join(root_dir, 'settings.json')
        print(path)
        if os.path.isfile(path):

            json_open = open(path, 'r', encoding='utf-8')
            self.data = json.load(json_open)

        self.modalities = self.data.get("Modalities", [])
        self.shifts = self.data.get("Shifts", [])
        self.skills = self.data.get("Skills", [])
        self.modalityConfigHeaders = self.data.get("ModalityConfigHeader", [])
        self.workCountHeaders = self.data.get("WorkCountHeader", [])      

    def set_table_view(self, data):
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)

        if not data:
            return

        columns = list(data[0].keys())

        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)

        for i, row_data in enumerate(data):
            self.tableWidget.insertRow(i)

            for j, key in enumerate(columns):
                value = row_data.get(key, "")

                if key == "status":
                    cell_widget = QComboBox()
                    cell_widget.addItem("日勤")
                    cell_widget.addItem("夜勤")
                    cell_widget.addItem("休診日日勤")
                    cell_widget.setCurrentText(value)
                    cell_widget.setEditable(True)
                    cell_widget.setLineEdit(cell_widget.lineEdit())
                    self.tableWidget.setCellWidget(i, j, cell_widget)
                    cell_widget.setToolTip(self.get_tooltip_text(key))
                elif key == "target":
                    cell_widget = QComboBox()
                    cell_widget.addItem("True")
                    cell_widget.addItem("False")
                    cell_widget.setCurrentText(str(value))
                    self.tableWidget.setCellWidget(i, j, cell_widget)
                    cell_widget.setToolTip(self.get_tooltip_text(key))
                elif key == "color":
                    item = QTableWidgetItem(",".join(str(x) for x in value))
                    self.tableWidget.setItem(i,j,item)
                    color = QColor(value[0], value[1], value[2])
                    self.tableWidget.item(i, j).setBackground(color)
                    self.tableWidget.item(i, j).setToolTip(self.get_tooltip_text(key))
                elif key == "searchStr":
                    item = QTableWidgetItem(",".join(str(x) for x in value))
                    self.tableWidget.setItem(i, j, item)
                    self.tableWidget.item(i, j).setToolTip(self.get_tooltip_text(key))
                else:
                    item = QTableWidgetItem(str(value))
                    self.tableWidget.setItem(i, j, item)
                    self.tableWidget.item(i, j).setToolTip(self.get_tooltip_text(key))
                

        self.tableWidget.setCurrentCell(-1, -1)
        self.disableCellValueChangedEvent = False

    def get_tooltip_text(self, column_name):
        tooltip_text = ""
        if column_name == "name":
            tooltip_text = "同じ名前は使用できません。"
        elif column_name == "acronym":
            tooltip_text = "略語を設定します。\n勤務表の所属モダリティや勤務シフトのボタン名など"
        elif column_name == "databasename":
            tooltip_text = "アクセスデータベースを検索する文字列を記載してください。\n間違うとプログラムがうまく起動できないので正確に入力してください。"
        elif column_name == "order":
            tooltip_text = "表示順を設定します。\n上下ボタンで設定します。"
        elif column_name == "target":
            tooltip_text = "勤務の対象とするか判別する設定です。\nTrueにするとモダリティ設定に反映される勤務となります。"
        elif column_name == "color":
            tooltip_text = "セルやボタンの色を設定します\nダブルクリックでフォームから設定します"
        elif column_name == "searchStr":
            tooltip_text = "セルの値をカウントするための文字列を設定します\n検索する文字列をカンマ区切りで設定します"
        elif column_name == "status":
            tooltip_text = "通常は日勤・夜勤・休診日日勤です。\n追加があれば、直接編集してください。"
        return tooltip_text

    def on_radio_button_clicked(self):
        if self.radio_button1.isChecked():
            self.set_table_view(self.modalities)
        elif self.radio_button2.isChecked():
            self.set_table_view(self.shifts)
        elif self.radio_button3.isChecked():
            self.set_table_view(self.workCountHeaders)
        elif self.radio_button4.isChecked():
            self.set_table_view(self.modalityConfigHeaders)
        elif self.radio_button5.isChecked():
            self.set_table_view(self.skills)

    def on_selection_changed(self):
        selected_indexes = self.tableWidget.selectedIndexes()

        if selected_indexes:
            selected_row = selected_indexes[0].row()
            selected_column = selected_indexes[0].column()
            column_name = self.tableWidget.horizontalHeaderItem(selected_column).text()

            if column_name in ["color", "order"]:
                self.tableWidget.clearSelection()
            else:
                item = self.tableWidget.item(selected_row, selected_column)
                if item is not None:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

    def onCellDoubleClicked(self, row, col): 

        column_name = self.tableWidget.horizontalHeaderItem(col).text()
        cell = self.tableWidget.item(row, col)

        if column_name == "color":

            self.on_color_change(cell)

        # if not column_name in ["order"]:
        #     editcell = self.tableWidget.item(row, col)
        #     # self.tableWidget.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        #     self.lock_cells()

    def lock_cells(self):
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                cell = self.tableWidget.item(row, col)
                if cell == self.editCell:
                    cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                else:
                    cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def save_changes_to_json_file(self):
        json_file_path = "settings.json"

        updated_data = {
            "Modalities": self.modalities,
            "Shifts": self.shifts,
            "ModalityConfigHeader": self.modalityConfigHeaders,
            "WorkCountHeader": self.workCountHeaders,
            "Skills": self.skills,
        }

        with open(json_file_path, "w") as f:
            json.dump(updated_data, f, indent=4)

    def move_row(self, shift_index):
        selected_row = self.tableWidget.currentRow()

        if selected_row < 0:
            return

        arr_to_move = self.currentData[selected_row]
        self.currentData.pop(selected_row)

        target_index = selected_row + shift_index
        self.currentData.insert(target_index, arr_to_move)
        self.currentData[target_index]["order"] = target_index + 1
        self.currentData[selected_row]["order"] = selected_row + 1

        self.set_table_view(self.currentData)

        self.tableWidget.setCurrentCell(target_index, 0)

    def on_move_up_clicked(self):
        self.move_row(-1)

    def on_move_down_clicked(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row < self.tableWidget.rowCount() - 1:
            self.move_row(1)

    def on_remove_item_clicked(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row >= 0:
            message = f"{selected_row + 1}行目のデータを削除しますか？"
            result = QMessageBox.question(self, "確認", message, QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                self.tableWidget.removeRow(selected_row)
                self.currentData.pop(selected_row)
                self.set_object_data()

    def on_add_item_clicked(self):
        self.disableCellValueChangedEvent = True
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        ro = len(self.currentData)
        co = len(self.currentData[0])
        new_row = {}

        for j in range(co):
            column_name = self.tableWidget.horizontalHeaderItem(j).text()

            if column_name == "name":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(self.DEFAULTNAME))
                new_row[column_name] = self.DEFAULTNAME
            elif column_name == "acronym":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(self.DEFAULTACRONYM))
                new_row[column_name] = self.DEFAULTACRONYM
            elif column_name == "databasename":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(self.DEFAULTDATABASENAME))
                new_row[column_name] = self.DEFAULTDATABASENAME
            elif column_name == "order":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(str(ro + 1)))
                new_row[column_name] = ro + 1
            elif column_name == "target":
                self.tableWidget.setItem(ro, j, QTableWidgetItem("False"))
                new_row[column_name] = False
            elif column_name == "color":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(",".join(map(str, self.DEFAULTCOLOR))))
                color_arr = self.DEFAULTCOLOR.copy()
                new_row[column_name] = color_arr
                self.tableWidget.item(ro, j).setBackground(QColor(*color_arr))
            elif column_name == "searchStr":
                self.tableWidget.setItem(ro, j, QTableWidgetItem(",".join(self.DEFAULTSEARCHSTR)))
                str_arr = self.DEFAULTSEARCHSTR.copy()
                new_row[column_name] = str_arr
            elif column_name == "status":
                self.tableWidget.setCellWidget(ro, j, QComboBox())
                self.tableWidget.cellWidget(ro, j).addItems(["日勤", "夜勤", "休診日日勤"])
                new_row[column_name] = "日勤"

        self.currentData.append(new_row)
        self.tableWidget.setCurrentCell(ro, 0)
        self.editCell = self.tableWidget.item(ro, 0)
        self.lock_cells()
        self.tableWidget.editItem(self.editCell)

        self.disableCellValueChangedEvent = False

    def on_color_change(self, cell):
        color = QColorDialog.getColor()
        if color.isValid():
            color_arr = [color.red(), color.green(), color.blue()]
            cell.setText(",".join(map(str, color_arr)))
            cell.setBackground(color)

    def on_cell_value_changed(self, row, column):
        if not self.disableCellValueChangedEvent:
            column_name = self.tableWidget.horizontalHeaderItem(column).text()
            cell = self.tableWidget.item(row, column)

            if column_name == "order":
                self.set_object_data()

            elif column_name == "name":
                self.validate_string(cell)

            elif column_name == "databasename":
                self.validate_database_name(cell)

            elif column_name == "color":
                self.validate_color(cell)

            elif column_name == "searchStr":
                self.validate_search_str(cell)

            elif column_name == "target":
                value = cell.text()
                if value.lower() in ["true", "false"]:
                    self.set_object_data()

            elif column_name == "status":
                cell_widget = self.tableWidget.cellWidget(row, column)
                value = cell_widget.currentText()
                if value in ["日勤", "夜勤", "休診日日勤"]:
                    self.set_object_data()

    def set_object_data(self):
        row_count = self.tableWidget.rowCount()
        col_count = self.tableWidget.columnCount()
        for row in range(row_count):
            new_row = {}
            for col in range(col_count):
                column_name = self.tableWidget.horizontalHeaderItem(col).text()
                cell = self.tableWidget.item(row, col)
                if column_name == "color":
                    color_str = cell.text()
                    color_arr = [int(c) for c in re.findall(r'\d+', color_str)]
                    cell.setBackground(QColor(*color_arr))
                    new_row[column_name] = color_arr
                elif column_name == "searchStr":
                    search_str = cell.text()
                    new_row[column_name] = search_str.split(',')
                elif column_name == "target":
                    value = cell.text().lower() == "true"
                    new_row[column_name] = value
                else:
                    new_row[column_name] = cell.text()

            self.currentData[row] = new_row

    def validate_string(self, cell):
        target_str = cell.text()
        column_name = self.tableWidget.horizontalHeaderItem(cell.column()).text()
        target_row = cell.row()

        for i in range(self.tableWidget.rowCount()):
            if target_str == self.tableWidget.item(i, cell.column()).text():
                if i != target_row:
                    QToolTip.showText(cell.rect().center(), "無効な値です")
                    cell.setText(self.currentData[target_row][column_name])
                    return

        self.currentData[target_row][column_name] = target_str

    def validate_database_name(self, cell):
        str_value = cell.text()
        valid = re.match(r'^(?![0-9])[a-zA-Z0-9]+$', str_value)
        if not valid:
            QToolTip.showText(cell.rect().center(), "無効な値です")
            cell.setText(self.currentData[cell.row()]["databasename"])

    def validate_color(self, cell):
        color_str = cell.text()
        parts = color_str.split(',')
        if len(parts) != 3 or not all(part.isdigit() and 0 <= int(part) < 256 for part in parts):
            QToolTip.showText(cell.rect().center(), "無効な値です")
            cell.setText(",".join(map(str, self.currentData[cell.row()]["color"])))

    def validate_search_str(self, cell):
        search_str = cell.text()
        parts = search_str.split(',')
        if not parts:
            QToolTip.showText(cell.rect().center(), "無効な値です")
            cell.setText(",".join(self.currentData[cell.row()]["searchStr"]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec_())
