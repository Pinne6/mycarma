from hubstorage import HubstorageClient
import csv
import datetime


API = '702252227b054416b7b8823270989547'
hc = HubstorageClient(auth=API)
lista = []
# lista dei job, il primo della lista è l'ultimo eseguito
jobs = hc.get_project('119655').jobq.list()
items = hc.get_job('119655/1/1').items.list()
print(len(items))
for item in items:
    lista.append((item['isin'], item['isin_titolo'], item['scadenza'], item['strike'], item['tipo_opzione'], item['volatilita_implicita']))
csv_filename = datetime.datetime.today().strftime("%Y%m%d") + '.csv'
with open(csv_filename, 'w', newline="") as f:
    w = csv.writer(f)
    for item in lista:
        w.writerow(item)
exit()
