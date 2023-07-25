import sys
import os
import json
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, \
                            QHeaderView, QAbstractItemView, QComboBox, \
                            QColorDialog, QToolTip, QTableWidget, QRadioButton, \
                            QLabel, QPushButton, QMessageBox, QStyledItemDelegate, \
                            QLineEdit, QMessageBox, QCompleter
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal

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
        # self.tableWidget.setSelectionMode(QAbstractItemView.NoSelection)

         # テーブルのセルを選択したときに編集可能にする
        # self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.itemSelectionChanged.connect(self.on_selection_changed)
        # cellDoubleClickedシグナルにスロットを接続
        self.tableWidget.cellDoubleClicked.connect(self.onCellDoubleClicked)
        # セルの値が変更された後に発生、
        # self.tableWidget.itemChanged.connect(self.on_cell_value_changed)
        # self.tableWidget.cellChanged.connect(self.on_cell_value_changed)


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

        for i, row_data in enumerate(data):
            self.tableWidget.insertRow(i)

            self.create_cell(row_data, i, columns)
            for j, key in enumerate(columns):
                value = row_data.get(key, "")

                if key == "status":
                    # cell_widget = QComboBox()
                    # cell_widget.addItems(["日勤","夜勤","休診日日勤"])
                    # # cell_widget.setCurrentText(value)
                    # cell_widget.setEditable(True)
                    # cell_widget.setLineEdit(cell_widget.lineEdit())
                    # self.tableWidget.setCellWidget(i, j, cell_widget)
                    # cell_widget.setToolTip(self.get_tooltip_text(key))
                    # cell_widget.currentIndexChanged.connect(lambda idx, r=i, c=j: self.on_cell_value_changed(r,c))
                    # cell_widget.setCurrentText(value)
                    self.create_status_cell(value, i, j)
                elif key == "target":
                    # cell_widget = QComboBox()
                    # cell_widget.addItems(["True","False"])
                    # # cell_widget.setCurrentText(str(value))
                    # self.tableWidget.setCellWidget(i, j, cell_widget)
                    # cell_widget.setToolTip(self.get_tooltip_text(key))
                    # cell_widget.currentIndexChanged.connect(lambda idx, r=i, c=j: self.on_cell_value_changed(r,c))
                    # cell_widget.setCurrentText(str(value))
                    self.create_target_cell(value, i, j)
                elif key == "color":
                    item = QTableWidgetItem(",".join(str(x) for x in value))
                    self.tableWidget.setItem(i,j,item)
                    self.tableWidget.item(i, j).setBackground(QColor(*value))
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

    def create_cell(self, row_data, row, columns):
        for j, key in enumerate(columns):
            value = row_data.get(key, "")
            cell = self.tableWidget
            if key == "status":
                    # cell_widget = QComboBox()
                    # cell_widget.addItems(["日勤","夜勤","休診日日勤"])
                    # cell_widget.setEditable(True)
                    # cell_widget.setLineEdit(cell_widget.lineEdit())
                    # cell.setCellWidget(row, j, cell_widget)
                    # cell_widget.setToolTip(self.get_tooltip_text(key))
                    # cell_widget.currentIndexChanged.connect(lambda idx, r=row, c=j: self.on_cell_value_changed(r,c))
                    # cell_widget.setCurrentText(value)
                    self.create_status_cell(value, row, j)
            elif key == "target":
                    cell_widget = QComboBox()
                    cell_widget.addItems(["True","False"])
                    cell.setCellWidget(row, j, cell_widget)
                    cell_widget.setToolTip(self.get_tooltip_text(key))
                    cell_widget.currentIndexChanged.connect(lambda idx, r=row, c=j: self.on_cell_value_changed(r,c))
                    cell_widget.setCurrentText(str(value))
            elif key == "color":
                    item = QTableWidgetItem(",".join(str(x) for x in value))
                    cell.setItem(row,j,item)
                    cell.item(row, j).setBackground(QColor(*value))
                    cell.item(row, j).setToolTip(self.get_tooltip_text(key))
            elif key == "searchStr":
                    item = QTableWidgetItem(",".join(str(x) for x in value))
                    cell.setItem(row, j, item)
                    cell.item(row, j).setToolTip(self.get_tooltip_text(key))
            else:
                    item = QTableWidgetItem(str(value))
                    cell.setItem(row, j, item)
                    cell.item(row, j).setToolTip(self.get_tooltip_text(key))        

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
            self.currentData = self.modalities

        elif self.radio_button2.isChecked():
            self.currentData = self.shifts

        elif self.radio_button3.isChecked():
            self.currentData = self.workCountHeaders

        elif self.radio_button4.isChecked():
            self.currentData = self.modalityConfigHeaders

        elif self.radio_button5.isChecked():
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


    # def lock_cells(self):
    #     for row in range(self.tableWidget.rowCount()):
    #         for col in range(self.tableWidget.columnCount()):
    #             cell = self.tableWidget.item(row, col)
    #             cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                # if cell == self.editCell:
                #     cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                # else:
                #     cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

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

        # self.currentData.append(new_row)
        self.tableWidget.setCurrentCell(ro, 0)
        self.editCell = self.tableWidget.item(ro, 0)
        # self.lock_cells()
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
        
        if self.radio_button1.isChecked():
            self.modalities = self.currentData 

        elif self.radio_button2.isChecked():
            self.shifts = self.currentData

        elif self.radio_button3.isChecked():
            self.workCountHeaders = self.currentData

        elif self.radio_button4.isChecked():
            self.modalityConfigHeaders = self.currentData

        elif self.radio_button5.isChecked():
            self.skills = self.currentData 

        self.save_changes_to_json_file()


    # def set_object_data(self):
    #     row_count = self.tableWidget.rowCount()
    #     col_count = self.tableWidget.columnCount()
    #     for row in range(row_count):
    #         new_row = {}
    #         for col in range(col_count):
    #             column_name = self.tableWidget.horizontalHeaderItem(col).text()
    #             cell = self.tableWidget.item(row, col)
    #             if column_name == "color":
    #                 color_str = cell.text()
    #                 color_arr = [int(c) for c in re.findall(r'\d+', color_str)]
    #                 cell.setBackground(QColor(*color_arr))
    #                 new_row[column_name] = color_arr
    #             elif column_name == "searchStr":
    #                 search_str = cell.text()
    #                 new_row[column_name] = search_str.split(',')
    #             elif column_name == "target":
    #                 value = cell.text().lower() == "true"
    #                 new_row[column_name] = value
    #             else:
    #                 new_row[column_name] = cell.text()

    #         self.currentData[row] = new_row

    # def validate_string(self, cell):
    #     target_str = cell.text()
    #     column_name = self.tableWidget.horizontalHeaderItem(cell.column()).text()
    #     target_row = cell.row()

    #     for i in range(self.tableWidget.rowCount()):
    #         if target_str == self.tableWidget.item(i, cell.column()).text():
    #             if i != target_row:
    #                 self.show_tooltip_at_cell_center(cell, "無効な値です")
    #                 cell.setText(self.currentData[target_row][column_name])
    #                 return

    #     self.currentData[target_row][column_name] = target_str

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
