# -*- coding: utf-8 -*-

from .settings import *

DEBUG = True

STATIC_ROOT = "home/carma/mycarma/static"


def show_toolbar(request):
    return True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'YourAppName.settings.development.show_toolbar',
}

INTERNAL_IPS = ['127.0.0.1']
