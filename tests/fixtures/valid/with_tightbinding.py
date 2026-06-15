"""Valid PyATB script using TightBinding class."""

import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
