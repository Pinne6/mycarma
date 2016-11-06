from django.db import models
from django.contrib.auth.models import User
import django.utils
import numpy as np
import datetime
from django.conf import settings
import os.path

# Create your models here.


class UserPerm(models.Model):
    class Meta:
        permissions = (
            ("take_fisso", "Può simulare senza limiti a take fisso"),
            ("take_variabile", "Può simulare senza limiti a take variabile"),
        )


class SimulazioneStatistiche(models.Model):
    data_ora = models.DateTimeField(default=django.utils.timezone.now)
    durata = models.DurationField()
    user_id = models.ForeignKey(User)
    indirizzo_ip = models.GenericIPAddressField()
    isin = models.CharField(max_length=15)
    limite_inferiore = models.DecimalField(max_digits=15, decimal_places=5)
    limite_superiore = models.DecimalField(max_digits=15, decimal_places=5)
    step = models.DecimalField(max_digits=15, decimal_places=5)
    quantita_acquisto = models.IntegerField()
    quantita_vendita = models.IntegerField()
    primo_acquisto = models.DecimalField(max_digits=15, decimal_places=5)
    take_inizio = models.DecimalField(max_digits=15, decimal_places=5)
    take_fine = models.DecimalField(max_digits=15, decimal_places=5)
    take_incremento = models.DecimalField(max_digits=15, decimal_places=5)
    in_carico = models.IntegerField()
    tipo_commissione = models.CharField(max_length=1)
    commissione = models.DecimalField(max_digits=15, decimal_places=5)
    min_commissione = models.DecimalField(max_digits=15, decimal_places=5)
    max_commissione = models.DecimalField(max_digits=15, decimal_places=5)

    def salvare(self):
        self.save()


class SimulazioneSingola(models.Model):
    simulazione = models.ForeignKey('SimulazioneStatistiche', on_delete=models.CASCADE)
    isin = models.CharField(max_length=15)
    limite_inferiore = models.DecimalField(max_digits=15, decimal_places=5)
    limite_superiore = models.DecimalField(max_digits=15, decimal_places=5)
    step = models.DecimalField(max_digits=15, decimal_places=5)
    quantita_acquisto = models.IntegerField()
    quantita_vendita = models.IntegerField()
    primo_acquisto = models.DecimalField(max_digits=15, decimal_places=5)
    take = models.DecimalField(max_digits=15, decimal_places=5)
    in_carico = models.IntegerField()
    tipo_commissione = models.CharField(max_length=1)
    commissione = models.DecimalField(max_digits=15, decimal_places=5)
    min_commissione = models.DecimalField(max_digits=15, decimal_places=5)
    max_commissione = models.DecimalField(max_digits=15, decimal_places=5)
    nr_acquisti = models.IntegerField()
    nr_vendite = models.IntegerField()
    gain = models.DecimalField(max_digits=10, decimal_places=2)
    commissioni = models.DecimalField(max_digits=10, decimal_places=2)
    profitto = models.DecimalField(max_digits=10, decimal_places=2)
    valore_attuale = models.DecimalField(max_digits=10, decimal_places=2)
    valore_carico = models.DecimalField(max_digits=10, decimal_places=2)
    valore_min = models.DecimalField(max_digits=10, decimal_places=2)
    valore_max = models.DecimalField(max_digits=10, decimal_places=2)
    quantita_totale = models.DecimalField(max_digits=10, decimal_places=2)
    rendimento = models.DecimalField(max_digits=10, decimal_places=2)
    rendimento_teorico = models.DecimalField(max_digits=10, decimal_places=2)
    # checkFX = models.IntegerField()
    # tick = models.IntegerField()
    # tipo_tappetino = models.CharField(max_length=1)
    # percentuale_incrementale = models.DecimalField(max_digits=15, decimal_places=5)
    # tipo_steptake = models.CharField(max_length=1)

    def salvare(self):
        self.save()


