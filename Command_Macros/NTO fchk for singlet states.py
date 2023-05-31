"""
For Gaussian TD mission output like Molecule_1_TD.out and Molecule_1_TD.fchk, generate NTOs for all singlet states:
Molecule_1_TD.NTO_S1.fchk
Molecule_1_TD.NTO_S2.fchk
Molecule_1_TD.NTO_S3.fchk
...
"""

import re
import time
from pathlib import Path
import Multiwfn
inputs, outputs = Multiwfn.inputs, Multiwfn.outputs
get_input_filename = Multiwfn.get_input_filename

singlet_states = []
excitation_energies = []


def filename_fchk_to_out():
    """
    read the given out filename, set the global out_filename variable, return the corresponding fchk file name
    """

    fchk_filename = get_input_filename()
    out_filename = Path(fchk_filename).with_suffix('.out')

    return str(out_filename)


def get_singlet_states():
    """
    read excited states from output of 18/6 of Multiwfn,
    get a list of singlet excited state numbers to global variable singlet_states
        and a list of excitation energies (in eV) to global variable encitation_energies
    """
    global commands, singlet_states, excitation_energies

    if "Summary of excited states:" not in outputs[-1]:
        raise Exception("Summary of excited states not found")

    output = outputs[-1].splitlines()
    # match text: "State:    5    Exc. Energy:   3.911 eV   Multi.: 1    MO pairs:   39669"
    re_ret = [re.findall(r"State:\s+(\d+)\s+Exc. Energy:\s+(-*\d+\.\d+) eV\s+Multi.: 1\s+MO pairs:\s+\d+", line) for line in output]
    for ret in re_ret:
        if ret:
            ret = ret[0]
            singlet_states.append(ret[0])
            excitation_energies.append(float(ret[1]))

    for singlet_state in singlet_states[1:]:
        commands += ["[Note] Excited state "+str(singlet_state),
                     6,
                     filename_fchk_to_out,
                     singlet_state,
                     2,
                     NTO_output_filename]

    commands.append('[Quit]')

    return singlet_states[0]


def NTO_output_filename():
    state = inputs[-2]
    excitation_energy = excitation_energies[singlet_states.index(state)]
    wavelength = 1239.8 / excitation_energy
    return f"NTO_S{state}_{wavelength:.1f}nm.fchk"


commands = [18,  # Electron excitation analysis
            6,  # Generate NTO
            filename_fchk_to_out,  # Replace .fchk in the filename to .out, and save it as a variable
            get_singlet_states,  #
            2,
            NTO_output_filename]
