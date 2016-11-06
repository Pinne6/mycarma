# Create your views here.

"""
1.03.06 - 06/11/2016
- API con supporto per ticker
1.03.05 - 06/11/2016
- fix su data inizio controlli
1.03.04 - 06/11/2016
- fix controllo su take singolo in jquery
1.03.04 - 06/11/2016
- fix controllo su take singolo in jquery
1.03.03 - 06/11/2016
- rimosso controllo form da forms.py
1.03.02 - 06/11/2016
- implementato controllo aggiuntivo su data inizio per evitare aggiramento del limite giorni
1.03.01 - 05/11/2016
- creazione form take variabile sotto login
- tutto il form sotto login
1.03.00 - 05/11/2016
- creata API per eseguire simulazione
1.02.00 - 03/11/2016
- cambiato il form usando il built in di Django
- spostata tutta la logica nei modelli
1.01.00 - 02/11/2016
- risolto problema con user.session su firefox
- aggiunto nomenclatura pacchi long e short
- aggiunto calcolo max esposizione long e short
1.00.07 - 01/11/2016
- inserito numero negativo per i pacchi in carico per simulare lo short
1.00.06 - 01/11/2016
- tutte le pagine di login e registrazione senza il modal per essere compatibili con mobile
- risolto problema di memorizzazione sempre utente anonymous nelle statistiche
1.00.05 - 01/11/2016
- risolto problema con pacchi in carico
- pagina di login su iphone
1.00.04 - 01/11/2016
- rounded numbers
- euro nella tabella dei take
1.00.03 - 01/11/2016
- nella navbar evidenziato home per la homepage
1.00.02 - 01/11/2016
- spostato index.html nella directory home
1.00.01 - 30/10/2016
- inserito index nella app home
1.00.00 - 30/10/2016
- implementate variabili di sessione
- implementato massimo valore teorico del tappeto
- inserito bootstrap datepicker
0.12.00 - 27/10/2016
- implementato calcolo corretto gain con short
0.11.00 - 26/10/2016
- prima versione con login parziale
0.10.04 - 25/10/2016
- tolto i print
0.10.03 - 25/10/2016
- risolto permission nel file di configurazione apache
0.10.02 - 25/10/2016
- inserito print permission nel template per troubleshoot sul server di test
0.10.01 - 25/10/2016
- tolto riferimento a pandas array che causava errore
0.10.00 - 25/10/2016
- implementato numpy array
0.09.00 - 22/10/2016
- sistemati i permessi
0.08.00 - 21/10/2016
- inserite statistiche migliore e peggiore simulazione
- creato database di test nel settings sul server
0.07.00 - 20/10/2016
- inserite statistiche della simulazione totale nel database
0.06.00 - 19/10/2016
- form validation
0.05.00 - 18/10/2016
- versione funzionante
0.04.01 - 17/10/2016
- impostato diverse configurazioni per test e development, punta ai dati corretti sul server remoto
0.04.00 - 13/10/2016
- cambiato db in MySQL
0.03.00 - 10/10/2016
- aggiunto passaggi parametri da una chiamata all'altra per preservare i valori immessi
0.02.00 - 07/10/2016
- messo tabella accanto al form e inserito il numero di pacchi in carico

DA FARE
- gestire lo short (guadagno sull'acquisto e non sulla vendita) (dovrebbe essere fatto)
- grafici
- statistiche totale tappeto
- controlli sugli input
- per ogni data il take migliore
"""

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import *
import datetime
import os.path
import numpy as np
from django.conf import settings
from django.db import transaction
from django.template import RequestContext
import mysql.connector
from django.forms.models import model_to_dict
from .forms import FormTakeSingolo, FormTakeVariabile
from django import forms


def line_profiler(view=None, extra_view=None):
    import line_profiler

    def wrapper(view):
        def wrapped(*args, **kwargs):
            prof = line_profiler.LineProfiler()
            prof.add_function(view)
            if extra_view:
                [prof.add_function(v) for v in extra_view]
            with prof:
                resp = view(*args, **kwargs)
            prof.print_stats()
            return resp

        return wrapped

    if view:
        return wrapper(view)
    return wrapper


def read_csv_files(dire):
    """
    Legge il file con la lista ISIN e memorizza in un array
    :param dire: percorso dove trovare il file ISIN
    :return: array con lista ISIN
    """
    isin_conf = []
    if os.path.exists(dire):
        with open(dire) as f:
            for line in f:
                line = line.split("|")
                isin_conf.append(line)
    return isin_conf


def form_singolo(request):
    if settings.SERVER_DEV is False:
        dire = "/home/carma/dati/isin.conf"
        folder = "/home/carma/dati/intra/"
    else:
        dire = "C:\\Users\\fesposti\\Box Sync\\Simulatore\\intra\\isin.conf"
        folder = "C:\\intra\\"
    isin_conf = read_csv_files(dire)
    form = FormTakeSingolo(request=request, isin_conf=isin_conf)
    return render(request, 'simulatore/form_singolo.html', {'form': form})


# view che apre il div del dettaglio singola simulazione. Passa come parametro request
def dettagli_simulazione(request):
    print(request)
    dettagli_tappeto = [x for x in request.POST.get('tappeto') if x.take == request.POST.get('take')]
    return render(request, 'simulatore/dettagli_simulazione.html', {'dettagli_tappeto': dettagli_tappeto})