class Pacco:
    def __init__(self, package_number, ticker, order_type, buy_price, sell_price, take, quantity_buy, quantity_sell,
                 adj, carica):
        self.package_number = package_number
        self.ticker = ticker
        self.order_type = order_type
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.take = take
        self.quantity_buy = quantity_buy
        self.quantity_sell = quantity_sell
        self.adj = adj
        self.nr_acquisti = 0
        self.nr_vendite = 0
        self.gain = 0
        self.commissioni = 0
        self.profitto = 0
        self.operazioni = []
        self.incremento = 0
        self.incremento_acquistato = 0
        self.buy_price_real = buy_price
        self.sell_price_real = sell_price
        self.carica = carica

    def acquisto(self, prezzo, tappeto, data, ora, storico):
        self.nr_acquisti += 1
        self.buy_price_real = prezzo
        if self.carica == 1:
            gain = (self.sell_price_real * self.quantity_sell) - (self.buy_price_real * self.quantity_buy)
            self.gain += gain
            storico[len(storico) - 1].gain += gain
        else:
            gain = 0
        commissione = self.calcola_commissioni(self.quantity_buy, prezzo, tappeto)
        self.commissioni += commissione
        tappeto.operazioni.append(Operazione(self.order_type, data, ora, prezzo, self.quantity_buy, gain, commissione,
                                             self.buy_price))
        tappeto.operazione(self.order_type, data, ora, prezzo, self.quantity_buy, gain, commissione, self.carica)
        # if data in storico:
        #    i = storico.index(data)
        #    storico[i].acquisti += 1
        #    storico[i].commissioni += commissione
        # [item.nr_acquisti + 1 for item in tappeto.storico if item.data == data]
        for item in tappeto.storico:
            if item.data == data:
                item.nr_acquisti += 1
                item.commissioni += commissione
                item.profitto += (gain - commissione)
                break
        storico[len(storico) - 1].nr_acquisti += 1
        storico[len(storico) - 1].commissioni += commissione
        storico[len(storico) - 1].profitto += (gain - commissione)
        self.order_type = "VENAZ"
        if self.carica == 1:
            self.carica = 0
            self.order_type = "VENAZ_S"
        else:
            self.carica = 1
            self.order_type = "VENAZ_L"
        return storico

    def vendita(self, prezzo, tappeto, data, ora, storico):
        self.nr_vendite += 1
        self.sell_price_real = prezzo
        if self.carica == 1:
            gain = (prezzo * self.quantity_sell) - (self.buy_price_real * self.quantity_buy)
            self.gain += gain
            storico[len(storico) - 1].gain += gain
        else:
            gain = 0
        commissione = self.calcola_commissioni(self.quantity_sell, prezzo, tappeto)
        self.commissioni += commissione
        tappeto.operazioni.append(Operazione(self.order_type, data, ora, prezzo, self.quantity_sell, gain, commissione,
                                             self.sell_price))
        tappeto.operazione(self.order_type, data, ora, prezzo, self.quantity_sell, gain, commissione, self.carica)
        for item in tappeto.storico:
            if item.data == data:
                item.nr_vendite += 1
                item.commissioni += commissione
                item.profitto += (gain - commissione)
                break
        storico[len(storico) - 1].nr_vendite += 1
        storico[len(storico) - 1].commissioni += commissione
        storico[len(storico) - 1].profitto += (gain - commissione)
        self.order_type = "ACQAZ"
        if self.carica == 1:
            self.carica = 0
            self.order_type = "ACQAZ_L"
        else:
            self.carica = 1
            self.order_type = "ACQAZ_S"
        return storico

    @staticmethod
    def calcola_commissioni(quantita, prezzo, tappeto):
        if tappeto.tipo_commissione == 'P':
            p = (prezzo * quantita * tappeto.commissione) / 100
            if p < tappeto.min_commissione:
                p = tappeto.min_commissione
            if p > tappeto.max_commissione:
                p = tappeto.max_commissione
            return p
        else:
            return round(tappeto.commissione, 4)


class Operazione:
    def __init__(self, tipo, data, ora, prezzo, quantita, gain, commissioni, prezzo_teorico):
        self.data = data
        self.ora = ora
        self.tipo = tipo
        self.prezzo = prezzo
        self.quantita = quantita
        self.gain = gain
        self.commissioni = commissioni
        self.profitto = gain - commissioni
        self.prezzo_teorico = prezzo_teorico


