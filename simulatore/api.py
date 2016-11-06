# myapp/api.py
from tastypie.resources import ModelResource, Resource
from tastypie.utils import trailing_slash
from tastypie import fields
from simulatore.models import GeneraSimulazione, SimulazioneStatistiche, SimulazioneSingola, Tappeto
from django.conf.urls import url, include
import datetime
from django.conf import settings
from tastypie.authentication import BasicAuthentication
import os


class EntryResource(Resource):
    class Meta:
        resource_name = 'entry'
        allowed_methods = ['post']
        object_class = Tappeto
        authentication = BasicAuthentication()

    def prepend_urls(self):
        """ Add the following array of urls to the GameResource base urls """
        return [
            url(r"^(?P<resource_name>%s)/simula%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('simula'), name="simula"),
        ]

    def simula(self, request, **kwargs):
        self.is_authenticated(request)
        """ proxy for the game.start method """

        # you can do a method check to avoid bad requests
        self.method_check(request, allowed=['post'])

        if settings.SERVER_DEV is False:
            dire = "/home/carma/dati/isin.conf"
            ticker = "/home/carma/dati/isin_ticker.conf"
            folder = "/home/carma/dati/intra/"
        else:
            dire = "C:\\Users\\fesposti\\Box Sync\\Simulatore\\intra\\isin.conf"
            ticker = "C:\\Users\\fesposti\\Box Sync\\Simulatore\\intra\\isin_ticker.conf"
            folder = "C:\\intra\\"

        isin_isin = []
        isin_ticker = []
        if os.path.exists(ticker):
            with open(ticker) as f:
                for line in f:
                    line = line.split("|")
                    isin_isin.append(line[0])
                    isin_ticker.append(line[1][:-1])
        if request.POST.get('isin') in isin_ticker:
            isin = isin_isin[isin_ticker.index(request.POST.get('isin'))]
            ticker = True
        else:
            isin = request.POST.get('isin')
            ticker = False
        # creo l'oggetto simulazione prendendo i dati in POST.
        simulazione = GeneraSimulazione(request=request, isin=isin, ticker=ticker)

        # creo l'array numpy
        tappeto, pacchi_numpy = simulazione.creazione_array()

        # eseguo la simulazione
        start_time = datetime.datetime.today()
        tappeto, pacchi_numpy = simulazione.simula(tappeto, pacchi_numpy, folder)
        time = datetime.datetime.today() - start_time

        # eseguo le statistiche
        simsingolamax, take_array, take_array_size = simulazione.genera_statistiche(request, tappeto, time)

        # bundles = [Resource.build_bundle(self, obj=tappeto, request=request) for Tappeto in tappeto]
        # data = [Resource.full_dehydrate(bundle) for bundle in bundles]
        # Resource.serialize(None, data, 'application/json'),
        keys = ['isin', 'limite_inferiore', 'limite_superiore', 'step', 'take', 'quantita_acquisto',
                'quantita_vendita', 'primo_acquisto',
                'tipo_commissione', 'commissione', 'min_commissione', 'max_commissione', 'in_carico',
                'nr_acquisti', 'nr_vendite', 'gain', 'commissioni', 'profitto', 'valore_attuale', 'valore_carico_long',
                'valore_carico_short', 'valore_min', 'valore_max', 'quantita_totale', 'rendimento', 'rendimento_teorico']
        # [dict(zip(keys, row)) for row in tappeto]
        risultato = []
        for item in tappeto:
            row = [item.isin, item.limite_inferiore, item.limite_superiore, item.step, item.take,
                   item.quantita_acquisto, item.quantita_vendita, item.primo_acquisto, item.tipo_commissione,
                   item.commissione, item.min_commissione, item.max_commissione, item.in_carico, item.nr_acquisti,
                   item.nr_vendite, item.gain, item.commissioni, item.profitto, item.valore_attuale,
                   item.valore_carico_long, item.valore_carico_short, item.valore_min, item.valore_max,
                   item.quantita_totale, item.rendimento, item.rendimento_teorico]
            risultato.append([dict(zip(keys, row))])
            # risultato = [dict(zip(keys, row)) for row in item]
        # Return what the method output, tastypie will handle the serialization
        return self.create_response(request, risultato)