# line_profiler
def index(request):
    version = '1.03.06'
    if settings.SERVER_DEV is False:
        dire = "/home/carma/dati/isin.conf"
        folder = "/home/carma/dati/intra/"
    else:
        dire = "C:\\Users\\fesposti\\Box Sync\\Simulatore\\intra\\isin.conf"
        folder = "C:\\intra\\"
    isin_conf = read_csv_files(dire)
    # se method = POST --> c'è una richiesta di creazione del tappeto o simulazione del tappeto
    if request.method == "POST":
        #
        # creo tutti i tappeti per la simulazione
        isin = ''
        ticker = False
        simulazione = GeneraSimulazione(request, isin, ticker)
        #
        # creo il numpy array per la simulazione
        tappeto, pacchi_numpy = simulazione.creazione_array()
        #
        # pacchi_numpy.dtype.names('tappeto', 'pacco', 'stato', 'prezzo_acquisto', 'prezzo_vendita')
        if request.POST.get('bottone') == 'simula':
            start_time = datetime.datetime.today()
            #
            # effettuo la simulazione
            tappeto, pacchi_numpy = simulazione.simula(tappeto, pacchi_numpy, folder)
            #
            # dividere per 1 milione per avere i secondi
            time = datetime.datetime.today() - start_time
            #
            # calcolo e memorizzo le statistiche
            simsingolamax, take_array, take_array_size = simulazione.genera_statistiche(request, tappeto, time)
            #
        # context è un dizionario che associa variabili del template a oggetti python
        if request.POST.get('bottone') == 'simula':
            best_take = simsingolamax.take
        else:
            best_take = ''
            take_array = []
            take_array_size = 0
        request.session['isin'] = simulazione.crea_isin
        request.session['data_inizio'] = datetime.datetime.strftime(simulazione.data_inizio_2, "%d/%m/%Y")
        request.session['data_fine'] = datetime.datetime.strftime(simulazione.data_fine_2, "%d/%m/%Y")
        request.session['limite_inferiore'] = simulazione.crea_limite_inferiore
        request.session['limite_superiore'] = simulazione.crea_limite_superiore
        request.session['primo_acquisto'] = simulazione.crea_primo_acquisto
        request.session['in_carico'] = simulazione.crea_in_carico_2
        request.session['step'] = simulazione.crea_step
        request.session['take_inizio'] = simulazione.crea_take_inizio_2
        request.session['take_fine'] = simulazione.crea_take_fine
        request.session['take_incremento'] = simulazione.crea_take_incremento
        request.session['quantita_acquisto'] = simulazione.crea_quantita_acquisto
        request.session['quantita_vendita'] = simulazione.crea_quantita_vendita
        request.session['tipo_commissione'] = simulazione.tipo_commissione
        request.session['commissione'] = simulazione.commissione
        request.session['min_commissione'] = simulazione.min_commissione
        request.session['max_commissione'] = simulazione.max_commissione
        form_s = FormTakeSingolo(request=request, isin_conf=isin_conf)
        form_v = FormTakeVariabile(request=request, isin_conf=isin_conf)
        context = {
            'bottone': request.POST.get('bottone'),
            'tipo_take': request.POST.get('tipo_take'),
            'tappeto': tappeto,
            'data_inizio': datetime.datetime.strftime(simulazione.data_inizio_2, "%d/%m/%Y"),
            'data_fine': datetime.datetime.strftime(simulazione.data_fine_2, "%d/%m/%Y"),
            'data_inizio_2': datetime.datetime.strftime(simulazione.data_inizio_2, "%d/%m/%Y"),
            'data_fine_2': datetime.datetime.strftime(simulazione.data_fine_2, "%d/%m/%Y"),
            'isin_conf': isin_conf,
            'isin': simulazione.crea_isin,
            'primo_tappeto': tappeto[0],
            'mostra_risultati': '',
            'take_inizio': simulazione.crea_take_inizio_2,
            'take_fine': simulazione.crea_take_fine,
            'take_incremento': simulazione.crea_take_incremento,
            'tipo_commissione': simulazione.tipo_commissione,
            'take_array': take_array,
            'take_array_size': take_array_size,
            'data_oggi': datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y"),
            'data_max': datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15),
                                                   "%d/%m/%Y"),
            'check': simulazione.check,
            'check2': simulazione.check2,
            'best_take': best_take,
            'version': version,
            'form_singolo': form_s,
            'form_variabile': form_v
        }
    else:
        prova = 'Ciao stronzo'
        mostra_risultati = 'hidden'
        form_s = FormTakeSingolo(request=request, isin_conf=isin_conf)
        form_v = FormTakeVariabile(request=request, isin_conf=isin_conf)
        # context è un dizionario che associa variabili del template a oggetti python
        context = {
            'prova': prova,
            'isin_conf': isin_conf,
            'mostra_risultati': mostra_risultati,
            'server_remoto': settings.DEBUG,
            'dire': dire,
            'data_oggi': datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y"),
            'data_max': datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15), "%d/%m/%Y"),
            'version': version,
            'form_singolo': form_s,
            'form_variabile': form_v
        }
    return render(request, 'simulatore/index.html', context)
