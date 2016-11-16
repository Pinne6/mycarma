from hubstorage import HubstorageClient
import csv
import datetime
import smtplib
import os
import scraping_settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# server 'local' o 'remoto'
server = scraping_settings.server
# your email address, the sender
mail_from = scraping_settings.mail_from
# the TO address
mail_to = scraping_settings.mail_to
# your mail username
mail_username = scraping_settings.mail_username
# your mail password
mail_password = scraping_settings.mail_password
# your mail server
mail_server = scraping_settings.mail_server
# your mail port
mail_port = scraping_settings.mail_port
# API key
API = scraping_settings.API
# directory
dir = scraping_settings.dir
storico_jobs_csv = scraping_settings.storico_jobs_csv
lista = []
storico_jobs = []


def send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject,
               mail_body):
    """
    Invia una mail con tutti i parametri
    :param mail_from:
    :param mail_to:
    :param mail_username:
    :param mail_password:
    :param mail_server:
    :param mail_port:
    :param mail_subject:
    :param mail_body:
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = 'servizio.tappeto@gmail.com'
        msg['To'] = mail_to
        msg['Subject'] = mail_subject
        body = mail_body
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login('servizio.tappeto@gmail.com', 'amicifxt')
        text2 = msg.as_string()
        server.sendmail('servizio.tappeto@gmail.com', mail_to, text2)
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + 'Email inviata con successo')
        server.quit()
    except smtplib.SMTPException:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + 'Errore: Problema di invio mail')


if os.path.exists(storico_jobs_csv):
    with open(storico_jobs_csv) as f:
        for line in f:
            storico_jobs.append(line)
else:
    mail_subject = "Problema, non trovo file con lo storico jobs"
    mail_body = "Problema, non trovo file con lo storico jobs"
    send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
    exit()

hc = HubstorageClient(auth=API)
# lista dei job, il primo della lista e' l'ultimo eseguito
jobs = hc.get_project('119655').jobq.list()
for job in jobs:
    if job['state'] != 'finished':
        mail_subject = "Problema, stato job non finito"
        mail_body = job
        send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
        exit()
    if job['items'] == 0:
        mail_subject = "Problema, job non contiene elementi"
        mail_body = job
        send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
        exit()
    if job['key'] in str(storico_jobs):
        mail_subject = "Problema, job nuovo non presente"
        mail_body = job
        send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
        exit()
    items = hc.get_job(job['key']).items.list()
    job_key = [job['key']]
    break
for item in items:
    lista.append((item['isin'], item['isin_titolo'], item['scadenza'], item['strike'], item['tipo_opzione'],
                  item['volume_contratti'], item['volatilita_implicita']))
if server == 'remoto':
    directory = dir + lista[0][1] + "/opzioni/"
    csv_filename = dir + lista[0][1] + "/opzioni/" + datetime.datetime.today().strftime("%Y%m%d") + '.csv'
elif server == 'local':
    directory = dir + lista[0][1] + "\\opzioni\\"
    csv_filename = dir + lista[0][1] + "\\opzioni\\" + datetime.datetime.today().strftime("%Y%m%d") + '.csv'
if not os.path.exists(directory):
    os.makedirs(directory)
with open(csv_filename, 'w', newline="") as f:
    w = csv.writer(f)
    for item in lista:
        w.writerow(item)
with open(storico_jobs_csv, 'a', newline="") as f:
    writer = csv.writer(f)
    writer.writerow(job_key)
exit()
