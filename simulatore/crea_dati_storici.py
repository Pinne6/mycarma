import os
import datetime
import csv

data_inizio = datetime.date(2015, 9, 29)
data_fine = datetime.date(2017, 9, 28)
data_diff = data_fine - data_inizio
# il ticker di destinazione
crea_isin = 'US43289P1066'
# non serve
crea_isin2 = 'NL6666666666'
# la cartella di destinazione
folder = "C:\\intra\\"
# il file sorgente con i dati daily
tappa_buchi = "C:\\intra\\HIMAX.csv"
alternare = True

if os.path.exists(tappa_buchi):
    with open(tappa_buchi, newline='') as csvfile:
        for row in (list(csv.reader(csvfile, delimiter=";"))):
            if row[0] == '' or row[0] == 'DATA':
                continue
            data = row[0].split('/')
            nome_file = data[2] + data[1] + data[0]
            filename = folder + crea_isin + "\\" + nome_file + ".csv"
            apertura = row[1].replace(',', '.')
            massimo = row[2].replace(',', '.')
            minimo = row[3].replace(',', '.')
            chiusura = row[4].replace(',', '.')
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f, delimiter="|")
                if alternare:
                    linee = [('17.30.00', chiusura, '10000'), ('15.00.00', massimo, '10000'),
                             ('12.00.00', minimo, '10000'), ('09.00.00', apertura, '10000')]
                    alternare = False
                else:
                    linee = [('17.30.00', chiusura, '10000'), ('15.00.00', minimo, '10000'),
                             ('12.00.00', massimo, '10000'), ('09.00.00', apertura, '10000')]
                    alternare = True
                writer.writerows(linee)
                f.close()
exit()

for i in range(data_diff.days + 1):
    filename = folder + crea_isin + "\\" + data_inizio.strftime("%Y%m%d") + ".csv"
    filename2 = folder + crea_isin2 + "\\" + data_inizio.strftime("%Y%m%d") + ".csv"
    intra = []
    if os.path.exists(filename):
        f = csv.reader(open(filename), delimiter='|')
        linee = [l for l in f]
        for item in linee:
            if item[1] == '':
                continue
            item[1] = round(float(item[1]) * 0.66301798, 4)
        writer = csv.writer(open(filename2, 'w', newline=''), delimiter='|')
        writer.writerows(linee)
    else:
        data_inizio += datetime.timedelta(days=1)
        continue
    data_inizio += datetime.timedelta(days=1)
