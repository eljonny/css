# Source - https://stackoverflow.com/a/75753567
# Posted by Salvatore Cosentino, modified by community. See post 'Timeline' for change history
# Retrieved 2026-08-09, License - CC BY-SA 4.0

from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

# Add setup.py for libplist Cython extension build -
# libplist Python bindings -
# Modified significantly from the SO source -
# Jonathan Hyry <jonathan.hyry@outlook.com> - 2026-08-09

Options.annotate = True
Options.cache_builtins = True
Options.clear_to_none = True
Options.convert_range = True
Options.docstrings = True
Options.embed_pos_in_docstring = True
Options.error_on_uninitialized = True
Options.error_on_unknown_names = True
Options.extra_warnings = True
Options.gcc_branch_hints = False
Options.generate_cleanup_code = True
Options.warning_errors = True

setup(
  name='cs.app.osx.plist',

  ext_modules=cythonize(
    "libplist/cython/plist.pyx",
    compiler_directives={
      "language_level": 3,
      "profile": False
    },
    include_path=[
      "libplist/"
    ],
    force=True,
    show_all_warnings=False
  ),

  include_dirs=[
    "libplist/cython",
    "libplist/src"
  ]
)
