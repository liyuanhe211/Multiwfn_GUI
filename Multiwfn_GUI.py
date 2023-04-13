# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

# TODO: 如何关掉跳出来的图形窗口
# TODO: 提取特定物理量
# TODO: 确定退出的信号
# TODO: Call function的时候参数要就给，不要就不给
# TODO: 传输命令的时候都做一次str()转换
# TODO: 显示Multiwfn版本，并在可执行文件中记录

import subprocess
from datetime import datetime

from Python_Lib.My_Lib_PyQt6 import *
from Multiwfn_Lib import *

temp_folder = os.path.join(filename_class(sys.argv[0]).path, 'Temp')
if not os.path.isdir(temp_folder):
    os.mkdir(temp_folder)
log_file = open(os.path.join(temp_folder, "Temp_record_" + str(random.randint(0, 10000)) + '.log'), 'w')

# import pathlib
# parent_path = str(pathlib.Path(__file__).parent.resolve())
# sys.path.insert(0,parent_path)


Application = QtWidgets.QApplication(sys.argv)
font = Application.font()
font.setFamily("Arial")
Application.setFont(font)

if platform.system() == 'Windows':
    import ctypes

    APPID = 'LYH.XXXXXXXXXX.0.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    Application.setWindowIcon(QtGui.QIcon('UI/XXXXXXXXXX.png'))
    # matplotlib_DPI_setting = get_matplotlib_DPI_setting(Windows_DPI_ratio)

if __name__ == '__main__':
    pyqt_ui_compile('Multiwfn_GUI.py')
    from UI.Multiwfn_GUI import Ui_Multiwfn_GUI_Form


class HighlightRule:
    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlight_color = QColor(Qt_Colors.yellow).lighter(150)

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#D0CE00"))
        self.keyword_format.setBackground(QColor("#1E1E1E"))
        # self.keyword_format.setFontWeight(Qfont.Bold)

        self.reset_rules()

    def reset_rules(self):
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

    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)

        style_sheet = '''color: #DCDCDC; 
                         background-color: #1E1E1E;
                         font: 10pt "Consolas";
                         border-color: #1E1E1E'''

        self.setStyleSheet(style_sheet)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.highlighter = PythonHighlighter(self.document())
        self.show()

    def keyPressEvent(self, event: QKeyEvent):
        if isinstance(event, QKeyEvent):
            if event.key() == Qt_Keys.Key_Tab:
                self.tab_signal.emit()
                return None
        super().keyPressEvent(event)


class Multiwfn_GUI(Ui_Multiwfn_GUI_Form, QWidget, Qt_Widget_Common_Functions):
    tab_signal = pyqtSignal()

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.show()

        self.open_config_file()

        # self.default_font_name = 'Consolas'
        # self.default_font_size = 10

        self.output_textEdit = Output_textEdit(self.output_widget)
        self.output_verticalLayout.addWidget(self.output_textEdit)

        # self.set_font(self.output_textEdit, 'self.output_textEdit')
        # self.set_font(self.input_lineEdit, 'self.input_lineEdit')

        self.process = QProcess()
        self.process.start(multiwfn_executable)
        connect_once(self.process.readyReadStandardOutput, lambda process=self.process: self.write_output(self.process))
        connect_once(self.process.readyReadStandardError, lambda process=self.process: self.write_output(self.process))
        connect_once(self.output_textEdit.tab_signal, lambda: self.input_lineEdit.setFocus())
        connect_once(self.input_lineEdit.returnPressed, self.write_input)

    def set_font(self, target, target_name):
        new_font = QFont()
        if target_name + '_font' not in self.config:
            self.config[target_name + '_font'] = (self.default_font_name, self.default_font_size, self.default_style_sheet)
        self.save_config()
        font_name, font_size, style_sheet = self.load_config(target_name + '_font')
        new_font.setFamily(font_name)
        new_font.setPointSize(font_size)
        target.setFont(new_font)
        target.setStyleSheet(style_sheet)

    def save_font(self, target_name, font_name, font_size, style_sheet):
        self.config[target_name + '_font'] = (font_name, font_size, style_sheet)
        self.save_config()

    def write_output(self, process):

        if isinstance(process, str):
            # 把输入的东西写上去
            text = process
        else:
            text = bytes(process.readAllStandardOutput()).decode('gbk')
            text += bytes(process.readAllStandardError()).decode('gbk')

        log_file.write(text)

        self.output_textEdit.insertPlainText(text)
        print(text, end="")
        cursor = self.output_textEdit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        self.output_textEdit.verticalScrollBar().setSliderPosition(self.output_textEdit.verticalScrollBar().maximum())

    def write_input(self):
        text = self.input_lineEdit.text()
        self.write_output("\n\n>>> " + text + '\n\n\n')
        self.input_lineEdit.setText("")
        self.process.writeData(bytearray(text + "\n", encoding='gbk'))


if __name__ == '__main__':
    gui = Multiwfn_GUI()

    gui.show()
    sys.exit(Application.exec())
