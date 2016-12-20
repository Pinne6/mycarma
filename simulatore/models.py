from django.db import models
from django.contrib.auth.models import User
import django.utils
import numpy as np
import datetime
from django.conf import settings
import os.path
import copy
import csv

stampa = True
# Create your models here.


class CalcoloPacco:
    def __init__(self, primo_acquisto, copertura, capitale, incremento_step, step_iniziale, step_finale):
        self.primo_acquisto = primo_acquisto
        self.copertura = copertura
        self.capitale = capitale
        self.limite_inferiore = 0
        self.limite_superiore = 0
        self.incremento_step = incremento_step
        self.step_iniziale = step_iniziale
        self.step_finale = step_finale
        self.tick = 4
        self.risultati = []

    def costruzione_array(self, i, tipo, step, limite_inferiore):
        if tipo == 'long':
            pacco = limite_inferiore + (step * i)
        else:
            pacco = self.primo_acquisto + (step * i) + step
        return pacco

    def calcolo_pacco(self):
        # calcolo limite inferiore e superiore
        self.limite_inferiore = self.primo_acquisto / (1 + self.copertura)
        self.limite_superiore = self.primo_acquisto * (1 + self.copertura)
        step = self.step_iniziale
        while step <= self.step_finale:
            check = round(round((self.primo_acquisto - self.limite_inferiore), self.tick) / step, self.tick)
            check2 = round(round((self.limite_superiore - self.primo_acquisto), self.tick) / step, self.tick)
            # controlli per verificare che i parametri abbiano senso
            if not check.is_integer():
                # se il primo acquisto non è multiplo dello step, arrotondo alla cifra inferiore
                limite_inferiore = round(
                    self.primo_acquisto - (np.ceil((self.primo_acquisto - self.limite_inferiore) / step) * step),
                    self.tick)
            else:
                limite_inferiore = self.limite_inferiore
            if not check2.is_integer():
                limite_superiore = round((((self.limite_superiore - self.limite_inferiore) // step) *
                                          step) + self.limite_inferiore, self.tick)
            else:
                limite_superiore = self.limite_superiore
            numero_pacchi_long = int(((self.primo_acquisto - limite_inferiore) / step) + 1)
            array_long = np.fromfunction(lambda i: self.costruzione_array(i, 'long', step, limite_inferiore),
                                         (numero_pacchi_long,))
            numero_pacchi_short = int(((limite_superiore - self.primo_acquisto) / step))
            array_short = np.fromfunction(lambda i: self.costruzione_array(i, 'short', step, 0), (numero_pacchi_short,))
            dim_pacchi_long = np.floor(self.capitale / np.sum(array_long))
            dim_pacchi_short = np.floor(self.capitale / np.sum(array_short))
            capitale_long = dim_pacchi_long * np.sum(array_long)
            capitale_short = dim_pacchi_short * np.sum(array_short)
            self.risultati.append(
                [limite_inferiore, limite_superiore, round(step, 4), numero_pacchi_long, dim_pacchi_long,
                 int(capitale_long), numero_pacchi_short, dim_pacchi_short, int(capitale_short)])
            step += self.incremento_step
        return


class UserPerm(models.Model):
    class Meta:
        permissions = (
            ("take_fisso", "Può simulare senza limiti a take fisso"),
            ("take_variabile", "Può simulare senza limiti a take variabile"),
            ("aggiustamento", "Può simulare con aggiustamento")
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
                 autoadj, carica, disable):
        self.package_number = package_number
        self.ticker = ticker
        self.order_type = order_type
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.take = take
        self.quantity_buy = quantity_buy
        self.quantity_sell = quantity_sell
        self.autoadj = autoadj
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
        self.disable = disable
        self.aggiustamento_carico = 0
        self.pmc_gain = 0

    def acquisto(self, prezzo, tappeto, data, ora, storico):
        self.nr_acquisti += 1
        if tappeto.con_gap:
            self.buy_price_real = prezzo
        if self.carica == 1:
            gain = round((self.sell_price_real * self.quantity_sell) - (self.buy_price_real * self.quantity_buy), 4)
            self.gain += gain
            storico[len(storico) - 1].gain += gain
            pmc_gain = (self.buy_price_real - tappeto.pmc) * self.quantity_buy
            self.pmc_gain += pmc_gain * (-1)
        else:
            gain = 0
            self.aggiustamento_carico = round(self.buy_price_real * self.quantity_buy, 2)
            pmc_gain = 0
        commissione = self.calcola_commissioni(self.quantity_buy, self.buy_price_real, tappeto)
        self.commissioni += commissione
        if self.order_type == "ACQAZ_S":
            tappeto.capitale += round((self.sell_price_real * self.quantity_buy) - commissione + gain, 2)
            costo_operazione = round(((self.sell_price_real * self.quantity_buy) - commissione + gain), 2)
            tappeto.pmc_capitale += (self.sell_price_real * self.quantity_buy) - commissione - pmc_gain
        else:
            tappeto.capitale -= round((self.buy_price_real * self.quantity_buy) + commissione, 2)
            costo_operazione = round(((self.buy_price_real * self.quantity_buy) + commissione) * -1, 2)
            tappeto.pmc_capitale -= (self.buy_price_real * self.quantity_buy) + commissione
        op = Operazione(self.order_type, data, ora, self.buy_price_real, self.quantity_buy, gain, commissione,
                        self.buy_price, round(tappeto.capitale, 2), round(costo_operazione, 2), 0, 0, 0, self.autoadj,
                        self.aggiustamento_carico, 0, 0, 0, 0, pmc_gain, round(tappeto.pmc_capitale, 2), 0,
                        tappeto.punto_flat)
        # op.paccus = copy.deepcopy(tappeto.pacchi)
        # tappeto.operazioni.append(Operazione(self.order_type, data, ora, prezzo, self.quantity_buy, gain, commissione,
        #                                      self.buy_price, round(tappeto.capitale, 2), round(costo_operazione, 2),
        #                                      copy.deepcopy(tappeto.pacchi)))
        tappeto.operazione(self.order_type, data, ora, self.buy_price_real, self.quantity_buy, gain, commissione, self.carica,
                           self.aggiustamento_carico)
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
        if self.carica == 1:
            self.carica = 0
            self.order_type = "VENAZ_S"

        else:
            self.carica = 1
            self.order_type = "VENAZ_L"
        op.valore_attuale = round(tappeto.valore_attuale, 2)
        op.valore_max = round(tappeto.valore_max, 2)
        op.quantita_totale = round(tappeto.quantita_totale, 2)
        op.valore_in_carico = round(tappeto.valore_in_carico, 2)
        op.marginazione = round(tappeto.marginazione, 2)
        op.carico_pmc = round(tappeto.carico_pmc, 2)
        op.pmc = round(tappeto.pmc, 4)
        op.patrimonio = round(tappeto.patrimonio, 2)
        tappeto.operazioni.append(op)
        """
        filename = "C:\\ope\\" + str(len(tappeto.operazioni)) + ".csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Pacco', 'Operazione', 'Acquisto', 'Vendita', 'Autoagg', 'Disable', 'Carica',
                             'n_Operazione', 'n_Autoagg', 'n_Disable', 'n_Carica'])
            for idx, item in enumerate(tappeto.pacchi):
                if item.autoadj != 0:
                    tipo = item.order_type + '_A'
                else:
                    tipo = item.order_type
                writer.writerow([item.package_number, tipo, item.buy_price, item.sell_price, item.autoadj,
                                 item.disable, item.carica, tappeto.numpy[idx]['f2'],
                                 tappeto.numpy[idx]['f5'], tappeto.numpy[idx]['f6'], tappeto.numpy[idx]['f7']])
            csvfile.close()
        """
        return storico

    def vendita(self, prezzo, tappeto, data, ora, storico):
        self.nr_vendite += 1
        if tappeto.con_gap:
            self.sell_price_real = prezzo
        if self.carica == 1:
            gain = round((prezzo * self.quantity_sell) - (self.buy_price_real * self.quantity_buy), 4)
            self.gain += gain
            storico[len(storico) - 1].gain += gain
            pmc_gain = (self.sell_price_real - tappeto.pmc) * self.quantity_sell
            self.pmc_gain += pmc_gain
        else:
            gain = 0
            self.aggiustamento_carico = round(self.sell_price_real * self.quantity_sell, 2)
            pmc_gain = 0
        commissione = self.calcola_commissioni(self.quantity_sell, self.sell_price_real, tappeto)
        self.commissioni += commissione
        if self.order_type == "VENAZ_S":
            tappeto.capitale -= round((self.quantity_sell * self.sell_price_real) + commissione, 2)
            costo_operazione = round(((self.quantity_sell * self.sell_price_real) + commissione) * -1, 2)
            tappeto.pmc_capitale -= (self.quantity_sell * self.sell_price_real) + commissione
        else:
            tappeto.capitale += round((self.quantity_sell * self.sell_price_real) - commissione, 2)
            costo_operazione = round((self.quantity_sell * self.sell_price_real) - commissione, 2)
            tappeto.pmc_capitale += (self.quantity_sell * self.sell_price_real) + pmc_gain - commissione
        op = Operazione(self.order_type, data, ora, self.sell_price_real, self.quantity_sell, gain, commissione,
                        self.buy_price, round(tappeto.capitale, 2), round(costo_operazione, 2), 0, 0, 0, self.autoadj,
                        self.aggiustamento_carico, 0, 0, 0, 0, pmc_gain, round(tappeto.pmc_capitale, 2), 0,
                        tappeto.punto_flat)
        # op.paccus = copy.deepcopy(tappeto.pacchi)
        # tappeto.operazioni.append(Operazione(self.order_type, data, ora, prezzo, self.quantity_sell, gain,
        #                                       commissione,
        #                                      self.sell_price, round(tappeto.capitale, 2), round(costo_operazione, 2),
        #                                      copy.deepcopy(tappeto.pacchi)))
        tappeto.operazione(self.order_type, data, ora, self.sell_price_real, self.quantity_sell, gain, commissione, self.carica,
                           self.aggiustamento_carico)
        for item in tappeto.storico:
            if item.data == data:
                item.nr_vendite += 1
                item.commissioni += commissione
                item.profitto += (gain - commissione)
                break
        storico[len(storico) - 1].nr_vendite += 1
        storico[len(storico) - 1].commissioni += commissione
        storico[len(storico) - 1].profitto += (gain - commissione)
        if self.carica == 1:
            self.carica = 0
            self.order_type = "ACQAZ_L"
        else:
            self.carica = 1
            self.order_type = "ACQAZ_S"
        op.valore_attuale = round(tappeto.valore_attuale, 2)
        op.valore_max = round(tappeto.valore_max, 2)
        op.quantita_totale = round(tappeto.quantita_totale, 2)
        op.valore_in_carico = round(tappeto.valore_in_carico, 2)
        op.marginazione = round(tappeto.marginazione, 2)
        op.carico_pmc = round(tappeto.carico_pmc, 4)
        op.pmc = round(tappeto.pmc, 4)
        op.patrimonio = round(tappeto.patrimonio, 2)
        tappeto.operazioni.append(op)
        """
        filename = "C:\\ope\\" + str(len(tappeto.operazioni)) + ".csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Pacco', 'Operazione', 'Acquisto', 'Vendita', 'Autoagg', 'Disable', 'Carica',
                             'n_Operazione', 'n_Autoagg', 'n_Disable', 'n_Carica'])
            for idx, item in enumerate(tappeto.pacchi):
                if item.autoadj != 0:
                    tipo = item.order_type + '_A'
                else:
                    tipo = item.order_type
                writer.writerow([item.package_number, tipo, item.buy_price, item.sell_price, item.autoadj,
                                 item.disable, item.carica, tappeto.numpy[idx]['f2'],
                                 tappeto.numpy[idx]['f5'], tappeto.numpy[idx]['f6'], tappeto.numpy[idx]['f7']])
            csvfile.close()
        """
        return storico

    @staticmethod
    def calcola_commissioni(quantita, prezzo, tappeto):
        if tappeto.tipo_commissione == 'P':
            p = (prezzo * quantita * tappeto.commissione) / 100
            if p < tappeto.min_commissione:
                p = tappeto.min_commissione
            if p > tappeto.max_commissione:
                p = tappeto.max_commissione
            return round(p, 2)
        else:
            return round(tappeto.commissione, 2)


class Operazione:
    def __init__(self, tipo, data, ora, prezzo, quantita, gain, commissioni, prezzo_teorico, capitale, costo_operazione,
                 valore_attuale, valore_max, quantita_totale, autoadj, agg, valore_in_carico, marginazione, carico_pmc,
                 pmc, pmc_gain, pmc_capitale, patrimonio, punto_flat):
        self.data = data
        self.ora = ora
        self.tipo = tipo
        self.prezzo = prezzo
        self.quantita = quantita
        self.gain = gain
        self.commissioni = commissioni
        self.profitto = round(gain - commissioni, 2)
        self.prezzo_teorico = prezzo_teorico
        self.capitale = capitale
        self.costo_operazione = costo_operazione
        self.valore_attuale = valore_attuale
        self.valore_max = valore_max
        self.quantita_totale = quantita_totale
        self.autoadj = autoadj
        self.aggiustamento_carico = agg
        self.valore_in_carico = valore_in_carico
        self.marginazione = marginazione
        self.carico_pmc = carico_pmc
        self.pmc = pmc
        self.pmc_gain = round(pmc_gain, 2)
        self.pmc_profitto = round(pmc_gain - commissioni, 2)
        self.pmc_capitale = pmc_capitale
        self.patrimonio = patrimonio
        self.punto_flat = punto_flat


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
                 max_commissione, in_carico, while_counter, aggiustamento, aggiustamento_step,
                 aggiustamento_limite_inferiore, aggiustamento_limite_superiore, capitale, con_gap):
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
        if aggiustamento == 'True':
            self.aggiustamento = True
        else:
            self.aggiustamento = False
        self.aggiustamento_limite_inferiore = aggiustamento_limite_inferiore
        self.aggiustamento_limite_superiore = aggiustamento_limite_superiore
        self.aggiustamento_step = aggiustamento_step
        self.valore_carico_aggiustamento_long = 0
        self.valore_carico_aggiustamento_short = 0
        self.aggiustamento_carichi = 0
        self.capitale = capitale
        self.valore_in_carico = 0
        self.marginazione = 0
        self.marginazione_fattore = 0.8
        self.carico_pmc = 0
        self.pmc = 0
        self.pmc_capitale = capitale
        self.patrimonio = 0
        self.pmc_gain = 0
        self.pmc_profitto = 0
        self.negativo = False
        self.rendimento_capitale = 0
        if self.checkFX is True:
            self.tick = 5
        else:
            self.tick = 4
        self.con_gap = con_gap
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
        self.punto_flat = self.primo_acquisto
        pacchi_acquisto = []
        pacchi_vendita = []
        pacchi_stato = []
        pacchi_carica = []
        self.pacchi = []
        self.operazioni = []
        self.storico = []
        i = 0
        if self.aggiustamento:
            pacco_acquisto = self.aggiustamento_limite_inferiore
            limite_sup = self.aggiustamento_limite_superiore
        else:
            pacco_acquisto = self.limite_inferiore
            limite_sup = self.limite_superiore
        pacco_vendita = round(pacco_acquisto + self.take, 5)
        lista_per_panda = []
        while pacco_vendita <= limite_sup:
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
            if self.aggiustamento:
                check_aggiustamento_acquisto = round(round(self.limite_inferiore - pacchi_acquisto[i], tick) /
                                                     self.step, tick) / self.aggiustamento_step
                check_aggiustamento_vendita = round(round(pacchi_vendita[i] - self.limite_superiore, tick) / self.step,
                                                    tick) / self.aggiustamento_step
                if pacchi_acquisto[i] < self.limite_inferiore and not check_aggiustamento_acquisto.is_integer():
                    disable = 1
                    autoadj = 1
                elif pacchi_acquisto[i] < self.limite_inferiore and check_aggiustamento_acquisto.is_integer():
                    disable = 1
                    autoadj = 2
                elif pacchi_acquisto[i] == self.limite_inferiore:
                    disable = 0
                    autoadj = 3
                elif pacchi_vendita[i] > self.limite_superiore and not check_aggiustamento_vendita.is_integer():
                    disable = 1
                    autoadj = -1
                elif pacchi_vendita[i] > self.limite_superiore and check_aggiustamento_vendita.is_integer():
                    disable = 1
                    autoadj = -2
                elif pacchi_vendita[i] == self.limite_superiore:
                    disable = 0
                    autoadj = -3
                else:
                    disable, autoadj = 0, 0
            else:
                disable, autoadj = 0, 0
            singolo_pacco = Pacco(i + 1, self.isin, pacchi_stato[i], pacchi_acquisto[i], pacchi_vendita[i], self.take,
                                  self.quantita_acquisto, self.quantita_vendita, autoadj, pacchi_carica[i], disable)
            self.pacchi.append(singolo_pacco)
            if pacchi_stato[i] == 'ACQAZ_L' and pacchi_carica[i] == 0:
                # lista_per_panda(numero tappeto, numero_pacco, stato 0=ACQ,1=VEN, prezzo_acquisto, prezzo_vendita,
                # autoadj stato 0=regular,1=attivato da 2,2=attivato da 3,3=limite inferiore,
                # 0=regular,-1=attivato da -2,-2=attivato da -3-,3=limite superiore, disable, valore_carico)
                lista_per_panda.append(
                    (while_counter, i + 1, 0, pacchi_acquisto[i], pacchi_vendita[i], autoadj, disable, 0))
                if autoadj == 0 or autoadj == 3:
                    self.valore_carico_long += pacchi_acquisto[i] * self.quantita_vendita
                else:
                    self.valore_carico_aggiustamento_long += pacchi_acquisto[i] * self.quantita_vendita
            elif pacchi_stato[i] == 'ACQAZ_S' and pacchi_carica[i] == 1:
                lista_per_panda.append(
                    (while_counter, i + 1, 0, pacchi_acquisto[i], pacchi_vendita[i], autoadj, disable, 0))
                self.valore_attuale += (pacchi_acquisto[i] * self.quantita_acquisto)
            elif pacchi_stato[i] == 'VENAZ_S' and pacchi_carica[i] == 0:
                lista_per_panda.append(
                    (while_counter, i + 1, 1, pacchi_acquisto[i], pacchi_vendita[i], autoadj, disable, 0))
                if autoadj == 0 or autoadj == -3:
                    self.valore_carico_short += pacchi_acquisto[i] * self.quantita_vendita
                else:
                    self.valore_carico_aggiustamento_short += pacchi_acquisto[i] * self.quantita_vendita
            elif pacchi_stato[i] == 'VENAZ_L' and pacchi_carica[i] == 1:
                lista_per_panda.append(
                    (while_counter, i + 1, 1, pacchi_acquisto[i], pacchi_vendita[i], autoadj, disable, 0))
                self.valore_attuale += (pacchi_acquisto[i] + self.quantita_acquisto)
            i += 1
        dt = np.dtype('int,int,int,float,float,int,int,float')
        self.numpy = np.array(lista_per_panda, dtype=dt)

    def operazione(self, tipo_operazione, data, ora, prezzo, quantita, gain, commissioni, carica, aggiustamento_carico):
        if tipo_operazione == "ACQAZ_L" and carica == 0:
            self.quantita_totale += quantita
            self.valore_attuale += aggiustamento_carico
            self.valore_in_carico = self.quantita_totale * prezzo
            self.carico_pmc += (prezzo * quantita)  # + commissioni
            self.pmc = round(self.carico_pmc / self.quantita_totale, 4)
            self.marginazione = self.capitale + (self.marginazione_fattore * self.valore_in_carico)
            self.patrimonio = self.pmc_capitale + self.valore_in_carico
        elif tipo_operazione == "ACQAZ_S" and carica == 1:
            self.quantita_totale -= quantita
            self.valore_attuale -= aggiustamento_carico
            self.valore_in_carico = self.quantita_totale * prezzo
            self.marginazione = self.capitale + (self.marginazione_fattore * self.valore_in_carico)
            self.carico_pmc = round(self.quantita_totale * self.pmc, 4)
            self.patrimonio = self.pmc_capitale + self.carico_pmc + self.carico_pmc - self.valore_in_carico
        elif tipo_operazione == "VENAZ_L" and carica == 1:
            self.quantita_totale -= quantita
            self.valore_attuale -= aggiustamento_carico
            self.valore_in_carico = self.quantita_totale * prezzo
            self.marginazione = self.capitale + (self.marginazione_fattore * self.valore_in_carico)
            self.carico_pmc = round(self.quantita_totale * self.pmc, 4)
            self.patrimonio = self.pmc_capitale + self.valore_in_carico
        elif tipo_operazione == "VENAZ_S" and carica == 0:
            self.quantita_totale += quantita
            self.valore_attuale += aggiustamento_carico
            self.valore_in_carico = self.quantita_totale * prezzo
            self.marginazione = self.capitale + (self.marginazione_fattore * self.valore_in_carico)
            self.carico_pmc += (quantita * prezzo)  # + commissioni
            self.pmc = round(self.carico_pmc / self.quantita_totale, 4)
            self.patrimonio = self.pmc_capitale + self.carico_pmc + self.carico_pmc - self.valore_in_carico
        if self.carico_pmc >= self.valore_max:
            self.valore_max = round(self.carico_pmc, 2)
        if self.pmc_capitale < 0:
            self.negativo = True


