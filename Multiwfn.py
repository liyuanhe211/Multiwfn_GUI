# Cross file global variables

from Python_Lib.My_Lib_Stock import *


def setup_global_variable():
    global all_sessions_inputs, all_sessions_outputs, inputs, outputs
    # global variable for access from macro
    all_sessions_inputs = []  # list of list of str
    all_sessions_outputs = []  # list of list of str
    inputs = []  # list of str
    outputs = [""]  # list of str


def get_input_filename():
    if len(outputs) >= 2:
        for output in outputs: # 不能只看第二个，因为有时第一次输文件名输错了
            for i in output.splitlines():
                if i.strip().startswith("Loaded ") and i.strip().endswith(" successfully!"):
                    ret = left_strip_sequence_from_str(i.strip(), "Loaded ")
                    ret = right_strip_sequence_from_str(ret, " successfully!").strip()
                    return ret
