# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

# TODO: 如何关掉跳出来的图形窗口
# TODO: 提取特定物理量
# TODO: 确定退出的信号
# TODO: Call function的时候参数要就给，不要就不给
# TODO: 传输命令的时候都做一次str()转换
# TODO: 显示Multiwfn版本，并在可执行文件中记录

import os.path
import re
import shutil
import time

from Python_Lib.My_Lib_PyQt6 import *
from Python_Lib.My_Lib_System import process_is_CPU_idle
from Lib import *
import Multiwfn

Multiwfn.setup_global_variable()
get_input_filename = Multiwfn.get_input_filename
all_sessions_inputs, all_sessions_outputs = Multiwfn.all_sessions_inputs, Multiwfn.all_sessions_outputs
inputs, outputs = Multiwfn.inputs, Multiwfn.outputs

pyqt_ui_compile('Multiwfn_GUI.py')
from UI.Multiwfn_GUI import Ui_Multiwfn_GUI_Form
from GUI_Lib import *

if __name__ == "__main__":
    temp_folder = os.path.join(filename_class(sys.argv[0]).path, 'Temp')
    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)
    log_file = os.path.abspath(os.path.join(temp_folder, "Temp_record_" + readable_timestamp() + '.log'))

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


def move_generated_files():
    if get_input_filename():
        output_file_prefix = filename_class(os.path.abspath(get_input_filename())).only_remove_append + ".Multiwfn."
        for file in list_folder_content(temp_folder):
            target_output_filename = get_unused_filename(output_file_prefix + filename_class(file).name, use_proper_filename=False)
            print("Moving", file, target_output_filename)
            shutil.move(file, target_output_filename)
    else:
        print("No input file loaded in the last session. No clean up done.")

    print("Deleting temp folder:", temp_folder)
    shutil.rmtree(temp_folder)


