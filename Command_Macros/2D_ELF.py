# Plot 2D ELF in a plane defined by three atoms
commands = [4,  # Output and plot specific property in a plane
            9,  # ELF
            1,  # Color-filled map
            "", # Default grid
            4,  # Define plane by three atoms
            "[Input: Index of three atoms to define the plane, e.g. 3,6,7]",
            -6] # Export plane plot data
