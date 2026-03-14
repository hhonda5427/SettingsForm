# -*- coding: utf-8 -*-
"""
設定エディタ - 設定JSONを編集するGUI

デフォルトでは settings.json を読み書き。コマンドライン引数やメニュー「開く」で
任意のファイルを指定可能。images フォルダのUIを参考に、カテゴリごとの説明表示に対応。
"""
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QColorDialog,
    QTableWidget,
    QLabel,
    QPushButton,
    QMessageBox,
    QStyledItemDelegate,
    QLineEdit,
    QCompleter,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QMenuBar,
    QMenu,
    QAction,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal


# -----------------------------------------------------------------------------
# デリゲート（セル編集完了時にのみ変更を反映するため）
# -----------------------------------------------------------------------------


class EditingFinishedDelegate(QStyledItemDelegate):
    """セル編集で Enter/フォーカス喪失時のみシグナルを発火するデリゲート。"""

    editingFinished = pyqtSignal(int, int)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.editingFinished.connect(self._on_editing_finished)
        return editor

    def _on_editing_finished(self):
        editor = self.sender()
        if isinstance(editor, QLineEdit):
            index = self.parent()._table.indexAt(editor.pos())
            self.editingFinished.emit(index.row(), index.column())


# -----------------------------------------------------------------------------
# 設定定数（変更しやすいよう一箇所に集約）
# -----------------------------------------------------------------------------


class AppConfig:
    """アプリ全体の設定。ファイル名・デフォルト値・列挙値などを定義。"""
    JSON_FILENAME = "settings.json"
    DEFAULT_COLUMN_WIDTH = 100
    DEFAULT_COLOR = [255, 255, 255]
    DEFAULT_SEARCH_STR = ["search", "str"]
    DEFAULT_STATUS = "日勤"
    DEFAULT_TARGET = False
    STATUS_CHOICES = ["日勤", "夜勤", "休日勤"]
    TARGET_CHOICES = ["True", "False"]
    IS_SUBSTITUTE_DAYOFF_CHOICES = ["required", "assigned", "holiday"]
    TYPE_CHOICES = ["float", "integer"]
    STRETCH_COLUMNS = ("searchStr", "remarks", "name", "color")
    NON_EDITABLE_SELECTION_COLUMNS = ("color", "order")
    WIDGET_COLUMNS = ("target", "status", "isSubstituteDayoff", "type")
    NUMERIC_DEFAULT_KEYS = (
        "regular", "core", "staffs", "inputItems",
        "value", "staffsOnOpen", "staffsOnClose",
    )
    # テーブル・ボタン・説明ブロック間の余白（ピクセル）
    SECTION_SPACING = 12
    # min_skill_count: 曜日順（日〜土）のカンマ区切り7要素
    MIN_SKILL_COUNT_DAY_LABELS = ("日", "月", "火", "水", "木", "金", "土")
    DEFAULT_MIN_SKILL_COUNT_PER_DAY = [3, 3, 3, 3, 3, 3, 3]


# -----------------------------------------------------------------------------
# メインウィンドウ
# -----------------------------------------------------------------------------


