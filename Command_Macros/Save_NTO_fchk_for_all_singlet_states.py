import re
from pathlib import Path

out_filename = ""
singlet_states = []
excitation_energies = []


def filename_out_to_fchk(previous_inputs):
    """
    read the given out filename, set the global out_filename variable, return the corresponding fchk file name
    """

    global out_filename, singlet_states
    out_filename = previous_inputs[0]
    fchk_filename = str(Path(out_filename).with_suffix('.fchk'))

    return fchk_filename


def get_singlet_states(previous_inputs, previous_outputs):
    """
    read excited states from output of 18/6 of Multiwfn,
    get a list of singlet excited state numbers to global variable singlet_states
        and a list of excitation energies (in eV) to global variable encitation_energies
    """
    global singlet_states,excitation_energies
    output = previous_outputs[-1].splitlines()
    # match text: "State:    5    Exc. Energy:   3.911 eV   Multi.: 1    MO pairs:   39669"
    re_ret = [re.findall(r"State:\s+(\d+)\s+Exc. Energy:\s+(-*\d+\.\d+) eV\s+Multi.: 1\s+MO pairs:\s+\d+", line) for line in output]
    for i in re_ret:
        if i:
            singlet_states.append(i[0])
            excitation_energies.append(float(i[1]))
    return singlet_states[0]


def NTO_output_filename(previous_inputs, previous_outputs):
    state = previous_inputs[-2]
    excitation_energy = excitation_energies[singlet_states.index(state)]
    wavelength = 1239.8/excitation_energy
    out_filename_obj = Path(out_filename)
    return f"{out_filename_obj.stem}.NTO_S{state}_{wavelength:.1f}nm.fchk"


commands = [filename_out_to_fchk,
            18,
            6,
            out_filename,
            get_singlet_states,
            2,
            NTO_output_filename]

for singlet_state in singlet_states[1:]:
    commands += [6,
                 out_filename,
                 singlet_state,
                 2,
                 NTO_output_filename]

commands.append('q')
