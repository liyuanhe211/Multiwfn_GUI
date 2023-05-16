# Launch
TODO

# Features

 * GUI with pushbutton navigation, highlight, and easier copy-paste. 
 * Record command history and replay common macros.
 * Programmable automation with output-dependent operations.
 * File selection with GUI (although Multiwfn have native support, most don't know about it).
 * Show input filename in GUI to see which session you are in.

# The GUI

TODO

# Writing a command macro

You can save snippets of commands as command macro, and run it in the GUI with one click.

By default, the macros should be store in the folder `./Command_Macros/`

## Save from current session

TODO

## As fixed command list
For a list of fixed commands, write a .txt file, where each line is a multiwfn command (not including the first command of giving input file).

Each line contains the input to Multiwfn and an optional comment divided by `//`. E.g.:
```TypeScript
2 // Topology analysis. Search all critical points (CPs) by inputting below commands
2 // Use nuclear positions as initial guesses, generally used to search (3,-3) CPs
3 // Use midpoint of each atomic pair in turn as initial guesses. Generally all (3,-1) CPs could be found, some (3,+1) or (3,+3) may also be found at the same time
```
### Special tags
Any line starts with `[Note]` will be omitted. 

By using the special tag `[Input: prompt]` as a line, you will be prompted to input certain text in the GUI. For example, the following macro plots 2D ELF data along a plane defined by three atoms: 
<a name="2D_ELF_Example"></a>
```TypeScript
[Note] Plot 2D ELF in a plane defined by three atoms
4 // Output and plot specific property in a plane
9 // ELF
1 // Color-filled map
  // Default grid
4 // Define plane by three atoms
[Input: Index of three atoms to define the plane, e.g. 3,6,7]
-6 // Export plane plot data
```
Another special tag `[Reboot]` will cause Multiwfn to reboot.

## As python functions

For a complete control of program behaviors, you can write python functions to automate what input you need next. 

To do this, write a .py script, with the end goal of generating a python list called `commands`.

The `commands` list could contain simple text or numbers. For example, the [2D ELF script above](#2D_ELF_Example) are equivalent to the following script:
```python
# Plot 2D ELF in a plane defined by three atoms
commands = [4,  # Output and plot specific property in a plane
            9,  # ELF
            1,  # Color-filled map
            "", # Default grid
            4,  # Define plane by three atoms
            "[Input: Index of three atoms to define the plane, e.g. 3,6,7]",
            -6] # Export plane plot data
```
You can fully automate the interaction process by adding function objects into the `commands` list. The function will be called, and should return a string as the command to be fed into Multiwfn.  

Optionally, the function could be fed with two parameters, `previous_inputs`, and `previous_outputs`. Both are tuples, which contain all inputs and outputs of the session. 

For example, if one have a batch of Gaussian TD missions, and wish to generate NTOs as fchk files for all singlet excited states. Suppose the input files are:
```
Molecule_1_TD.out
Molecule_1_TD.fchk
Molecule_2_TD.out
Molecule_2_TD.fchk
...
```
And for each molecule, the generated NTOs should be saved to:
```
Molecule_1_TD.NTO_S1.fchk
Molecule_1_TD.NTO_S2.fchk
Molecule_1_TD.NTO_S3.fchk
...
```
To automate this process, one can wrote the following script:

TODO