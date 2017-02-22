"""mycarma URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.contrib.auth import views as auth_views
from home import views
from simulatore.api import EntryResource
# from django.conf.urls.static import static

entry_resource = EntryResource()

urlpatterns = [
    url(r'^$', views.index),
    url(r'^simulatore/', include('simulatore.urls')),
    url(r'^admin/', admin.site.urls),
    # url(r'^login/$', auth_views.login, name='login'),
    # url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^api/', include(entry_resource.urls)),
    url(r'^carma/', include('carma.urls')),
]  # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
   ]
