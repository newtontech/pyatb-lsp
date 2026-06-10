"""Valid PyATB workflow script for testing."""

import pyatb

# Configure tight-binding model
hr_file = "HR.dat"
sr_file = "SR.dat"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
