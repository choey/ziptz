"""ziptz as a package: the library itself is one file, ziptz.py beside this.

Two ways in, because the library is copied as often as it is installed. A
program that vendors this directory beside itself imports it and finds it
before anything installed -- and this hands straight through to the module.
Copy `ziptz.py` somewhere on its own and it imports as itself, with no package
around it. Both give the same names.
"""

from . import ziptz as _module
from .ziptz import *  # noqa: F401,F403
from .ziptz import EXCEPTIONS, GENERIC, RUNS, ZONES, __version__  # noqa: F401

# help(ziptz) and the docs sites read __doc__, and an installed user reaches
# this file rather than the module under it -- so without this they got the
# paragraph above, which is about packaging, instead of the one in ziptz.py
# with the examples, the accuracy note and the attribution.
__doc__ = _module.__doc__

# So that `from ziptz import *` binds the library's names and not the
# submodule that happens to share its name with the package.
__all__ = list(_module.__all__)
