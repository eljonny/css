# Source - https://stackoverflow.com/a/28154841
# Posted by vaultah, modified by community. See post 'Timeline' for change history
# Retrieved 2026-08-30, License - CC BY-SA 3.0

# Add __init__.py code for adding the base package directory to the
#   Python Module Path, if in the dev env -
# Jonathan Hyry <jonathan.hyry@outlook.com> - 2026-08-30

import os
import sys
from pathlib import Path  # if you haven't already done so

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[5]
dev_path = f"{str(root)}/libplist/cython/.libs"
if os.path.isdir(dev_path):
  sys.path.append(dev_path)

  # Additionally remove the current file's directory from sys.path
  try:
      sys.path.remove(str(parent))
  except ValueError:  # Already removed
      pass
