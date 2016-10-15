from django.db import models

# Create your models here.

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
        return storico

    def vendita(self, prezzo, tappeto, data, ora, storico):
        self.nr_vendite += 1
        self.sell_price_real = prezzo
        if self.carica == 0:
            gain = (prezzo * self.quantity_sell) - (self.buy_price_real * self.quantity_buy)
            self.gain += gain
            storico[len(storico) - 1].gain += gain
        else:
            gain = 0
        commissione = self.calcola_commissioni(self.quantity_sell, prezzo, tappeto)
        self.commissioni += commissione
        tappeto.operazioni.append(Operazione(self.order_type, data, ora, prezzo, self.quantity_sell, gain, commissione,
                                             self.sell_price))
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
        return storico

    def calcola_commissioni(self, quantita, prezzo, tappeto):
        if tappeto.tipo_commissione == 'P':
            p = (prezzo * quantita * tappeto.commissione) / 100
            if p < tappeto.min_commissione:
                p = tappeto.min_commissione
            if p > tappeto.max_commissione:
                p = tappeto.max_commissione
            return p
        else:
            return tappeto.commissione


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
                 max_commissione, in_carico):
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
        self.nr_acquisti = 0
        self.nr_vendite = 0
        self.gain = 0
        self.commissioni = 0
        self.profitto = 0
        self.valore_attuale = 0
        self.valore_carico = 0
        self.valore_min = 0
        self.valore_max = 0
        self.quantita_totale = 0
        self.rendimento = 0
        self.rendimento_teorico = 0
        if self.checkFX is True:
            self.tick = 5
        else:
            self.tick = 4
        prima_vendita = self.primo_acquisto + self.take + self.step
        check = round(round((self.primo_acquisto - self.limite_inferiore), self.tick) / self.step, self.tick)
        # controlli per verificare che i parametri abbiano senso
        pacchi_acquisto = []
        pacchi_vendita = []
        pacchi_stato = []
        pacchi_carica = []
        tappeto = []
        self.pacchi = []
        self.operazioni = []
        self.storico = []
        i = 0
        pacco_acquisto = self.limite_inferiore
        pacco_vendita = round(pacco_acquisto + self.take, 5)
        while pacco_vendita <= self.limite_superiore:
            pacchi_acquisto.append(pacco_acquisto)
            pacchi_vendita.append(pacco_vendita)
            if pacco_acquisto <= self.primo_acquisto:
                pacchi_stato.append('ACQAZ')
                pacchi_carica.append(0)
            if pacco_vendita >= prima_vendita:
                pacchi_stato.append('VENAZ')
                if in_carico > 0:
                    pacchi_carica.append(1)
                    in_carico -= 1
                else:
                    pacchi_carica.append(0)
            pacco_acquisto = round(pacco_acquisto + self.step, self.tick)
            pacco_vendita = round(pacco_acquisto + self.take, self.tick)
            singolo_pacco = Pacco(i + 1, self.isin, pacchi_stato[i], pacchi_acquisto[i], pacchi_vendita[i], self.take,
                                  self.quantita_acquisto, self.quantita_vendita, 0, pacchi_carica[i])
            self.pacchi.append(singolo_pacco)
            i += 1

    def operazione(self, tipo_operazione, data, ora, prezzo, quantita, gain, commissioni):
        if tipo_operazione == "ACQAZ":
            self.quantita_totale += quantita
            self.valore_attuale += (prezzo * quantita)
        elif tipo_operazione == "VENAZ":
            self.quantita_totale -= quantita
            self.valore_attuale -= (prezzo * quantita)
        if valore_attuale >= valore_max:
            valore_max = valore_attuale
