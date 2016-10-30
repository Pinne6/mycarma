from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^dettagli_simulazione', views.dettagli_simulazione, name='dettagli_simulazione'),
]
