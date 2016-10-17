# Create your views here.

"""
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

version = '0.04.00'


def index(request):
    if settings.SERVER_REMOTO:
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
        prova = 'Ciao POST'
        start_time = datetime.datetime.today()
        if settings.SERVER_REMOTO:
            folder = "/home/carma/dati/intra/"
        else:
            folder = "C:\\Users\\fesposti\\Downloads\\dati agosto\\"
        crea_isin = request.POST.get('isin')
        print(prova)
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
        tick = 4
        tipo_tappeto = ''
        percentuale_incrementale = 0
        tipo_steptake = 0
        tipo_commissione = request.POST.get('commissioni_tipo')
        commissione = float(request.POST.get('commissioni_importo'))
        min_commissione = float(request.POST.get('commissioni_min'))
        max_commissione = float(request.POST.get('commissioni_max'))
        data_inizio = request.POST.get('crea_data_inizio').split('-')
        data_inizio = datetime.date(int(data_inizio[0]), int(data_inizio[1]), int(data_inizio[2]))
        data_fine = request.POST.get('crea_data_fine').split('-')
        data_fine = datetime.date(int(data_fine[0]), int(data_fine[1]), int(data_fine[2]))
        data_inizio_2 = data_inizio
        data_fine_2 = data_fine
        tappeto = []
        storico = []
        take_array = []
        while crea_take_inizio <= (crea_take_fine + 0.0001):
            tappeto_singolo = Tappeto(crea_isin, crea_limite_inferiore, crea_limite_superiore,
                                                         crea_step, crea_take_inizio, crea_quantita_acquisto,
                                                         crea_quantita_vendita, crea_primo_acquisto, crea_checkFX, tick,
                                                         tipo_tappeto, percentuale_incrementale, tipo_steptake,
                                                         tipo_commissione, commissione, min_commissione,
                                                         max_commissione, crea_in_carico)
            tappeto.append(tappeto_singolo)
            crea_take_inizio += crea_take_incremento
        if request.POST.get('bottone') == 'simula':
            take_migliore_data = []
            data_diff = data_fine - data_inizio
            # per ogni data cerco il file del tick by tick
            for c in range(0, len(tappeto), +1):
                data_ciclo = data_inizio
                for i in range(data_diff.days + 1):
                    tappeto[c].storico.append(Storico(data_ciclo))
                    data_ciclo += datetime.timedelta(days=1)
            for i in range(data_diff.days + 1):
                filename = folder + crea_isin + "\\" + data_inizio.strftime("%Y%m%d") + ".csv"
                intra = []
                if os.path.exists(filename):
                    with open(filename) as f:
                        for line in f:
                            line = line.split("|")
                            intra.append(line)
                storico.append(Storico(data_inizio))
                ultimo_prezzo = 0
                # print(filename)
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
                    for c in range(0, len(tappeto), +1):
                        for b in range(0, len(tappeto[c].pacchi), +1):
                            if tappeto[c].pacchi[b].order_type == "ACQAZ" and tappeto[c].pacchi[b].buy_price >= prezzo:
                                tappeto[c].pacchi[b].acquisto(prezzo, tappeto[c], data, ora, storico)
                                # print("Eseguito acquisto a " + str(prezzo))
                            elif tappeto[c].pacchi[b].order_type == "VENAZ" and tappeto[c].pacchi[b].sell_price <= prezzo:
                                tappeto[c].pacchi[b].vendita(prezzo, tappeto[c], data, ora, storico)
                                # print("Eseguito vendita a " + str(prezzo))
                data_inizio += datetime.timedelta(days=1)
                take_data = []
            for item in tappeto:
                item.nr_acquisti = sum(pack.nr_acquisti for pack in item.pacchi)
                item.nr_vendite = sum(pack.nr_vendite for pack in item.pacchi)
                item.gain = sum(pack.gain for pack in item.pacchi)
                item.commissioni = sum(pack.commissioni for pack in item.pacchi)
                item.profitto = item.gain - item.commissioni
                print(
                    "Take: " + str(item.take) + " Acquisti: " + str(item.nr_acquisti) + " Vendite: " + str(item.nr_vendite) + " Gain: " +
                    str(item.gain) + " Profitto: " + str(item.profitto))
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
                print(lista)
                if i == 0:
                    dt = np.dtype('float')
                    xarr = np.array(lista, dtype=dt)
                else:
                    xarr = np.vstack((xarr, np.array(lista)))
                i += 1
            xarr.round(4)
            print(xarr)
            maxi = np.amax(xarr, axis=0)
            maxi_index = np.argmax(xarr, axis=0)
            print(maxi)
            for item in maxi_index:
                take_array.append(tappeto[item].take)
            print(take_array)

                # for Operazione in Tappeto.operazioni:
                #     print(str(Operazione.data) + " " + str(Operazione.ora) + " " + str(Operazione.prezzo) + " " + str(Operazione.gain))
            time = datetime.datetime.today() - start_time
            print(time)
        # context è un dizionario che associa variabili del template a oggetti python
        context = {
            'bottone': request.POST.get('bottone'),
            'tipo_take': request.POST.get('tipo_take'),
            'tappeto': tappeto,
            'data_inizio': datetime.datetime.strftime(data_inizio_2, "%d/%m/%Y"),
            'data_fine': datetime.datetime.strftime(data_fine_2, "%d/%m/%Y"),
            'data_inizio_2': datetime.datetime.strftime(data_inizio_2, "%Y-%m-%d"),
            'data_fine_2': datetime.datetime.strftime(data_fine_2, "%Y-%m-%d"),
            'isin_conf': isin_conf,
            'isin': crea_isin,
            'primo_tappeto': tappeto[0],
            'mostra_risultati': '',
            'take_inizio': crea_take_inizio_2,
            'take_fine': crea_take_fine,
            'take_incremento': crea_take_incremento,
            'tipo_commissione': tipo_commissione,
            'take_array': take_array
        }
    else:
        prova = 'Ciao stronzo'
        mostra_risultati = 'hidden'
        # context è un dizionario che associa variabili del template a oggetti python
        context = {
            'prova': prova,
            'isin_conf': isin_conf,
            'mostra_risultati': mostra_risultati
        }
    return render(request, 'simulatore/index.html', context)