class Storico:
    def __init__(self, data):
        self.data = data
        self.valore = 0
        self.quantita = 0
        self.nr_acquisti = 0
        self.nr_vendite = 0
        self.gain = 0
        self.commissioni = 0
        self.profitto = 0

    def reset(self):
        self.valore = 0
        self.quantita = 0
        self.nr_acquisti = 0
        self.nr_vendite = 0
        self.gain = 0
        self.commissioni = 0
        self.profitto = 0
        return


class Tappeto:
    isin = ''
    limite_inferiore = 0
    limite_superiore = 0
    step = 0
    take = 0

    def __init__(self, crea_isin, crea_limite_inferiore, crea_limite_superiore, crea_step, crea_take,
                 crea_quantita_acquisto, crea_quantita_vendita, crea_primo_acquisto, crea_checkFX, tick, tipo_tappeto,
                 percentuale_incrementale, tipo_steptake, tipo_commissione, commissione, min_commissione,
                 max_commissione, in_carico, while_counter):
        self.isin = crea_isin
        self.limite_inferiore = round(crea_limite_inferiore, tick)
        self.limite_superiore = round(crea_limite_superiore, tick)
        self.step = round(crea_step, tick)
        self.take = round(crea_take, tick)
        self.quantita_acquisto = round(crea_quantita_acquisto, tick)
        self.quantita_vendita = round(crea_quantita_vendita, tick)
        self.primo_acquisto = round(crea_primo_acquisto, tick)
        self.checkFX = crea_checkFX
        self.tick = tick
        self.tipo_tappetino = tipo_tappeto
        self.percentuale_incrementale = percentuale_incrementale
        self.tipo_steptake = tipo_steptake
        self.tipo_commissione = tipo_commissione
        self.commissione = commissione
        self.min_commissione = min_commissione
        self.max_commissione = max_commissione
        self.in_carico = in_carico
        self.while_counter = while_counter
        self.nr_acquisti = 0
        self.nr_vendite = 0
        self.gain = 0
        self.commissioni = 0
        self.profitto = 0
        self.valore_attuale = 0
        self.valore_carico_long = 0
        self.valore_carico_short = 0
        self.valore_min = 0
        self.valore_max = 0
        self.quantita_totale = 0
        self.rendimento = 0
        self.rendimento_teorico = 0
        if self.checkFX is True:
            self.tick = 5
        else:
            self.tick = 4
        check = round(round((self.primo_acquisto - self.limite_inferiore), self.tick) / self.step, self.tick)
        check2 = round(round((self.limite_superiore - self.limite_inferiore), self.tick) / self.step, self.tick)
        # controlli per verificare che i parametri abbiano senso
        if not check.is_integer():
            # se il primo acquisto non è multiplo dello step, arrotondo alla cifra inferiore
            self.primo_acquisto = round(
                (((self.primo_acquisto - self.limite_inferiore) // self.step) * self.step) + self.limite_inferiore,
                self.tick)
        if not check2.is_integer():
            self.limite_superiore = round(
                (((self.limite_superiore - self.limite_inferiore) // self.step) * self.step) + self.limite_inferiore,
                self.tick)
        prima_vendita = round(self.primo_acquisto + self.take + self.step, self.tick)
        pacchi_acquisto = []
        pacchi_vendita = []
        pacchi_stato = []
        pacchi_carica = []
        self.pacchi = []
        self.operazioni = []
        self.storico = []
        if in_carico < 0:
            logica_tappeto = 'short'
        else:
            logica_tappeto = 'long'
        i = 0
        pacco_acquisto = self.limite_inferiore
        pacco_vendita = round(pacco_acquisto + self.take, 5)
        lista_per_panda = []
        while pacco_vendita <= self.limite_superiore:
            pacchi_acquisto.append(pacco_acquisto)
            pacchi_vendita.append(pacco_vendita)
            if pacco_acquisto <= self.primo_acquisto:
                pacchi_stato.append('ACQAZ_L')
                pacchi_carica.append(0)
            # se in_carico < 0 allora sono in logica short, carico pacchi short mettendo lo stato in ACQAZ
            # se in_carico > 0 allora sono in logica long, carico pacchi long mettendo lo stato in VENAZ
            if pacco_vendita >= prima_vendita:
                if in_carico > 0:
                    pacchi_stato.append('VENAZ_L')
                    pacchi_carica.append(1)
                    in_carico -= 1
                elif in_carico < 0:
                    pacchi_stato.append('ACQAZ_S')
                    pacchi_carica.append(1)
                    in_carico += 1
                elif in_carico == 0:
                    pacchi_stato.append('VENAZ_S')
                    pacchi_carica.append(0)
            pacco_acquisto = round(pacco_acquisto + self.step, self.tick)
            pacco_vendita = round(pacco_acquisto + self.take, self.tick)
            singolo_pacco = Pacco(i + 1, self.isin, pacchi_stato[i], pacchi_acquisto[i], pacchi_vendita[i], self.take,
                                  self.quantita_acquisto, self.quantita_vendita, 0, pacchi_carica[i])
            self.pacchi.append(singolo_pacco)
            if pacchi_stato[i] == 'ACQAZ_L' and pacchi_carica[i] == 0:
                # lista_per_panda(numero tappeto, numero_pacco, stato 0=ACQ,1=VEN, prezzo_acquisto, prezzo_vendita)
                lista_per_panda.append((while_counter, i + 1, 0, pacchi_acquisto[i], pacchi_vendita[i]))
                self.valore_carico_long += pacchi_acquisto[i] * self.quantita_vendita
            elif pacchi_stato[i] == 'ACQAZ_S' and pacchi_carica[i] == 1:
                lista_per_panda.append((while_counter, i + 1, 0, pacchi_acquisto[i], pacchi_vendita[i]))
                self.valore_attuale += (pacchi_acquisto[i] * self.quantita_acquisto)
            elif pacchi_stato[i] == 'VENAZ_S' and pacchi_carica[i] == 0:
                lista_per_panda.append((while_counter, i + 1, 1, pacchi_acquisto[i], pacchi_vendita[i]))
                self.valore_carico_short += pacchi_acquisto[i] * self.quantita_vendita
            elif pacchi_stato[i] == 'VENAZ_L' and pacchi_carica[i] == 1:
                lista_per_panda.append((while_counter, i + 1, 1, pacchi_acquisto[i], pacchi_vendita[i]))
                self.valore_attuale += (pacchi_acquisto[i] + self.quantita_acquisto)
            i += 1
        dt = np.dtype('int,int,int,float,float')
        self.numpy = np.array(lista_per_panda, dtype=dt)

    def operazione(self, tipo_operazione, data, ora, prezzo, quantita, gain, commissioni, carica):
        if tipo_operazione == "ACQAZ_L" and carica == 0:
            self.quantita_totale += quantita
            self.valore_attuale += (prezzo * quantita)
        elif tipo_operazione == "ACQAZ_S" and carica == 1:
            self.quantita_totale -= quantita
            self.valore_attuale -= (prezzo * quantita)
        elif tipo_operazione == "VENAZ_L" and carica == 1:
            self.quantita_totale -= quantita
            self.valore_attuale -= (prezzo * quantita)
        elif tipo_operazione == "VENAZ_S" and carica == 0:
            self.quantita_totale += quantita
            self.valore_attuale += (prezzo * quantita)
        if self.valore_attuale >= self.valore_max:
            self.valore_max = self.valore_attuale


class GeneraSimulazione:
    def __init__(self, request):
        self.start_time = datetime.datetime.today()
        self.crea_isin = request.POST.get('isin')
        self.crea_limite_inferiore = float(request.POST.get('crea_limite_inferiore'))
        self.crea_limite_superiore = float(request.POST.get('crea_limite_superiore'))
        self.crea_step = float(request.POST.get('step'))
        self.crea_quantita_acquisto = float(request.POST.get('quantita_acquisto'))
        self.crea_quantita_vendita = float(request.POST.get('quantita_vendita'))
        self.crea_primo_acquisto = float(request.POST.get('primo_acquisto'))
        self.crea_checkFX = True
        if request.POST.get('tipo_take') == 'take_singolo':
            self.crea_take_inizio = float(request.POST.get('take'))
            self.crea_take_fine = self.crea_take_inizio
            self.crea_take_incremento = 1
        elif request.POST.get('tipo_take') == 'take_variabile':
            self.crea_take_inizio = float(request.POST.get('take_inizio'))
            self.crea_take_fine = float(request.POST.get('take_fine'))
            self.crea_take_incremento = float(request.POST.get('take_incremento'))
        self.crea_in_carico = int(request.POST.get('in_carico'))
        self.crea_take_inizio_2 = self.crea_take_inizio
        self.crea_in_carico_2 = self.crea_in_carico
        self.tick = 4
        self.tipo_tappeto = ''
        self.percentuale_incrementale = 0
        self.tipo_steptake = 0
        self.tipo_commissione = request.POST.get('commissioni_tipo')
        self.commissione = float(request.POST.get('commissioni_importo'))
        self.min_commissione = float(request.POST.get('commissioni_min'))
        self.max_commissione = float(request.POST.get('commissioni_max'))
        self.data_inizio = request.POST.get('crea_data_inizio').split('/')
        self.data_inizio = datetime.date(int(self.data_inizio[2]), int(self.data_inizio[1]), int(self.data_inizio[0]))
        self.data_fine = request.POST.get('crea_data_fine').split('/')
        self.data_fine = datetime.date(int(self.data_fine[2]), int(self.data_fine[1]), int(self.data_fine[0]))
        self.data_inizio_2 = self.data_inizio
        self.data_fine_2 = self.data_fine
        self.tappeto = []
        self.storico = []
        self.take_array = []
        self.take_array_size = 0
        self.check = round(round((self.crea_primo_acquisto - self.crea_limite_inferiore), self.tick) / self.crea_step, self.tick)
        self.check2 = round(round((self.crea_limite_superiore - self.crea_limite_inferiore), self.tick) / self.crea_step, self.tick)
        # controlli per verificare che i parametri abbiano senso
        if not self.check.is_integer():
            # se il primo acquisto non è multiplo dello step, arrotondo alla cifra inferiore
            self.crea_primo_acquisto = round((((self.crea_primo_acquisto - self.crea_limite_inferiore) // self.crea_step) * self.crea_step) +
                                             self.crea_limite_inferiore, self.tick)
            self.check = 'Yes'
        if not self.check2.is_integer():
            self.crea_limite_superiore = round(
                (((self.crea_limite_superiore - self.crea_limite_inferiore) // self.crea_step) * self.crea_step) +
                self.crea_limite_inferiore, self.tick)
            self.check2 = 'Yes'

    def creazione_array(self):
        # creo un numpy array per memorizzare tutti  i pacchi di tutti i tappeti
        dt = np.dtype('int,int,int,float,float')
        while_counter = 1
        # ciclo per creare un tappeto per ogni unità di take
        while self.crea_take_inizio <= (self.crea_take_fine + 0.0001):
            tappeto_singolo = Tappeto(self.crea_isin, self.crea_limite_inferiore, self.crea_limite_superiore,
                                      self.crea_step, self.crea_take_inizio, self.crea_quantita_acquisto,
                                      self.crea_quantita_vendita, self.crea_primo_acquisto, self.crea_checkFX,
                                      self.tick,
                                      self.tipo_tappeto, self.percentuale_incrementale, self.tipo_steptake,
                                      self.tipo_commissione, self.commissione, self.min_commissione,
                                      self.max_commissione, self.crea_in_carico, while_counter)
            self.tappeto.append(tappeto_singolo)
            # se è il primo giro devo creare l'array, se è dopo allora devo appendere i pacchi all'array già creato
            if while_counter == 1:
                pacchi_numpy = np.array(tappeto_singolo.numpy, dtype=dt)
            else:
                pacchi_numpy = np.concatenate((pacchi_numpy, tappeto_singolo.numpy))
            self.crea_take_inizio += self.crea_take_incremento
            while_counter += 1
        return self.tappeto, pacchi_numpy

    def simula(self, tappeto, pacchi_numpy, folder):
        # pacchi_numpy.dtype.names('tappeto', 'pacco', 'stato', 'prezzo_acquisto', 'prezzo_vendita')
        data_diff = self.data_fine - self.data_inizio
        # per ogni tappeto creo lo storico vuoto di ogni data
        for c in range(0, len(tappeto), +1):
            data_ciclo = self.data_inizio
            for i in range(data_diff.days + 1):
                tappeto[c].storico.append(Storico(data_ciclo))
                data_ciclo += datetime.timedelta(days=1)
        # per ogni data cerco il file del tick by tick
        for i in range(data_diff.days + 1):
            if settings.SERVER_DEV is False:
                filename = folder + self.crea_isin + "/" + self.data_inizio.strftime("%Y%m%d") + ".csv"
            else:
                filename = folder + self.crea_isin + "\\" + self.data_inizio.strftime("%Y%m%d") + ".csv"
            intra = []
            if os.path.exists(filename):
                with open(filename) as f:
                    for line in f:
                        line = line.split("|")
                        intra.append(line)
                self.storico.append(Storico(self.data_inizio))
            else:
                self.data_inizio += datetime.timedelta(days=1)
                continue
            ultimo_prezzo = 0
            # per ogni file giornaliero ciclo tra tutti i prezzi
            for a in range(len(intra) - 1, 0, -1):
                if intra[a][1] == '':
                    continue
                prezzo = float(intra[a][1])
                data = self.data_inizio
                ora = intra[a][0]
                if prezzo == ultimo_prezzo:
                    continue
                ultimo_prezzo = prezzo
                # se il prezzo è diverso dall'ultimo prezzo allora ciclo tra tutti i tappeti
                # per eseguire operazione
                # ciclo tra tutti i tappeti
                # cerco dentro il dataframe dove stato = ACQAZ 0 o VENAZ 1 e prezzo
                lis_a = np.flatnonzero(
                    np.logical_and(pacchi_numpy['f2'] == 0, pacchi_numpy['f3'] >= prezzo))
                lis_b = np.flatnonzero(
                    np.logical_and(pacchi_numpy['f2'] == 1, pacchi_numpy['f4'] <= prezzo))
                for item in lis_a:
                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                        prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                    pacchi_numpy[item]['f2'] = 1
                for item in lis_b:
                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                        prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                    pacchi_numpy[item]['f2'] = 0
            self.data_inizio += datetime.timedelta(days=1)
        return tappeto, pacchi_numpy

    def genera_statistiche(self, request, tappeto, time):
        # leggo l'indirizzo IP per memorizzarlo nelle statistice
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')  # Real IP address of client Machine
        # se user non è loggato, allora associo la simulazione a Anonymous
        if not request.user:
            user_id = User.objects.get(username='Anonymous')
        elif request.user.is_anonymous:
            user_id = User.objects.get(username='Anonymous')
        else:
            user_id = request.user
        n = SimulazioneStatistiche.objects.create(durata=time, user_id=user_id, indirizzo_ip=ip,
                                                  isin=self.crea_isin,
                                                  limite_inferiore=self.crea_limite_inferiore,
                                                  limite_superiore=self.crea_limite_superiore, step=self.crea_step,
                                                  quantita_acquisto=self.crea_quantita_acquisto,
                                                  quantita_vendita=self.crea_quantita_vendita,
                                                  primo_acquisto=self.crea_primo_acquisto,
                                                  take_inizio=self.crea_take_inizio_2,
                                                  take_fine=self.crea_take_fine,
                                                  take_incremento=self.crea_take_incremento,
                                                  in_carico=self.crea_in_carico,
                                                  tipo_commissione=self.tipo_commissione,
                                                  commissione=self.commissione,
                                                  min_commissione=self.min_commissione,
                                                  max_commissione=self.max_commissione)
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
                                           valore_carico=tappeto[classifica_rendimenti[1]].valore_carico_long,
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
                                           valore_carico=tappeto[classifica_rendimenti[0]].valore_carico_long,
                                           valore_min=tappeto[classifica_rendimenti[0]].valore_min,
                                           valore_max=tappeto[classifica_rendimenti[0]].valore_max,
                                           quantita_totale=tappeto[classifica_rendimenti[0]].quantita_totale,
                                           rendimento=tappeto[classifica_rendimenti[0]].rendimento,
                                           rendimento_teorico=tappeto[
                                               classifica_rendimenti[0]].rendimento_teorico)
        SimulazioneSingola.objects.bulk_create([simsingolamax, simsingolamin])
        i = 0
        take_array = []
        for item in tappeto:
            lista = [sto.profitto for sto in item.storico]
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
        return simsingolamax, take_array, take_array_size
