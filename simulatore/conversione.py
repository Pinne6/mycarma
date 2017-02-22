import os
import datetime
import csv

data_inizio = datetime.date(2014, 11, 12)
data_fine = datetime.date(2014, 11, 13)
data_diff = data_fine - data_inizio
crea_isin = 'NL0010877643'
crea_isin2 = 'NL6666666666'
# la cartella di destinazione
folder = "C:\\intra\\"

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
