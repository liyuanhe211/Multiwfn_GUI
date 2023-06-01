# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import os.path

from Python_Lib.My_Lib_PyQt6 import *

pyqt_ui_compile('Multiwfn_Gui_Pushbutton.py')
from UI.Multiwfn_Gui_Pushbutton import Ui_Multiwfn_Pushbutton

vertical_scroll_bar_stylesheet = """QScrollBar:vertical {
                                  background: #303030;
                                  width: 12px;
                              }
                              QScrollBar::handle:vertical {
                                  background: #A0A0A0;
                                  min-height: 20px;
                              }
                              QScrollBar::add-line:vertical {
                                  background: #303030;
                                  subcontrol-position: bottom;
                                  subcontrol-origin: margin;
                              }
                              
                              QScrollBar::sub-line:vertical {
                                  background: #303030;
                                  subcontrol-position: top;
                                  subcontrol-origin: margin;
                              }
                              
                              QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                  background: none;
                              }"""

horizontal_scroll_bar_stylesheet = """QScrollBar:horizontal {
                                  background: #303030;
                                  height: 12px;
                              }
                              QScrollBar::handle:horizontal {
                                  background: #A0A0A0;
                                  min-width: 20px;
                              }
                              QScrollBar::add-line:horizontal {
                                  background: #303030;
                                  subcontrol-position: right;
                                  subcontrol-origin: margin;
                              }
                              
                              QScrollBar::sub-line:horizontal {
                                  background: #303030;
                                  subcontrol-position: left;
                                  subcontrol-origin: margin;
                              }
                              
                              QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                                  background: none;
                              }"""
class HighlightRule:
    def __init__(self, pattern, highlight_format):
        self.pattern = pattern
        self.format = highlight_format


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlight_color = QColor(Qt_Colors.yellow).lighter(150)

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#D0CE00"))
        self.keyword_format.setBackground(QColor("#1E1E1E"))
        rules = []

        pattern = re.compile(r'^>>>(.*)')
        rule = HighlightRule(pattern, self.keyword_format)
        rules.append(rule)

        self.rules = rules

    def highlightBlock(self, text):
        for rule in self.rules:
            expression = re.compile(rule.pattern)
            match = expression.search(text)
            while match is not None:
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, rule.format)
                match = expression.search(text, match.end())


class Output_textEdit(QTextEdit):
    tab_signal = pyqtSignal()
    file_dropped = pyqtSignal(str)

    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)

        # style_sheet = '''color: #DCDCDC;
        #                  background-color: #1E1E1E;
        #                  font: 10pt "Consolas";
        #                  border-color: #1E1E1E'''
        #
        # self.setStyleSheet(style_sheet)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAcceptDrops(True)
        # self.setReadOnly(True)
        self.setStyleSheet(vertical_scroll_bar_stylesheet)

        self.highlighter = PythonHighlighter(self.document())
        self.show()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def keyPressEvent(self, event: QKeyEvent):
        if isinstance(event, QKeyEvent):
            if event.key() == Qt_Keys.Key_Tab:
                self.tab_signal.emit()
                return None
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                self.file_dropped.emit(path)
        event.acceptProposedAction()


class Macro_Pushbutton(Ui_Multiwfn_Pushbutton, QtWidgets.QWidget, Qt_Widget_Common_Functions):
    clicked = pyqtSignal(str)

    def __init__(self, filepath):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        filepath = os.path.abspath(filepath)
        rel_path = os.path.relpath(filepath,filename_class(os.path.abspath(__file__)).path)

        name_stem = left_strip_sequence_from_str(filename_class(rel_path).only_remove_append,"Command_Macros/")
        extension = filename_class(filepath).append
        self.filepath = filepath
        if extension.lower() == 'py':
            icon = "images/Python_LOGO.png"
        else:
            icon = "images/text_LOGO.png"
        icon = QIcon(icon)
        self.pushButton.setText(name_stem)
        self.pushButton.setIcon(icon)
        connect_once(self.pushButton.clicked, self.emit_clicked)

    def emit_clicked(self):
        self.clicked.emit(self.filepath)
