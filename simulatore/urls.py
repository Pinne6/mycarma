from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^dettagli_simulazione', views.dettagli_simulazione, name='dettagli_simulazione'),
    url(r'^form_singolo', views.form_singolo, name='form_singolo'),
    url(r'^export_operazioni', views.export_operazioni, name='export_operazioni'),
]
