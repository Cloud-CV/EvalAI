# -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    from .dev import *  # noqa
except ImportError:
    pass

try:
    from .prod import *  # noqa
except ImportError:
    pass
