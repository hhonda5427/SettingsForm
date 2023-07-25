import sys
import os
import json
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, \
                            QHeaderView, QAbstractItemView, QComboBox, \
                            QColorDialog, QTableWidget, \
                            QLabel, QPushButton, QMessageBox, QStyledItemDelegate, \
                            QLineEdit, QMessageBox, QCompleter
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal

# ORDERWIDTH = 50
# NAMEWIDTH = 100
# ACRONYMWIDTH = 100
# TARGETWIDTH = 100
# STATUSWIDTH = 100
# DATABASEWIDTH = 100
# DEFAULTWIDTH = 100

# セルを選択した際に、編集した場合のみ信号を発火するためのクラス
class EditingFinishedDelegate(QStyledItemDelegate):
    editingFinished = pyqtSignal(int, int)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.editingFinished.connect(self.emitEditingFinished)  # QLineEditのeditingFinishedシグナルを接続
        return editor

    def emitEditingFinished(self):
        editor = self.sender()  # 送信元のエディタを取得
        if isinstance(editor, QLineEdit):
            index = self.parent().tableWidget.indexAt(editor.pos())  # エディタの位置からセルのインデックスを取得
            row, column = index.row(), index.column()
            self.editingFinished.emit(row, column)  # 行と列の情報を含むシグナルを発行

class SettingsFormApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.DEFAULTNAME = "name"
        self.DEFAULTACRONYM = "acronym"
        self.DEFAULTDATABASENAME = "db"
        self.DEFAULTCOLOR = [255, 255, 255]
        self.DEFAULTSEARCHSTR = ["search", "str"]
        self.DEFAULTSTATUS = "日勤"
        self.DEFAULTTARGET = False

        self.ORDERWIDTH = 50
        self.NAMEWIDTH = 100
        self.ACRONYMWIDTH = 100
        self.TARGETWIDTH = 100
        self.STATUSWIDTH = 100
        self.DATABASEWIDTH = 100
        self.DEFAULTWIDTH = 100
        self.data = {}
        self.modalities = []
        self.shifts = []
        self.skills = []
        self.modalityConfigHeaders = []
        self.workCountHeaders = []
        self.currentData = []

        self.disableCellValueChangedEvent = True

        self.init_ui()

        self.delegate = EditingFinishedDelegate(self)
        self.delegate.editingFinished.connect(self.on_cell_value_changed)
        self.tableWidget.setItemDelegate(self.delegate)

    def init_ui(self):
        self.setWindowTitle("Setting Form")
        self.setGeometry(100, 100, 800, 600)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(20, 60, 760, 440)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)

         # テーブルのセルを選択したときに編集可能にする
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.itemSelectionChanged.connect(self.on_selection_changed)
        # cellDoubleClickedシグナルにスロットを接続
        self.tableWidget.cellDoubleClicked.connect(self.onCellDoubleClicked)
        # セルの値が変更された後に発生、
        self.tableWidget.verticalHeader().setVisible(False)

        self.combo_box = QComboBox(self)
        self.combo_box.setGeometry(20, 20, 300, 30)
        self.combo_box.addItems(["Modalities", "Shifts", "Work Count Header", "Modality Config Header", "Skills"])
        self.combo_box.currentIndexChanged.connect(self.on_combo_box_index_changed)

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
        self.currentData = self.modalities
        self.set_table_view(self.currentData)

    def load_data_from_json(self):

        root_dir = os.getcwd()

        path = os.path.join(root_dir, 'settings.json')

        if os.path.isfile(path):

            json_open = open(path, 'r', encoding='utf-8')
            self.data = json.load(json_open)

        self.modalities = self.data.get("Modalities", [])
        self.shifts = self.data.get("Shifts", [])
        self.skills = self.data.get("Skills", [])
        self.modalityConfigHeaders = self.data.get("ModalityConfigHeader", [])
        self.workCountHeaders = self.data.get("WorkCountHeader", [])      

    def set_table_view(self, data):
        self.disableCellValueChangedEvent = True
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)

        if not data:
            return

        columns = list(data[0].keys())
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        self.set_column_width(columns)
        
        for i, row_data in enumerate(data):
            self.tableWidget.insertRow(i)
            self.create_cell(row_data, columns, i)

        self.tableWidget.setCurrentCell(-1, -1)

        self.disableCellValueChangedEvent = False

    def set_column_width(self, columns):
        header = self.tableWidget.horizontalHeader()
        for j, key in enumerate(columns):
            
            if key == "order":
                header.setSectionResizeMode(j, QHeaderView.ResizeToContents)
                self.tableWidget.horizontalHeaderItem(j).setTextAlignment(Qt.AlignCenter)
            elif key == "searchStr":
                header.setSectionResizeMode(j, QHeaderView.Stretch)
            elif key == "color":
                header.setSectionResizeMode(j, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(j, QHeaderView.Fixed)
                header.resizeSection(j, self.DEFAULTWIDTH)
                
    def create_cell(self, row_data, columns, row):
        for j, key in enumerate(columns):
            value = row_data.get(key, "")

            if key == "status":
                self.create_status_cell(value, row, j)
            elif key == "target":
                self.create_target_cell(value, row, j)
            elif key == "color":
                self.create_color_cell(value, row, j)
            elif key == "searchStr":
                self.create_searchStr_cell(value, row, j)
            else:
                self.create_default_cell(value, row, j, key)


    def create_status_cell(self, value, row, column):
        cell_widget = QComboBox()
        cell_widget.addItems(["日勤","夜勤","休診日日勤"])
        cell_widget.setEditable(True)
        completer = QCompleter(["日勤", "夜勤", "休診日日勤"])
        cell_widget.setCompleter(completer)
        line_edit = cell_widget.lineEdit()
        line_edit.setProperty("row", row)
        line_edit.setProperty("column", column)
        self.tableWidget.setCellWidget(row, column, cell_widget)
        cell_widget.setToolTip(self.get_tooltip_text("status"))
        cell_widget.currentIndexChanged.connect(lambda idx, r=row, c=column: self.on_cell_value_changed(r,c))
        cell_widget.setCurrentText(value)

    def create_target_cell(self, value, row, column):
        cell_widget = QComboBox()
        cell_widget.addItems(["True","False"])
        self.tableWidget.setCellWidget(row, column, cell_widget)
        cell_widget.setToolTip(self.get_tooltip_text("target"))
        cell_widget.currentIndexChanged.connect(lambda idx, r=row, c=column: self.on_cell_value_changed(r,c))
        cell_widget.setCurrentText(str(value)) 

    def create_color_cell(self, value, row, column):
        item = QTableWidgetItem(",".join(str(x) for x in value))
        self.tableWidget.setItem(row, column, item)
        self.tableWidget.item(row, column).setBackground(QColor(*value))
        self.tableWidget.item(row, column).setToolTip(self.get_tooltip_text("color"))

    def create_searchStr_cell(self, value, row, column):
        item = QTableWidgetItem(",".join(str(x) for x in value))
        self.tableWidget.setItem(row, column, item)
        self.tableWidget.item(row, column).setToolTip(self.get_tooltip_text("searchStr"))

    def create_default_cell(self, value, row, column, column_name):
        item = QTableWidgetItem(str(value))
        self.tableWidget.setItem(row, column, item)
        self.tableWidget.item(row, column).setToolTip(self.get_tooltip_text(column_name))

    def get_tooltip_text(self, column_name):
        tooltip_text = ""
        if column_name == "name":
            tooltip_text = "同じ名前は使用できません。"
        elif column_name == "acronym":
            tooltip_text = "略語を設定します。\n勤務表の所属モダリティや勤務シフトのボタン名など"
        elif column_name == "databasename":
            tooltip_text = "アクセスデータベースを検索する文字列を記載してください。\n間違うとプログラムがうまく起動できないので正確に入力してください。"
        elif column_name == "order":
            tooltip_text = "表示順を設定します。\n直接編集はできません。\n上下ボタンで設定します。"
        elif column_name == "target":
            tooltip_text = "モダリティ設定人数計算の対象とするか判別する設定です。\nTrueにするとモダリティ設定に反映される勤務となります。"
        elif column_name == "color":
            tooltip_text = "セルやボタンの色を設定します\nダブルクリックでフォームから設定します"
        elif column_name == "searchStr":
            tooltip_text = "セルの値をカウントするための文字列を設定します\n検索する文字列をカンマ区切りで設定します"
        elif column_name == "status":
            tooltip_text = "通常は日勤・夜勤・休診日日勤です。\n追加があれば、直接編集してください。"
        return tooltip_text

    def on_combo_box_index_changed(self):
        selected_index = self.combo_box.currentIndex()
        if selected_index == 0:
            self.currentData = self.modalities
        elif selected_index == 1:
            self.currentData = self.shifts
        elif selected_index == 2:
            self.currentData = self.workCountHeaders
        elif selected_index == 3:
            self.currentData = self.modalityConfigHeaders
        elif selected_index == 4:
            self.currentData = self.skills

        self.set_table_view(self.currentData)

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

        elif column_name != "order":
            self.tableWidget.editItem(cell)

    def save_changes_to_json_file(self):
        json_file_path = "settings.json"
  
        updated_data = {
            "Modalities": self.modalities,
            "Shifts": self.shifts,
            "ModalityConfigHeader": self.modalityConfigHeaders,
            "WorkCountHeader": self.workCountHeaders,
            "Skills": self.skills,
        }

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=4, ensure_ascii=False)

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

        self.convet_currentData_to_origin()


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
                self.reset_order()
                self.convet_currentData_to_origin()

    def reset_order(self):
        data = self.currentData
        columns = list(data[0].keys())
        for i, row_data in enumerate(data):
            for j, key in enumerate(columns):
                value = row_data.get(key, "")
                if key == "order":
                    row_data[key] = i + 1
                    item = QTableWidgetItem(str(i + 1))
                    self.tableWidget.setItem(i, j, item)
        
    def on_add_item_clicked(self):

        self.disableCellValueChangedEvent = True
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        ro = len(self.currentData)

        columns = list(self.currentData[0].keys())
        new_row = {}

        for j, key in enumerate(columns):
            if key == "status":
                new_row[key] = self.DEFAULTSTATUS
            elif key == "target":
                new_row[key] = self.DEFAULTTARGET
            elif key == "color":
                new_row[key] = self.DEFAULTCOLOR
            elif key == "searchStr":
                new_row[key] = self.DEFAULTSEARCHSTR
            elif key == "order":
                new_row[key] = ro + 1
            else:
                new_row[key] = key
            
        self.currentData.append(new_row)

        self.create_cell(new_row, columns, ro)

        self.tableWidget.setCurrentCell(ro, 0)

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
            flg = False

            if column_name == "order":
                if cell.text().isdigit():
                    flg = (int(cell.text()) == row + 1)

            elif column_name == "databasename":
                flg = self.validate_database_name(cell)

            elif column_name == "color":
                flg = self.validate_color(cell)

            elif column_name == "searchStr":
                flg = self.validate_search_str(cell)
                
            elif column_name == "target":
                cell_widget = self.tableWidget.cellWidget(row,column)
                flg = self.validate_target(cell_widget, row, column)

            elif column_name == "status":
                cell_widget = self.tableWidget.cellWidget(row, column)
                flg = self.validate_status(cell_widget, row, column)

            else:
                flg = self.validate_strip(cell) 

            if flg:
                self.set_currentData(row)

    # 値を変えた行はすべてデータを書き換える
    def set_currentData(self, row):
        col_count = self.tableWidget.columnCount()

        for col in range(col_count):
            column_name = self.tableWidget.horizontalHeaderItem(col).text()
            if column_name == "order":
                self.currentData[row][column_name] = int(self.tableWidget.item(row, col).text())
            elif column_name == "color":
                color_str = self.tableWidget.item(row,col).text()
                color = [int(c) for c in color_str.split(',')]
                self.currentData[row][column_name] = color
            elif column_name == "searchStr":
                self.currentData[row][column_name] = self.tableWidget.item(row,col).text().split(',')
            elif column_name == "target":
                value = self.tableWidget.cellWidget(row, col).currentText()
                self.currentData[row][column_name] = value.lower() == "true"
            elif column_name == "status":
                print(f"pre:{self.tableWidget.cellWidget(row, col).currentText()}")
                self.currentData[row][column_name] = self.tableWidget.cellWidget(row, col).currentText()
                print(f"post:{self.currentData[row][column_name]}")
            else:
                self.currentData[row][column_name] = self.tableWidget.item(row, col).text()

        self.convet_currentData_to_origin()


    def convet_currentData_to_origin(self):
        
        selected_index = self.combo_box.currentIndex()
        if selected_index == 0:
            self.modalities = self.currentData
        elif selected_index == 1:
            self.shifts = self.currentData
        elif selected_index == 2:
            self.workCountHeaders = self.currentData
        elif selected_index == 3:
            self.modalityConfigHeaders = self.currentData
        elif selected_index == 4:
            self.skills = self.currentData

        self.save_changes_to_json_file()

    def validate_strip(self, cell):
        str_value = cell.text()
        if not str_value.strip():
            column_name = self.tableWidget.horizontalHeaderItem(cell.column()).text()
            QMessageBox.warning(self,"エラー", "空白です")
            cell.setText(self.currentData[cell.row()][column_name])
            return False
        return True
    
    def validate_database_name(self, cell):
        str_value = cell.text()
   
        valid = re.match(r'^(?![0-9])[a-zA-Z0-9]+$', str_value)
        if not valid:
            QMessageBox.warning(self, "エラー", "無効な値です")
            cell.setText(self.currentData[cell.row()]["databasename"])
            return False
    
        return True
    
    def validate_color(self, cell):
        color_str = cell.text()
        parts = color_str.split(',')
        if len(parts) != 3 or not all(part.isdigit() and 0 <= int(part) < 256 for part in parts):
            QMessageBox.warning(self, "エラー", "無効な値です")
            cell.setText(",".join(map(str, self.currentData[cell.row()]["color"])))
            return False
    
        return True


    def validate_search_str(self, cell):
        search_str = cell.text()
        parts = search_str.split(',')
        if not parts:
            QMessageBox.warning(self, "エラー", "無効な値です")
            cell.setText(",".join(self.currentData[cell.row()]["searchStr"]))

    def validate_status(self, cell_widget, row, column):
        status = cell_widget.currentText()
        
        if not status.strip():
            QMessageBox.warning(self, "空白です。文字を入力してください")
            return False
        elif not status in ["日勤", "夜勤", "休診日日勤"]:
            # メッセージボックスを作成
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("確認")
            msg_box.setText("日勤・夜勤・休診日日勤以外の文字列が選択されています。\nこのままでよろしいですか?")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            # メッセージボックスを表示し、ユーザーの選択結果を取得
            result = msg_box.exec_()
            # ユーザーがNoを選んだ場合
            if result == QMessageBox.No:
                cell_widget.setCurrentText(str(self.currentData[row]["status"]))
                return False
        return True
            
    def validate_target(self, cell_widget, row, column):
        target = cell_widget.currentText()
        if not target.lower() in ["true", "false"]:
            cell_widget.setCurrentText(str(self.currentData[row]["target"]))
            return False
        return True
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsFormApp()
    window.show()
    sys.exit(app.exec_())
