# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import os
import math
import copy
import shutil
import re
import time
import random

from Python_Lib.My_Lib_Stock import *
import subprocess
from Lib import *

multiwfn_folder = os.path.join(filename_class(os.path.realpath(__file__)).path, "executable")
multiwfn_executable = os.path.join(multiwfn_folder, 'Multiwfn.exe')
os.environ['Multiwfnpath'] = multiwfn_folder

def show_command_list(commands):
    ret = []
    for i in commands:
        if callable(i):
            ret.append(i.__name__ + "()")
        else:
            ret.append(str(i))
    return ret

def modify_settings_ini_file(multiwfn_folder, items_value_dict: dict):
    settings_ini_path = os.path.join(multiwfn_folder, "settings.ini")

    with open(settings_ini_path) as settings_ini_current_content:
        settings_ini_current_content = settings_ini_current_content.readlines()

    settings_ini_new_content = copy.deepcopy(settings_ini_current_content)
    for item, value in items_value_dict.items():
        value = str(value)
        for count, line in enumerate(settings_ini_new_content):
            if item in line:
                re_ret = re.findall(r'(\s+' + item + r'= )(.+)( \/\/.+)', line)
                new_line = re_ret[0][0] + value + re_ret[0][2].rstrip('\n') + '\n'
                new_line = "".join(new_line)
                settings_ini_new_content[count] = new_line
                break

    with open(settings_ini_path, 'w') as settings_ini_new_content_object:
        settings_ini_new_content_object.write("".join(settings_ini_new_content))


def run_multiwfn(multiwfn_folder,
                 input_file,
                 commands,
                 settings_ini_change_dict={},
                 output_file_prefix="",
                 output_file_suffix=""):
    """
    Runs multiwfn, copy the newly generated file to the original place, while renaming to a name that's input_filename + genreated_file_name
    Args:
        multiwfn_folder:
        input_file:
        commands: a list of commands, one item per line,
                  \n not included,
                  numbers will be automatically convert to str e.g. [4,7,1,'',4,'3,1,2','-6']
                  callables will be run with the input file as the parameter, e.g. to provide additional input, like fchk & out file
        settings_ini_change_dict:
        output_file_prefix:
        output_file_suffix:

    Returns:

    """
    if not output_file_prefix:
        output_file_prefix = filename_class(input_file).only_remove_append
    output_file_prefix = output_file_prefix + "_M_" + ("[" + output_file_suffix + "]" if output_file_suffix else "")

    # create temp Multiwfn exe folder
    if not os.path.isdir(os.path.realpath("temp")):
        os.mkdir('temp')
    target_multiwfn_folder = get_unused_filename(os.path.join('temp', 'Multiwfn'))
    shutil.copytree(os.path.realpath(multiwfn_folder), target_multiwfn_folder)
    target_multiwfn_folder = os.path.realpath(target_multiwfn_folder)
    os.chdir(target_multiwfn_folder)
    original_content = os.listdir(target_multiwfn_folder)

    # change settings.ini
    settings_ini_change_dict['isilent'] = 1
    modify_settings_ini_file(target_multiwfn_folder, settings_ini_change_dict)

    # create input file
    input_commands_file = "Input.txt"
    commands = [input_file] + commands
    with open(input_commands_file, 'w') as input_commands_object:
        for command in commands:
            input_commands_object.write(str(command) + '\n')

    # call Multiwfn
    with open(input_commands_file) as input_commands_object:
        subprocess.call('Multiwfn.exe', stdin=input_commands_object)
    output_files = []

    # extract output files
    for file in os.listdir(target_multiwfn_folder):
        if file not in original_content:
            target_output_filename = get_unused_filename(output_file_prefix + file, use_proper_filename=False)
            shutil.copy(os.path.join(target_multiwfn_folder, file), target_output_filename)
            output_files.append(target_output_filename)

    # remove temp Multiwfn
    os.chdir(filename_class(sys.argv[0]).path)
    shutil.rmtree(target_multiwfn_folder)
    return output_files


import numpy as np



def get_singlet_excited_states(previous_inputs, previous_outputs):
    """
    read excited states from output of 18/15 of Multiwfn,
    return a list of singlet excited state numbers to global variable singlet_states

    e.g.
    Input:
         The reference state is closed-shell
         The number of basis functions:   703
         Note: This file is recognized as a Gaussian output file
         There are   8 excited states, loading basic information...

         Loading configuration coefficients...
         Summary of excited states:
         Exc.state#     Exc.energy(eV)     Multi.   MO pairs    Normalization
           1           2.77700           3           11        0.461698
           2           3.23900           3           14        0.466362
           3           3.45340           3           12        0.465280
           4           3.77030           3           13        0.457104
           5           3.91130           1           11        0.468954
           6           3.96140           3           18        0.437162
           7           4.20470           1           11        0.465570
           8           4.52780           1            5        0.484647

         HOMO index:    62
         ...

    Return:
        ["5","7","8"]
    """
    output = previous_outputs[-1].splitlines()
    singlet_states = [re.findall(r"(\d+)\s+-*\d+\.\d+\s+1\s+\d+\s+-*\d+\.\d+") for x in output]
    singlet_states = [x for x in singlet_states if x]
    return singlet_states


def integral_cube_file_splited_by_plain(cube_x_y_z_value_file, plane_origin: np.array, plane_vector: np.array, selected_centers: list, all_centers,
                                        radius=1.0 / bohr__A):
    '''
    
    :param cube_x_y_z_value_file: A file generated by Multiwfn 13-1
    :param plain_origin: 
    :param plain_vector: 
    :return: 
    '''

    # 每个原子附近单独处理
    up_sum = [0 for x in range(len(selected_centers))]
    down_sum = [0 for x in range(len(selected_centers))]
    abs_sum = [0 for x in range(len(selected_centers))]
    selected_centers = [np.array(x) for x in selected_centers]
    all_abs_sum = 0

    for count, line in enumerate(open(cube_x_y_z_value_file)):
        if count % 100000 == 0:
            print(count)

        line = [float(x) for x in line.split()]
        if len(line) != 4:
            continue
        coord = np.array(line[:3])
        value = line[3]
        direction = np.dot(coord - plane_origin, plane_vector)
        for atom_count, atom in enumerate(all_centers):
            in_sphere = np.linalg.norm(atom - coord) < radius
            if in_sphere:
                all_abs_sum += abs(value)
                for selected_atom_count, selected_center in enumerate(selected_centers):
                    if np.equal(selected_center, atom).all():
                        abs_sum[selected_atom_count] += abs(value)
                        if direction > 0:
                            up_sum[selected_atom_count] += value
                            # up_square_sum[atom_count]+=value**2
                        elif direction < 0:
                            down_sum[selected_atom_count] += value
                    # down_square_sum[atom_count] += value ** 2
    for i in range(len(selected_centers)):
        print(abs_sum[i], up_sum[i], down_sum[i])

    print(all_abs_sum)
    # print(up_square_sum,down_square_sum)

# print(coordinate_from_cube_file(r"D:\Gaussian\LuYong2_2\Alpha_Substrate\Rerun_Confsearch_T1\Pi_to_PiStar\Alpha_Substrate_G15_M001_8_02[Opt_PBE0_DZ]_xtb_Pull_xtb_Pull_Step0_M_[MO_LUMO+346]MOvalue.cub"))
