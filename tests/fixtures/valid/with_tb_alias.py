"""Valid PyATB script using TB alias."""

import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"

tb = pyatb.TB(hr_file=hr_file, sr_file=sr_file)
