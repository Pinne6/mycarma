# Create your views here.

"""
1.00.06 - 01/11/2016
- tutte le pagine di login e registrazione senza il modal per essere compatibili con mobile
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


def dettagli_simulazione(request):
    print(request)
    dettagli_tappeto = [x for x in request.POST.get('tappeto') if x.take == request.POST.get('take')]
    return render(request, 'simulatore/dettagli_simulazione.html', {'dettagli_tappeto': dettagli_tappeto})


# line_profiler
def index(request):
    version = '1.00.04'
    if settings.SERVER_DEV is False:
        dire = "/home/carma/dati/isin.conf"
    else:
        dire = "C:\\Users\\fesposti\\Box Sync\\Simulatore\\intra\\isin.conf"
    isin_conf = []
    if os.path.exists(dire):
        with open(dire) as f:
            for line in f:
                line = line.split("|")
                isin_conf.append(line)
    if request.method == "POST":
        start_time = datetime.datetime.today()
        if settings.SERVER_DEV is False:
            folder = "/home/carma/dati/intra/"
        else:
            folder = "C:\\intra\\"
        crea_isin = request.POST.get('isin')
        crea_limite_inferiore = float(request.POST.get('crea_limite_inferiore'))
        crea_limite_superiore = float(request.POST.get('crea_limite_superiore'))
        crea_step = float(request.POST.get('step'))
        crea_quantita_acquisto = float(request.POST.get('quantita_acquisto'))
        crea_quantita_vendita = float(request.POST.get('quantita_vendita'))
        crea_primo_acquisto = float(request.POST.get('primo_acquisto'))
        crea_checkFX = True
        if request.POST.get('tipo_take') == 'take_singolo':
            crea_take_inizio = float(request.POST.get('take'))
            crea_take_fine = crea_take_inizio
            crea_take_incremento = 1
        elif request.POST.get('tipo_take') == 'take_variabile':
            crea_take_inizio = float(request.POST.get('take_inizio'))
            crea_take_fine = float(request.POST.get('take_fine'))
            crea_take_incremento = float(request.POST.get('take_incremento'))
        crea_in_carico = int(request.POST.get('in_carico'))
        crea_take_inizio_2 = crea_take_inizio
        crea_in_carico_2 = crea_in_carico
        tick = 4
        tipo_tappeto = ''
        percentuale_incrementale = 0
        tipo_steptake = 0
        tipo_commissione = request.POST.get('commissioni_tipo')
        commissione = float(request.POST.get('commissioni_importo'))
        min_commissione = float(request.POST.get('commissioni_min'))
        max_commissione = float(request.POST.get('commissioni_max'))
        data_inizio = request.POST.get('crea_data_inizio').split('/')
        data_inizio = datetime.date(int(data_inizio[2]), int(data_inizio[1]), int(data_inizio[0]))
        data_fine = request.POST.get('crea_data_fine').split('/')
        data_fine = datetime.date(int(data_fine[2]), int(data_fine[1]), int(data_fine[0]))
        data_inizio_2 = data_inizio
        data_fine_2 = data_fine
        tappeto = []
        storico = []
        take_array = []
        take_array_size = 0
        check = round(round((crea_primo_acquisto - crea_limite_inferiore), tick) / crea_step, tick)
        check2 = round(round((crea_limite_superiore - crea_limite_inferiore), tick) / crea_step, tick)
        # controlli per verificare che i parametri abbiano senso
        if not check.is_integer():
            # se il primo acquisto non è multiplo dello step, arrotondo alla cifra inferiore
            crea_primo_acquisto = round((((crea_primo_acquisto - crea_limite_inferiore) // crea_step) * crea_step) +
                                        crea_limite_inferiore, tick)
            check = 'Yes'
        if not check2.is_integer():
            crea_limite_superiore = round((((crea_limite_superiore - crea_limite_inferiore) // crea_step) * crea_step) +
                                          crea_limite_inferiore, tick)
            check2 = 'Yes'
        dt = np.dtype('int,int,int,float,float')
        while_counter = 1
        while crea_take_inizio <= (crea_take_fine + 0.0001):
            tappeto_singolo = Tappeto(crea_isin, crea_limite_inferiore, crea_limite_superiore,
                                      crea_step, crea_take_inizio, crea_quantita_acquisto,
                                      crea_quantita_vendita, crea_primo_acquisto, crea_checkFX, tick,
                                      tipo_tappeto, percentuale_incrementale, tipo_steptake,
                                      tipo_commissione, commissione, min_commissione,
                                      max_commissione, crea_in_carico, while_counter)
            tappeto.append(tappeto_singolo)
            if while_counter == 1:
                pacchi_numpy = np.array(tappeto_singolo.numpy, dtype=dt)
            else:
                pacchi_numpy = np.concatenate((pacchi_numpy, tappeto_singolo.numpy))
            crea_take_inizio += crea_take_incremento
            while_counter += 1
        # pacchi_numpy.dtype.names('tappeto', 'pacco', 'stato', 'prezzo_acquisto', 'prezzo_vendita')
        if request.POST.get('bottone') == 'simula':
            data_diff = data_fine - data_inizio
            # per ogni tappeto creo lo storico vuoto di ogni data
            for c in range(0, len(tappeto), +1):
                data_ciclo = data_inizio
                for i in range(data_diff.days + 1):
                    tappeto[c].storico.append(Storico(data_ciclo))
                    data_ciclo += datetime.timedelta(days=1)
            # per ogni data cerco il file del tick by tick
            for i in range(data_diff.days + 1):
                if settings.SERVER_DEV is False:
                    filename = folder + crea_isin + "/" + data_inizio.strftime("%Y%m%d") + ".csv"
                else:
                    filename = folder + crea_isin + "\\" + data_inizio.strftime("%Y%m%d") + ".csv"
                intra = []
                # now1 = datetime.datetime.today()
                if os.path.exists(filename):
                    with open(filename) as f:
                        for line in f:
                            line = line.split("|")
                            intra.append(line)
                    storico.append(Storico(data_inizio))
                    # print(datetime.datetime.today() - now1)
                else:
                    data_inizio += datetime.timedelta(days=1)
                    continue
                ultimo_prezzo = 0
                # print(filename)
                # per ogni file giornaliero ciclo tra tutti i prezzi
                for a in range(len(intra) - 1, 0, -1):
                    if intra[a][1] == '':
                        continue
                    prezzo = float(intra[a][1])
                    data = data_inizio
                    ora = intra[a][0]
                    # print(prezzo)
                    if prezzo == ultimo_prezzo:
                        continue
                    ultimo_prezzo = prezzo
                    # se il prezzo è diverso dall'ultimo prezzo allora ciclo tra tutti i tappeti
                    # per eseguire operazione
                    # ciclo tra tutti i tappeti
                    # cerco dentro il dataframe dove stato = ACQAZ o VENAZ e prezzo
                    lis_a = np.flatnonzero(np.logical_and(pacchi_numpy['f2'] == 0, pacchi_numpy['f3'] >= prezzo))
                    lis_b = np.flatnonzero(np.logical_and(pacchi_numpy['f2'] == 1, pacchi_numpy['f4'] <= prezzo))
                    for item in lis_a:
                        pacchi_numpy[item]['f2'] = 1
                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                            prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, storico)
                    for item in lis_b:
                        pacchi_numpy[item]['f2'] = 0
                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                            prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, storico)
                data_inizio += datetime.timedelta(days=1)
            # dividere per 1 milione per avere i secondi
            time = datetime.datetime.today() - start_time
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')  # Real IP address of client Machine
            if not hasattr(request.POST, 'user'):
                user_id = User.objects.get(username='Anonymous')
            else:
                user_id = request.user
            n = SimulazioneStatistiche.objects.create(durata=time, user_id=user_id, indirizzo_ip=ip,
                                                      isin=crea_isin,
                                                      limite_inferiore=crea_limite_inferiore,
                                                      limite_superiore=crea_limite_superiore, step=crea_step,
                                                      quantita_acquisto=crea_quantita_acquisto,
                                                      quantita_vendita=crea_quantita_vendita,
                                                      primo_acquisto=crea_primo_acquisto,
                                                      take_inizio=crea_take_inizio_2,
                                                      take_fine=crea_take_fine,
                                                      take_incremento=crea_take_incremento,
                                                      in_carico=crea_in_carico,
                                                      tipo_commissione=tipo_commissione, commissione=commissione,
                                                      min_commissione=min_commissione,
                                                      max_commissione=max_commissione)
            n.salvare()
            # per ogni tappeto creo le statistiche andando a vedere i pacchi eseguiti
            for count, item in enumerate(tappeto):
                item.nr_acquisti = sum(pack.nr_acquisti for pack in item.pacchi)
                item.nr_vendite = sum(pack.nr_vendite for pack in item.pacchi)
                item.gain = round(sum(pack.gain for pack in item.pacchi), 2)
                item.commissioni = round(sum(pack.commissioni for pack in item.pacchi), 2)
                item.profitto = round(item.gain - item.commissioni, 2)
                if item.valore_max == 0:
                    item.rendimento = 0
                else:
                    item.rendimento = round(((item.gain - item.commissioni) / item.valore_max) * 100, 2)
                # print(
                #     "Take: " + str(item.take) + " Acquisti: " + str(item.nr_acquisti) + " Vendite: " + str(
                #         item.nr_vendite) + " Gain: " +
                #     str(item.gain) + " Profitto: " + str(item.profitto) + " Valore max: " + str(item.valore_max) +
                #     " Rendimento: " + str(item.rendimento))
                # se è il primo giro, inizializzo la simulazione migliore e peggiore al valore attuale
                # a [0] metto il numero tappeto della simulazione migliore, a [1] quello peggiore
                if count == 0:
                    rendimento_max = item.rendimento
                    rendimento_min = item.rendimento
                    classifica_rendimenti = [count, count]
                    continue
                if item.rendimento > rendimento_max:
                    rendimento_max = item.rendimento
                    classifica_rendimenti[0] = count
                elif item.rendimento < rendimento_min:
                    rendimento_min = item.rendimento
                    classifica_rendimenti[1] = count
            simsingolamin = SimulazioneSingola(simulazione=n, isin=tappeto[classifica_rendimenti[1]].isin,
                                               limite_inferiore=tappeto[classifica_rendimenti[1]].limite_inferiore,
                                               limite_superiore=tappeto[classifica_rendimenti[1]].limite_superiore,
                                               step=tappeto[classifica_rendimenti[1]].step,
                                               quantita_acquisto=tappeto[
                                                   classifica_rendimenti[1]].quantita_acquisto,
                                               quantita_vendita=tappeto[classifica_rendimenti[1]].quantita_vendita,
                                               primo_acquisto=tappeto[classifica_rendimenti[1]].primo_acquisto,
                                               take=tappeto[classifica_rendimenti[1]].take,
                                               in_carico=tappeto[classifica_rendimenti[1]].in_carico,
                                               tipo_commissione=tappeto[classifica_rendimenti[1]].tipo_commissione,
                                               commissione=tappeto[classifica_rendimenti[1]].commissione,
                                               min_commissione=tappeto[classifica_rendimenti[1]].min_commissione,
                                               max_commissione=tappeto[classifica_rendimenti[1]].max_commissione,
                                               nr_acquisti=tappeto[classifica_rendimenti[1]].nr_acquisti,
                                               nr_vendite=tappeto[classifica_rendimenti[1]].nr_vendite,
                                               gain=tappeto[classifica_rendimenti[1]].gain,
                                               commissioni=tappeto[classifica_rendimenti[1]].commissioni,
                                               profitto=tappeto[classifica_rendimenti[1]].profitto,
                                               valore_attuale=tappeto[classifica_rendimenti[1]].valore_attuale,
                                               valore_carico=tappeto[classifica_rendimenti[1]].valore_carico,
                                               valore_min=tappeto[classifica_rendimenti[1]].valore_min,
                                               valore_max=tappeto[classifica_rendimenti[1]].valore_max,
                                               quantita_totale=tappeto[classifica_rendimenti[1]].quantita_totale,
                                               rendimento=tappeto[classifica_rendimenti[1]].rendimento,
                                               rendimento_teorico=tappeto[
                                                   classifica_rendimenti[1]].rendimento_teorico)
            simsingolamax = SimulazioneSingola(simulazione=n, isin=tappeto[classifica_rendimenti[0]].isin,
                                               limite_inferiore=tappeto[classifica_rendimenti[0]].limite_inferiore,
                                               limite_superiore=tappeto[classifica_rendimenti[0]].limite_superiore,
                                               step=tappeto[classifica_rendimenti[0]].step,
                                               quantita_acquisto=tappeto[
                                                   classifica_rendimenti[0]].quantita_acquisto,
                                               quantita_vendita=tappeto[classifica_rendimenti[0]].quantita_vendita,
                                               primo_acquisto=tappeto[classifica_rendimenti[0]].primo_acquisto,
                                               take=tappeto[classifica_rendimenti[0]].take,
                                               in_carico=tappeto[classifica_rendimenti[0]].in_carico,
                                               tipo_commissione=tappeto[classifica_rendimenti[0]].tipo_commissione,
                                               commissione=tappeto[classifica_rendimenti[0]].commissione,
                                               min_commissione=tappeto[classifica_rendimenti[0]].min_commissione,
                                               max_commissione=tappeto[classifica_rendimenti[0]].max_commissione,
                                               nr_acquisti=tappeto[classifica_rendimenti[0]].nr_acquisti,
                                               nr_vendite=tappeto[classifica_rendimenti[0]].nr_vendite,
                                               gain=tappeto[classifica_rendimenti[0]].gain,
                                               commissioni=tappeto[classifica_rendimenti[0]].commissioni,
                                               profitto=tappeto[classifica_rendimenti[0]].profitto,
                                               valore_attuale=tappeto[classifica_rendimenti[0]].valore_attuale,
                                               valore_carico=tappeto[classifica_rendimenti[0]].valore_carico,
                                               valore_min=tappeto[classifica_rendimenti[0]].valore_min,
                                               valore_max=tappeto[classifica_rendimenti[0]].valore_max,
                                               quantita_totale=tappeto[classifica_rendimenti[0]].quantita_totale,
                                               rendimento=tappeto[classifica_rendimenti[0]].rendimento,
                                               rendimento_teorico=tappeto[
                                                   classifica_rendimenti[0]].rendimento_teorico)
            SimulazioneSingola.objects.bulk_create([simsingolamax, simsingolamin])
            # transaction.set_autocommit(False)
            # SimulazioneSingola.objects.bulk_create(tappeti)
            # transaction.commit()
            # transaction.set_autocommit(True)
            data_inizio = data_inizio_2
            """
            for sto in storico:
                if sto.data == data_inizio and len(take_data) > 0:
                    if take_data[0][2] < (sto.gain - sto.commissioni):
                        take_data.append((data_inizio, item.take, sto.gain - sto.commissioni))
                        data_inizio += datetime.timedelta(days=1)
                elif sto.data == data_inizio and len(take_data) == 0:
                    take_data.append((data_inizio, item.take, sto.gain - sto.commissioni))
                    data_inizio += datetime.timedelta(days=1)
                """
            i = 0
            for item in tappeto:
                lista = [sto.profitto for sto in item.storico]
                # print(lista)
                if i == 0:
                    dt = np.dtype('float')
                    xarr = np.array(lista, dtype=dt)
                else:
                    xarr = np.vstack((xarr, np.array(lista)))
                i += 1
            xarr.round(4)
            # print(xarr)
            # maxi = np.amax(xarr, axis=0)
            maxi_index = np.argmax(xarr, axis=0)
            # print(maxi)
            if maxi_index.size > 1:
                for item in maxi_index:
                    take_array.append(tappeto[item].take)
                    take_array_size = 1
            else:
                take_array = maxi_index
                take_array_size = 0
            # print(take_array)
            # time = datetime.datetime.today() - start_time
            # print(time)
        # context è un dizionario che associa variabili del template a oggetti python
        if request.POST.get('bottone') == 'simula':
            best_take = simsingolamax.take
        else:
            best_take = ''
        request.session['isin'] = crea_isin
        request.session['data_inizio'] = datetime.datetime.strftime(data_inizio_2, "%d/%m/%Y")
        request.session['data_fine'] = datetime.datetime.strftime(data_fine_2, "%d/%m/%Y")
        request.session['limite_inferiore'] = crea_limite_inferiore
        request.session['limite_superiore'] = crea_limite_superiore
        request.session['primo_acquisto'] = crea_primo_acquisto
        request.session['in_carico'] = crea_in_carico_2
        request.session['step'] = crea_step
        request.session['take_inizio'] = crea_take_inizio_2
        request.session['take_fine'] = crea_take_fine
        request.session['take_incremento'] = crea_take_incremento
        request.session['quantita_acquisto'] = crea_quantita_acquisto
        request.session['quantita_vendita'] = crea_quantita_vendita
        request.session['tipo_commissione'] = tipo_commissione
        request.session['commissione'] = commissione
        request.session['min_commissione'] = min_commissione
        request.session['max_commissione'] = max_commissione
        context = {
            'bottone': request.POST.get('bottone'),
            'tipo_take': request.POST.get('tipo_take'),
            'tappeto': tappeto,
            'data_inizio': datetime.datetime.strftime(data_inizio_2, "%d/%m/%Y"),
            'data_fine': datetime.datetime.strftime(data_fine_2, "%d/%m/%Y"),
            'data_inizio_2': datetime.datetime.strftime(data_inizio_2, "%d/%m/%Y"),
            'data_fine_2': datetime.datetime.strftime(data_fine_2, "%d/%m/%Y"),
            'isin_conf': isin_conf,
            'isin': crea_isin,
            'primo_tappeto': tappeto[0],
            'mostra_risultati': '',
            'take_inizio': crea_take_inizio_2,
            'take_fine': crea_take_fine,
            'take_incremento': crea_take_incremento,
            'tipo_commissione': tipo_commissione,
            'take_array': take_array,
            'take_array_size': take_array_size,
            'data_oggi': datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y"),
            'data_max': datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15),
                                                   "%d/%m/%Y"),
            'check': check,
            'check2': check2,
            'best_take': best_take,
            'version': version
        }
    else:
        prova = 'Ciao stronzo'
        mostra_risultati = 'hidden'
        # context è un dizionario che associa variabili del template a oggetti python
        context = {
            'prova': prova,
            'isin_conf': isin_conf,
            'mostra_risultati': mostra_risultati,
            'server_remoto': settings.DEBUG,
            'dire': dire,
            'data_oggi': datetime.datetime.strftime(datetime.date.today(), "%d/%m/%Y"),
            'data_max': datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=15), "%d/%m/%Y"),
            'version': version
        }
    return render(request, 'simulatore/index.html', context)
