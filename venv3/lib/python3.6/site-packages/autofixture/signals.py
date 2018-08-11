# -*- coding: utf-8 -*-
from django.dispatch import Signal


instance_created = Signal(providing_args=['model', 'instance', 'committed'])
