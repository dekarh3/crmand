from __future__ import print_function

from httplib2 import Http
from subprocess import Popen, PIPE
import os, sys
from string import digits
from random import random
from dateutil.parser import parse
import openpyxl

from apiclient import discovery                             # Механизм запроса данных
from googleapiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime
import time

from PyQt5.QtCore import QDate

#try:
#    import argparse
#    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#except ImportError:
#    flags = None
flags = None

from lib import unique, l, s, fine_phone, format_phone, lenl


SCOPES_CON = 'https://www.googleapis.com/auth/contacts' #.readonly'       #!!!!!!!!!!!!!!!!!!!!!!!!! read-only !!!!!!!!!!!
SCOPES_CAL = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'People API Python Quickstart'

IN_SNILS = ['ID']
IN_NAME = ['Площадь, м2', 'Участок', 'Телефоны', 'Цена', 'Ссылка на объявление']

def get_credentials_con():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'people.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES_CON)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def refresh_contacts():                             # Обновляем все контакты из гугля
    credentials_con = get_credentials_con()
    http_con = credentials_con.authorize(Http())
    service = discovery.build('people', 'v1', http=http_con,
                              discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

    # Вытаскиваем названия групп
    serviceg = discovery.build('contactGroups', 'v1', http=http_con,
                               discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
    resultsg = serviceg.contactGroups().list(pageSize=200).execute()
    groups_resourcenames = {}
    groups_resourcenames_reversed = {}
    contactGroups = resultsg.get('contactGroups', [])
    for i, contactGroup in enumerate(contactGroups):
        groups_resourcenames[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
        groups_resourcenames_reversed[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]

    # Контакты
    results = service.people().connections() \
        .list(
        resourceName='people/me',
        pageSize=2000,
        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                     'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                     'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                     'residences,skills,taglines,urls,userDefined') \
        .execute()
    connections = results.get('connections', [])
    contacts = []
    for i, connection in enumerate(connections):
        contact = {}
        name = ''
        iof = ''
        onames = connection.get('names', [])
        if len(onames) > 0:
            if onames[0].get('familyName'):
                name += onames[0].get('familyName').title() + ' '
            if onames[0].get('givenName'):
                name += onames[0].get('givenName').title() + ' '
                iof +=  onames[0].get('givenName').title() + ' '
            if onames[0].get('middleName'):
                name += onames[0].get('middleName').title()
                iof += onames[0].get('middleName').title() + ' '
            if onames[0].get('familyName'):
                iof += onames[0].get('familyName').title() + ' '
        contact['fio'] = name
        contact['iof'] = iof
        biographie = ''
        obiographies = connection.get('biographies', [])
        if len(obiographies) > 0:
            biographie = obiographies[0].get('value')
        contact['note'] = biographie
        phones = []
        ophones = connection.get('phoneNumbers', [])
        if len(ophones) > 0:
            for ophone in ophones:
                if ophone:
                    if ophone.get('canonicalForm'):
                        phones.append(format_phone(ophone.get('canonicalForm')))
                    else:
                        phones.append(format_phone(ophone.get('value')))
        contact['phones'] = phones
        memberships = []
        omemberships = connection.get('memberships', [])
        if len(omemberships) > 0:
            for omembership in omemberships:
                memberships.append(groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
        contact['groups'] = memberships
        stage = '---'
        calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
        cost = 0
        ostages = connection.get('userDefined', [])
        if len(ostages) > 0:
            for ostage in ostages:
                if ostage['key'].lower() == 'stage':
                    stage = ostage['value'].lower()
                if ostage['key'].lower() == 'calendar':
                    calendar = ostage['value']
                if ostage['key'].lower() == 'cost':
                    cost = float(ostage['value'])
        contact['stage'] = stage
        contact['calendar'] = calendar
        contact['cost'] = cost + random() * 1e-5

        town = ''
        oaddresses = connection.get('addresses', [])
        if len(oaddresses) > 0:
            town = oaddresses[0].get('formattedValue')
        contact['town'] = town
        email = ''
        oemailAddresses = connection.get('emailAddresses', [])
        if len(oemailAddresses) > 0:
            for oemailAddress in oemailAddresses:
                if oemailAddress:
                    email += oemailAddresses[0].get('value') + ' '
        contact['email'] = email
        contact['etag'] = connection['etag']
        contact['resourceName'] = connection['resourceName']
        urls = []
        ourls = connection.get('urls', [])
        if len(ourls) > 0:
            for ourl in ourls:
                urls.append(ourl['value'])
        contact['urls'] = urls
        contacts.append(contact)
    return {'cnt' : contacts, 'grp' : groups_resourcenames, 'grp_r' : groups_resourcenames_reversed}

cg = refresh_contacts()

workbooks =  []
sheets = []
for i, xlsx_file in enumerate(sys.argv):                              # Загружаем все xlsx файлы
    if i == 0:
        continue
    workbooks.append(openpyxl.load_workbook(filename=xlsx_file, read_only=True))
    sheets.append(workbooks[i-1][workbooks[i-1].sheetnames[0]])

a = sys.argv[1]
if len(a.split('/')) > 1:
    path = '/'.join(a.split('/')[:len(a.split('/'))-1])+'/'              # только путь без имени файла
else:
    path = ''


sheets_keys = []
for i, sheet in enumerate(sheets):                                    # Маркируем нужные столбцы
    keys = {}
    for j, row in enumerate(sheet.rows):
        if j > 0:
            break
        for k, cell in enumerate(row):                                # Проверяем, чтобы был СНИЛС
            if cell.value in IN_SNILS:
                keys[IN_SNILS[0]] = k
        if len(keys) > 0:
            for k, cell in enumerate(row):
                for n, name in enumerate(IN_NAME):
                    if n == 0:
                        continue
                    if cell.value != None:
                        if cell.value == name:
                            keys[name] = k
        else:
            print('В файле "' + sys.argv[i+1] + '" отсутствует колонка с ID')
            time.sleep(3)
            sys.exit()
    sheets_keys.append(keys)

without = True
for i, sheet in enumerate(sheets):
    if len(sheets_keys[i]) > 1:
        print('\nВ файле "' + sys.argv[i+1] + '" найдены столбцы:')
        for q in sheets_keys[i].keys():
            print('    ' + q)
        without = False
if without:
    print('Во всех файлах нет никаких столбцов, кроме СНИЛС')
    time.sleep(3)
    sys.exit()

    #print('\n'+ datetime.datetime.now().strftime("%H:%M:%S") +' Начинаем расчет \n')

our_statuses = []
fond_pays = []
total_rows = sheets[0].max_row
perc_rows = 0
big_rows = []
for j, row in enumerate(sheets[0].rows):                     # Загружаем все входные данные в одну строку
    our_status = {}
    fond_pay = {}
    if j == 0:
        continue
    big_row = {}
    for i, sheet in enumerate(sheets):
        if l(row[sheets_keys[i][IN_SNILS[0]]].value) < 1:
            continue
        for k, sheet_key in enumerate(sheets_keys[i]):
            if row[sheets_keys[i][sheet_key]].value != None and str(row[sheets_keys[i][sheet_key]].value).strip() != '': # and str(row[sheets_keys[0][sheet_key]].value).strip() != '—'
                if k == 2:
                    big_row[sheet_key] = str(row[sheets_keys[i][sheet_key]].value).split(',')
                else:
                    big_row[sheet_key] = str(row[sheets_keys[i][sheet_key]].value)
        big_rows.append(big_row)
q = 0
