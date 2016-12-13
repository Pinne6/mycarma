import os
import datetime
import csv

data_inizio = datetime.date(2002, 11, 17)
data_fine = datetime.date(2016, 11, 25)
data_diff = data_fine - data_inizio
crea_isin = 'IT0000000002'
crea_isin2 = 'NL6666666666'
folder = "C:\\intra\\"
tappa_buchi = "C:\\intra\\mini_14.csv"
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