class SettingsEditorApp(QMainWindow):
    """
    settings_new.json を編集するメインウィンドウ。

    責務:
    - カテゴリ一覧の表示・切り替え
    - 現在カテゴリのテーブル表示・編集
    - 行の追加・削除・並び替え
    - 説明文の表示
    - JSON の読み込み・保存
    """

    def __init__(self, initial_json_path=None):
        super().__init__()
        self._data = {}
        self._dynamic_data = {}
        self._category_descriptions = {}
        self._current_data = []
        self._suppress_cell_change_event = True
        self._json_path = self._resolve_initial_path(initial_json_path)

        self._build_ui()
        self._setup_table_delegate()
        self._load_data()
        self._refresh_table_and_description()
        self._update_window_title()

    # -------------------------------------------------------------------------
    # UI 構築
    # -------------------------------------------------------------------------

    def _build_ui(self):
        """ウィンドウとコントロールを組み立てる。"""
        self.setWindowTitle("Setting Form")
        self.setGeometry(100, 100, 900, 700)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(AppConfig.SECTION_SPACING)

        self._build_menu_bar()
        layout.addWidget(self._build_category_combo())
        layout.addWidget(self._build_table())
        layout.addLayout(self._build_button_row())
        # 説明ブロックは残りスペースを占有（ストレッチ 1）
        layout.addWidget(self._build_description_block(), 1)

    def _build_menu_bar(self):
        """メニューバー（ファイル → 開く / 名前を付けて保存）を生成する。"""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル(&F)")
        open_act = QAction("開く(&O)...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._on_open_file)
        file_menu.addAction(open_act)
        save_as_act = QAction("名前を付けて保存(&A)...", self)
        save_as_act.setShortcut("Ctrl+Shift+S")
        save_as_act.triggered.connect(self._on_save_as_file)
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()
        quit_act = QAction("終了(&X)", self)
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

    def _on_open_file(self):
        """「開く」: ファイルダイアログで選択したJSONを読み込む。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "設定JSONを開く",
            os.path.dirname(self._json_path) if self._json_path else "",
            "JSONファイル (*.json);;すべてのファイル (*)",
        )
        if not path:
            return
        self._json_path = os.path.abspath(path)
        self._load_data()
        self._refresh_table_and_description()
        self._update_window_title()

    def _on_save_as_file(self):
        """「名前を付けて保存」: 別パスにJSONを保存する。"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "名前を付けて保存",
            os.path.dirname(self._json_path) if self._json_path else "",
            "JSONファイル (*.json);;すべてのファイル (*)",
        )
        if not path:
            return
        if not path.endswith(".json"):
            path = path + ".json"
        self._json_path = os.path.abspath(path)
        self._save_data()
        self._update_window_title()
        QMessageBox.information(self, "保存完了", f"保存しました:\n{self._json_path}")

    def _update_window_title(self):
        """ウィンドウタイトルとステータスバーに現在のファイルパスを表示する。"""
        if self._json_path:
            path_display = self._json_path
            title = os.path.basename(self._json_path)
        else:
            path_display = "(未保存)"
            title = "(未保存)"
        self.setWindowTitle(f"Setting Form - {title}")
        self.statusBar().showMessage(f"読み込み: {path_display}")

    def _build_category_combo(self):
        """カテゴリ選択用コンボボックスを生成する。"""
        combo = QComboBox(self)
        combo.setMinimumWidth(300)
        combo.setMinimumHeight(28)
        combo.currentIndexChanged.connect(self._on_category_changed)
        self._combo_category = combo
        return combo

    def _build_table(self):
        """メインテーブルを生成する。"""
        table = QTableWidget(self)
        table.setMinimumHeight(350)
        table.setSelectionBehavior(QAbstractItemView.SelectItems)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.itemSelectionChanged.connect(self._on_selection_changed)
        table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        table.verticalHeader().setVisible(False)
        self._table = table
        return table

    def _build_button_row(self):
        """Move Up / Down, Add / Remove のボタン行を生成する。"""
        layout = QHBoxLayout()
        for label, slot in [
            ("Move Up", self._on_move_up),
            ("Move Down", self._on_move_down),
            ("Add Item", self._on_add_item),
            ("Remove Item", self._on_remove_item),
        ]:
            btn = QPushButton(label, self)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
        return layout

    def _build_description_block(self):
        """説明ラベルと読み取り専用テキストを生成する。余白は SECTION_SPACING で統一し、テキストは残り高さを使用。"""
        self._lbl_description = QLabel("説明", self)
        desc = QTextEdit(self)
        desc.setReadOnly(True)
        desc.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #ccc; padding: 4px;"
        )
        self._text_description = desc
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppConfig.SECTION_SPACING)
        layout.addWidget(self._lbl_description)
        # テキストは説明ブロック内の残りスペースを占有（ストレッチ 1）
        layout.addWidget(desc, 1)
        return container

    def _setup_table_delegate(self):
        """テーブルにデリゲートを設定し、編集完了時にのみ変更を反映する。"""
        delegate = EditingFinishedDelegate(self)
        delegate.editingFinished.connect(self._on_cell_value_changed)
        self._table.setItemDelegate(delegate)

    # -------------------------------------------------------------------------
    # データの読み込み・保存
    # -------------------------------------------------------------------------

    def _resolve_initial_path(self, initial_json_path):
        """起動時のJSONパスを決定する。引数があればその絶対パス、なければデフォルト。"""
        if initial_json_path and initial_json_path.strip():
            return os.path.abspath(initial_json_path.strip())
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            AppConfig.JSON_FILENAME,
        )

    def _get_json_path(self):
        """現在の設定JSONの絶対パスを返す。"""
        return self._json_path

    def _load_data(self):
        """現在のJSONパスからデータを読み込み、カテゴリ一覧と説明を保持する。"""
        path = self._get_json_path()
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}

        self._dynamic_data = {}
        self._category_descriptions = {}
        for key, val in self._data.items():
            if isinstance(val, dict):
                self._dynamic_data[key] = list(val.get("data", []))
                self._category_descriptions[key] = val.get("description", "")
            elif isinstance(val, list):
                self._dynamic_data[key] = list(val)
                self._category_descriptions[key] = ""

        self._combo_category.clear()
        self._combo_category.addItems(list(self._dynamic_data.keys()))

    def _save_data(self):
        """現在の dynamic_data と説明を現在のJSONパスに書き出す。"""
        path = self._get_json_path()
        out = {}
        for key in self._dynamic_data:
            out[key] = {
                "description": self._category_descriptions.get(key, ""),
                "data": self._dynamic_data[key],
            }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=4, ensure_ascii=False)

    def _refresh_table_and_description(self):
        """現在カテゴリのテーブルと説明文を更新する。"""
        if not self._dynamic_data:
            return
        name = self._combo_category.currentText()
        self._current_data = self._dynamic_data[name]
        self._set_table_view(self._current_data)
        self._update_description_text()

    def _update_description_text(self):
        """説明エリアに現在カテゴリの説明を表示する。"""
        name = self._combo_category.currentText()
        self._text_description.setPlainText(
            self._category_descriptions.get(name, "")
        )

    # -------------------------------------------------------------------------
    # テーブル表示・セル生成
    # -------------------------------------------------------------------------

    def _set_table_view(self, data):
        """指定したデータでテーブルを再構築する。"""
        self._suppress_cell_change_event = True
        self._table.clear()
        self._table.setRowCount(0)
        self._table.setColumnCount(0)
        if not data:
            self._suppress_cell_change_event = False
            return

        columns = list(data[0].keys())
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(columns)
        self._apply_column_widths(columns)
        for i, row_data in enumerate(data):
            self._table.insertRow(i)
            self._fill_row_cells(row_data, columns, i)
        self._table.setCurrentCell(-1, -1)
        self._suppress_cell_change_event = False

    def _apply_column_widths(self, columns):
        """列ごとのリサイズモードと幅を設定する。"""
        header = self._table.horizontalHeader()
        for j, key in enumerate(columns):
            if key == "order":
                header.setSectionResizeMode(j, QHeaderView.ResizeToContents)
                self._table.horizontalHeaderItem(j).setTextAlignment(
                    Qt.AlignCenter
                )
            elif key in AppConfig.STRETCH_COLUMNS:
                header.setSectionResizeMode(j, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(j, QHeaderView.Fixed)
                header.resizeSection(j, AppConfig.DEFAULT_COLUMN_WIDTH)

    def _fill_row_cells(self, row_data, columns, row_index):
        """1行分のセルを列タイプに応じて作成する。"""
        cell_creators = {
            "status": self._cell_status,
            "target": self._cell_target,
            "color": self._cell_color,
            "searchStr": self._cell_search_str,
            "isSubstituteDayoff": self._cell_is_substitute_dayoff,
            "type": self._cell_type,
            "min_skill_count": self._cell_min_skill_count,
        }
        for col_index, key in enumerate(columns):
            value = row_data.get(key, "")
            creator = cell_creators.get(key, self._cell_default)
            creator(value, row_index, col_index, key)

    def _cell_status(self, value, row, col, _key):
        """status 列: 日勤/夜勤/休日勤のコンボ（編集可）。"""
        widget = QComboBox()
        widget.addItems(AppConfig.STATUS_CHOICES)
        widget.setEditable(True)
        widget.setCompleter(QCompleter(AppConfig.STATUS_CHOICES))
        widget.setCurrentText(str(value) if value else AppConfig.DEFAULT_STATUS)
        widget.currentIndexChanged.connect(
            lambda *_, r=row, c=col: self._on_cell_value_changed(r, c)
        )
        self._table.setCellWidget(row, col, widget)

    def _cell_target(self, value, row, col, _key):
        """target 列: True/False コンボ。"""
        widget = QComboBox()
        widget.addItems(AppConfig.TARGET_CHOICES)
        widget.setCurrentText(str(value))
        widget.currentIndexChanged.connect(
            lambda *_, r=row, c=col: self._on_cell_value_changed(r, c)
        )
        self._table.setCellWidget(row, col, widget)

    def _cell_color(self, value, row, col, _key):
        """color 列: RGB 表示＋背景色。ダブルクリックで色変更。"""
        if not isinstance(value, list) or len(value) != 3:
            value = AppConfig.DEFAULT_COLOR
        item = QTableWidgetItem(",".join(str(x) for x in value))
        self._table.setItem(row, col, item)
        self._table.item(row, col).setBackground(QColor(*value))

    def _cell_search_str(self, value, row, col, _key):
        """searchStr 列: カンマ区切り文字列。"""
        text = ",".join(str(x) for x in value) if isinstance(value, list) else str(value)
        self._table.setItem(row, col, QTableWidgetItem(text))

    def _cell_is_substitute_dayoff(self, value, row, col, _key):
        """isSubstituteDayoff 列: required / assigned / holiday。"""
        widget = QComboBox()
        widget.addItems(AppConfig.IS_SUBSTITUTE_DAYOFF_CHOICES)
        widget.setEditable(True)
        widget.setCurrentText(str(value) if value else "required")
        widget.currentIndexChanged.connect(
            lambda *_, r=row, c=col: self._on_cell_value_changed(r, c)
        )
        self._table.setCellWidget(row, col, widget)

    def _cell_type(self, value, row, col, _key):
        """type 列: float / integer。"""
        widget = QComboBox()
        widget.addItems(AppConfig.TYPE_CHOICES)
        widget.setEditable(True)
        widget.setCurrentText(str(value) if value else "float")
        widget.currentIndexChanged.connect(
            lambda *_, r=row, c=col: self._on_cell_value_changed(r, c)
        )
        self._table.setCellWidget(row, col, widget)

    def _cell_min_skill_count(self, value, row, col, _key):
        """min_skill_count 列: 曜日順（日,月,火,水,木,金,土）のカンマ区切り7整数。"""
        if isinstance(value, list) and len(value) == 7:
            text = ",".join(str(x) for x in value)
        elif isinstance(value, (int, float)):
            text = ",".join(str(int(value)) for _ in AppConfig.MIN_SKILL_COUNT_DAY_LABELS)
        else:
            text = str(value) if value else ",".join(str(x) for x in AppConfig.DEFAULT_MIN_SKILL_COUNT_PER_DAY)
        item = QTableWidgetItem(text)
        item.setToolTip("曜日順（日,月,火,水,木,金,土）でカンマ区切り。例: 3,3,3,3,3,3,3")
        self._table.setItem(row, col, item)

    def _cell_default(self, value, row, col, _key):
        """その他: 通常のテキストセル。"""
        if value is None:
            value = ""
        self._table.setItem(row, col, QTableWidgetItem(str(value)))

    # -------------------------------------------------------------------------
    # イベントハンドラ（UI）
    # -------------------------------------------------------------------------

    def _on_category_changed(self):
        """カテゴリ変更時: 表示データを切り替え、テーブルと説明を更新。"""
        name = self._combo_category.currentText()
        if name not in self._dynamic_data:
            return
        self._current_data = self._dynamic_data[name]
        self._set_table_view(self._current_data)
        self._update_description_text()

    def _on_selection_changed(self):
        """選択変更時: color/order は編集不可のまま、他は編集可能にする。"""
        selected = self._table.selectedIndexes()
        if not selected:
            return
        row, col = selected[0].row(), selected[0].column()
        column_name = self._table.horizontalHeaderItem(col).text()
        if column_name in AppConfig.NON_EDITABLE_SELECTION_COLUMNS:
            self._table.clearSelection()
            return
        item = self._table.item(row, col)
        if item is not None:
            item.setFlags(item.flags() | Qt.ItemIsEditable)

    def _on_cell_double_clicked(self, row, col):
        """セルダブルクリック: color なら色ダイアログ、それ以外は編集。"""
        column_name = self._table.horizontalHeaderItem(col).text()
        cell = self._table.item(row, col)
        if cell is None:
            return
        if column_name == "color":
            self._open_color_picker(cell)
        elif column_name != "order":
            self._table.editItem(cell)

    def _on_cell_value_changed(self, row, column):
        """セルまたはウィジェットの値変更時: 検証してからモデルに反映。"""
        if self._suppress_cell_change_event:
            return
        column_name = self._table.horizontalHeaderItem(column).text()
        cell = self._table.item(row, column)

        if column_name in AppConfig.WIDGET_COLUMNS:
            self._sync_row_to_model(row)
            return
        if column_name == "color":
            if cell and self._validate_color(cell):
                self._sync_row_to_model(row)
            return
        if column_name == "searchStr":
            if cell and self._validate_search_str(cell):
                self._sync_row_to_model(row)
            return
        if column_name == "order":
            if cell and cell.text().isdigit() and int(cell.text()) == row + 1:
                self._sync_row_to_model(row)
            return
        if column_name == "min_skill_score":
            if cell and self._validate_non_negative_int(cell, row, column_name):
                self._sync_row_to_model(row)
            return
        if column_name == "min_skill_count":
            if cell and self._validate_min_skill_count_list(cell, row):
                self._sync_row_to_model(row)
            return
        if cell and self._validate_non_empty(cell):
            self._sync_row_to_model(row)

    def _open_color_picker(self, cell):
        """カラーダイアログを開き、選択色をセルに反映する。"""
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        color_list = [color.red(), color.green(), color.blue()]
        cell.setText(",".join(map(str, color_list)))
        cell.setBackground(color)
        self._suppress_cell_change_event = False
        self._sync_row_to_model(cell.row())
        self._suppress_cell_change_event = True

    # -------------------------------------------------------------------------
    # 行操作
    # -------------------------------------------------------------------------

    def _on_move_up(self):
        self._move_row(-1)

    def _on_move_down(self):
        if self._table.currentRow() < self._table.rowCount() - 1:
            self._move_row(1)

    def _move_row(self, delta):
        """選択行を delta だけ上下に移動する。"""
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._current_data[row].copy()
        self._current_data.pop(row)
        new_index = row + delta
        self._current_data.insert(new_index, item)
        self._renumber_order()
        self._set_table_view(self._current_data)
        self._table.setCurrentCell(new_index, 0)
        self._persist_current_category()

    def _on_remove_item(self):
        """選択行を削除する。確認ダイアログあり。"""
        row = self._table.currentRow()
        if row < 0:
            return
        if QMessageBox.question(
            self,
            "確認",
            f"{row + 1}行目のデータを削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._table.removeRow(row)
        self._current_data.pop(row)
        self._renumber_order()
        self._persist_current_category()

    def _on_add_item(self):
        """現在カテゴリのスキーマに合わせて1行追加する。"""
        if not self._current_data:
            return
        self._suppress_cell_change_event = True
        columns = list(self._current_data[0].keys())
        new_row = {
            key: self._default_value_for_column(key)
            for key in columns
        }
        row_index = len(self._current_data)
        self._current_data.append(new_row)
        self._table.insertRow(row_index)
        self._fill_row_cells(new_row, columns, row_index)
        self._table.setCurrentCell(row_index, 0)
        self._suppress_cell_change_event = False
        self._persist_current_category()

    def _renumber_order(self):
        """current_data の order を 1 始まりで振り直す。"""
        if not self._current_data:
            return
        for i, row in enumerate(self._current_data):
            if "order" in row:
                row["order"] = i + 1

    def _default_value_for_column(self, key):
        """新規行の列 key のデフォルト値を返す。"""
        if key == "order":
            return len(self._current_data) + 1
        if key == "status":
            return AppConfig.DEFAULT_STATUS
        if key == "target":
            return AppConfig.DEFAULT_TARGET
        if key == "color":
            return list(AppConfig.DEFAULT_COLOR)
        if key == "searchStr":
            return list(AppConfig.DEFAULT_SEARCH_STR)
        if key == "isSubstituteDayoff":
            return "required"
        if key == "type":
            return "float"
        if key == "min_skill_score":
            return 40
        if key == "min_skill_count":
            return list(AppConfig.DEFAULT_MIN_SKILL_COUNT_PER_DAY)
        if key in AppConfig.NUMERIC_DEFAULT_KEYS:
            for row in self._current_data:
                v = row.get(key)
                if v is not None:
                    return 0 if isinstance(v, (int, float)) else v
            return 0
        if key == "dailyNight":
            return "日勤"
        if key == "workType":
            return "勤務"
        return key

    # -------------------------------------------------------------------------
    # モデル同期（テーブル → current_data → JSON）
    # -------------------------------------------------------------------------

    def _sync_row_to_model(self, row):
        """指定行のテーブル表示を current_data に反映し、JSON に保存する。"""
        columns = [
            self._table.horizontalHeaderItem(c).text()
            for c in range(self._table.columnCount())
        ]
        for col, key in enumerate(columns):
            value = self._read_cell_value(row, col, key)
            if value is not None:
                self._current_data[row][key] = value
        self._persist_current_category()

    def _read_cell_value(self, row, col, key):
        """
        1セルの値を current_data に格納する型で返す。
        ウィジェット列はウィジェットから、それ以外はアイテムから取得。
        """
        if key == "order":
            item = self._table.item(row, col)
            if item and item.text().isdigit():
                return int(item.text())
            return None
        if key == "color":
            item = self._table.item(row, col)
            if not item:
                return None
            parts = item.text().split(",")
            if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
                return [int(p.strip()) for p in parts]
            return None
        if key == "searchStr":
            item = self._table.item(row, col)
            if item:
                return [s.strip() for s in item.text().split(",") if s.strip()]
            return None
        if key == "min_skill_count":
            item = self._table.item(row, col)
            if not item:
                return None
            parts = [s.strip() for s in item.text().split(",")]
            if len(parts) != 7:
                return None
            if not all(p.isdigit() and int(p) >= 0 for p in parts):
                return None
            return [int(p) for p in parts]
        if key in AppConfig.WIDGET_COLUMNS:
            widget = self._table.cellWidget(row, col)
            if widget:
                return widget.currentText()
            return None
        item = self._table.item(row, col)
        if not item:
            return None
        text = item.text()
        if text.isdigit():
            return int(text)
        try:
            return float(text)
        except ValueError:
            return text

    def _persist_current_category(self):
        """現在カテゴリの current_data を dynamic_data に書き戻し、JSON 保存。"""
        name = self._combo_category.currentText()
        if name in self._dynamic_data:
            self._dynamic_data[name] = self._current_data
        self._save_data()

    # -------------------------------------------------------------------------
    # バリデーション
    # -------------------------------------------------------------------------

    def _validate_non_empty(self, cell):
        """セルが空白でないことを検証する。"""
        if not cell.text().strip():
            QMessageBox.warning(self, "エラー", "空白です")
            return False
        return True

    def _validate_non_negative_int(self, cell, row, column_name):
        """min_skill_score が 0 以上の整数であることを検証する。"""
        text = cell.text().strip()
        if not text:
            QMessageBox.warning(
                self, "エラー",
                f"{column_name} には 0 以上の整数を入力してください。",
            )
            self._revert_cell_to_model(row, column_name, cell)
            return False
        if not text.isdigit():
            QMessageBox.warning(
                self, "エラー",
                f"{column_name} には 0 以上の整数を入力してください。",
            )
            self._revert_cell_to_model(row, column_name, cell)
            return False
        val = int(text)
        if val < 0:
            QMessageBox.warning(
                self, "エラー",
                f"{column_name} には 0 以上の整数を入力してください。",
            )
            self._revert_cell_to_model(row, column_name, cell)
            return False
        return True

    def _validate_min_skill_count_list(self, cell, row):
        """min_skill_count が「日,月,火,水,木,金,土」の7個の0以上整数であることを検証する。"""
        text = cell.text().strip()
        parts = [s.strip() for s in text.split(",")] if text else []
        if len(parts) != 7:
            QMessageBox.warning(
                self, "エラー",
                "min_skill_count は曜日順（日,月,火,水,木,金,土）で"
                "7個の数をカンマ区切りで入力してください。",
            )
            self._revert_cell_to_model(row, "min_skill_count", cell)
            return False
        for i, p in enumerate(parts):
            if not p.isdigit() or int(p) < 0:
                day = AppConfig.MIN_SKILL_COUNT_DAY_LABELS[i]
                QMessageBox.warning(
                    self, "エラー",
                    f"min_skill_count の{day}曜の値は 0 以上の整数にしてください。",
                )
                self._revert_cell_to_model(row, "min_skill_count", cell)
                return False
        return True

    def _revert_cell_to_model(self, row, column_name, cell):
        """セル表示を current_data の値に戻す。"""
        if row >= len(self._current_data):
            return
        value = self._current_data[row].get(column_name, "")
        if column_name == "min_skill_count" and isinstance(value, list) and len(value) == 7:
            cell.setText(",".join(str(x) for x in value))
        else:
            cell.setText(str(value))

    def _validate_color(self, cell):
        """R,G,B 形式かつ 0–255 であることを検証する。"""
        parts = cell.text().split(",")
        if len(parts) != 3:
            QMessageBox.warning(
                self, "エラー",
                "無効な色です。R,G,B の形式で 0-255 を入力してください。",
            )
            return False
        if not all(
            p.strip().isdigit() and 0 <= int(p.strip()) < 256
            for p in parts
        ):
            QMessageBox.warning(
                self, "エラー",
                "無効な色です。R,G,B の形式で 0-255 を入力してください。",
            )
            return False
        return True

    def _validate_search_str(self, cell):
        """searchStr が空でないことを検証する。"""
        if not cell.text().strip():
            QMessageBox.warning(self, "エラー", "無効な値です")
            return False
        return True


# -----------------------------------------------------------------------------
# エントリポイント
# -----------------------------------------------------------------------------


def main():
    app = QApplication(sys.argv)
    # 第1引数でJSONファイルパスを指定可能（省略時はデフォルトの settings.json）
    initial_path = sys.argv[1] if len(sys.argv) >= 2 else None
    window = SettingsEditorApp(initial_json_path=initial_path)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