class GeneraSimulazione:
    def __init__(self, request, isin, ticker):
        self.start_time = datetime.datetime.today()
        if ticker:
            self.crea_isin = isin
        else:
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
        self.aggiustamento = request.POST.get('aggiustamento')
        if self.aggiustamento:
            self.aggiustamento_step = int(request.POST.get('aggiustamento_step'))
            self.aggiustamento_limite_inferiore = float(request.POST.get('aggiustamento_limite_inferiore'))
            self.aggiustamento_limite_superiore = float(request.POST.get('aggiustamento_limite_superiore'))
            self.capitale = float(request.POST.get('capitale'))
        self.con_gap = request.POST.get('con_gap')
        if self.con_gap == 'True':
            self.con_gap = True
        else:
            self.con_gap = False
        self.tappeto = []
        self.storico = []
        self.take_array = []
        self.take_array_size = 0
        self.check = round(round((self.crea_primo_acquisto - self.crea_limite_inferiore), self.tick) / self.crea_step,
                           self.tick)
        self.check2 = round(
            round((self.crea_limite_superiore - self.crea_limite_inferiore), self.tick) / self.crea_step, self.tick)
        # controlli per verificare che i parametri abbiano senso
        if not self.check.is_integer():
            # se il primo acquisto non è multiplo dello step, arrotondo alla cifra inferiore
            self.crea_primo_acquisto = round(
                (((self.crea_primo_acquisto - self.crea_limite_inferiore) // self.crea_step) * self.crea_step) +
                self.crea_limite_inferiore, self.tick)
            self.check = 'Yes'
        if not self.check2.is_integer():
            self.crea_limite_superiore = round(
                (((self.crea_limite_superiore - self.crea_limite_inferiore) // self.crea_step) * self.crea_step) +
                self.crea_limite_inferiore, self.tick)
            self.check2 = 'Yes'

    def creazione_array(self):
        # creo un numpy array per memorizzare tutti  i pacchi di tutti i tappeti
        dt = np.dtype('int,int,int,float,float,int,int,float')
        while_counter = 1
        # ciclo per creare un tappeto per ogni unità di take
        while self.crea_take_inizio <= (self.crea_take_fine + 0.0001):
            tappeto_singolo = Tappeto(self.crea_isin, self.crea_limite_inferiore, self.crea_limite_superiore,
                                      self.crea_step, self.crea_take_inizio, self.crea_quantita_acquisto,
                                      self.crea_quantita_vendita, self.crea_primo_acquisto, self.crea_checkFX,
                                      self.tick,
                                      self.tipo_tappeto, self.percentuale_incrementale, self.tipo_steptake,
                                      self.tipo_commissione, self.commissione, self.min_commissione,
                                      self.max_commissione, self.crea_in_carico, while_counter, self.aggiustamento,
                                      self.aggiustamento_step, self.aggiustamento_limite_inferiore,
                                      self.aggiustamento_limite_superiore, self.capitale, self.con_gap)
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
            # per ogni file giornaliero ciclo tra tutti i prezzi
            if os.path.exists(filename):
                with open(filename, newline='') as csvfile:
                    self.storico.append(Storico(self.data_inizio))
                    ultimo_prezzo = 0
                    print(filename)
                    data = self.data_inizio
                    for row in reversed(list(csv.reader(csvfile, delimiter='|'))):
                        if row[1] == '':
                            continue
                        prezzo = float(row[1])
                        ora = row[0]
                        if prezzo == ultimo_prezzo:
                            continue
                        ultimo_prezzo = prezzo
                        # se il prezzo è diverso dall'ultimo prezzo allora ciclo tra tutti i tappeti
                        # per eseguire operazione
                        # ciclo tra tutti i tappeti
                        # cerco dentro il dataframe dove stato = ACQAZ 0 o VENAZ 1 e prezzo
                        lis_a = np.flatnonzero(
                            np.logical_and(np.logical_and(pacchi_numpy['f2'] == 0, pacchi_numpy['f3'] >= prezzo),
                                           pacchi_numpy['f6'] == 0))
                        np.flipud(lis_a)
                        lis_b = np.flatnonzero(
                            np.logical_and(np.logical_and(pacchi_numpy['f2'] == 1, pacchi_numpy['f4'] <= prezzo),
                                           pacchi_numpy['f6'] == 0))
                        # np.flipud(lis_b)
                        # with open('operazioni.csv', 'w', newline='') as opfile:
                        #     writer = csv.writer(opfile, delimiter=';')
                        for item in lis_a[::-1]:
                            #
                            # se stato aggiustamento == 3, sono in fondo alla sequenza, devo attivare aggiustamento
                            #
                            if pacchi_numpy[item]['f5'] == 3:
                                # devo attivare  il primo con stato 2, metto il 3 a stato 0

                                # gestione del pacco con autoadj == 3
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # imposto lo stato di autoadj a 0, pacco regular
                                pacchi_numpy[item]['f5'] = 0
                                # imposto stato a VENAZ
                                pacchi_numpy[item]['f2'] = 1
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1
                                # prendo l'aggiustamento_step e diminuisco l'indice di questo valore
                                # così so quale pacco 2 attivare
                                # imposto autoadj a 0
                                # pacchi_numpy[item - (tappeto[pacchi_numpy[item]['f0'] - 1].step * tappeto[
                                #     pacchi_numpy[item]['f0'] - 1].aggiustamento_step)]['f5'] = 0
                                # imposto disabled a 0
                                pacchi_numpy[item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step]['f6'] = 0
                                # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                # imposto autoadj a 0
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                                # imposto disabled a 0
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 - tappeto[
                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].disable = 0
                                # devo aggiungere il nuovo pacco al carico long
                                tappeto[pacchi_numpy[item]['f0'] - 1].valore_carico_long += \
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1].quantity_buy * \
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].buy_price

                            #
                            # - se stato aggiustamento == 2, devo attivare n pacchi sopra questo, n = molt step - 1
                            # - se c'è un altro pacco con autoadj == 2 sotto e stato disabled, devo abilitarlo
                            # - devo scalare sopra l'autoaggiustamento di x = molt step verso il basso
                            # - devo scalare tutto il carico di n = molt step - 1, quindi il pacco z ha carico del pacco z + n
                            #   lo scalare del valore di carico parte dal pacco appena sopra il pacco appena eseguito
                            # - devo modificare gli ultimi n pacchi long (n = agg_step - 1) da VENAZ_L a VENAZ_S
                            #   devo cambiare il carico da long a short, toglierli da carica
                            #
                            elif pacchi_numpy[item]['f5'] == 2 and pacchi_numpy[item]['f2'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].punto_flat -= tappeto[pacchi_numpy[item][
                                                                                                'f0'] - 1].step * (
                                                                                    tappeto[pacchi_numpy[item][
                                                                                                'f0'] - 1].aggiustamento_step - 1)
                                # devo attivare tutti quelli con id maggiore e autoadj = 1 e questo che è a 2 lo tengo a 2

                                # gestione del pacco con autoadj == 2
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # imposto lo stato di autoadj a 0, pacco regular
                                # pacchi_numpy[item]['f5'] = 0
                                # imposto stato a VENAZ
                                pacchi_numpy[item]['f2'] = 1
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1

                                # prendo l'aggiustamento step del tappeto corrispondente a questo pacco (-1 perchè conto da 0)
                                # così so quanti pacchi in stato == 1 devo attivare (aggiustamento_step - 1)
                                numero_pacchi_da_attivare = tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step
                                i = 1
                                while i < numero_pacchi_da_attivare:
                                    # imposto autoadj a 0
                                    # pacchi_numpy[item + i]['f5'] = 0
                                    # imposto disabled a 0
                                    pacchi_numpy[item + i]['f6'] = 0
                                    # imposto stato in VEN
                                    pacchi_numpy[item + i]['f2'] = 1
                                    # imposto carica a 1
                                    pacchi_numpy[item + i]['f7'] = 1
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a 0
                                    # tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 + i].autoadj = 0
                                    # imposto disabled a 0
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 + i].disable = 0
                                    # imposto stato in VENAZ_L
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 + i].order_type = 'VENAZ_L'
                                    # imposto un finto acquisto al prezzo di carico: pacco_acq + (step*aggiustamento_step)
                                    # imposto il buy_real_price
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 + i].buy_price_real = \
                                        round(tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                  pacchi_numpy[item]['f1'] - 1 + i].buy_price + (
                                                  tappeto[pacchi_numpy[item]['f0'] - 1].step * (tappeto[
                                                                                                    pacchi_numpy[item][
                                                                                                        'f0'] - 1].aggiustamento_step - 1)),
                                              5)
                                    # imposto il valore di carico di aggiustamento al buy price * quantita
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 + i].aggiustamento_carico = round(
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                            pacchi_numpy[item]['f1'] - 1 + i].buy_price_real *
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                            pacchi_numpy[item]['f1'] - 1 + i].quantity_buy, 2)
                                    # imposto carica a 1
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 + i].carica = 1
                                    i += 1

                                # se c'è un altro pacco con autoadj == 2 sotto e stato disabled, devo abilitarlo
                                # controllo anche che l'id tappeto sia lo stesso
                                if not pacchi_numpy[item]['f3'] - (
                                    tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step * tappeto[
                                        pacchi_numpy[item]['f0'] - 1].step) < tappeto[
                                            pacchi_numpy[item]['f0'] - 1].aggiustamento_limite_inferiore:
                                    if pacchi_numpy[item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                        'f5'] == 2 \
                                            and pacchi_numpy[
                                                        item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                                'f0'] == pacchi_numpy[item]['f0']:
                                        # imposto autoadj a 0
                                        # pacchi_numpy[item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step]['f5'] = 0
                                        # imposto disabled a 0
                                        pacchi_numpy[item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                            'f6'] = 0
                                        # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                        # imposto autoadj a 0
                                        # tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                                        # imposto disabled a 0
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 - tappeto[
                                            pacchi_numpy[item]['f0'] - 1].aggiustamento_step].disable = 0
                                        # devo aggiungere il nuovo pacco al carico long
                                        tappeto[pacchi_numpy[item]['f0'] - 1].valore_carico_long += \
                                            tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                pacchi_numpy[item]['f1'] - 1 - tappeto[
                                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].quantity_buy * \
                                            tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                pacchi_numpy[item]['f1'] - 1 - tappeto[
                                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].buy_price
                                # devo scalare sopra l'autoaggiustamento di x = molt step verso il basso
                                # cerco pacco con autoadj a -3 e con lo stesso id tappeto f0
                                pacco_meno_3 = np.flatnonzero(
                                    np.logical_and(np.logical_and(pacchi_numpy['f5'] == -3, pacchi_numpy['f6'] == 0),
                                                   pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                # devo scalarlo di moltiplicatore step e questo pacco diventa -2
                                if pacco_meno_3.size == 0:
                                    pacco_senza_3 = np.flatnonzero(
                                        np.logical_and(
                                            np.logical_and(pacchi_numpy['f5'] == -1, pacchi_numpy['f6'] == 1),
                                            pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                    # se non trovo nemmeno il pacco con autoadj 1 allora ho finito l'aggiustamento
                                    # devo ripartire dagli ultimi pacchi short in alto
                                    if pacco_senza_3.size == 0:
                                        # da fareeeeeeeeeeeeeeeeeeeeeeee
                                        zzzz = 1
                                    else:
                                        # scalo tutti gli aggiustamenti, prendo ultimo pacco della lista
                                        for item2 in pacco_senza_3:
                                            i = 1
                                            agg_step = tappeto[pacchi_numpy[item2]['f0'] - 1].aggiustamento_step - 1
                                            # imposto autoadj a -1
                                            pacchi_numpy[item2 - agg_step]['f5'] = -1
                                            # imposto stato a VENAZ
                                            pacchi_numpy[item2 - agg_step]['f2'] = 1
                                            # imposto disable a 1
                                            pacchi_numpy[item2 - agg_step]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # imposto autoadj a -1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - agg_step].autoadj = -1
                                            # imposto stato a VENAZ_S
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - agg_step].order_type = "VENAZ_S"
                                            # imposto carica a 0
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - agg_step].carica = 0
                                            # imposto disable a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - agg_step].disable = 1
                                            # modifico il vecchio pacco 1 e lo metto a stato -1 e disabilitato
                                            # imposto autoadj a -1
                                            # pacchi_numpy[item2]['f5'] = -1
                                            # imposto disabled a 1
                                            # pacchi_numpy[item2]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # imposto autoadj a -1
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].autoadj = -1
                                            # imposto disabled a 1
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].disable = 1
                                            # imposto carica a 0
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].carica = 0
                                            # lo tolgo dal carico short
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                            #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #         pacchi_numpy[item2]['f1'] - 1].quantity_sell * \
                                            #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #         pacchi_numpy[item2]['f1'] - 1].sell_price
                                            # adesso devo ricostruire tutta la parte di aggiustamento avendo scalato
                                            # riparto dal pacco appena sotto il nuovo 3 e ricostruisco
                                            # finchè non sono sotto al limite inferiore di aggiustamento, modifico
                                            first = 0
                                            while pacchi_numpy[item2 - agg_step + i]['f3'] >= tappeto[
                                                        pacchi_numpy[item2]['f0'] - 1].aggiustamento_limite_inferiore:
                                                # se i / agg non ha resto --> è pacco -2
                                                # se i / agg ha resto --> è pacco -1
                                                if ((i + 1) % (agg_step + 1)) == 0:
                                                    # imposto autoadj a -2
                                                    pacchi_numpy[item2 - agg_step + i]['f5'] = -2
                                                    # imposto stato a ACQAZ
                                                    pacchi_numpy[item2 - agg_step + i]['f2'] = 1
                                                    # se è il primo -2, allora lo devo mettere abilitato
                                                    if first == 0:
                                                        # imposto disabled a 0
                                                        pacchi_numpy[item2 - agg_step + i]['f6'] = 0
                                                    else:
                                                        # imposto disabled a 1
                                                        pacchi_numpy[item2 - agg_step + i]['f6'] = 1
                                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                                    # se il vecchio disabled è 0 allora lo devo togliere dal carico short
                                                    if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                                pacchi_numpy[item2][
                                                                                    'f1'] - 1 + i - agg_step].disable == 0:
                                                        # lo tolgo dal carico short
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2][
                                                                    'f1'] - 1 + i - agg_step].quantity_sell * \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].sell_price
                                                    # imposto autoadj a -2
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].autoadj = -2
                                                    # imposto stato a ACQAZ_S
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2][
                                                            'f1'] - 1 + i - agg_step].order_type = "VENAZ_S"
                                                    if first == 0:
                                                        # imposto disabled a 0
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                            pacchi_numpy[item2]['f1'] - 1 + i - agg_step].disable = 0
                                                        first = 1
                                                    else:
                                                        # imposto disabled a 1
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                            pacchi_numpy[item2]['f1'] - 1 + i - agg_step].disable = 1
                                                else:
                                                    # imposto autoadj a -1
                                                    pacchi_numpy[item2 - agg_step + i]['f5'] = -1
                                                    # imposto stato a VENAZ
                                                    pacchi_numpy[item2 - agg_step + i]['f2'] = 1
                                                    # imposto disabled a 1
                                                    pacchi_numpy[item2 - agg_step + i]['f6'] = 1
                                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                                    # se il vecchio disabled è 0 allora lo devo togliere dal carico long
                                                    if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                                pacchi_numpy[item2][
                                                                                    'f1'] - 1 + i - agg_step].disable == 0:
                                                        # lo tolgo dal carico short
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2][
                                                                    'f1'] - 1 + i - agg_step].quantity_sell * \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].sell_price
                                                    # imposto autoadj a -1
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].autoadj = -1
                                                    # imposto stato a VENAZ_S
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2][
                                                            'f1'] - 1 + i - agg_step].order_type = "VENAZ_S"
                                                    # imposto disabled a 1
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].disable = 1
                                                i += 1
                                                if (item2 - agg_step + i) >= len(
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi):
                                                    break
                                            break
                                for item2 in pacco_meno_3:
                                    i = 1
                                    agg_step = tappeto[pacchi_numpy[item2]['f0'] - 1].aggiustamento_step - 1
                                    # imposto autoadj a -3
                                    pacchi_numpy[item2 - agg_step]['f5'] = -3
                                    # imposto stato a VENAZ
                                    pacchi_numpy[item2 - agg_step]['f2'] = 1
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a -3
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 - agg_step].autoadj = -3
                                    # imposto stato a VENAZ_S
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 - agg_step].order_type = "VENAZ_S"
                                    # imposto carica a 0
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 - agg_step].carica = 0
                                    # modifico il vecchio pacco -3 e lo metto a stato -1 e disabilitato
                                    # imposto autoadj a -1
                                    # pacchi_numpy[item2]['f5'] = -1
                                    # imposto disabled a 1
                                    # pacchi_numpy[item2]['f6'] = 1
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a -1
                                    # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                    #    pacchi_numpy[item2]['f1'] - 1].autoadj = -1
                                    # imposto disabled a 1
                                    # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                    #     pacchi_numpy[item2]['f1'] - 1].disable = 1
                                    # imposto carica a 0
                                    # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                    #     pacchi_numpy[item2]['f1'] - 1].carica = 0
                                    # lo tolgo dal carico short
                                    # tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                    #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                    #         pacchi_numpy[item2]['f1'] - 1].quantity_sell * \
                                    #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                    #         pacchi_numpy[item2]['f1'] - 1].sell_price
                                    # adesso devo ricostruire tutta la parte di aggiustamento avendo scalato
                                    # riparto dal pacco appena sopra il nuovo -3 e ricostruisco
                                    # finchè non sono sopra al limite superiore di aggiustamento, modifico
                                    while pacchi_numpy[item2 - agg_step + i]['f3'] <= tappeto[
                                                pacchi_numpy[item2]['f0'] - 1].aggiustamento_limite_superiore:
                                        # se i / agg non ha resto --> è pacco -2
                                        # se i / agg ha resto --> è pacco -1
                                        if (i % (agg_step + 1)) == 0:
                                            # imposto autoadj a -2
                                            pacchi_numpy[item2 - agg_step + i]['f5'] = -2
                                            # imposto stato a VENAZ
                                            pacchi_numpy[item2 - agg_step + i]['f2'] = 1
                                            # imposto disabled a 1
                                            pacchi_numpy[item2 - agg_step + i]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # se il vecchio disabled è 0 allora lo devo togliere dal carico short
                                            if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                        pacchi_numpy[item2][
                                                                            'f1'] - 1 + i - agg_step].disable == 0:
                                                # lo tolgo dal carico short
                                                tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].quantity_sell * \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].sell_price
                                            # imposto autoadj a -2
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].autoadj = -2
                                            # imposto stato a VENAZ_S
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].order_type = "VENAZ_S"
                                            # imposto disabled a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].disable = 1
                                        else:
                                            # imposto autoadj a -1
                                            pacchi_numpy[item2 - agg_step + i]['f5'] = -1
                                            # imposto stato a VENAZ
                                            pacchi_numpy[item2 - agg_step + i]['f2'] = 1
                                            # imposto disabled a 1
                                            pacchi_numpy[item2 - agg_step + i]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # se il vecchio disabled è 0 allora lo devo togliere dal carico short
                                            if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                        pacchi_numpy[item2][
                                                                            'f1'] - 1 + i - agg_step].disable == 0:
                                                # lo tolgo dal carico short
                                                tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_short -= \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].quantity_sell * \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 + i - agg_step].sell_price
                                            # imposto autoadj a -1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].autoadj = -1
                                            # imposto stato a VENAZ_S
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].order_type = "VENAZ_S"
                                            # imposto disabled a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + i - agg_step].disable = 1
                                        i += 1
                                        if (item2 - agg_step + i) >= len(tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi):
                                            break

                                # devo scalare tutto il carico di n = molt step - 1, quindi il pacco z ha carico del pacco z + n
                                # lo scalare del valore di carico parte dal pacco appena sopra il pacco appena eseguito
                                # modifico il carico di tutti i pacchi con carico = 1 e con id tappeto
                                pacco_carico = np.flatnonzero(
                                    np.logical_and(pacchi_numpy['f7'] == 1,
                                                   pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                # inverto e parto dall'alto, così i primi n pacchi in carico che trovo li cambio
                                # a carica = 0 e stato = VENAZ_S
                                z = 1
                                agg_step = tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step
                                for pac in pacco_carico[::-1]:
                                    # se il pacco è in carico, allora devo scalare
                                    if tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].carica == 1:
                                        if z < agg_step:
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].carica = 0
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].order_type = 'VENAZ_S'
                                            # imposto stato a VENAZ
                                            pacchi_numpy[pac]['f2'] = 1
                                            # imposto autoadj a 0
                                            pacchi_numpy[pac]['f5'] = 0
                                            # imposto carico a 0
                                            pacchi_numpy[pac]['f7'] = 0
                                            # anche nella struttura
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].autoadj = 0
                                            z += 1
                                        # è uno dei pacchi da cambiare carico e da long a short
                                        # imposto il nuovo real_buy_price
                                        tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                            pacchi_numpy[pac]['f1'] - 1].buy_price_real = \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].buy_price + (
                                                tappeto[pacchi_numpy[pac]['f0'] - 1].step * (tappeto[pacchi_numpy[pac][
                                                                                                         'f0'] - 1].aggiustamento_step - 1))
                                        # imposto il nuovo carico aggiustamento
                                        tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                            pacchi_numpy[pac]['f1'] - 1].aggiustamento_carico = \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].buy_price * \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].quantity_buy
                                # devo trasformare gli ultimi x = agg.step - 1 pacchi long in short
                                # cerco tutti i pacchi
                                pacco_short = np.flatnonzero(
                                    np.logical_and(np.logical_and(pacchi_numpy['f5'] == 0, pacchi_numpy['f7'] == 0),
                                                   pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                            #
                            # se audoadj == 2 e pacco in VEN, ho chiuso pacco, diventa regular
                            #
                            elif pacchi_numpy[item]['f5'] == 2 and pacchi_numpy[item]['f2'] == 1:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 0
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                            #
                            # se autoadj == 1 lo eseguo e poi lo metto a stato autoadj = 0
                            #
                            elif pacchi_numpy[item]['f5'] == 1:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 1
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                            #
                            # se autoadj == 0, pacco regular
                            #
                            elif pacchi_numpy[item]['f5'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # se ho pacco in carico --> acquisto short, altrimenti acquisto long
                                if pacchi_numpy[item]['f7'] == 1:
                                    # imposto carico a 0
                                    pacchi_numpy[item]['f7'] = 0
                                else:
                                    # imposto carico a 1
                                    pacchi_numpy[item]['f7'] = 1
                                pacchi_numpy[item]['f2'] = 1

                            #
                            # se autoadj == -2 e stato ACQ vuol dire che sto comprando un pacco venduto short in aggiustamento
                            #
                            elif pacchi_numpy[item]['f5'] == -2 and pacchi_numpy[item]['f6'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 1
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0

                            #
                            # se autoadj == -1 e stato ACQ vuol dire che sto comprando un pacco venduto short in aggiustamento
                            #
                            elif pacchi_numpy[item]['f5'] == -1 and pacchi_numpy[item]['f6'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 1
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                                # lu = len(tappeto[pacchi_numpy[item]['f0'] - 1].operazioni)
                                # for val in tappeto[pacchi_numpy[item]['f0'] - 1].pacchi:
                                #    writer.writerow([val.package_number])
                                # strutture.append(copy.deepcopy(tappeto[pacchi_numpy[item]['f0'] - 1].pacchi))
                            if stampa:
                                filename = "C:\\ope\\" + str(len(tappeto[0].operazioni)) + ".csv"
                                with open(filename, 'w', newline='') as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        ['Pacco', 'Operazione', 'Acquisto', 'Vendita', 'Autoagg', 'Disable', 'Carica',
                                         'n_Operazione', 'n_Autoagg', 'n_Disable', 'n_Carica'])
                                    for idx, item in enumerate(tappeto[0].pacchi):
                                        if item.autoadj != 0:
                                            tipo = item.order_type + '_A'
                                        else:
                                            tipo = item.order_type
                                        writer.writerow(
                                            [item.package_number, tipo, item.buy_price, item.sell_price, item.autoadj,
                                             item.disable, item.carica, pacchi_numpy[idx]['f2'],
                                             pacchi_numpy[idx]['f5'], pacchi_numpy[idx]['f6'], pacchi_numpy[idx]['f7']])
                                    csvfile.close()

                        for item in lis_b:
                            #
                            # se stato aggiustamento == -3, sono in fondo alla sequenza, devo attivare aggiustamento
                            #
                            if pacchi_numpy[item]['f5'] == -3:
                                # devo attivare  il primo con stato -2, metto il -3 a stato 0

                                # gestione del pacco con autoadj == -3
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # imposto lo stato di autoadj a 0, pacco regular
                                pacchi_numpy[item]['f5'] = 0
                                # imposto stato a ACQAZ
                                pacchi_numpy[item]['f2'] = 0
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1
                                # prendo l'aggiustamento_step e aumento l'indice di questo valore
                                # così so quale pacco -2 attivare
                                # imposto autoadj a 0
                                # pacchi_numpy[item - (tappeto[pacchi_numpy[item]['f0'] - 1].step * tappeto[
                                #     pacchi_numpy[item]['f0'] - 1].aggiustamento_step)]['f5'] = 0
                                # imposto disabled a 0
                                pacchi_numpy[item + tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step]['f6'] = 0
                                # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                # imposto autoadj a 0
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                                # imposto disabled a 0
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 + tappeto[
                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].disable = 0
                                # devo aggiungere il nuovo pacco al carico long
                                tappeto[pacchi_numpy[item]['f0'] - 1].valore_carico_long += \
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1].quantity_buy * \
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].buy_price

                            #
                            # - se stato aggiustamento == -2, devo attivare n pacchi sopra questo, n = molt step - 1
                            # - se c'è un altro pacco con autoadj == -2 sotto e stato disabled, devo abilitarlo
                            # - devo scalare sopra l'autoaggiustamento di x = molt step verso l'alto
                            # - devo scalare tutto il carico di n = molt step - 1, quindi il pacco z ha carico del pacco z + n
                            #   lo scalare del valore di carico parte dal pacco appena sopra il pacco appena eseguito
                            # - devo modificare gli ultimi n pacchi short (n = agg_step - 1) da ACQAZ_S a ACQAZ_L
                            #   devo cambiare il carico da short a long, toglierli da carica
                            #
                            elif pacchi_numpy[item]['f5'] == -2 and pacchi_numpy[item]['f2'] == 1:
                                # devo attivare tutti quelli con id maggiore e autoadj = -1 e questo che è a -2 lo tengo a -2
                                tappeto[pacchi_numpy[item]['f0'] - 1].punto_flat += tappeto[pacchi_numpy[item][
                                                                                                'f0'] - 1].step * (
                                                                                        tappeto[pacchi_numpy[item][
                                                                                                    'f0'] - 1].aggiustamento_step - 1)
                                # gestione del pacco con autoadj == -2
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # imposto lo stato di autoadj a 0, pacco regular
                                # pacchi_numpy[item]['f5'] = 0
                                # imposto stato a ACQAZ
                                pacchi_numpy[item]['f2'] = 0
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1

                                # prendo l'aggiustamento step del tappeto corrispondente a questo pacco (-1 perchè conto da 0)
                                # così so quanti pacchi in stato == -1 devo attivare (aggiustamento_step - 1)
                                numero_pacchi_da_attivare = tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step
                                i = 1
                                while i < numero_pacchi_da_attivare:
                                    # imposto autoadj a 0
                                    # pacchi_numpy[item + i]['f5'] = 0
                                    # imposto disabled a 0
                                    pacchi_numpy[item - i]['f6'] = 0
                                    # imposto stato in ACQ
                                    pacchi_numpy[item - i]['f2'] = 0
                                    # imposto carica a 1
                                    pacchi_numpy[item - i]['f7'] = 1
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a 0
                                    # tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 + i].autoadj = 0
                                    # imposto disabled a 0
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 - i].disable = 0
                                    # imposto stato in ACQAZ_S
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 - i].order_type = 'ACQAZ_S'
                                    # imposto una finta vendita al prezzo di carico: pacco_ven - (step*aggiustamento_step)
                                    # imposto il sell_real_price
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 - i].sell_price_real = \
                                        round(tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                  pacchi_numpy[item]['f1'] - 1 - i].sell_price - (
                                                  tappeto[pacchi_numpy[item]['f0'] - 1].step * (
                                                      tappeto[pacchi_numpy[item][
                                                                  'f0'] - 1].aggiustamento_step - 1)),
                                              5)
                                    # imposto il valore di carico di aggiustamento al sell price * quantita
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 - i].aggiustamento_carico = round(
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                            pacchi_numpy[item]['f1'] - 1 - i].sell_price_real *
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                            pacchi_numpy[item]['f1'] - 1 - i].quantity_sell, 2)
                                    # imposto carica a 1
                                    tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                        pacchi_numpy[item]['f1'] - 1 - i].carica = 1
                                    i += 1

                                # se c'è un altro pacco con autoadj == -2 sopra e stato disabled, devo abilitarlo
                                # controllo anche che l'id tappeto sia lo stesso
                                if not pacchi_numpy[item]['f4'] + (tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step * tappeto[pacchi_numpy[item]['f0'] - 1].step) > tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_limite_superiore:
                                    if pacchi_numpy[item + tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                        'f5'] == -2 \
                                            and pacchi_numpy[
                                                        item + tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                                'f0'] == pacchi_numpy[item]['f0']:
                                        # imposto autoadj a 0
                                        # pacchi_numpy[item - tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step]['f5'] = 0
                                        # imposto disabled a 0
                                        pacchi_numpy[item + tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step][
                                            'f6'] = 0
                                        # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                        # imposto autoadj a 0
                                        # tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                                        # imposto disabled a 0
                                        tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1 + tappeto[
                                            pacchi_numpy[item]['f0'] - 1].aggiustamento_step].disable = 0
                                        # devo aggiungere il nuovo pacco al carico short
                                        tappeto[pacchi_numpy[item]['f0'] - 1].valore_carico_short += \
                                            tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                pacchi_numpy[item]['f1'] - 1 + tappeto[
                                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].quantity_sell * \
                                            tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[
                                                pacchi_numpy[item]['f1'] - 1 + tappeto[
                                                    pacchi_numpy[item]['f0'] - 1].aggiustamento_step].sell_price
                                # devo scalare sopra l'autoaggiustamento di x = molt step - 1 verso l'alto
                                # cerco pacco con autoadj a 3 e con lo stesso id tappeto f0
                                pacco_meno_3 = np.flatnonzero(
                                    np.logical_and(np.logical_and(pacchi_numpy['f5'] == 3, pacchi_numpy['f6'] == 0),
                                                   pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                # devo scalarlo di moltiplicatore step - 1 e questo pacco diventa 2
                                # se non ho pacchi 3 vuol dire che ho già aggiustato dall'altra parte
                                # allora devo cercare un pacco 1 e partire da li a scalare
                                if pacco_meno_3.size == 0:
                                    pacco_senza_3 = np.flatnonzero(
                                        np.logical_and(np.logical_and(pacchi_numpy['f5'] == 1, pacchi_numpy['f6'] == 1),
                                                       pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                    # se non trovo nemmeno il pacco con autoadj 1 allora ho finito l'aggiustamento
                                    # devo ripartire dagli ultimi pacchi short in alto
                                    if pacco_senza_3.size == 0:
                                        # da fareeeeeeeeeeeeeeeeeeeeeeee
                                        zzzz = 1
                                    else:
                                        # scalo tutti gli aggiustamenti, prendo ultimo pacco della lista
                                        for item2 in pacco_senza_3[::-1]:
                                            i = 1
                                            agg_step = tappeto[pacchi_numpy[item2]['f0'] - 1].aggiustamento_step - 1
                                            # imposto autoadj a 1
                                            pacchi_numpy[item2 + agg_step]['f5'] = 1
                                            # imposto stato a ACQAZ
                                            pacchi_numpy[item2 + agg_step]['f2'] = 0
                                            # imposto disable a 1
                                            pacchi_numpy[item2 + agg_step]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # imposto autoadj a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + agg_step].autoadj = 1
                                            # imposto stato a ACQAZ_L
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + agg_step].order_type = "ACQAZ_L"
                                            # imposto carica a 0
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + agg_step].carica = 0
                                            # imposto disable a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 + agg_step].disable = 1
                                            # modifico il vecchio pacco 1 e lo metto a stato 1 e disabilitato
                                            # imposto autoadj a 1
                                            # pacchi_numpy[item2]['f5'] = 1
                                            # imposto disabled a 1
                                            # pacchi_numpy[item2]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # imposto autoadj a 1
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].autoadj = 1
                                            # imposto disabled a 1
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].disable = 1
                                            # imposto carica a 0
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #     pacchi_numpy[item2]['f1'] - 1].carica = 0
                                            # lo tolgo dal carico long
                                            # tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                            #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #         pacchi_numpy[item2]['f1'] - 1].quantity_buy * \
                                            #     tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            #         pacchi_numpy[item2]['f1'] - 1].buy_price
                                            # adesso devo ricostruire tutta la parte di aggiustamento avendo scalato
                                            # riparto dal pacco appena sotto il nuovo 3 e ricostruisco
                                            # finchè non sono sotto al limite inferiore di aggiustamento, modifico
                                            first = 0
                                            while pacchi_numpy[item2 + agg_step - i]['f3'] >= tappeto[
                                                        pacchi_numpy[item2]['f0'] - 1].aggiustamento_limite_inferiore:
                                                # se i / agg non ha resto --> è pacco 2
                                                # se i / agg ha resto --> è pacco 1
                                                if ((i + 1) % (agg_step + 1)) == 0:
                                                    # imposto autoadj a 2
                                                    pacchi_numpy[item2 + agg_step - i]['f5'] = 2
                                                    # imposto stato a ACQAZ
                                                    pacchi_numpy[item2 + agg_step - i]['f2'] = 0
                                                    # se è il primo -2, allora metto disable a 0
                                                    if first == 0:
                                                        # imposto disabled a 0
                                                        pacchi_numpy[item2 + agg_step - i]['f6'] = 0
                                                    else:
                                                        # imposto disabled a 1
                                                        pacchi_numpy[item2 + agg_step - i]['f6'] = 1
                                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                                    # se il vecchio disabled è 0 allora lo devo togliere dal carico long
                                                    if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                                pacchi_numpy[item2][
                                                                                    'f1'] - 1 - i + agg_step].disable == 0:
                                                        # lo tolgo dal carico long
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2][
                                                                    'f1'] - 1 - i + agg_step].quantity_buy * \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].buy_price
                                                    # imposto autoadj a 2
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].autoadj = 2
                                                    # imposto stato a ACQAZ_L
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2][
                                                            'f1'] - 1 - i + agg_step].order_type = "ACQAZ_L"
                                                    if first == 0:
                                                        # imposto disabled a 0
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                            pacchi_numpy[item2]['f1'] - 1 - i + agg_step].disable = 0
                                                        first = 1
                                                    else:
                                                        # imposto disabled a 1
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                            pacchi_numpy[item2]['f1'] - 1 - i + agg_step].disable = 1
                                                else:
                                                    # imposto autoadj a 1
                                                    pacchi_numpy[item2 + agg_step - i]['f5'] = 1
                                                    # imposto stato a ACQAZ
                                                    pacchi_numpy[item2 + agg_step - i]['f2'] = 0
                                                    # imposto disabled a 1
                                                    pacchi_numpy[item2 + agg_step - i]['f6'] = 1
                                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                                    # se il vecchio disabled è 0 allora lo devo togliere dal carico long
                                                    if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                                pacchi_numpy[item2][
                                                                                    'f1'] - 1 - i + agg_step].disable == 0:
                                                        # lo tolgo dal carico long
                                                        tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2][
                                                                    'f1'] - 1 - i + agg_step].quantity_buy * \
                                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].buy_price
                                                    # imposto autoadj a 1
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].autoadj = 1
                                                    # imposto stato a ACQAZ_L
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2][
                                                            'f1'] - 1 - i + agg_step].order_type = "ACQAZ_L"
                                                    # imposto disabled a 1
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].disable = 1
                                                i += 1
                                                if (item2 + agg_step - i) < 0:
                                                    break
                                            break
                                for item2 in pacco_meno_3:
                                    i = 1
                                    agg_step = tappeto[pacchi_numpy[item2]['f0'] - 1].aggiustamento_step - 1
                                    # imposto autoadj a 3
                                    pacchi_numpy[item2 + agg_step]['f5'] = 3
                                    # imposto stato a ACQAZ
                                    pacchi_numpy[item2 + agg_step]['f2'] = 0
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a 3
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 + agg_step].autoadj = 3
                                    # imposto stato a ACQAZ_L
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 + agg_step].order_type = "ACQAZ_L"
                                    # imposto carica a 0
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1 + agg_step].carica = 0
                                    # modifico il vecchio pacco 3 e lo metto a stato 1 e disabilitato
                                    # imposto autoadj a 1
                                    pacchi_numpy[item2]['f5'] = 1
                                    # imposto disabled a 1
                                    pacchi_numpy[item2]['f6'] = 1
                                    # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                    # imposto autoadj a 1
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1].autoadj = 1
                                    # imposto disabled a 1
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1].disable = 1
                                    # imposto carica a 0
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                        pacchi_numpy[item2]['f1'] - 1].carica = 0
                                    # lo tolgo dal carico long
                                    tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            pacchi_numpy[item2]['f1'] - 1].quantity_buy * \
                                        tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                            pacchi_numpy[item2]['f1'] - 1].buy_price
                                    # adesso devo ricostruire tutta la parte di aggiustamento avendo scalato
                                    # riparto dal pacco appena sotto il nuovo 3 e ricostruisco
                                    # finchè non sono sotto al limite inferiore di aggiustamento, modifico
                                    while pacchi_numpy[item2 + agg_step - i]['f3'] >= tappeto[
                                                pacchi_numpy[item2]['f0'] - 1].aggiustamento_limite_inferiore:
                                        # se i / agg non ha resto --> è pacco 2
                                        # se i / agg ha resto --> è pacco 1
                                        if (i % (agg_step + 1)) == 0:
                                            # imposto autoadj a 2
                                            pacchi_numpy[item2 + agg_step - i]['f5'] = 2
                                            # imposto stato a ACQAZ
                                            pacchi_numpy[item2 + agg_step - i]['f2'] = 0
                                            # imposto disabled a 1
                                            pacchi_numpy[item2 + agg_step - i]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # se il vecchio disabled è 0 allora lo devo togliere dal carico long
                                            if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                        pacchi_numpy[item2][
                                                                            'f1'] - 1 - i + agg_step].disable == 0:
                                                # lo tolgo dal carico long
                                                tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].quantity_buy * \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].buy_price
                                            # imposto autoadj a 2
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].autoadj = 2
                                            # imposto stato a ACQAZ_L
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].order_type = "ACQAZ_L"
                                            # imposto disabled a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].disable = 1
                                        else:
                                            # imposto autoadj a 1
                                            pacchi_numpy[item2 + agg_step - i]['f5'] = 1
                                            # imposto stato a ACQAZ
                                            pacchi_numpy[item2 + agg_step - i]['f2'] = 0
                                            # imposto disabled a 1
                                            pacchi_numpy[item2 + agg_step - i]['f6'] = 1
                                            # ora devo modificare anche nella struttura del tappeto, non solo nell'array numpy
                                            # se il vecchio disabled è 0 allora lo devo togliere dal carico long
                                            if tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                                        pacchi_numpy[item2][
                                                                            'f1'] - 1 - i + agg_step].disable == 0:
                                                # lo tolgo dal carico long
                                                tappeto[pacchi_numpy[item2]['f0'] - 1].valore_carico_long -= \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].quantity_buy * \
                                                    tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                        pacchi_numpy[item2]['f1'] - 1 - i + agg_step].buy_price
                                            # imposto autoadj a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].autoadj = 1
                                            # imposto stato a ACQAZ_L
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].order_type = "ACQAZ_L"
                                            # imposto disabled a 1
                                            tappeto[pacchi_numpy[item2]['f0'] - 1].pacchi[
                                                pacchi_numpy[item2]['f1'] - 1 - i + agg_step].disable = 1
                                        i += 1
                                        if (item2 + agg_step - i) < 0:
                                            break

                                # devo scalare tutto il carico di n = molt step - 1, quindi il pacco z ha carico del pacco z + n
                                # lo scalare del valore di carico parte dal pacco appena sopra il pacco appena eseguito
                                # modifico il carico di tutti i pacchi con carico == 1 e con id tappeto
                                pacco_carico = np.flatnonzero(
                                    np.logical_and(pacchi_numpy['f7'] == 1,
                                                   pacchi_numpy['f0'] == pacchi_numpy[item]['f0']))
                                # parto dal basso, così i primi n pacchi in carico che trovo li cambio
                                # a carica = 0 e stato = ACQAZ_L
                                z = 1
                                agg_step = tappeto[pacchi_numpy[item]['f0'] - 1].aggiustamento_step
                                for pac in pacco_carico:
                                    # se il pacco è in carico, allora devo scalare
                                    if tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].carica == 1:
                                        if z < agg_step:
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].carica = 0
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].order_type = 'ACQAZ_L'
                                            # stato a ACQAZ
                                            pacchi_numpy[pac]['f2'] = 0
                                            # autoadj a 0
                                            pacchi_numpy[pac]['f5'] = 0
                                            # carico a 0
                                            pacchi_numpy[pac]['f7'] = 0
                                            # anche nella struttura
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].autoadj = 0
                                            z += 1
                                            # è uno dei pacchi da cambiare carico e da long a short
                                for pac in pacco_carico:
                                    # se il pacco è in carico, allora devo scalare
                                    if tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].carica == 1:
                                        # imposto il nuovo real_sell_price
                                        tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                            pacchi_numpy[pac]['f1'] - 1].sell_price_real = \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].sell_price - (
                                                tappeto[pacchi_numpy[pac]['f0'] - 1].step * (tappeto[pacchi_numpy[pac][
                                                                                                         'f0'] - 1].aggiustamento_step - 1))
                                        # imposto il nuovo aggiustamento carico
                                        tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                            pacchi_numpy[pac]['f1'] - 1].aggiustamento_carico = \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].sell_price * \
                                            tappeto[pacchi_numpy[pac]['f0'] - 1].pacchi[
                                                pacchi_numpy[pac]['f1'] - 1].quantity_sell
                            #
                            # se audoadj == -2 e pacco in ACQ, ho chiuso pacco, diventa regular
                            #
                            elif pacchi_numpy[item]['f5'] == -2 and pacchi_numpy[item]['f2'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].acquisto(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 1
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                            #
                            # se autoadj == -1 lo eseguo e poi lo metto a stato autoadj = 0
                            #
                            elif pacchi_numpy[item]['f5'] == -1:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 0
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 1
                                pacchi_numpy[item]['f7'] = 1
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                            #
                            # se autoadj == 0, pacco regular
                            #
                            elif pacchi_numpy[item]['f5'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                # se ho pacco in carico --> vendita long, altrimenti vendita short
                                if pacchi_numpy[item]['f7'] == 1:
                                    # imposto carico a 0
                                    pacchi_numpy[item]['f7'] = 0
                                else:
                                    # imposto carico a 1
                                    pacchi_numpy[item]['f7'] = 1
                                pacchi_numpy[item]['f2'] = 0

                            #
                            # se autoadj == 2 e sono in vendita, sto vendendo un pacco comprato in aggiustamento
                            #
                            elif pacchi_numpy[item]['f5'] == 2 and pacchi_numpy[item]['f6'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 0
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0
                            #
                            # se autoadj == 1 e sono in vendita, sto vendendo un pacco comprato in aggiustamento
                            #
                            elif pacchi_numpy[item]['f5'] == 1 and pacchi_numpy[item]['f6'] == 0:
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].vendita(
                                    prezzo, tappeto[pacchi_numpy[item]['f0'] - 1], data, ora, self.storico)
                                pacchi_numpy[item]['f2'] = 0
                                # imposto autoadj = 0
                                pacchi_numpy[item]['f5'] = 0
                                # imposto carico a 0
                                pacchi_numpy[item]['f7'] = 0
                                # anche nella struttura
                                tappeto[pacchi_numpy[item]['f0'] - 1].pacchi[pacchi_numpy[item]['f1'] - 1].autoadj = 0

                                # lu = len(tappeto[pacchi_numpy[item]['f0'] - 1].operazioni)
                                # tappeto[pacchi_numpy[item]['f0'] - 1].operazioni[lu - 1].paccus = copy.deepcopy(
                                # tappeto[pacchi_numpy[item]['f0'] - 1].pacchi)
                                # for val in tappeto[pacchi_numpy[item]['f0'] - 1].pacchi:
                                # writer.writerow([tappeto[pacchi_numpy[item]['f0'] - 1].pacchi])
                                # strutture.append(copy.deepcopy(tappeto[pacchi_numpy[item]['f0'] - 1].pacchi))
                            if stampa:
                                filename = "C:\\ope\\" + str(len(tappeto[0].operazioni)) + ".csv"
                                with open(filename, 'w', newline='') as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(
                                        ['Pacco', 'Operazione', 'Acquisto', 'Vendita', 'Autoagg', 'Disable', 'Carica',
                                         'n_Operazione', 'n_Autoagg', 'n_Disable', 'n_Carica'])
                                    for idx, item in enumerate(tappeto[0].pacchi):
                                        if item.autoadj != 0:
                                            tipo = item.order_type + '_A'
                                        else:
                                            tipo = item.order_type
                                        writer.writerow(
                                            [item.package_number, tipo, item.buy_price, item.sell_price, item.autoadj,
                                             item.disable, item.carica, pacchi_numpy[idx]['f2'],
                                             pacchi_numpy[idx]['f5'], pacchi_numpy[idx]['f6'], pacchi_numpy[idx]['f7']])
                                    csvfile.close()

                self.data_inizio += datetime.timedelta(days=1)
                csvfile.close()
                # opfile.close()
            else:
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
            item.pmc_gain = round(sum(pack.pmc_gain for pack in item.pacchi), 2)
            item.commissioni = round(sum(pack.commissioni for pack in item.pacchi), 2)
            item.profitto = round(item.gain - item.commissioni, 2)
            item.pmc_profitto = round(item.pmc_gain - item.commissioni, 2)
            if item.valore_max == 0:
                item.rendimento = 0
            else:
                # questo è quello vecchio senza pmc
                # item.rendimento = round(((item.gain - item.commissioni) / item.valore_max) * 100, 2)
                item.rendimento = round(((item.pmc_gain - item.commissioni) / item.valore_max) * 100, 2)
                item.rendimento_capitale = round(((item.pmc_gain - item.commissioni) / item.capitale) * 100, 2)
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
