# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys

if "test" in sys.argv:
    print("\033[1;91mNo django tests.\033[0m")
    print("Try: \033[1;33mpy.test\033[0m")
    sys.exit(0)

TEST = [arg for arg in sys.argv if 'py.test' in arg]
if TEST:
    print("Using Test settings")
    from .test import * # noqa
else:
    try:
        from .dev import *  # noqa
        print("Using Dev settings")
    except ImportError:
        try:
            from .prod import *  # noqa
            print("Using Prod settings")
        except ImportError:
            pass
