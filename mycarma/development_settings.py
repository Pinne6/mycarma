# -*- coding: utf-8 -*-

from .settings import *

DEBUG = True

TEMPLATE_DEBUG = DEBUG

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
print(STATIC_ROOT)