class Multiwfn_GUI(Ui_Multiwfn_GUI_Form, QWidget, Qt_Widget_Common_Functions):
    tab_signal = pyqtSignal()

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.show()
        self.open_config_file()

        self.output_textEdit = Output_textEdit(self.output_widget)
        self.output_verticalLayout.addWidget(self.output_textEdit)

        self.macro_selector_scrollArea.setStyleSheet(scroll_bar_stylesheet)

        self.current_round_output = ""  # 记录每次新输入之前的输出，用于合并standard error和standard output

        self.macro_files = []
        self.macro_pushbuttons = []
        self.macro_mode: Literal['txt', 'py'] = "txt"
        self.activated_macro_file = None
        self.macro_txt_content = ""
        self.macro_py_module = None
        self.macro_preview = []
        self.macro_current_line_no = -1

        # 把macro_selector_scrollArea和macro_content_textEdit的grid区域加起来，二者不同时显示
        self.main_grid_layout: QGridLayout = self.layout().itemAt(0).layout()

        # 4-tuple of row, column, row_span, column_span
        self.macro_selector_scrollArea_pos = self.main_grid_layout.getItemPosition(self.main_grid_layout.indexOf(self.macro_selector_scrollArea))
        self.macro_content_textEdit_pos = self.main_grid_layout.getItemPosition(self.main_grid_layout.indexOf(self.macro_content_textEdit))
        self.macro_grid_area = (self.macro_selector_scrollArea_pos[0],
                                self.macro_selector_scrollArea_pos[1],
                                self.macro_content_textEdit_pos[0] + self.macro_content_textEdit_pos[2],
                                self.macro_selector_scrollArea_pos[3])

        connect_once(self.output_textEdit.tab_signal, lambda: self.input_lineEdit.setFocus())
        connect_once(self.input_lineEdit.returnPressed, self.write_input)
        connect_once(self.send_command_pushButton, self.write_input)
        connect_once(self.reboot_pushButton, self.reboot)
        connect_once(self.step_forward_pushButton, self.step_forward)
        connect_once(self.execute_macro_pushButton, self.execute)
        connect_once(self.open_GaussView_pushButton, self.open_with_GaussView)
        connect_once(self.output_textEdit.file_dropped, self.file_dropped)
        connect_once(self.load_file_path_pushButton, self.load_file_path)

        self.launch()

        self.back_to_macros_list()
        self.load_macro_list()

        # periodically check status of Multiwfn subprocess, to decide whether its terminated.
        self.monitor_status_timer = QTimer(self)
        self.monitor_status_timer.timeout.connect(self.check_process_status)
        self.monitor_status_timer_interval = 500
        self.monitor_status_timer.start(self.monitor_status_timer_interval)

    def launch(self):
        self.process = QProcess()
        global temp_folder
        temp_folder = os.path.realpath("Temp/" + "Instance_" + str(readable_timestamp()))
        os.makedirs(temp_folder, exist_ok=True)
        self.process.setWorkingDirectory(temp_folder)
        self.process.start(multiwfn_executable)

        connect_once(self.process.readyReadStandardOutput, lambda process=self.process: self.write_output(self.process))
        connect_once(self.process.readyReadStandardError, lambda process=self.process: self.write_output(self.process))

    def load_macro_list(self):
        for i in self.macro_pushbuttons:
            i.setParent(None)
        self.macro_pushbuttons = []

        macro_folder = os.path.join(filename_class(__file__).path, "Command_Macros")
        self.macro_files = walk_all_files(macro_folder, "*.py") + walk_all_files(macro_folder, "*.txt")
        self.macro_files.sort()
        for file in self.macro_files:
            self.create_macro_pushbutton(file)
        self.macro_selector_scrollArea.widget().layout().addStretch()

    def create_macro_pushbutton(self, filepath):
        button = Macro_Pushbutton(filepath)
        self.macro_selector_scrollArea.widget().layout().addWidget(button)
        self.macro_pushbuttons.append(button)
        connect_once(button.clicked, self.read_macro)

    def read_macro(self, filepath):
        self.activated_macro_file = filepath
        self.macro_selector_scrollArea.setParent(None)
        self.main_grid_layout.addWidget(self.macro_content_textEdit, *self.macro_grid_area)
        connect_once(self.show_macro_list_pushButton, self.back_to_macros_list)

        extension = filename_class(filepath).append
        if extension.lower() == 'py':
            self.macro_mode = 'py'
            self.macro_txt_content = ""
            self.macro_py_module = import_from_absolute_path(os.path.abspath(filepath))
            self.macro_preview = show_command_list(self.macro_py_module.commands)
        else:
            self.macro_mode = 'txt'
            self.macro_py_module = None
            self.macro_preview = []
            with open(filepath) as macro_file_object:
                self.macro_preview = macro_file_object.read().splitlines()
                self.macro_txt_content = self.macro_preview
        self.show_macro_preview()

    def show_macro_preview(self):
        self.refresh_macro_list_pushButton.hide()
        self.execute_macro_pushButton.show()
        self.step_forward_pushButton.show()
        self.batch_run_pushButton.show()
        self.show_macro_list_pushButton.show()

        max_digit = int(math.log10(len(self.macro_preview))) + 1
        number_format = "{:<[MAX_DIGIT].0f}".replace("[MAX_DIGIT]", str(max_digit))
        rets = []

        for count, line in enumerate(self.macro_preview):
            sep = " >>> " if count == self.macro_current_line_no else "  |  "
            # if line.startswith("[Note]"):
            #     line = left_strip_sequence_from_str(line, "[Note] ")
            #     line = left_strip_sequence_from_str(line, "[Note]")
            ret = number_format.format(count + 1) + sep + line
            rets.append(ret)
        self.macro_content_textEdit.setPlainText("\n".join(rets))
        set_slider_to_line(self.macro_content_textEdit, self.macro_current_line_no - 10)

    def back_to_macros_list(self):
        self.show_macro_list_pushButton.hide()
        self.macro_content_textEdit.setParent(None)
        self.refresh_macro_list_pushButton.show()
        self.execute_macro_pushButton.hide()
        self.step_forward_pushButton.hide()
        self.batch_run_pushButton.hide()
        self.main_grid_layout.addWidget(self.macro_selector_scrollArea, *self.macro_grid_area)
        disconnect_all(self.show_macro_list_pushButton, self.back_to_macros_list)

    def write_text(self, text):

        with open(log_file, 'a') as log_file_object:
            log_file_object.write(text.replace('\r\n', '\n'))  # 不知道为什么不replace就会变成两行
            log_file_object.write("----------------------------------\n")

        self.output_textEdit.insertPlainText(text)
        cursor = self.output_textEdit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        vertical_scroll_to_end(self.output_textEdit)

    def write_output(self, process):

        text = bytes(process.readAllStandardOutput()).decode('gbk')
        text += bytes(process.readAllStandardError()).decode('gbk')
        self.write_text(text)

        self.current_round_output += text
        outputs[-1] = self.current_round_output

        if get_input_filename():
            self.input_file_lineEdit.setText("Input file: " + get_input_filename())
        else:
            self.input_file_lineEdit.setText("")

    def write_input(self):
        self.wait_idle()
        self.current_round_output = ""
        outputs.append("")
        text = self.input_lineEdit.text()

        inputs.append(text)
        self.write_text("\n\n>>> " + text + '\n\n\n')
        self.input_lineEdit.setText("")
        self.input_lineEdit.setPlaceholderText("Input command...")

        if text.lower().startswith("[quit]") or text.lower().startswith("[reboot]"):
            self.reboot()
            return None

        self.process.writeData(bytearray(text + "\n", encoding='gbk'))

        max_digit = int(math.log10(len(inputs))) + 1
        number_format = "{:<[MAX_DIGIT].0f}".replace("[MAX_DIGIT]", str(max_digit))
        command_history = [number_format.format(count + 1) + " |  " + line for count, line in enumerate(inputs)]
        self.command_history_textEdit.setPlainText("\n".join(command_history))
        vertical_scroll_to_end(self.command_history_textEdit)

    def file_dropped(self, filepath):
        filepath = filepath.strip().strip('"')
        if " " in filepath:
            filepath = '"' + filepath + '"'
        if self.input_lineEdit.text():
            self.input_lineEdit.setText(self.input_lineEdit.text() + " " + filepath)
        else:
            self.input_lineEdit.setText(filepath)

        self.input_lineEdit.setFocus()

        self.config['last_load_file_path'] = filename_class(filepath).path
        self.save_config()

    def load_file_path(self):
        last_load_file_path = self.get_config("last_load_file_path", ".")
        filename = get_open_file_UI(self, last_load_file_path, "*", "Load file path", single=True)
        self.file_dropped(filename)

    def save_output(self, output_file):
        output_file = get_unused_filename(output_file, False, False)
        with open(output_file, 'w') as output_file_object:
            output_file_object.write(self.output_textEdit.toPlainText())

    def save_output_default(self):
        filename = filename_class(get_input_filename()).replace_append_to("Multiwfn.out")
        self.save_output(filename)

    def save_output_as(self):
        input_path = filename_class(get_input_filename()).path
        filename = get_save_file_UI(self, input_path, "txt", "Save Output")
        self.save_output(filename)

    def open_with_GaussView(self):
        input_filename = get_input_filename()
        gview_exe = self.get_config('Gview_Path', r"C:\g09w\gview.exe")
        if not os.path.isfile(gview_exe):
            exe = get_open_file_UI(self, r"C:\g09w", 'exe', 'Choose GView .exe')
            if os.path.isfile(exe):
                gview_exe = exe
        self.config['Gview_Path'] = gview_exe
        self.save_config()
        if os.path.isfile(gview_exe):
            if os.path.isfile(input_filename):
                subprocess.Popen([gview_exe, input_filename])
        else:
            self.open_GaussView_pushButton.setText("GView Not Found")

    def reboot(self):
        self.wait_idle()
        self.reboot_pushButton.setText("Rebooting...")
        self.process.setWorkingDirectory(filename_class(__file__).path)
        move_generated_files()
        all_sessions_outputs.append(copy.deepcopy(outputs))
        all_sessions_inputs.append(copy.deepcopy(inputs))
        outputs.clear()
        inputs.clear()
        outputs.append("")
        self.write_text("\n\n-------------------------------------REBOOT-------------------------------------\n\n")
        self.process.kill()
        while self.process.state() == self.process.ProcessState.Running:
            Application.processEvents()
            time.sleep(0.1)
        self.launch()

        self.reboot_pushButton.setText("Reboot")

    def step_forward(self):
        disconnect_all(self.step_forward_pushButton, self.step_forward)
        self.macro_current_line_no += 1
        self.show_macro_preview()
        self.input_lineEdit.setPlaceholderText("")
        note = False
        if self.macro_mode == 'txt':
            if self.macro_current_line_no == len(self.macro_txt_content):
                return None
            command = self.macro_txt_content[self.macro_current_line_no]

        elif self.macro_mode == 'py':
            if self.macro_current_line_no == len(self.macro_py_module.commands):
                return None
            command = self.macro_py_module.commands[self.macro_current_line_no]
            if callable(command):
                self.wait_idle(sampling_interval=0.5)
                command = command()
                self.macro_preview = show_command_list(self.macro_py_module.commands)
                self.show_macro_preview()

        command = str(command)
        if command.lower().startswith("[note]"):
            return self.step_forward()

        if command.lower().startswith("[input]"):
            self.input_lineEdit.setPlaceholderText(command)
            self.input_lineEdit.setFocus()
            return True

        self.input_lineEdit.setText(str(command))
        self.input_lineEdit.returnPressed.emit()
        connect_once(self.step_forward_pushButton, self.step_forward)
        return True

    def execute(self):
        while True:
            Application.processEvents()
            if self.step_forward() is None:
                break

    def batch_run(self):
        if self.activated_macro_file is None:
            return None
        files = get_open_file_UI(self, self.get_config("last_load_file_path", '.'), "*", "Batch operation input files")
        if not files:
            return None
        for file in files:
            self.reboot()
            self.file_dropped(file)
            self.read_macro(self.activated_macro_file)
            self.execute()

    def wait_idle(self, sampling_interval=0.1):
        while process_is_CPU_idle(self.process.processId(), interval=sampling_interval) is False:
            Application.processEvents()
            time.sleep(0.1)

    def check_process_status(self):
        if self.process.state() == self.process.ProcessState.NotRunning:
            self.reboot()
        if process_is_CPU_idle(self.process.processId(), interval=0.1):
            self.send_command_pushButton.setText("Send")
            self.send_command_pushButton.setEnabled(True)
        else:
            self.send_command_pushButton.setText("Busy...")
            self.send_command_pushButton.setEnabled(False)


if __name__ == '__main__':
    gui = Multiwfn_GUI()
    gui.show()
    exit_code = Application.exec()
    move_generated_files()

    sys.exit(exit_code)
