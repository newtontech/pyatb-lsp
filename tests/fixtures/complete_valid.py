"""Complete valid PyATB script with all references."""

import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"
output_path = "results/"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
