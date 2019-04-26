from __future__ import print_function

from httplib2 import Http
from subprocess import Popen, PIPE
import os
from sys import argv
from string import digits
from random import random
from dateutil.parser import parse
from collections import OrderedDict
import urllib.request, urllib.parse
import locale
import openpyxl


from apiclient import discovery                             # Механизм запроса данных
from googleapiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from instaparser.agents import Agent, exception_manager
from instaparser.entities import Account, Media
from instaparser.exceptions import InstagramException, InternetException
from requests.exceptions import HTTPError

from datetime import datetime, timedelta, time
import time
import pytz
utc=pytz.UTC

from PyQt5.QtCore import QDate, QDateTime, QSize, Qt, QByteArray, QTimer, QUrl, QEventLoop
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QMainWindow, QWidget, QApplication, QDialog, QLabel, \
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile


from crm_win import Ui_Form

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from lib import unique, l, s, fine_phone, format_phone
#---------------------------------------------------------------------------------------------------------------------
ALL_STAGES = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                     'нет на месте', 'недозвон', 'пауза', 'нет объявления', 'недоступен', '---', 'подумаю',
                    'нет контактов', 'не занимаюсь', 'не понимает', 'не интересно', 'мне не интересно', 'уже продали',
                    'не верит', 'дубль', 'по другому отработали', 'рыпу']
WORK_STAGES = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                     'нет на месте', 'недозвон', 'пауза']
LOST_STAGES = ['нет объявления']
PAUSE_STAGES = ['пауза']
PAUSE_NED_STAGES = ['недозвон', 'пауза'] # Откуда можно изменить на 'нет объявления'
PLUS_STAGES = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                     'нет на месте']
MINUS_STAGES = ['недоступен', '---', 'подумаю', 'нет контактов', 'не занимаюсь', 'не понимает', 'не интересно',
                'мне не интересно', 'уже продали', 'не верит', 'дубль', 'по другому отработали', 'рыпу']
#---------------------------------------------------------------------------------------------------------------------
AVITO_GROUPS = {
    '_КоттеджиСочи': 'https://www.avito.ru/sochi/doma_dachi_kottedzhi/',
    '_КвартирыСочи': 'https://www.avito.ru/sochi/kvartiry/',
    'КоттеджиАстр': 'https://www.avito.ru/astrahan/doma_dachi_kottedzhi/',
    'КвартирыАстр': 'https://www.avito.ru/astrahan/kvartiry/'
}
AVITO_GROUPS_SPLITS = {
    '_КоттеджиСочи': 'https://www.avito.ru/',
    '_КвартирыСочи': 'https://www.avito.ru/',
    'КоттеджиАстр': 'https://www.avito.ru/',
    'КвартирыАстр': 'https://www.avito.ru/'
}
#AVITO_GROUPS_SPLITS = {
#    '_КоттеджиСочи': 'https://www.avito.ru/sochi/',
#    '_КвартирыСочи': 'https://www.avito.ru/sochi/',
#    'КоттеджиАстр': 'https://www.avito.ru/astrahan/',
#    'КвартирыАстр': 'https://www.avito.ru/astrahan/'
#}
METABOLISM_GROUPS = {'_Метаболизм': 'http://emdigital.ru/stars/?cat='}

#MAX_PAGE = 2

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/people.googleapis.com-python-quickstart.json
SCOPES_CON = 'https://www.googleapis.com/auth/contacts' #.readonly'       #!!!!!!!!!!!!!!!!!!!!!!!!! read-only !!!!!!!!!!!
SCOPES_CAL = 'https://www.googleapis.com/auth/calendar'
APPLICATION_NAME = 'People API Python Quickstart'

#USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.11.1 ' \
#             'Chrome/65.0.3325.230 Safari/537.36'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap ' \
             'Chromium/70.0.3538.110 Chrome/70.0.3538.110 Safari/537.36'

def get_credentials(cr_file, sec_file, scopes):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join(os.path.expanduser('~'), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, cr_file)
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(sec_file, scopes)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials

#def get_credentials_cal():
#    home_dir = os.path.expanduser('~')
#    credential_dir = os.path.join(home_dir, '.credentials')
#    if not os.path.exists(credential_dir):
#        os.makedirs(credential_dir)
#    credential_path = os.path.join(credential_dir, 'calendar.googleapis.com-python-quickstart.json')#
#
#    store = Storage(credential_path)
#    credentials = store.get()
#    if not credentials or credentials.invalid:
#        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES_CAL)
#        flow.user_agent = APPLICATION_NAME + 'and test'
#        if flags:
#            credentials = tools.run_flow(flow, store, flags)
#        else: # Needed only for compatibility with Python 2.6
#            credentials = tools.run(flow, store)
#        print('Storing credentials to ' + credential_path)
#    return credentials


class MainWindowSlots(Ui_Form):   # Определяем функции, которые будем вызывать в слотах

    def setupUi(self, form):
        Ui_Form.setupUi(self,form)
        if len(argv):
            print(argv)
        self.agent = Agent()
        self.events_syncToken = ''
        self.contacty_syncTokenM = ''
        self.contacty_syncTokenS = ''
        self.show_site = 'avito'
        self.my_html = ''
        self.contacty = {}
        self.contacts_filtered = {}
        self.contacts_filtered_reverced = []
        self.contacts_filtered_reverced_main = []
        self.contacts_id_avitos = {}
        self.avitos_id_contacts = {}
        self.contacts_id_instas = {}
        self.instas_id_contacts = {}
        self.new_contact = False
        self.groups = []
        self.groups_resourcenames = {}
        self.group_cur = ''
        self.group_cur_id = 0
        self.group_last = '_Бигль'
        self.group_saved_id = None
        self.FIO_cur_id = ''
        self.FIO_saved_id = ''
        credentials = get_credentials('people.googleapis.com-python-quickstart.json','client_secret.json', SCOPES_CON)
        self.http_conM = credentials.authorize(Http())
        credentials = get_credentials('people.googleapis.com-python-quickstart-s.json','client_secret_9d.json',SCOPES_CON)
        self.http_conS = credentials.authorize(Http())
        credentials = get_credentials('calendar.googleapis.com-python-quickstart.json','client_secret.json',
                                      SCOPES_CAL)
        self.http_calM = credentials.authorize(Http())
        credentials = get_credentials('calendar.googleapis.com-python-quickstart-s.json','client_secret_9d.json',
                                      SCOPES_CAL)
        self.http_calS = credentials.authorize(Http())
        self.all_events = {}
        self.google2db4allM()
        self.google2db4allS()
        self.all_stages = []
        self.all_stages_reverce = {}
        self.refresh_stages()
        self.id_tek = 0
        self.show_clear = True
        self.stStageFrom = 0
        self.cbStageFrom.addItems(self.all_stages)
        self.cbStageFrom.setCurrentIndex(self.stStageFrom)
        self.stStageTo = len(self.all_stages) - 1
        self.cbStageTo.addItems(self.all_stages)
        self.cbStageTo.setCurrentIndex(self.stStageTo)
        self.cbStage.addItems(self.all_stages)
        self.calls = []
        calls = []
        calls_in = os.listdir('Incoming')
        for call in calls_in:
            calls.append('Incoming/'+ call)
        calls_out = os.listdir('Outgoing')
        for call in calls_out:
            calls.append('Outgoing/'+ call)
        calls_amr = [x for x in calls if x.endswith('.amr')]
        calls_wav = [x for x in calls if x.endswith('.wav')]
        calls_mp3 = [x for x in calls if x.endswith('.mp4')]
        self.calls = calls_amr + calls_mp3 +calls_wav
        self.calls_ids = []
        self.setup_twGroups()
        self.progressBar.hide()
        self.avitos = {}
        self.metabolitos = []
        self.labelAvitos.hide()
        return

    def clickBack(self):  # Отчет по звонкам с FROM_DATE по выбранной группе
        FROM_DATE = datetime(2019, 3, 14)
        calls_group_ids = []
        for i, call in enumerate(self.calls):
            for contact in self.contacts_filtered:
                for phone in self.contacts_filtered[contact]['phones']:
                    if format_phone(call.split(']_[')[1]) == format_phone(phone):
                        calls_group_ids.append(i)
        calls_sorted = {}
        for call_id in calls_group_ids:
            a = self.calls[call_id]
            t = datetime(l(a.split(']_[')[2][6:]), l(a.split(']_[')[2][3:5]), l(a.split(']_[')[2][:2]),
                         l(a.split(']_[')[3][:2]), l(a.split(']_[')[3][3:5]), l(a.split(']_[')[3][6:8]))
            calls_sorted[t] = call_id
        calls_sorted_filtered = {}
        for call_sorted in calls_sorted:
            if call_sorted > FROM_DATE:
                calls_sorted_filtered[call_sorted] = calls_sorted[call_sorted]
        calls_ids_buff = []
        for kk, i in sorted(calls_sorted_filtered.items(), key=lambda item: item[0]):  # Хитровычурная сортировка с исп. sorted()
            calls_ids_buff.append(i)
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet('Звонки')
        for call_id_buff in calls_ids_buff:
            a = self.calls[call_id_buff]
            name = a.split(']')[0].split('[')[1]
            tek_phone = a.split('[')[2].split(']')[0]
            t = datetime(l(a.split(']_[')[2][6:]), l(a.split(']_[')[2][3:5]), l(a.split(']_[')[2][:2]),
                         l(a.split(']_[')[3][:2]), l(a.split(']_[')[3][3:5]), l(a.split(']_[')[3][6:8]))
            ws.append([t,tek_phone,name])
        wb.save('звонки.xlsx')
        return

    def google2db4allM(self):                  # Google -> Внутр БД (все контакты) с полным обновлением
        # Доступы
        service = discovery.build('people', 'v1', http=self.http_conM,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        serviceg = discovery.build('contactGroups', 'v1', http=self.http_conM,
                                   discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        service_cal = discovery.build('calendar', 'v3', http=self.http_calM)  # Считываем весь календарь

        # Вытаскиваем названия групп
        groups_ok= False
        while not groups_ok:
            try:
                resultsg = serviceg.contactGroups().list(pageSize=200).execute()
                groups_ok = True
            except errors.HttpError as ee:
                print(datetime.now().strftime("%H:%M:%S") +' вытаскиваем названия групп еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
        self.groups_resourcenames = {}
        self.groups_resourcenames_main = {}
        self.groups_resourcenames_reversedM = {}
        contactGroups = resultsg.get('contactGroups', [])
        for i, contactGroup in enumerate(contactGroups):
            self.groups_resourcenames[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
            self.groups_resourcenames_main[contactGroup['resourceName'].split('/')[1]] = True
            self.groups_resourcenames_reversedM[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]


        # Контакты
        contacts_ok = False
        contacts_full = 'None'
        while not contacts_ok:
            if not self.contacty_syncTokenM:                             # Пустой syncToken - полное обновление
                connections = []
                results = {'nextPageToken':''}
                while str(results.keys()).find('nextPageToken') > -1:
                    if results['nextPageToken'] == '':
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageSize=2000,
                                requestSyncToken=True,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                                            ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    else:
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageToken=results['nextPageToken'],
                                pageSize=2000,
                                requestSyncToken=True,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                                            ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    connections.extend(results.get('connections', []))
                contacts_ok = True
                contacts_full = 'Full'
                self.contacty_syncTokenM = results['nextSyncToken']
            else:                                                       # Частичное обновление
                need_full_reload = False
                connections = []
                results = {'nextPageToken': ''}
                while str(results.keys()).find('nextPageToken') > -1:
                    if results['nextPageToken'] == '':
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageSize=2000,
                                requestSyncToken=True,
                                syncToken=self.contacty_syncTokenM,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                                                ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    else:
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageToken=results['nextPageToken'],
                                pageSize=2000,
                                requestSyncToken=True,
                                syncToken=self.contacty_syncTokenM,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                                                ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    connections.extend(results.get('connections', []))
                if need_full_reload:
                    self.contacty_syncTokenM = ''
                else:
                    self.contacty_syncTokenM = results['nextSyncToken']
                    contacts_ok = True
                    contacts_full = 'Part'

        # Календарь
        events_ok = False
        events_full = 'None'
        while not events_ok:
            if not self.events_syncToken:                             # Пустой syncToken - полное обновление
                calendars = []
                calendars_result = {'nextPageToken':''}
                while str(calendars_result.keys()).find('nextPageToken') > -1:
                    if calendars_result['nextPageToken'] == '':
                        try:
                            calendars_result = service_cal.events().list(
                                calendarId='primary',
                                showDeleted=True,
                                showHiddenInvitations=True,
                                singleEvents=True,
                                maxResults = 2000
                            ).execute()
                            token = calendars_result.get('nextSyncToken')
                            if token:
                                self.events_syncToken = token
                                print('==============',token)
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз - ошибка',
                                                            ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    else:
                        try:
                            calendars_result = service_cal.events().list(
                                calendarId='primary',
                                showDeleted=True,
                                showHiddenInvitations=True,
                                pageToken=calendars_result['nextPageToken'],
                                singleEvents=True,
                                maxResults = 2000
                            ).execute()
                            token = calendars_result.get('nextSyncToken')
                            if token:
                                self.events_syncToken = token
#                                print('==============',token)
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз - ошибка',
                                                             ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    calendars.extend(calendars_result.get('items', []))
                events_ok = True
                events_full = 'Full'
            else:                                                    # Частичное обновление
                need_full_reload = False
                calendars = []
                calendars_result = {'nextPageToken': ''}
                while str(calendars_result.keys()).find('nextPageToken') > -1:
                    if calendars_result['nextPageToken'] == '':
                        try:
                            calendars_result = service_cal.events().list(
                                calendarId='primary',
                                maxResults=2000,
                                showDeleted=True,
                                showHiddenInvitations=True,
                                syncToken=self.events_syncToken,
                                singleEvents=True
                            ).execute()
                            token = calendars_result.get('nextSyncToken')
                            if token:
                                self.events_syncToken = token
#                                print('==============',token)
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") +
                                        ' попробуем считать изменения в календаре еще раз - ошибка',
                                        ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    else:
                        try:
                            calendars_result = service_cal.events().list(
                                calendarId='primary',
                                maxResults=2000,
                                showDeleted=True,
                                showHiddenInvitations=True,
                                syncToken=self.events_syncToken,
                                pageToken=calendars_result['nextPageToken'],
                                singleEvents=True
                            ).execute()
                            token = calendars_result.get('nextSyncToken')
                            if token:
                                self.events_syncToken = token
#                                print('==============',token)
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") +
                                        ' попробуем считать изменения в календаре еще раз - ошибка',
                                        ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    calendars.extend(calendars_result.get('items', []))
                if need_full_reload:
                    self.events_syncToken = ''
                else:
                    events_ok = True
                    events_full = 'Part'

        changed_ids = set()                                    # Для частичного обновления (не все карточки)
        calendars_d = {}
        connections_d = {}
        if events_full == 'Part':
            for calendar in calendars:
                changed_ids.add(calendar['id'])
                calendars_d[calendar['id']] = calendar
        if contacts_full == 'Part':
            for connection in connections:
                changed_ids.add(connection['resourceName'].split('/')[1])
                connections_d[connection['resourceName'].split('/')[1]] = connection

        if events_full == 'None':
            print(datetime.now().strftime("%H:%M:%S") + ' синхронизация не удалась')
            return
        elif events_full == 'Full':
            self.all_events = {}
            for calendar in calendars:
                event = {}
                event['id'] = calendar['id']
                if str(calendar['start'].keys()).find('dateTime') > -1:
                    event['start'] = calendar['start']['dateTime']
                else:
                    event['start'] = str(utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00',
                                                                        "%Y-%m-%d %H:%M:%S")))
                if str(calendar.keys()).find('htmlLink') > -1:
                    event['www'] =calendar['htmlLink']
                else:
                    event['www'] = ''
                self.all_events[calendar['id']] = event
        elif events_full == 'Part':
            for changed_id in changed_ids:
                try:                                            # Если обновилось - обновляем в БД
                    calendar = calendars_d[changed_id]
                    event = {}
                    event['id'] = calendar['id']
                    if str(calendar['start'].keys()).find('dateTime') > -1:
                        event['start'] = calendar['start']['dateTime']
                    else:
                        event['start'] = str(
                            utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00', "%Y-%m-%d %H:%M:%S")))
                    if str(calendar.keys()).find('htmlLink') > -1:
                        event['www'] = calendar['htmlLink']
                    else:
                        event['www'] = ''
                    self.all_events[calendar['id']] = event
                except Exception as ee:
                    q = 0

        if contacts_full == 'None':
            print(datetime.now().strftime("%H:%M:%S") + ' синхронизация не удалась')
            return
        elif contacts_full == 'Full':
            self.avitos_id_contacts = {}
            self.contacts_id_avitos = {}
            self.contacts_id_instas = {}
            self.instas_id_contacts = {}
            self.contacty = {}
            events4delete = []
            number_of_new = 0
            for i, connection in enumerate(connections):
                contact = {}
                contact['main'] = True
                contact['resourceName'] = connection['resourceName'].split('/')[1]
                if not self.FIO_cur_id:
                    self.FIO_cur_id = connection['resourceName'].split('/')[1]
                name = ''
                iof = ''
                onames = connection.get('names', [])
                if len(onames) > 0:
                    if onames[0].get('familyName'):
                        name += onames[0].get('familyName').title() + ' '
                    if onames[0].get('givenName'):
                        name += onames[0].get('givenName').title() + ' '
                        iof += onames[0].get('givenName').title() + ' '
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
                memberships_id = []
                omemberships = connection.get('memberships', [])
                if len(omemberships) > 0:
                    for omembership in omemberships:
                        memberships.append(
                            self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
                        memberships_id.append(omembership['contactGroupMembership']['contactGroupId'])
                contact['groups'] = memberships
                contact['groups_ids'] = memberships_id
                stage = '---'
                calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
                cost = 0
                changed = QDate().currentDate().toString("dd.MM.yyyy")
                nameLink = ''
                ostages = connection.get('userDefined', [])
                if len(ostages) > 0:
                    for ostage in ostages:
                        if ostage['key'].lower() == 'stage':
                            stage = ostage['value'].lower()
                        if ostage['key'].lower() == 'calendar':
                            calendar = ostage['value']
                        if ostage['key'].lower() == 'cost':
                            cost = float(ostage['value'])
                        if ostage['key'].lower() == 'changed':
                            changed = ostage['value']
                        if ostage['key'].lower() == 'nameLink':
                            nameLink = ostage['value']
                contact['stage'] = stage
                contact['calendar'] = calendar
                contact['cost'] = cost + random() * 1e-5
                contact['changed'] = changed
                contact['nameLink'] = nameLink
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
                            email += oemailAddress.get('value') + ' '
                contact['email'] = email.strip()
                contact['etag'] = connection['etag']
                contact['avito'] = ''  # Фильтруем все ссылки на avito в поле 'avito'
                contact['instagram'] = ''  # а ссылки на instagram в поле 'instagram'
                urls = []
                ourls = connection.get('urls', [])
                if len(ourls) > 0:
                    for ourl in ourls:
                        urls.append(ourl['value'])
                        if ourl['value'].find('www.avito.ru') > -1:
                            contact['avito'] = ourl['value']
                        if ourl['value'].find('instagram.com') > -1:
                            contact['instagram'] = ourl['value'].strip().split('https://www.instagram.com/')[1]\
                                                                                                        .replace('/','')
                            self.contacts_id_instas[contact['resourceName']] = contact['instagram']
                            self.instas_id_contacts[contact['instagram']] = contact['resourceName']
                contact['urls'] = urls
                if str(contact.keys()).find('avito') > -1:
                    avito_x = contact['avito'].strip()
                    avito_i = len(avito_x) - 1
                    for j in range(len(avito_x) - 1, 0, -1):
                        if avito_x[j] not in digits:
                            avito_i = j + 1
                            break
                    contact['avito_id'] = avito_x[avito_i:]
                    self.contacts_id_avitos[contact['resourceName']] = contact['avito_id']
                    self.avitos_id_contacts[contact['avito_id']] = contact['resourceName']
                self.contacty[contact['resourceName']] = contact
                try:
                    contact_event = parse(self.all_events[contact['resourceName']]['start'])
                    if contact_event > utc.localize(datetime(2013, 1, 1, 0, 0)) \
                            and contact['stage'] not in WORK_STAGES and contact['stage'] not in LOST_STAGES:
                        events4delete.append(contact['resourceName'])
                except KeyError:
                    q=0
            for event4delete in events4delete:
                event4 = service_cal.events().get(calendarId='primary', eventId=event4delete).execute()
                event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                updated_event = service_cal.events().update(calendarId='primary', eventId=event4delete,
                                                            body=event4).execute()
        elif contacts_full == 'Part':
            for changed_id in changed_ids:
                try:                                            # Если обновилось - обновляем в БД
                    connection = connections_d[changed_id]
                    contact = {}
                    contact['main'] = True
                    contact['resourceName'] = connection['resourceName'].split('/')[1]
                    name = ''
                    iof = ''
                    onames = connection.get('names', [])
                    if len(onames) > 0:
                        if onames[0].get('familyName'):
                            name += onames[0].get('familyName').title() + ' '
                        if onames[0].get('givenName'):
                            name += onames[0].get('givenName').title() + ' '
                            iof += onames[0].get('givenName').title() + ' '
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
                            memberships.append(
                                self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
                    contact['groups'] = memberships
                    stage = '---'
                    calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
                    changed = QDate().currentDate().toString("dd.MM.yyyy")
                    cost = 0
                    nameLink = ''
                    ostages = connection.get('userDefined', [])
                    if len(ostages) > 0:
                        for ostage in ostages:
                            if ostage['key'].lower() == 'stage':
                                stage = ostage['value'].lower()
                            if ostage['key'].lower() == 'calendar':
                                calendar = ostage['value']
                            if ostage['key'].lower() == 'cost':
                                cost = float(ostage['value'])
                            if ostage['key'].lower() == 'changed':
                                changed = ostage['value']
                            if ostage['key'].lower() == 'nameLink':
                                nameLink = ostage['value']
                    contact['stage'] = stage
                    contact['calendar'] = calendar
                    contact['cost'] = cost + random() * 1e-5
                    contact['changed'] = changed
                    contact['nameLink'] = nameLink
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
                                email += oemailAddress.get('value') + ' '
                    contact['email'] = email.strip()
                    contact['etag'] = connection['etag']
                    contact['avito'] = ''  # Фильтруем все ссылки на avito в поле 'avito'
                    contact['instagram'] = ''  # а ссылки на instagram в поле 'instagram'
                    urls = []
                    ourls = connection.get('urls', [])
                    if len(ourls) > 0:
                        for ourl in ourls:
                            urls.append(ourl['value'])
                            if ourl['value'].find('www.avito.ru') > -1:
                                contact['avito'] = ourl['value']
                            if ourl['value'].find('instagram.com') > -1:
                                contact['instagram'] = ourl['value'].strip().split('https://www.instagram.com/')[1]\
                                                                                                        .replace('/','')
                                self.contacts_id_instas[contact['resourceName']] = contact['instagram']
                                self.instas_id_contacts[contact['instagram']] = contact['resourceName']
                    contact['urls'] = urls
                    if str(contact.keys()).find('avito') > -1:
                        avito_x = contact['avito'].strip()
                        avito_i = len(avito_x) - 1
                        for j in range(len(avito_x) - 1, 0, -1):
                            if avito_x[j] not in digits:
                                avito_i = j + 1
                                break
                        contact['avito_id'] = avito_x[avito_i:]
                        self.contacts_id_avitos[contact['resourceName']] = contact['avito_id']
                        self.avitos_id_contacts[contact['avito_id']] = contact['resourceName']
                    self.contacty[contact['resourceName']] = contact
                except Exception as ee:
                    q = 0
        return

    def google2db4allS(self):  # Google -> Внутр БД (все контакты) с полным обновлением
        # Доступы
        service = discovery.build('people', 'v1', http=self.http_conS,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        serviceg = discovery.build('contactGroups', 'v1', http=self.http_conS,
                                   discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        #service_cal = discovery.build('calendar', 'v3', http=self.http_calS)  # Считываем весь календарь

        # Вытаскиваем названия групп
        groups_ok = False
        while not groups_ok:
            try:
                resultsg = serviceg.contactGroups().list(pageSize=200).execute()
                groups_ok = True
            except errors.HttpError as ee:
                print(datetime.now().strftime("%H:%M:%S") + ' вытаскиваем названия групп еще раз - ошибка',
                      ee.resp['status'], ee.args[1].decode("utf-8"))
        self.groups_resourcenames_reversedS = {}
        contactGroups = resultsg.get('contactGroups', [])
        for i, contactGroup in enumerate(contactGroups):
            self.groups_resourcenames[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
            self.groups_resourcenames_main[contactGroup['resourceName'].split('/')[1]] = False
            self.groups_resourcenames_reversedS[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]

        # Контакты
        contacts_ok = False
        contacts_full = 'None'
        while not contacts_ok:
            if not self.contacty_syncTokenS:  # Пустой syncToken - полное обновление
                connections = []
                results = {'nextPageToken': ''}
                while str(results.keys()).find('nextPageToken') > -1:
                    if results['nextPageToken'] == '':
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageSize=2000,
                                requestSyncToken=True,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    else:
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageToken=results['nextPageToken'],
                                pageSize=2000,
                                requestSyncToken=True,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                            continue
                    connections.extend(results.get('connections', []))
                contacts_ok = True
                contacts_full = 'Full'
                self.contacty_syncTokenS = results['nextSyncToken']
            else:  # Частичное обновление
                need_full_reload = False
                connections = []
                results = {'nextPageToken': ''}
                while str(results.keys()).find('nextPageToken') > -1:
                    if results['nextPageToken'] == '':
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageSize=2000,
                                requestSyncToken=True,
                                syncToken=self.contacty_syncTokenS,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(
                                    datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                      ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    else:
                        try:
                            results = service.people().connections() \
                                .list(
                                resourceName='people/me',
                                pageToken=results['nextPageToken'],
                                pageSize=2000,
                                requestSyncToken=True,
                                syncToken=self.contacty_syncTokenS,
                                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                             'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                             'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                             'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                             'userDefined') \
                                .execute()
                        except errors.HttpError as ee:
                            if ee.resp['status'] == '410':
                                print(
                                    datetime.now().strftime("%H:%M:%S") + ' нужна полная синхронизация, запускаем')
                                need_full_reload = True
                                break
                            else:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз - ошибка',
                                      ee.resp['status'], ee.args[1].decode("utf-8"))
                                continue
                    connections.extend(results.get('connections', []))
                if need_full_reload:
                    self.contacty_syncTokenS = ''
                else:
                    self.contacty_syncTokenS = results['nextSyncToken']
                    contacts_ok = True
                    contacts_full = 'Part'

        changed_ids = set()  # Для частичного обновления (не все карточки)
        connections_d = {}
        if contacts_full == 'Part':
            for connection in connections:
                changed_ids.add(connection['resourceName'].split('/')[1])
                connections_d[connection['resourceName'].split('/')[1]] = connection
        if contacts_full == 'None':
            print(datetime.now().strftime("%H:%M:%S") + ' синхронизация не удалась')
            return
        elif contacts_full == 'Full':
            number_of_new = 0
            for i, connection in enumerate(connections):
                contact = {}
                contact['main'] = False
                contact['resourceName'] = connection['resourceName'].split('/')[1]
                if not self.FIO_cur_id:
                    self.FIO_cur_id = connection['resourceName'].split('/')[1]
                name = ''
                iof = ''
                onames = connection.get('names', [])
                if len(onames) > 0:
                    if onames[0].get('familyName'):
                        name += onames[0].get('familyName').title() + ' '
                    if onames[0].get('givenName'):
                        name += onames[0].get('givenName').title() + ' '
                        iof += onames[0].get('givenName').title() + ' '
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
                memberships_id = []
                omemberships = connection.get('memberships', [])
                if len(omemberships) > 0:
                    for omembership in omemberships:
                        memberships.append(
                            self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
                        memberships_id.append(omembership['contactGroupMembership']['contactGroupId'])
                contact['groups'] = memberships
                contact['groups_ids'] = memberships_id
                stage = '---'
                calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
                cost = 0
                changed = QDate().currentDate().toString("dd.MM.yyyy")
                nameLink = ''
                ostages = connection.get('userDefined', [])
                if len(ostages) > 0:
                    for ostage in ostages:
                        if ostage['key'].lower() == 'stage':
                            stage = ostage['value'].lower()
                        if ostage['key'].lower() == 'calendar':
                            calendar = ostage['value']
                        if ostage['key'].lower() == 'cost':
                            cost = float(ostage['value'])
                        if ostage['key'].lower() == 'changed':
                            changed = ostage['value']
                        if ostage['key'].lower() == 'nameLink':
                            nameLink = ostage['value']
                contact['stage'] = stage
                contact['calendar'] = calendar
                contact['cost'] = cost + random() * 1e-5
                contact['changed'] = changed
                contact['nameLink'] = nameLink
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
                            email += oemailAddress.get('value') + ' '
                contact['email'] = email.strip()
                contact['etag'] = connection['etag']
                contact['avito'] = ''  # Фильтруем все ссылки на avito в поле 'avito'
                contact['instagram'] = ''  # а ссылки на instagram в поле 'instagram'
                urls = []
                ourls = connection.get('urls', [])
                if len(ourls) > 0:
                    for ourl in ourls:
                        urls.append(ourl['value'])
                        if ourl['value'].find('www.avito.ru') > -1:
                            contact['avito'] = ourl['value']
                        if ourl['value'].find('instagram.com') > -1:
                            contact['instagram'] = ourl['value'].strip().split('https://www.instagram.com/')[1] \
                                .replace('/', '')
                            self.contacts_id_instas[contact['resourceName']] = contact['instagram']
                            self.instas_id_contacts[contact['instagram']] = contact['resourceName']
                contact['urls'] = urls
                if str(contact.keys()).find('avito') > -1:
                    avito_x = contact['avito'].strip()
                    avito_i = len(avito_x) - 1
                    for j in range(len(avito_x) - 1, 0, -1):
                        if avito_x[j] not in digits:
                            avito_i = j + 1
                            break
                    contact['avito_id'] = avito_x[avito_i:]
                    self.contacts_id_avitos[contact['resourceName']] = contact['avito_id']
                    self.avitos_id_contacts[contact['avito_id']] = contact['resourceName']
                self.contacty[contact['resourceName']] = contact
        elif contacts_full == 'Part':
            for changed_id in changed_ids:
                try:  # Если обновилось - обновляем в БД
                    connection = connections_d[changed_id]
                    contact = {}
                    contact['main'] = False
                    contact['resourceName'] = connection['resourceName'].split('/')[1]
                    name = ''
                    iof = ''
                    onames = connection.get('names', [])
                    if len(onames) > 0:
                        if onames[0].get('familyName'):
                            name += onames[0].get('familyName').title() + ' '
                        if onames[0].get('givenName'):
                            name += onames[0].get('givenName').title() + ' '
                            iof += onames[0].get('givenName').title() + ' '
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
                            memberships.append(
                                self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
                    contact['groups'] = memberships
                    stage = '---'
                    calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
                    changed = QDate().currentDate().toString("dd.MM.yyyy")
                    cost = 0
                    nameLink = ''
                    ostages = connection.get('userDefined', [])
                    if len(ostages) > 0:
                        for ostage in ostages:
                            if ostage['key'].lower() == 'stage':
                                stage = ostage['value'].lower()
                            if ostage['key'].lower() == 'calendar':
                                calendar = ostage['value']
                            if ostage['key'].lower() == 'cost':
                                cost = float(ostage['value'])
                            if ostage['key'].lower() == 'changed':
                                changed = ostage['value']
                            if ostage['key'].lower() == 'nameLink':
                                nameLink = ostage['value']
                    contact['stage'] = stage
                    contact['calendar'] = calendar
                    contact['cost'] = cost + random() * 1e-5
                    contact['changed'] = changed
                    contact['nameLink'] = nameLink
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
                                email += oemailAddress.get('value') + ' '
                    contact['email'] = email.strip()
                    contact['etag'] = connection['etag']
                    contact['avito'] = ''  # Фильтруем все ссылки на avito в поле 'avito'
                    contact['instagram'] = ''  # а ссылки на instagram в поле 'instagram'
                    urls = []
                    ourls = connection.get('urls', [])
                    if len(ourls) > 0:
                        for ourl in ourls:
                            urls.append(ourl['value'])
                            if ourl['value'].find('www.avito.ru') > -1:
                                contact['avito'] = ourl['value']
                            if ourl['value'].find('instagram.com') > -1:
                                contact['instagram'] = ourl['value'].strip().split('https://www.instagram.com/')[1] \
                                    .replace('/', '')
                                self.contacts_id_instas[contact['resourceName']] = contact['instagram']
                                self.instas_id_contacts[contact['instagram']] = contact['resourceName']
                    contact['urls'] = urls
                    if str(contact.keys()).find('avito') > -1:
                        avito_x = contact['avito'].strip()
                        avito_i = len(avito_x) - 1
                        for j in range(len(avito_x) - 1, 0, -1):
                            if avito_x[j] not in digits:
                                avito_i = j + 1
                                break
                        contact['avito_id'] = avito_x[avito_i:]
                        self.contacts_id_avitos[contact['resourceName']] = contact['avito_id']
                        self.avitos_id_contacts[contact['avito_id']] = contact['resourceName']
                    self.contacty[contact['resourceName']] = contact
                except Exception as ee:
                    q = 0
        return


    def google2db4etagM(self, cur_id=None):  # Google -> etag внутр БД (текущий контакт)
        if not cur_id:
            cur_id = self.FIO_cur_id
        ok_google = False
        while not ok_google:
            try:
                service = discovery.build('people', 'v1', http=self.http_conM,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                result = service.people().get(
                    resourceName='people/' + cur_id, personFields='metadata').execute()
                ok_google = True
            except errors.HttpError as ee:
                print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
        self.contacts_filtered[cur_id]['etag'] = result['etag']
        return result['etag']

    def google2db4etagS(self, cur_id=None):  # Google -> etag внутр БД (текущий контакт)
        if not cur_id:
            cur_id = self.FIO_cur_id
        ok_google = False
        while not ok_google:
            try:
                service = discovery.build('people', 'v1', http=self.http_conS,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                result = service.people().get(
                    resourceName='people/' + cur_id, personFields='metadata').execute()
                ok_google = True
            except errors.HttpError as ee:
                print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
        self.contacts_filtered[cur_id]['etag'] = result['etag']
        return result['etag']


    def db2form4one(self):              #  внутр. БД -> Форма
        if self.group_cur in METABOLISM_GROUPS.keys():    # Если в одной из групп по Метаболизму
            if self.contacty[self.FIO_cur_id]['instagram']:
                account = Account(self.contacty[self.FIO_cur_id]['instagram'])
                has_text = False
                if self.contacty[self.FIO_cur_id]['note']:
                    if self.contacty[self.FIO_cur_id]['note'][0] == '|' and \
                                                            len(self.contacty[self.FIO_cur_id]['note'].strip('\n')) > 2:
                        has_text = True
                    elif self.contacty[self.FIO_cur_id]['note'][0] != '|' and \
                                                                        len(self.contacty[self.FIO_cur_id]['note'] > 3):
                        has_text = True
                medias, pointer = self.agent.get_media(account,count=1,limit=1)
                if has_text:
                    self.teNote.setText(self.contacty[self.FIO_cur_id]['note'])
                else:
                    text = ''
                    if account.full_name:
                        text += account.full_name + '\n'
                    if account.biography:
                        text += account.biography + '\n'
                    if account.country_block:
                        text += account.country_block + '\n'
                    note = ''
                    for ch in text:
                        if ord(ch) < 65535:
                            note += ch
                    self.teNote.setPlainText(note)
        else:
            self.teNote.setText(self.contacty[self.FIO_cur_id]['note'])
        try:
            contact_event = parse(self.all_events[self.FIO_cur_id]['start'])
        except KeyError:
            contact_event = utc.localize(datetime(2012, 12, 31, 15, 0))
        self.deCalendar.setDate(contact_event)
        self.cbTime.setTime(contact_event.time())
        self.cbStage.setCurrentIndex(self.all_stages_reverce[self.contacty[self.FIO_cur_id]['stage']])
        if len(self.contacty[self.FIO_cur_id]['phones']) > 0:
            phones = fine_phone(self.contacty[self.FIO_cur_id]['phones'][0])
            for i, phone in enumerate(self.contacty[self.FIO_cur_id]['phones']):
                if i == 0:
                    continue
                phones += ' ' + fine_phone(phone)
            self.lePhones.setText(phones)
        elif not self.lePhones.text():
            phones = ''
            self.lePhones.setText(phones)
        self.calls_ids = []
        for i, call in enumerate(self.calls):
            for phone in self.contacty[self.FIO_cur_id]['phones']:
                if format_phone(call.split(']_[')[1]) == format_phone(phone):
                    self.calls_ids.append(i)
        self.leAddress.setText(self.contacty[self.FIO_cur_id]['town'])
        self.leEmail.setText(' '.join(self.contacty[self.FIO_cur_id]['email']))
        self.leIOF.setText(self.contacty[self.FIO_cur_id]['iof'])
        urls = ''
        for url in self.contacty[self.FIO_cur_id]['urls']:
            urls += url + ' '
        self.leUrls.setText(urls)
#        ca = self.contacts_filtered[self.FIO_cur_id]['calendar'].split('.')
#        self.deCalendar.setDate(QDate(int(ca[2]),int(ca[1]),int(ca[0])))
        self.leCost.setText(str(round(self.contacty[self.FIO_cur_id]['cost'], 4)))
        self.setup_twCalls()

    def db2www4one(self):
        if len(self.contacty[self.FIO_cur_id]['avito']) > 10 and self.show_site == 'avito':
            profile = QWebEngineProfile(self.preview)
            profile.setHttpUserAgent(USER_AGENT)
            page = QWebEnginePage(profile, self.preview)
            page.setUrl(QUrl(self.contacty[self.FIO_cur_id]['avito']))
            self.preview.setPage(page)
            self.preview.load(QUrl(self.contacty[self.FIO_cur_id]['avito']))
            self.preview.show()
        #            avito_x = self.contacts_filtered[self.FIO_cur_id]['avito'].strip()
        #            for i in range(len(avito_x)-1,0,-1):
        #                if avito_x[i] not in digits:
        #                    break
        #            html_x = ''
        #            while not html_x:
        #                avito_data = {'page-url' : avito_x}
        #                adata = urllib.parse.urlencode(avito_data).encode("utf-8")
        #                req = urllib.request.Request('https://www.avito.ru/items/stat/' + avito_x[i+1:] + '?step=0', data=adata,
        #                                             headers={'User-Agent' : USER_AGENT})                #, 'Referer' : avito_x})
        #                response = urllib.request.urlopen(req)   #'https://www.avito.ru/items/stat/' + avito_x[i+1:] + '?step=0', data=req)
        #                html_x = response.read().decode('utf-8')
        #            self.leDateStart.setText(html_x.split('<strong>')[1].split('</strong>')[0])
        elif len(self.contacty[self.FIO_cur_id]['instagram']) > 1 and self.show_site == 'instagram':
            profile = QWebEngineProfile(self.preview)
            profile.setHttpUserAgent(USER_AGENT)
            page = QWebEnginePage(profile, self.preview)
            page.setUrl(QUrl('https://www.instagram.com/' + self.contacty[self.FIO_cur_id]['instagram'] + '/'))
            self.preview.setPage(page)
            self.preview.show()

    def form2db4one(self):      #  Форма -> внутр. БД
        givenName = ''
        middleName = ''
        familyName = ''
        if self.leIOF.text():
            self.contacts_filtered[self.FIO_cur_id]['iof'] = self.leIOF.text()
            if len(self.leIOF.text().strip().split(' ')) > 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                middleName = self.leIOF.text().strip().split(' ')[1]
                for i, name in enumerate(self.leIOF.text().strip().split(' ')):
                    if i > 1:
                        familyName += name + ' '
            elif len(self.leIOF.text().strip().split(' ')) == 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                familyName = self.leIOF.text().strip().split(' ')[1]
            elif len(self.leIOF.text().strip().split(' ')) == 1:
                givenName = self.leIOF.text().strip().split(' ')[0]
        self.contacts_filtered[self.FIO_cur_id]['fio'] = familyName.strip() + ' ' + givenName.strip() + ' ' \
                                                         + middleName.strip()
        phones = []
        if len(self.lePhones.text().strip().split(' ')) > 0:
            for i, phone in enumerate(self.lePhones.text().strip().split(' ')):
                if phone.strip() != '':
                    phones.append(fine_phone(phone))
        self.contacts_filtered[self.FIO_cur_id]['phones'] = phones
        self.contacts_filtered[self.FIO_cur_id]['stage'] = self.cbStage.currentText()
        self.contacts_filtered[self.FIO_cur_id]['calendar'] = self.deCalendar.date().toString("dd.MM.yyyy")
        try:
            self.contacts_filtered[self.FIO_cur_id]['cost'] = float(self.leCost.text()) + random() * 1e-5
        except ValueError:
            self.contacts_filtered[self.FIO_cur_id]['cost'] = 0
        self.contacts_filtered[self.FIO_cur_id]['town'] = self.leAddress.text().strip()
        emails = []
        if len(self.leEmail.text().strip().split(' ')) > 0:
            for i, email in enumerate(self.leEmail.text().strip().split(' ')):
                if email.strip() != '' and len(email.split('@')) > 0:
                    emails.append(email)
        self.contacts_filtered[self.FIO_cur_id]['email'] = emails
        urls = []
        if len(self.leUrls.text().strip().split(' ')) > 0:
            for i, url in enumerate(self.leUrls.text().strip().split(' ')):
                if url.strip() != '' and len(url.split('.')) > 0:
                    urls.append(url)
        self.contacts_filtered[self.FIO_cur_id]['urls'] = urls
        if len(self.teNote.toPlainText()) > 0:
            if self.teNote.toPlainText()[0] != '|':
                self.teNote.setText('|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                                    '|' + '{0:0g}'.format(round(self.contacts_filtered[self.FIO_cur_id]['cost']*1000)/1000)+
                                    'м|' + '\n' + self.teNote.toPlainText())
            else:
                txt = self.teNote.toPlainText()
                self.teNote.setText('|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                                    '|' + '{0:0g}'.format(round(self.contacts_filtered[self.FIO_cur_id]['cost']*1000)/1000)+
                                    'м|' + '\n' + txt[txt.find('\n') + 1:])
        else:
            self.teNote.setText('|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                                '|' + '{0:0g}'.format(round(self.contacts_filtered[self.FIO_cur_id]['cost'] * 1000) / 1000) +
                                'м|' + '\n' + self.teNote.toPlainText())
        self.contacts_filtered[self.FIO_cur_id]['note'] = self.teNote.toPlainText()

    def refresh_stages(self):          # Добавляем в стандартные стадии стадии из контактов
        self.all_stages = ALL_STAGES
        for i, all_stage in enumerate(self.all_stages):
            self.all_stages_reverce[all_stage] = i
        for i, contact in enumerate(self.contacty.values()):
            has = False
            for all_stage in self.all_stages:
                if all_stage == contact['stage']:
                    has = True
            if not has:
                self.all_stages.append(contact['stage'])
                self.all_stages_reverce[contact['stage']] = len(self.all_stages) - 1
        return

    def click_pbPeopleFilter(self):  # Кнопка фильтр
        try:
            if self.contacty[self.FIO_cur_id]['main']:
                self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
            else:
                self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
            self.FIO_saved_id = self.FIO_cur_id
        except KeyError:
            q=0
#        self.google2db4one()           # обновляем информацию о контакте
        self.setup_twGroups()
        return

    def setup_twGroups(self):
        self.twGroups.setColumnCount(0)
        self.twGroups.setRowCount(0)        # Кол-во строк из таблицы
        groups = set()
        if l(self.lePhone.text()) > 0:
            for contact in self.contacty.values():
                has_phone = False
                for phone in contact['phones']:
                    if str(l(phone)).find(str(l(self.lePhone.text()))) > -1:
                        has_phone = True
                if not self.chbHasPhone.isChecked():
                    has_phone = True
                if has_phone:
                    for group in contact['groups']:
                        groups.add(group)
        else:
            for i, contact in enumerate(self.contacty.values()):
                if self.chbToToday.isChecked():
                    to_today = utc.localize(datetime.now())
                else:
                    to_today = utc.localize(datetime(2100,12,31,0,0))
                try:
                    contact_event = parse(self.all_events[contact['resourceName']]['start'])
                except KeyError:
                    contact_event = utc.localize(datetime(2012, 12, 31, 15, 0))
                except TypeError:
                    print('=========ОШИБКА!!!!!!!!!!!!',self.all_events[contact['resourceName']]['start'])
                has_to_today = contact_event <= to_today
                has_FIO = contact['fio'].lower().find(self.leFIO.text().strip().lower()) > -1
                has_note = s(contact['note']).lower().find(self.leNote.text().lower().strip()) > -1
                has_stage = (self.all_stages_reverce[contact['stage']] <= self.cbStageTo.currentIndex())\
                            and (self.all_stages_reverce[contact['stage']] >= self.cbStageFrom.currentIndex())
                if has_FIO and has_note and has_stage and has_to_today:
                    for group in contact['groups']:
                        groups.add(group)
        self.groups = []
        self.groups = sorted(groups)
        self.twGroups.setColumnCount(1)               # Устанавливаем кол-во колонок
        self.twGroups.setRowCount(len(groups))        # Кол-во строк из таблицы
        for i, group in enumerate(self.groups):
            self.twGroups.setItem(i-1, 1, QTableWidgetItem(group))
        # Устанавливаем заголовки таблицы
        self.twGroups.setHorizontalHeaderLabels(["Группы"])
        # Устанавливаем выравнивание на заголовки
        self.twGroups.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        # делаем ресайз колонок по содержимому
        self.twGroups.resizeColumnsToContents()
        self.click_twGroups()
        return

    def click_twGroups(self, index=None):
        if index == None:
            index = self.twGroups.model().index(0, 0)
            self.twGroups.setCurrentIndex(index)
        if self.group_saved_id:
            try:
                index = self.twGroups.model().index(self.groups.index(self.groups_resourcenames[self.group_saved_id]), 0)
            except KeyError:
                index = self.twGroups.model().index(0, 0)
            except ValueError:
                index = self.twGroups.model().index(0, 0)
            self.twGroups.setCurrentIndex(index)
            self.group_saved_id = None
        if index.row() < 0:
            return None
        self.group_cur = self.groups[index.row()]
        self.group_cur_id = index.row()
        self.setup_twFIO()
        return

    def setup_twFIO(self):
        self.contacts_filtered = {}
        self.contacts_filtered_reverced = []
        self.contacts_filtered_reverced_main = []
        contacts_f = []
        contacts_f_event = {}
        contacts_f_cost = {}
        contacts_f_fio = {}
        cs = {}
        cc = {}
        i = 0
        if l(self.lePhone.text()) > 0:
            for ind, contact in enumerate(self.contacty.values()):
                has_phone = False
                tel = self.lePhone.text()
                tel = ''.join([char for char in tel if char in digits])
                for phone in contact['phones']:
                    if str(l(phone)).find(tel) > -1:
                        has_phone = True
                if not self.chbHasPhone.isChecked():
                    has_phone = True
                if has_phone:
                    contacts_f.append(contact)
                    contacts_f[i]['contact_ind'] = ind
                    try:
                        contacts_f_event[i] = parse(self.all_events[contacts_f[i]['resourceName']]['start'])
                    except KeyError:
                        contacts_f_event[i] = utc.localize(datetime(2012, 12, 31, 15, 0))
                    contacts_f_fio[i] = contacts_f[i]['fio']
                    contacts_f_cost[i] = contacts_f[i]['cost']
                    i += 1
        else:
            for ind, contact in enumerate(self.contacty.values()):
                if self.chbToToday.isChecked():
                    to_today = utc.localize(datetime.now())
                else:
                    to_today = utc.localize(datetime(2100,12,31,0,0))
                try:
                    contact_event = parse(self.all_events[contact['resourceName']]['start'])
                except KeyError:
                    contact_event = utc.localize(datetime(2012, 12, 31, 15, 0))
                has_to_today = contact_event <= to_today
                has_FIO = contact['fio'].lower().find(self.leFIO.text().strip().lower()) > -1
                has_note = s(contact['note']).lower().find(self.leNote.text().lower().strip()) > -1
                has_group = False
                for group in contact['groups']:
                    if group == self.group_cur:
                        has_group = True
                has_stage = (self.all_stages_reverce[contact['stage']] <= self.cbStageTo.currentIndex())\
                            and (self.all_stages_reverce[contact['stage']] >= self.cbStageFrom.currentIndex())
                if has_FIO and has_note and has_group and has_stage and has_to_today:
                    contacts_f.append(contact)
                    contacts_f[i]['contact_ind'] = ind
                    try:
                        contacts_f_event[i] = parse(self.all_events[contacts_f[i]['resourceName']]['start'])
                    except KeyError:
                        contacts_f_event[i] = utc.localize(datetime(2012, 12, 31, 15, 0))
                    contacts_f_fio[i] = contacts_f[i]['fio']
                    contacts_f_cost[i] = contacts_f[i]['cost']
                    i += 1
        if self.chbDateSort.isChecked():                                        # Сортировка по дате
            contacts_f_event_sorted = OrderedDict(sorted(contacts_f_event.items(), reverse = True, key=lambda t: t[1]))
            for j, contact_f_event_sorted in enumerate(contacts_f_event_sorted):
                self.contacts_filtered[contacts_f[contact_f_event_sorted]['resourceName']] = \
                                                                                    contacts_f[contact_f_event_sorted]
                self.contacts_filtered_reverced.append(contacts_f[contact_f_event_sorted]['resourceName'])
                self.contacts_filtered_reverced_main.append(contacts_f[contact_f_event_sorted]['main'])
        elif self.chbCostSort.isChecked():                                      # Сортировка по цене
            contacts_f_cost_sorted = OrderedDict(sorted(contacts_f_cost.items(), reverse = True, key=lambda t: t[1]))
            for j, contact_f_cost_sorted in enumerate(contacts_f_cost_sorted):
                self.contacts_filtered[contacts_f[contact_f_cost_sorted]['resourceName']] = \
                                                                                    contacts_f[contact_f_cost_sorted]
                self.contacts_filtered_reverced.append(contacts_f[contact_f_cost_sorted]['resourceName'])
                self.contacts_filtered_reverced_main.append(contacts_f[contact_f_cost_sorted]['main'])
        else:                                                                   # Сортировка по фамилии
            contacts_f_fio_sorted = OrderedDict(sorted(contacts_f_fio.items(), key=lambda t: t[1]))
            for j, contact_f_fio_sorted in enumerate(contacts_f_fio_sorted):
                self.contacts_filtered[contacts_f[contact_f_fio_sorted]['resourceName']] = \
                                                                                    contacts_f[contact_f_fio_sorted]
                self.contacts_filtered_reverced.append(contacts_f[contact_f_fio_sorted]['resourceName'])
                self.contacts_filtered_reverced_main.append(contacts_f[contact_f_fio_sorted]['main'])
        self.twFIO.setColumnCount(1)                                # Устанавливаем кол-во колонок
        self.twFIO.setRowCount(len(self.contacts_filtered))         # Кол-во строк из таблицы
        for i, contact_id in enumerate(self.contacts_filtered):
            self.twFIO.setItem(i-1, 1, QTableWidgetItem(self.contacts_filtered[contact_id]['fio']))
        # Устанавливаем заголовки таблицы
        self.twFIO.setHorizontalHeaderLabels(["Ф.И.О."])
        # Устанавливаем выравнивание на заголовки
        self.twFIO.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        # делаем ресайз колонок по содержимому
        self.twFIO.resizeColumnsToContents()
        self.click_twFIO()
        return

    def click_twFIO(self, index=None):
        if self.FIO_saved_id:
            try:
                index = self.twFIO.model().index(self.contacts_filtered_reverced.index(self.FIO_saved_id), 0)
            except ValueError:
                index = self.twFIO.model().index(0, 0)
#                self.FIO_saved_id = self.contacts_filtered_reverced[0]
            self.twFIO.setCurrentIndex(index)
        elif index == None:
            index = self.twFIO.model().index(0, 0)
            self.twFIO.setCurrentIndex(index)
        self.clbCheckPhone.setIcon(QIcon('phone-yellow.png'))
        if index.row() < 0:
            return None
        self.twFIO.setCurrentIndex(index)
        self.FIO_cur_id = self.contacts_filtered_reverced[index.row()] # обновляем информацию о контакте и карточку
        self.google2db4allM()
        self.google2db4allS()
        self.lePhones.setText('')
        self.db2form4one()
        self.db2www4one()
        self.FIO_saved_id = ''
        has_phone = False
        if len(self.contacts_filtered[self.FIO_cur_id]['phones']):
            if l(self.contacts_filtered[self.FIO_cur_id]['phones'][0]):
                for contact in self.contacty:
                    if len(self.contacty[contact]['phones']):
                        for phone in self.contacty[contact]['phones']:
                            if len(self.contacts_filtered[self.FIO_cur_id]['phones']) and self.FIO_cur_id != contact:
                                for phone_tek in self.contacts_filtered[self.FIO_cur_id]['phones']:
                                    if fine_phone(phone) ==  fine_phone(phone_tek):
                                        has_phone = True
                                        break
                            if has_phone:
                                break
                        if has_phone:
                            break
        if has_phone:
            self.clbCheckPhone.setIcon(QIcon('phone-red.png'))
        else:
            self.clbCheckPhone.setIcon(QIcon('phone-green.png'))
        return

    def setup_twCalls(self):
        self.twCalls.setColumnCount(0)
        self.twCalls.setRowCount(1)
        count = len(self.calls_ids)
        self.twCalls.setColumnCount(count)
        cs = {}
        for call_id in self.calls_ids:
            a = self.calls[call_id]
            t = datetime(l(a.split(']_[')[2][6:]), l(a.split(']_[')[2][3:5]), l(a.split(']_[')[2][:2]),
                         l(a.split(']_[')[3][:2]), l(a.split(']_[')[3][3:5]), l(a.split(']_[')[3][6:8]))
            cs[t] = call_id
        calls_ids_buff = []
        for kk, i in sorted(cs.items(), key=lambda item: item[0]):  # Хитровычурная сортирвка с исп. sorted()
            calls_ids_buff.append(i)
        self.calls_ids = calls_ids_buff
        for i, call_id in enumerate(self.calls_ids):
            a = self.calls[call_id]
            t = datetime(l(a.split(']_[')[2][6:]), l(a.split(']_[')[2][3:5]), l(a.split(']_[')[2][:2]),
                         l(a.split(']_[')[3][:2]), l(a.split(']_[')[3][3:5]), l(a.split(']_[')[3][6:8]))
            self.twCalls.setItem(0, i, QTableWidgetItem(t.strftime('%d.%m.%y %H:%M') + '#'
                                                            + s(l(a.split(']_[')[1]))[9:]))
        self.twCalls.resizeColumnsToContents()
        return

    def click_twCalls(self, index=None):
        audios = ''
        for i, call_id in enumerate(self.calls_ids):
            audios +=  self.calls[call_id] + ' '
        proc = Popen('gnome-mpv ' + audios, shell=True, stdout=PIPE, stderr=PIPE)
        proc.wait()  # дождаться выполнения
        res = proc.communicate()  # получить tuple('stdout', 'stderr')
        if proc.returncode:
            print(res[1])
            print('result:', res[0])

    def click_clbRedo(self):
        try:
            if self.contacty[self.FIO_cur_id]['main']:
                self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
            else:
                self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
            self.FIO_saved_id = self.FIO_cur_id
        except IndexError:
            q=0
        # Перезагружаем ВСЕ контакты из gmail
        self.events_syncToken = ''
        self.contacty_syncTokenM = ''
        self.contacty_syncTokenS = ''
        self.google2db4allM()
        self.google2db4allS()
        self.setup_twGroups()
        return

    def click_clbSave(self):
        if not self.new_contact:
            self.google2db4allM()
            self.google2db4allS()
            pred_stage = self.contacts_filtered[self.FIO_cur_id]['stage']
            self.form2db4one()
            buf_contact = {}
            buf_contact['userDefined'] = [{},{},{},{},{}]
            buf_contact['userDefined'][0]['value'] = self.contacts_filtered[self.FIO_cur_id]['stage']
            buf_contact['userDefined'][0]['key'] = 'stage'
            buf_contact['userDefined'][1]['value'] = self.contacts_filtered[self.FIO_cur_id]['calendar']
            buf_contact['userDefined'][1]['key'] = 'calendar'
            buf_contact['userDefined'][2]['value'] = str(round(self.contacts_filtered[self.FIO_cur_id]['cost'], 4))
            buf_contact['userDefined'][2]['key'] = 'cost'
            buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
            buf_contact['userDefined'][3]['key'] = 'changed'
            buf_contact['userDefined'][4]['value'] = self.contacts_filtered[self.FIO_cur_id]['nameLink']
            buf_contact['userDefined'][4]['key'] = 'nameLink'
            buf_contact['biographies'] = [{}]
            buf_contact['biographies'][0]['value'] = self.contacts_filtered[self.FIO_cur_id]['note']
            buf_contact['etag'] = self.contacts_filtered[self.FIO_cur_id]['etag']
        else:
            pred_stage = 'пауза'
            buf_contact = {}
            buf_contact['userDefined'] = [{},{},{},{},{}]
            buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
            buf_contact['userDefined'][0]['key'] = 'stage'
            buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
            buf_contact['userDefined'][1]['key'] = 'calendar'
            try:
                buf_contact['userDefined'][2]['value'] = str(round(float(self.leCost.text()) + random() * 1e-5, 4))
            except ValueError:
                buf_contact['userDefined'][2]['value'] = '0'
            buf_contact['userDefined'][2]['key'] = 'cost'
            buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
            buf_contact['userDefined'][3]['key'] = 'changed'
            buf_contact['userDefined'][4]['value'] = ''
            buf_contact['userDefined'][4]['key'] = 'nameLink'
            buf_contact['biographies'] = [{}]
            if len(self.teNote.toPlainText()) > 0:
                if self.teNote.toPlainText()[0] != '|':
                    self.teNote.setText(
                        '|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                        '|' + buf_contact['userDefined'][2]['value'] + 'м|' + '\n' + self.teNote.toPlainText())
                else:
                    txt = self.teNote.toPlainText()
                    self.teNote.setText(
                        '|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                        '|' + buf_contact['userDefined'][2]['value'] + 'м|' + '\n' + txt[txt.find('\n') + 1:])
            else:
                self.teNote.setText(
                    '|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                    '|' + buf_contact['userDefined'][2]['value'] + 'м|' + '\n' + self.teNote.toPlainText())
                buf_contact['biographies'][0]['value'] = self.teNote.toPlainText()
        givenName = ''
        middleName = ''
        familyName = ''
        if self.leIOF.text():
            if len(self.leIOF.text().strip().split(' ')) > 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                middleName = self.leIOF.text().strip().split(' ')[1]
                for i, name in enumerate(self.leIOF.text().strip().split(' ')):
                    if i > 1:
                        familyName += name + ' '
            elif len(self.leIOF.text().strip().split(' ')) == 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                familyName = self.leIOF.text().strip().split(' ')[1]
            elif len(self.leIOF.text().strip().split(' ')) == 1:
                givenName = self.leIOF.text().strip().split(' ')[0]
        familyName = familyName.strip()
        buf_contact['names'] = [{'familyName': familyName,
                                  'givenName' : givenName,
                                  'middleName': middleName}]
        if self.leUrls.text():
            buf_contact['urls'] = []
            if len(self.leUrls.text().strip().split(' ')) > 0:
                for i, url in enumerate(self.leUrls.text().strip().split(' ')):
                    if url.strip() != '':
                        buf_contact['urls'].append({'value': url})
        if self.lePhones.text():
            buf_contact['phoneNumbers'] = []
            if len(self.lePhones.text().strip().split(' ')) > 0:
                for i, phone in enumerate(self.lePhones.text().strip().split(' ')):
                    if phone.strip() != '':
                        buf_contact['phoneNumbers'].append({'value': fine_phone(phone)})

        if self.leEmail.text():
            buf_contact['emailAddresses'] = []
            if len(self.leEmail.text().strip().split(' ')) > 0:
                for i, email in enumerate(self.leEmail.text().strip().split(' ')):
                    if email.strip() != '' and len(email.split('@')) > 0:
                        buf_contact['emailAddresses'].append({'value': email})
        if self.leAddress.text():
            if len(self.leAddress.text().strip()) > 0:
                buf_contact['addresses'] = [{'streetAddress': self.leAddress.text().strip()}]
        # Обновление/создание контакта
        if self.new_contact:
            # Создаем контакт
            service = discovery.build('people', 'v1', http=self.http_conM,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            ok_google = False
            while not ok_google:
                try:
                    resultsc = service.people().createContact(body=buf_contact).execute()
                    ok_google = True
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз - ошибка',
                          ee.resp['status'], ee.args[1].decode("utf-8"))
            self.FIO_cur_id = resultsc['resourceName'].split('/')[1]
            # Добавляем в текущую группу
            ok_google = False
            while not ok_google:
                try:
                    if self.contacty[self.FIO_cur_id]['main']:
                        group_id = self.groups_resourcenames_reversedM[self.group_cur]
                    else:
                        group_id = self.groups_resourcenames_reversedS[self.group_cur]

                    group_body = {'resourceNamesToAdd': ['people/' + self.FIO_cur_id], 'resourceNamesToRemove': []}
                    # почему-то работает, хотя должен быть как в serviceg
                    resultsg = service.contactGroups().members().modify(
                        resourceName='contactGroups/' + group_id,
                        body=group_body
                    ).execute()
                    ok_google = True
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз - ошибка',
                          ee.resp['status'], ee.args[1].decode("utf-8"))
        else:
            if self.contacty[self.FIO_cur_id]['main']:
                service = discovery.build('people', 'v1', http=self.http_conM,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                buf_contact['etag'] = self.google2db4etagM()
            else:
                service = discovery.build('people', 'v1', http=self.http_conS,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                buf_contact['etag'] = self.google2db4etagS()
            ok_google = False
            while not ok_google:
                try:
                    resultsc = service.people().updateContact(
                        resourceName='people/' + self.FIO_cur_id,
                        updatePersonFields='addresses,biographies,emailAddresses,names,phoneNumbers,urls,userDefined',
                        body=buf_contact).execute()
                    ok_google = True
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз - ошибка',
                                      ee.resp['status'], ee.args[1].decode("utf-8"))
# Календарь
        if self.contacty[self.FIO_cur_id]['main']: # События (календарь) только в main
            has_event = False
            try:                                                    # есть такой event - update'им
                event = self.all_events[self.FIO_cur_id]
                has_event = True
            except KeyError:  # нет такого event'а - создаем
                has_event = False
            calendar = {}
            if not has_event:
                event = {}
                event['id'] = self.FIO_cur_id
            calendar['id'] = self.FIO_cur_id
            event['start'] = datetime.combine(self.deCalendar.date().toPyDate(), self.cbTime.time().toPyTime()).isoformat()\
                             + '+04:00'
            calendar['start'] = {'dateTime' : datetime.combine(self.deCalendar.date().toPyDate(),
                                            self.cbTime.time().toPyTime()).isoformat() + '+04:00'}
            event['end'] = (datetime.combine(self.deCalendar.date().toPyDate(), self.cbTime.time().toPyTime())
                            + timedelta(minutes=15)).isoformat() + '+04:00'
            calendar['end'] = {'dateTime' : (datetime.combine(self.deCalendar.date().toPyDate(),
                                            self.cbTime.time().toPyTime()) + timedelta(minutes=15)).isoformat() + '+04:00'}
            calendar['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
            # Если стадия не рабочая - ставим прошлую дату
            if self.cbStage.currentText() not in WORK_STAGES and self.cbStage.currentText() not in LOST_STAGES:
                event['start'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                calendar['start'] = {'dateTime' : datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'}
                event['end'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                calendar['end'] = {'dateTime': datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'}
            # Если нет объявления, ставим ближайшую субботу
            elif self.cbStage.currentText() not in WORK_STAGES:
                event_date = parse(event['start'])
                if event_date < utc.localize(datetime(2012, 1, 7)):
                    lost_date = utc.localize(datetime(2012, 1, 7))
                else:
                    lost_date = event_date
                while lost_date.weekday() != 5:
                    lost_date += timedelta(days=1)
                event['start'] = (lost_date + timedelta(hours=19)).isoformat()
                calendar['start'] = {'dateTime' : (lost_date + timedelta(hours=19)).isoformat()}
                event['end'] = (lost_date + timedelta(hours=19,minutes=15)).isoformat()
                calendar['end'] = {'dateTime': (lost_date + timedelta(hours=19, minutes=15)).isoformat()}
            # Если не было объявления, а сейчас есть - ОТЛАДИТЬ !!!!!
            elif self.cbStage.currentText() in WORK_STAGES and pred_stage in LOST_STAGES:
                event_date = parse(event['start'])
                if event_date < utc.localize(datetime(2012, 1, 7)):
                    lost_date = utc.localize(datetime(2012, 1, 7))
                else:
                    lost_date = event_date
                lost_date -= timedelta(days=1)
                event['start'] = (lost_date + timedelta(hours=19)).isoformat()
                calendar['start'] = {'dateTime' : (lost_date + timedelta(hours=19)).isoformat()}
                event['end'] = (lost_date + timedelta(hours=19,minutes=15)).isoformat()
                calendar['end'] = {'dateTime' : (lost_date + timedelta(hours=19,minutes=15)).isoformat()}
            if self.new_contact:
                if len(self.lePhones.text().strip().split(' ')) > 0:
                    phones_fine = ''
                    phones = self.lePhones.text().strip().split(' ')
                    for phone in phones:
                        phones_fine += ' ' + fine_phone(phone)
                    phones_fine = phones_fine.strip()
                memos = self.preview.page().url().toString()
                calendar['description'] = phones_fine + '\n' + memos + '\n' + self.teNote.toPlainText()
                calendar['summary'] = self.leIOF.text() + ' - ' +  self.cbStage.currentText()
            else:
                phones = ''
                if len(self.contacts_filtered[self.FIO_cur_id]['phones']) > 0:
                    phones = fine_phone(self.contacts_filtered[self.FIO_cur_id]['phones'][0])
                    for i, phone in enumerate(self.contacts_filtered[self.FIO_cur_id]['phones']):
                        if i == 0:
                            continue
                        phones += ', ' + fine_phone(phone)
                memos = ''
                if len(self.contacts_filtered[self.FIO_cur_id]['urls']):
                    memos = self.contacts_filtered[self.FIO_cur_id]['urls'][0] + '\n'
                    for i, memo in enumerate(self.contacts_filtered[self.FIO_cur_id]['urls']):
                        if i == 0:
                            continue
                        memos += memo + '\n'
                calendar['description'] = phones + '\n' + memos + '\n' \
                                       + self.contacts_filtered[self.FIO_cur_id]['note']
                calendar['summary'] = self.contacts_filtered[self.FIO_cur_id]['fio'] + ' - ' +\
                                   self.contacts_filtered[self.FIO_cur_id]['stage']
            self.all_events[self.FIO_cur_id] = event
            # Обновляем календарь
            service_cal = discovery.build('calendar', 'v3', http=self.http_calM)
            ok_google = False
            while not ok_google:
                try:
                    if has_event:
                        calendar_result = service_cal.events().update(
                            calendarId='primary',
                            eventId=calendar['id'],
                            body=calendar).execute()
                    else:
                        calendar_result = service_cal.events().insert(calendarId='primary', body=calendar).execute()
                    ok_google = True
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем добавить/обновить event еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
        # Обновляем реверс по группе
        if self.new_contact:
            try:
                if self.contacty[self.FIO_cur_id]['main']:
                    self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
                else:
                    self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
                self.FIO_saved_id = self.FIO_cur_id
            except IndexError:
                q = 0
            self.new_contact = False
            self.events_syncToken = ''
            self.contacty_syncTokenM = ''
            self.contacty_syncTokenS = ''
            self.google2db4allM()
            self.google2db4allS()
            self.setup_twGroups()
        return

    def click_clbGoURL1(self):
        if len(self.contacts_filtered[self.FIO_cur_id]['urls']) > 0:
            if len(self.contacts_filtered[self.FIO_cur_id]['urls'][0]) > 5:
                profile = QWebEngineProfile(self.preview)
                profile.setHttpUserAgent(USER_AGENT)
                page = QWebEnginePage(profile, self.preview)
                page.setUrl(QUrl(self.contacts_filtered[self.FIO_cur_id]['urls'][0]))
                self.preview.setPage(page)
                self.preview.show()
        return

    def click_clbGoURL2(self):
        if len(self.contacts_filtered[self.FIO_cur_id]['urls']) > 1:
            if len(self.contacts_filtered[self.FIO_cur_id]['urls'][1]) > 5:
                proc = Popen('firefox --new-tab ' + self.contacts_filtered[self.FIO_cur_id]['urls'][1],
                             shell=True, stdout=PIPE, stderr=PIPE)
                proc.wait()  # дождаться выполнения
                res = proc.communicate()  # получить tuple('stdout', 'stderr')
                if proc.returncode:
                    print(res[1])
                    print('result:', res[0])

    def leIOF_changed(self, text):
        self.leIOF.setText(self.filter_addres(text))

    def update_from_site(self, FIOid = ''):
        if self.group_cur in AVITO_GROUPS.keys():   # Если в одной из групп avito
            avito_html = str(self.my_html)
            try:
                kott = avito_html.split('class="title-info-title-text"')[1].split('>')[1].split('<')[0].replace('\n','')
                price = avito_html.split('"js-item-price"')[1].split('content="')[1].split('"')[0].replace('\n','')
                nameLink = avito_html.split('"seller-info-name')[1].split('href="')[1].split('"')[0].replace('\n','')
                name = self.my_html.split('"seller-info-name')[1].split('title="Нажмите, чтобы перейти в профиль">')[1]\
                    .split('<')[0].replace('\n','').strip().replace(' ','_') + ' '
                addres = avito_html.split('itemprop="streetAddress">')[1].split('<')[0].replace('\n','')
            except IndexError:
                return
            if not self.leAddress.text():
                self.leAddress.setText(addres)
            only_digits = True
            for char in self.leIOF.text():
                if char not  in digits:
                    only_digits = False
            if not self.leIOF.text() or only_digits:
                self.leIOF.setText(name + ' ' + self.filter_addres(kott))
            if not self.leUrls.text():
                self.leUrls.setText(self.preview.page().url().toString())
            if not self.leCost.text() or self.leCost.text() == '0.0':
                self.leCost.setText('{0:0g}'.format(round((l(price) / 1000000 + random() * 1e-5)  * 1000) / 1000))
            if not self.teNote.toPlainText():
                self.teNote.setText('|' + self.cbStage.currentText() + '|' + self.deCalendar.date().toString("dd.MM.yyyy") +
                              '|' + self.leCost.text() + 'м|' + '\n')
            if nameLink and FIOid:
                self.contacty[FIOid]['nameLink'] = nameLink
            return


    def filter_addres(self,str_):
        str_ = str_.strip()
        if str_.find('.') > -1:                             # Обработка точек
            count = str_.count('.')
            if str_.rfind('.') == len(str_) - 1:
                count -= 1
            if str_.find('.') < len(str_) - 1:
                str_ = str_.replace('.', '_', count)
            if str_.find('.') == len(str_) - 1:
                str_ = str_.replace('.', '')
        if str_.find('-') > -1:
            str_ = str_.replace('-', '')
        if str_.find('Коттедж') > -1:                       # Обработка дом/коттедж/дача/таунхаус
            str_ = str_.replace(' Коттедж ', '')
        if str_.find('Дача') > -1:
            str_ = str_.replace(' Дача ', '')
        if str_.find('Дом') > -1:
            str_ = str_.replace(' Дом ', '')
        if str_.find('Таунхаус') > -1:
            str_ = str_.replace(' Таунхаус ', '')
        if str_.find(' на участке ') > -1:
            str_ = str_.replace(' на участке ', '+')
        if str_.find(' м²') > -1:
            str_ = str_.replace(' м²', 'м²')
        if str_.find(' сот') > -1:
            str_ = str_.replace(' сот', 'сот')
        if str_.find(' га') > -1:
            str_ = str_.replace(' га', 'га')
        if str_.find('м², ') > -1:                          # Обработка квартира
            str_ = str_.replace('м², ', 'м²')
        if str_.find(' эт') > -1:
            str_ = str_.replace(' эт', 'эт')
        if str_.find('>') > -1:
            str_ = str_.replace('>', '')
        if str_.find(' квартира, ') > -1:
            str_ = str_.replace(' квартира, ', '')
        if str_.find('Студия, ') > -1:
            str_ = str_.replace('Студия, ', 'студ')
        return str_

    def click_clbAvito(self):                       # Переключение с календаря на карточку avito или instagram
        if self.show_site == 'instagram':
            self.clbAvito.setIcon(QIcon('avito.png'))
            self.show_site = 'avito'
            if len(self.contacts_filtered[self.FIO_cur_id]['avito']) > 10:
                profile = QWebEngineProfile(self.preview)
                profile.setHttpUserAgent(USER_AGENT)
                page = QWebEnginePage(profile, self.preview)
                page.setUrl(QUrl(self.contacts_filtered[self.FIO_cur_id]['avito']))
                self.preview.setPage(page)
                self.preview.load(QUrl(self.contacts_filtered[self.FIO_cur_id]['avito']))
                self.preview.show()
        elif self.show_site == 'calendar':
            self.clbAvito.setIcon(QIcon('instagram.png'))
            self.show_site = 'instagram'
            if len(self.contacts_filtered[self.FIO_cur_id]['instagram']) > 1:
                profile = QWebEngineProfile(self.preview)
                profile.setHttpUserAgent(USER_AGENT)
                page = QWebEnginePage(profile, self.preview)
                page.setUrl(QUrl('https://www.instagram.com/' + self.contacts_filtered[self.FIO_cur_id]['instagram']
                                 + '/'))
                self.preview.setPage(page)
                self.preview.show()
        else:
            self.clbAvito.setIcon(QIcon('gcal.png'))
            self.show_site = 'calendar'
            self.preview.load(QUrl('https://calendar.google.com'))
            self.preview.show()

    def click_clbGCal(self):
        q=0

    def preview_loading(self):
        self.clbPreviewLoading.setIcon(QIcon('load.gif'))
        self.labelAvitos.hide()


    def preview_loaded(self):
        # парсим данные в карточку, ищем на странице отсутствующие в БД ссылки avito и помечаем их для создания карточек
        self.new_contact = False
        self.clbPreviewLoading.setIcon(QIcon('wave.png'))
        self.labelAvitos.hide()
        self.preview.page().toHtml(self.processHtml)
        if len(self.my_html) < 1000:
            return
#        if self.show_site != 'avito':
#            return
        # Если переходим в другую группу - сбрасываем накопленную информацию
        if self.group_cur != self.group_last:
            self.avitos = {}
            self.metabolitos = []
            self.group_last = self.group_cur

        if self.group_cur in AVITO_GROUPS.keys():   # Если в одной из групп avito
            if self.preview.page().url().toString().find('avito') > -1:
                avito_x = self.preview.page().url().toString().strip()
                avito_i = len(avito_x) - 1
                for j in range(len(avito_x) - 1, 0, -1):
                    if avito_x[j] not in digits:
                        avito_i = j + 1
                        break
            if len(avito_x[avito_i:]) > 3:          # Если цифр в конце url больше 3 - парсим данные в карточку
                if avito_x[avito_i:] in self.contacts_id_avitos.values():
                    self.new_contact = False        # Есть такой контакт - показываем его и заполняем пустые поля карточки
                    self.FIO_cur_id = self.avitos_id_contacts[avito_x[avito_i:]]
                    self.db2form4one()
                    self.update_from_site(FIOid=self.FIO_cur_id)
                else:
                    self.new_contact = True         # Нет контакта - очищаем и заполняем поля карточки
                    self.teNote.setText('')
                    self.cbStage.setCurrentIndex(self.all_stages_reverce['пауза'])
                    self.lePhones.setText('')
                    self.leAddress.setText('')
                    self.leEmail.setText('')
                    self.leIOF.setText('')
                    self.leUrls.setText('')
                    self.deCalendar.setDate(utc.localize(datetime.now()))
                    self.cbTime.setTime(datetime(2018,12,1,19,00).time())
                    self.leCost.setText('')
                    self.update_from_site()
            if not self.chbSumm.isChecked():
                return
            self.len_avitos = len(self.avitos)
            #self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
            #self.FIO_saved_id = self.FIO_cur_id
            avitos_raw = self.my_html.split('href="/' + AVITO_GROUPS[self.group_cur].split(
                AVITO_GROUPS_SPLITS[self.group_cur])[1])
            for i, avito_raw in enumerate(avitos_raw):
                if i == 0:
                    continue
                if avito_raw[:6] != 'prodam':
                    avito_x = avito_raw.split('"')[0].strip()
                    for j in range(len(avito_x) - 1, 0, -1):
                        if avito_x[j] not in digits:
                            break
                    try:
                        q = self.avitos[avito_x[j + 1:]]
                    except KeyError:
                        self.avitos[avito_x[j + 1:]] = AVITO_GROUPS[self.group_cur] + avito_raw.split('"')[0]
            if len(self.avitos) > self.len_avitos + 30:
                self.clbPreviewLoading.setIcon(QIcon('loaded.png'))
            if self.chbSumm.isChecked():
                self.len_avitos = len(self.avitos)
                self.labelAvitos.setText(str(len(self.avitos)))
                self.labelAvitos.show()
            return
        elif self.group_cur in METABOLISM_GROUPS.keys():    # Если в одной из групп по Метаболизму
            if self.preview.page().url().toString().find('emdigital.ru') > -1:
                if not self.chbSumm.isChecked():
                    return
                # self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
                # self.FIO_saved_id = self.FIO_cur_id
                instas_raw = self.my_html.split('class="starInsta" href="/instagram?account=')
                for i, insta_raw in enumerate(instas_raw):
                    if i == 0:
                        continue
                    if not insta_raw.split('"')[0] in self.metabolitos:
                        self.metabolitos.append(insta_raw.split('"')[0])
        else:
            return

    def click_clbNewAdd(self):                   # Добавляем новые контакты (всегда в main)
        service_cal = discovery.build('calendar', 'v3', http=self.http_calM)
        service = discovery.build('people', 'v1', http=self.http_conM,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        j = round(random()*1000000)
        self.progressBar.show()
        if self.group_cur in AVITO_GROUPS.keys():   # Если в одной из групп avito
            self.progressBar.setMaximum(len(self.avitos) - 1)
            for i, avito in enumerate(self.avitos):
                self.progressBar.setValue(i)
                try:
                    q = self.avitos_id_contacts[avito]
                    has_in_db = True
                except KeyError:
                    has_in_db = False
                if not has_in_db:
                    j += 1
                    buf_contact = {}
                    buf_contact['userDefined'] = [{},{},{},{},{}]
                    buf_contact['userDefined'][0]['value'] = 'пауза'
                    buf_contact['userDefined'][0]['key'] = 'stage'
                    buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
                    buf_contact['userDefined'][1]['key'] = 'calendar'
                    buf_contact['userDefined'][2]['value'] = '0'
                    buf_contact['userDefined'][2]['key'] = 'cost'
                    buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
                    buf_contact['userDefined'][3]['key'] = 'changed'
                    buf_contact['userDefined'][4]['value'] = ''
                    buf_contact['userDefined'][4]['key'] = 'nameLink'
                    buf_contact['names'] = [{'givenName': str(j)}]
                    buf_contact['urls'] = {'value': self.avitos[avito]}
                    buf_contact['biographies'] = [{}]
                    buf_contact['biographies'][0]['value'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) \
                                                              + '|0м|\n'
                    #buf_contact['phoneNumbers'] = ['0']
                    # Создаем контакт
                    ok_google = False
                    while not ok_google:
                        try:
                            resultsc = service.people().createContact(body=buf_contact).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))

                    # Добавляем в текущую группу
                    ok_google = False
                    while not ok_google:
                        try:
                            group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                            # почему-то работает, хотя должен быть как в serviceg
                            resultsg = service.contactGroups().members().modify(
                                resourceName='contactGroups/' + self.groups_resourcenames_reversedM[self.group_cur],
                                body=group_body
                            ).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                    # Добавляем событие через 30 дней
                    event = {}
                    event['id'] = resultsc['resourceName'].split('/')[1]
                    event['start'] = {'dateTime' : datetime.combine((datetime.now().date() + timedelta(days=30)),
                                              datetime.strptime('19:00','%H:%M').time()).isoformat() + '+04:00'}
                    event['end'] = {'dateTime' : datetime.combine((datetime.now().date() + timedelta(days=30)),
                                              datetime.strptime('19:15','%H:%M').time()).isoformat() + '+04:00'}
                    event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
                    event['description'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) + '|0м|\n' + \
                                           self.avitos[avito]
                    event['summary'] = '- пауза'
                    ok_google = False
                    while not ok_google:
                        try:
                            calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить event еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
        elif self.group_cur in METABOLISM_GROUPS.keys():    # Если в одной из групп по Метаболизму
            self.progressBar.setMaximum(len(self.metabolitos) - 1)
            for i, metabolito in enumerate(self.metabolitos):
                self.progressBar.setValue(i)
                try:
                    q = self.instas_id_contacts[metabolito]
                    has_in_db = True
                except KeyError:
                    has_in_db = False
                if not has_in_db:
                    j += 1
                    buf_contact = {}
                    buf_contact['userDefined'] = [{},{},{},{},{}]
                    buf_contact['userDefined'][0]['value'] = 'пауза'
                    buf_contact['userDefined'][0]['key'] = 'stage'
                    buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
                    buf_contact['userDefined'][1]['key'] = 'calendar'
                    buf_contact['userDefined'][2]['value'] = '0'
                    buf_contact['userDefined'][2]['key'] = 'cost'
                    buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
                    buf_contact['userDefined'][3]['key'] = 'changed'
                    buf_contact['userDefined'][4]['value'] = ''
                    buf_contact['userDefined'][4]['key'] = 'nameLink'
                    buf_contact['names'] = [{'givenName': metabolito}]
                    buf_contact['urls'] = {'value': 'https://www.instagram.com/' + metabolito + '/'}
                    buf_contact['biographies'] = [{}]
                    try:
                        account = Account(metabolito)
                        medias, pointer = self.agent.get_media(account,count=1,limit=1)
                    except InternetException:
                        continue
                    except InstagramException:
                        continue
                    except HTTPError:
                        continue
                    text = ''
                    if account.full_name:
                        text += account.full_name + '\n'
                    if account.biography:
                        text += account.biography + '\n'
                    if account.country_block:
                        text += account.country_block + '\n'
                    note = ''
                    for ch in text:
                        if ord(ch) < 65535:
                            note += ch
                    buf_contact['biographies'][0]['value'] = '|пауза|' + str(datetime.now().date()) \
                                                             + '|0м|\n' + note
                    # Создаем контакт
                    ok_google = False
                    while not ok_google:
                        try:
                            resultsc = service.people().createContact(body=buf_contact).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))

                    # Добавляем в текущую группу
                    ok_google = False
                    while not ok_google:
                        try:
                            group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                            resultsg = service.contactGroups().members().modify(
                                resourceName='contactGroups/' + self.groups_resourcenames_reversedM[self.group_cur],
                                body=group_body
                            ).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                    # Добавляем событие на сегодня
                    event = {}
                    event['id'] = resultsc['resourceName'].split('/')[1]
                    event['start'] = {'dateTime': datetime.combine((datetime.now().date()), datetime.strptime('20:00',
                                                                                '%H:%M').time()).isoformat() + '+04:00'}
                    event['end'] = {'dateTime': datetime.combine((datetime.now().date()), datetime.strptime('20:15',
                                                                                '%H:%M').time()).isoformat() + '+04:00'}
                    event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
                    event['description'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) + '|0м|\n' + \
                                           'https://www.instagram.com/' + metabolito + '/'
                    event['summary'] = '- пауза'
                    ok_google = False
                    while not ok_google:
                        try:
                            calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить event еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
        self.progressBar.hide()
        # Перезагружаем ВСЕ контакты из gmail
        self.FIO_saved_id = self.FIO_cur_id
        self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
        self.contacty_syncTokenM = ''
        self.contacty_syncTokenS = ''
        self.events_syncToken = ''
        self.google2db4allM()
        self.google2db4allS()
        self.setup_twGroups()

    def processHtml(self, html_x):
        self.my_html = str(html_x)
        return

    def click_clbStageRefresh(self):                            # Обновляем стадию или удаляем контакт и его событие
        ax = """
        has_in_avito = True / has_in_avito = False
        PLUS_STAGES / PAUSE_NED_STAGES / LOST_STAGES / MINUS_STAGES
        contact_old = False / contact_old = True
        has_phone = True / has_phone = False
        бдM = serviceM + service_calM / бдS = serviceS
        1. (has_in_avito = False; has_phone = False; PAUSE_NED_STAGES+LOST_STAGES+MINUS_STAGES; бдM) => (удаляем; бдM)
        2. (has_in_avito = False; has_phone = False; PAUSE_NED_STAGES+LOST_STAGES+MINUS_STAGES; бдS) => (удаляем; бдS)
        3. (PAUSE_NED_STAGES; has_in_avito = False; has_phone = True; бдМ) => (дат.now; LOST_STAGES; +event2012; бдМ)
        4. (PAUSE_NED_STAGES; has_in_avito = False; has_phone = True; бдS) => (дат.now; LOST_STAGES; +event2012; бдS->бдМ)
        5. (LOST_STAGES; has_in_avito = True; has_phone = True; бдМ) => (PAUSE_STAGES; дат.now; +event=calendar; бдМ)
        6. (LOST_STAGES; has_in_avito = True; has_phone = True; бдS) => (PAUSE_STAGES; дат.now; +event=calendar; бдS->бдМ)
        7. (PLUS_STAGES+PAUSE_NED_STAGES; has_phone = True; бдS) => (дат.now; +event=calendar; бдS->бдМ)
        8. (LOST_STAGES+MINUS_STAGES; has_phone = True; contact_old = True; бдМ) => (бдМ->бдS; -event)
        """

        if self.group_cur not in AVITO_GROUPS.keys():
            return
        if self.leFIO.text() or self.leNote.text() or self.lePhone.text():
            self.errMessage('!!!! С фильтрами - нельзя !!!')
            return
        if len(self.avitos) < len(self.contacts_filtered) / 3:
            self.errMessage('Слишком мало контактов в списке авито, всего ' + str(len(self.avitos)))
            return
        self.progressBar.setMaximum(len(self.contacts_filtered) - 1)
        self.progressBar.show()
        for i, contact in enumerate(self.contacts_filtered):
            serviceM = discovery.build('people', 'v1', http=self.http_conM,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            service_calM = discovery.build('calendar', 'v3', http=self.http_calM)
            serviceS = discovery.build('people', 'v1', http=self.http_conS,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            service_calS = discovery.build('calendar', 'v3', http=self.http_calS)
            self.progressBar.setValue(i)
            has_in_avito = False
            if str(self.contacts_filtered[contact].keys()).find('avito_id') > -1:
                for avito in self.avitos:
                    if self.contacts_filtered[contact]['avito_id'] == avito:
                        has_in_avito = True
                        break
            else:
                continue
            has_phone = len(self.contacts_filtered[contact]['phones']) > 0
            contact_old = datetime.strptime(self.contacts_filtered[contact]['changed'],'%d.%m.%Y') \
                          < (datetime.now() - timedelta(days=31))

            # (1,2)
            if not has_in_avito and not has_phone and self.contacts_filtered[contact]['stage'] in \
                    (PAUSE_NED_STAGES + LOST_STAGES + MINUS_STAGES):
                print('(1,2) Удаляем и контакт и событие: ', self.contacts_filtered[contact]['iof'])
                if self.contacty[self.FIO_cur_id]['main']:
                    serv_c = service_calM
                    serv = serviceM
                else:
                    serv_c = None
                    serv = serviceS
                ok_google = False
                if serv_c:
                    while not ok_google:
                        try:
                            event4 = serv_c.events().get(calendarId='primary', eventId=contact) \
                                .execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем запросить событие еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                    event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                    event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                    ok_google = False
                    while not ok_google:
                        try:
                            updated_event = serv_c.events().update(calendarId='primary',
                                                                        eventId=contact,
                                                                        body=event4).execute()
                            ok_google = True
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем удалить событие еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))

                ok_google = False
                while not ok_google:
                    try:
                        resultsc = serv.people().deleteContact(
                            resourceName='people/' + contact).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем удалить контакт еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
            if self.contacts_filtered[contact]['stage'] in PAUSE_NED_STAGES and not has_in_avito and has_phone:                                                                               # (3,4)
                print(self.contacts_filtered[contact]['iof'], 'пауза -> нет объявления и есть телефон(ы) '
                                                              '=> Удаляем только событие')
                ok_google = False
                while not ok_google:
                    try:
                        event4 = service_cal.events().get(calendarId='primary', eventId=contact) \
                            .execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем запросить событие еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                ok_google = False
                while not ok_google:
                    try:
                        updated_event = service_cal.events().update(calendarId='primary',
                                                                    eventId=contact,
                                                                    body=event4).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем удалить событие еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                buf_contact = {}
                buf_contact['userDefined'] = [{},{},{},{},{}]
                buf_contact['userDefined'][0]['value'] = self.contacts_filtered[contact]['stage']
                buf_contact['userDefined'][0]['key'] = 'stage'
                buf_contact['userDefined'][1]['value'] = self.contacts_filtered[contact]['calendar']
                buf_contact['userDefined'][1]['key'] = 'calendar'
                buf_contact['userDefined'][2]['value'] = str(round(self.contacts_filtered[contact]['cost'], 4))
                buf_contact['userDefined'][2]['key'] = 'cost'
                buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
                buf_contact['userDefined'][3]['key'] = 'changed'
                buf_contact['userDefined'][4]['value'] = self.contacts_filtered[contact]['nameLink']
                buf_contact['userDefined'][4]['key'] = 'nameLink'
                if self.contacts_filtered[contact]['main']:
                    buf_contact['etag'] = self.google2db4etagM(cur_id=contact)
                else:
                    buf_contact['etag'] = self.google2db4etagS(cur_id=contact)
                ok_google = False
                while not ok_google:
                    try:
                        resultsc = service.people().updateContact(
                            resourceName='people/' + contact,
                            updatePersonFields='userDefined',
                            body=buf_contact).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем обновить стадию еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))

            if (5,6) self.contacts_filtered[contact]['stage'] == 'пауза':   # Было 'нет объявления' стало 'пауза' (5,6)
                print(self.contacts_filtered[contact]['iof'], 'нет объявления -> пауза')
                buf_contact = {}
                buf_contact['userDefined'] = [{},{},{},{},{}]
                buf_contact['userDefined'][0]['value'] = self.contacts_filtered[contact]['stage']
                buf_contact['userDefined'][0]['key'] = 'stage'
                buf_contact['userDefined'][1]['value'] = self.contacts_filtered[contact]['calendar']
                buf_contact['userDefined'][1]['key'] = 'calendar'
                buf_contact['userDefined'][2]['value'] = str(round(self.contacts_filtered[contact]['cost'], 4))
                buf_contact['userDefined'][2]['key'] = 'cost'
                buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
                buf_contact['userDefined'][3]['key'] = 'changed'
                buf_contact['userDefined'][4]['value'] = self.contacts_filtered[contact]['nameLink']
                buf_contact['userDefined'][4]['key'] = 'nameLink'
                if self.contacts_filtered[contact]['main']:
                    buf_contact['etag'] = self.google2db4etagM(cur_id=contact)
                else:
                    buf_contact['etag'] = self.google2db4etagS(cur_id=contact)
                ok_google = False
                while not ok_google:
                    try:
                        resultsc = service.people().updateContact(
                            resourceName='people/' + contact,
                            updatePersonFields='userDefined',
                            body=buf_contact).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем обновить стадию еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                        if self.contacts_filtered[contact]['main']:
                            buf_contact['etag'] = self.google2db4etagM(cur_id=contact)
                        else:
                            buf_contact['etag'] = self.google2db4etagS(cur_id=contact)
                ok_google = False
                while not ok_google:
                    try:
                        event4 = service_cal.events().get(calendarId='primary', eventId=contact) \
                            .execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем запросить событие еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                event4['start']['dateTime'] = datetime.combine(datetime.strptime(self.contacts_filtered[contact]['calendar'],
                            '%d.%m.%Y').date(), datetime.strptime('19:00', '%H:%M').time()).isoformat() + '+04:00'
                event4['end']['dateTime'] = datetime.combine(datetime.strptime(self.contacts_filtered[contact]['calendar'],
                            '%d.%m.%Y').date(), datetime.strptime('19:15', '%H:%M').time()).isoformat() + '+04:00'
                ok_google = False
                while not ok_google:
                    try:
                        updated_event = service_cal.events().update(calendarId='primary',
                                                                    eventId=contact,
                                                                    body=event4).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S"),'попробуем восстановить событие еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))


        self.progressBar.hide()
        # Перезагружаем ВСЕ контакты из gmail
        self.FIO_saved_id = self.FIO_cur_id
        if self.contacty[self.FIO_cur_id]['main']:
            self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
        else:
            self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
        self.contacty_syncTokenM = ''
        self.contacty_syncTokenS = ''
        self.events_syncToken = ''
        self.google2db4allM()
        self.google2db4allS()
        self.setup_twGroups()
        return

    def click_clbTrash(self): # Удаляем все контакты (и их события) без телефона
        if self.group_cur not in AVITO_GROUPS.keys():
            return
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        if self.contacty[self.FIO_cur_id]['main']:
            self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
        else:
            self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
        self.FIO_saved_id = self.FIO_cur_id
        self.progressBar.show()
        if self.contacty[self.FIO_cur_id]['main']:
            self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
        else:
            self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
        self.FIO_saved_id = self.FIO_cur_id
        service_cal = discovery.build('calendar', 'v3', http=self.http_calM)
        service = discovery.build('people', 'v1', http=self.http_conM,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        print('Всего:', len(self.contacts_filtered))
        number_of_new = 0
        self.progressBar.setMaximum(len(self.contacts_filtered) - 1)
        for i, contact in enumerate(self.contacts_filtered.values()):
            self.progressBar.setValue(i)
            if not len(contact['phones']):
                number_of_new += 1
                print(str(number_of_new), contact['fio'])
                ok_google = False
                while not ok_google:
                    try:
                        event4 = service_cal.events().get(calendarId='primary', eventId=contact['resourceName'])\
                                                                                                            .execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") +' попробуем запросить событие еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
                event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                ok_google = False
                while not ok_google:
                    try:
                        updated_event = service_cal.events().update(calendarId='primary',
                                                    eventId=contact['resourceName'], body=event4).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить событие еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))

                ok_google = False
                while not ok_google:
                    try:
                        resultsc = service.people().deleteContact(resourceName='people/' + contact['resourceName']).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить контакт еще раз - ошибка',
                                  ee.resp['status'], ee.args[1].decode("utf-8"))
        # Перезагружаем ВСЕ контакты из gmail
        self.FIO_saved_id = self.FIO_cur_id
        if self.contacty[self.FIO_cur_id]['main']:
            self.group_saved_id = self.groups_resourcenames_reversedM[self.group_cur]
        else:
            self.group_saved_id = self.groups_resourcenames_reversedS[self.group_cur]
        #self.group_saved_id = self.group_cur_id
        self.contacty_syncTokenM = ''
        self.contacty_syncTokenS = ''
        self.events_syncToken = ''
        self.google2db4allM()
        self.google2db4allS()
        self.setup_twGroups()

    def click_clbCheckPhone(self):
        phones = []
        if len(self.lePhones.text().strip().split(' ')) > 0:
            for i, phone in enumerate(self.lePhones.text().strip().split(' ')):
                if phone.strip() != '':
                    phones.append(fine_phone(phone))
        phone_double_contacts = []
        for contact in self.contacty:
            has_phone = False
            if len(self.contacty[contact]['phones']) > 0:
                for phone in self.contacty[contact]['phones']:
                    if contact != self.FIO_cur_id:
                        if fine_phone(phone) in phones:
                            has_phone = True
                            break
            if has_phone:
                phone_double_contacts.append(self.contacty[contact])
        if len(phone_double_contacts):
            doubled_contacts = []
            for phone_double_contact in phone_double_contacts:
                doubled_contacts.append([phone_double_contact['avito_id'], phone_double_contact['iof'],
                                         phone_double_contact['stage']])
            self.makeDialog(doubled_contacts)


    def errMessage(self, err_text):  ## Method to open a message box
        infoBox = QMessageBox()  ##Message Box that doesn't run
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText(err_text)
        #        infoBox.setInformativeText("Informative Text")
        infoBox.setWindowTitle(datetime.strftime(datetime.now(), "%H:%M:%S") + ' Внимание: ')
        #        infoBox.setDetailedText("Detailed Text")
        #        infoBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        infoBox.setStandardButtons(QMessageBox.Ok)
        #        infoBox.setEscapeButton(QMessageBox.Close)
        infoBox.exec_()

    def click_clbAddDate(self):
        if len(self.teNote.toPlainText()) > 0:
            if self.teNote.toPlainText()[len(self.teNote.toPlainText()) - 1] == '\n':
                self.teNote.setPlainText(self.teNote.toPlainText() + datetime.now().strftime("%d.%m.%Y") + ' ')
            else:
                self.teNote.setPlainText(self.teNote.toPlainText() + '\n' + datetime.now().strftime("%d.%m.%Y") + ' ')
        else:
            self.teNote.setPlainText(self.teNote.toPlainText() + datetime.now().strftime("%d.%m.%Y") + ' ')

    # Dialog - Дополнительное окно в произвольной форме (с таблицей и реакциями)
    def click_twDoubled(self, index=None): # Нажатие на строчку таблицы в Dialog
        if index == None:
            self.Dialog.close()
            return
        if index.row() < 0:
            self.Dialog.close()
            return
        else:
            self.FIO_saved_id = self.avitos_id_contacts[self.doubled[index.row()][0]]
            self.group_saved_id = self.contacty[self.avitos_id_contacts[self.doubled[index.row()][0]]]['groups_ids'][0]
            self.click_twGroups()
            self.FIO_saved_id = ''
            self.group_saved_id = None
            self.Dialog.close()
            return

    def pushCloseDialog(self):  # Нажатие на кнопку Отмена в Dialog
        self.Dialog.close()

    def makeDialog(self, doubled):  # Dialog - Дополнительное окно в произвольной форме (с таблицей и реакциями)
        self.doubled = doubled
        self.Dialog = QDialog()  # Само окно
        self.Dialog.resize(874, 0)
        verticalLayout = QVBoxLayout(self.Dialog)
        verticalLayout.setObjectName("verticalLayout")
        self.Dialog.tableWidget = QTableWidget(self.Dialog)
        self.Dialog.tableWidget.setObjectName("tableWidget")
        self.Dialog.tableWidget.setColumnCount(0)
        self.Dialog.tableWidget.setRowCount(0)

        self.Dialog.tableWidget.setColumnCount(3)               # Устанавливаем кол-во колонок
        self.Dialog.tableWidget.setRowCount(len(doubled))        # Кол-во строк из таблицы
        for i, double in enumerate(doubled):
            self.Dialog.tableWidget.setItem(i, 0, QTableWidgetItem(double[0]))
            self.Dialog.tableWidget.setItem(i, 1, QTableWidgetItem(double[1]))
            self.Dialog.tableWidget.setItem(i, 2, QTableWidgetItem(double[2]))

        # Устанавливаем заголовки таблицы
        self.Dialog.tableWidget.setHorizontalHeaderLabels(['id','Продавец','Стадия'])
        # Устанавливаем выравнивание на заголовки
        self.Dialog.tableWidget.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        # делаем ресайз колонок по содержимому
        self.Dialog.tableWidget.resizeColumnsToContents()
        verticalLayout.addWidget(self.Dialog.tableWidget)
        self.Dialog.pushButton = QPushButton(self.Dialog)
        self.Dialog.pushButton.setText('Отмена')
        self.Dialog.pushButton.setObjectName("pushButton")
        self.Dialog.pushButton.clicked.connect(self.pushCloseDialog)
        self.Dialog.tableWidget.clicked.connect(self.click_twDoubled)
        verticalLayout.addWidget(self.Dialog.pushButton)
        self.Dialog.setLayout(verticalLayout)
        self.Dialog.exec_()

    def qwe(self):
        q4 = """
        
    def google2db4one(self):               # Google -> Внутр БД (текущий контакт)
        ok_google = False
        while not ok_google:
            try:
                service = discovery.build('people', 'v1', http=self.http_con,
                                          discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                result = service.people().get(
                    resourceName='people/' + self.FIO_cur_id,
                    personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,'
                                 'events,genders,imClients,interests,locales,memberships,metadata,names,nicknames,'
                                 'occupations,organizations,phoneNumbers,photos,relations,relationshipInterests,'
                                 'relationshipStatuses,residences,skills,taglines,urls,userDefined') \
                .execute()
                connection = result
                ok_google = True
            except errors.HttpError as ee:
                print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз - ошибка',
                                                ee.resp['status'], ee.args[1].decode("utf-8"))
# Календарь

        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
        calendars = []
        calendars_result = {'nextPageToken':''}
        start = datetime(2011, 1, 1, 0, 0).isoformat() + 'Z'  # ('Z' indicates UTC time) с начала работы
        while str(calendars_result.keys()).find('nextPageToken') > -1:
            if calendars_result['nextPageToken'] == '':
                try:
                    calendars_result = service_cal.events().list(
                        calendarId='primary',
                        showDeleted=True,
                        showHiddenInvitations=True,
                        timeMin=start,
                        maxResults=2000,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                    calendars_result = service_cal.events().list(
                        calendarId='primary',
                        showDeleted=True,
                        showHiddenInvitations=True,
                        timeMin=start,
                        maxResults=2000,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
            else:
                try:
                    calendars_result = service_cal.events().list(
                        calendarId='primary',
                        showDeleted=True,
                        showHiddenInvitations=True,
                        timeMin=start,
                        maxResults=2000,
                        pageToken=calendars_result['nextPageToken'],
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                    calendars_result = service_cal.events().list(
                        calendarId='primary',
                        showDeleted=True,
                        showHiddenInvitations=True,
                        timeMin=start,
                        maxResults=2000,
                        pageToken=calendars_result['nextPageToken'],
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
            calendars.extend(calendars_result.get('items', []))
        eventds = {}
        for calendar in calendars:
            eventd = {}
            eventd['id'] = calendar['id']
            if str(calendar['start'].keys()).find('dateTime') > -1:
                eventd['start'] = calendar['start']['dateTime']
            else:
                eventd['start'] = str(utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00', "%Y-%m-%d %H:%M:%S")))
            if str(calendar.keys()).find('htmlLink') > -1:
                eventd['www'] =calendar['htmlLink']
            else:
                eventd['www'] = ''
            eventds[calendar['id']] = eventd

        contact = {}
        contact['resourceName'] = connection['resourceName'].split('/')[1]
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
                memberships.append(self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
        contact['groups'] = memberships
        stage = '---'
        calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
        changed = QDate().currentDate().toString("dd.MM.yyyy")
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
                if ostage['key'].lower() == 'changed':
                    changed = ostage['value']
        contact['stage'] = stage
        contact['calendar'] = calendar
        contact['cost'] = cost + random() * 1e-5
        contact['changed'] = changed
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
                    email += oemailAddress.get('value') + ' '
        contact['email'] = email.strip()
        contact['etag'] = connection['etag']
        contact['avito'] = ''
        contact['instagram'] = ''
        urls = []
        ourls = connection.get('urls', [])
        if len(ourls) > 0:
            for ourl in ourls:
                urls.append(ourl['value'])
                if ourl['value'].find('www.avito.ru') > -1:
                    contact['avito'] = ourl['value']
                if ourl['value'].find('instagram.com') > -1:
                    contact['instagram'] = ourl['value'].strip().split('https://www.instagram.com/')[1].replace('/','')
        contact['urls'] = urls
        if str(contact.keys()).find('avito') > -1:
            avito_x = contact['avito'].strip()
            avito_i = len(avito_x) - 1
            for j in range(len(avito_x) - 1, 0, -1):
                if avito_x[j] not in digits:
                    avito_i = j + 1
                    break
            contact['avito_id'] = avito_x[avito_i:]
        ind = self.contacts_filtered[self.FIO_cur_id]['contact_ind']
        self.contacts_filtered[self.FIO_cur_id] = contact
        self.contacts_filtered[self.FIO_cur_id]['contact_ind'] = ind
        self.contacty[self.contacts_filtered[self.FIO_cur_id]['contact_ind']] = contact
        return
    
    def FillChanged4All(self)   # Первичное заполнение ['changed'] в Google
        if self.group_cur not in AVITO_GROUPS.keys():
            return
        if self.leFIO.text() or self.leNote.text() or self.lePhone.text():
            self.errMessage('!!!! С фильтрами - нельзя !!!')
            return
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        self.progressBar.setMaximum(len(self.contacts_filtered) - 1)
        self.progressBar.show()
        for i, contact in enumerate(self.contacts_filtered):
            if i % 100 == 0:
                self.progressBar.setValue(i)
            if self.contacts_filtered[contact]['changed'] == QDate().currentDate().toString("dd.MM.yyyy"):
                buf_contact = {}
                buf_contact['userDefined'] = [{}, {}, {}, {}]
                buf_contact['userDefined'][0]['value'] = self.contacts_filtered[contact]['stage']
                buf_contact['userDefined'][0]['key'] = 'stage'
                buf_contact['userDefined'][1]['value'] = self.contacts_filtered[contact]['calendar']
                buf_contact['userDefined'][1]['key'] = 'calendar'
                buf_contact['userDefined'][2]['value'] = str(round(self.contacts_filtered[contact]['cost'], 4))
                buf_contact['userDefined'][2]['key'] = 'cost'
                buf_contact['userDefined'][3]['value'] = QDate().currentDate().toString("dd.MM.yyyy")
                buf_contact['userDefined'][3]['key'] = 'changed'
                buf_contact['etag'] = self.google2db4etag(cur_id=contact)
                ok_google = False
                while not ok_google:
                    try:
                        resultsc = service.people().updateContact(
                            resourceName='people/' + contact,
                            updatePersonFields='userDefined',
                            body=buf_contact).execute()
                        ok_google = True
                    except errors.HttpError as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем обновить стадию еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                        buf_contact['etag'] = self.google2db4etag(cur_id=contact)
        self.progressBar.hide()


    def click_clbBack(self): # удалил из осню текста наколпление истории в self.FIO_last_id
        self.lePhone.setText('')
        self.leFIO.setText('')
        self.leNote.setText('')
        self.setup_twFIO()
        try:
            self.click_twFIO(index=self.twFIO.model().index(self.contacts_filtered_reverced.index(
                self.FIO_last_id[len(self.FIO_last_id) - 3]), 0))
        except ValueError:
            q=0

    
    def click_clbTrashLoad(self):
        if self.group_cur != '_КоттеджиСочи':
            return
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.progressBar.show()
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        self.FIO_saved_id = self.FIO_cur_id
        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        print('Всего:', len(self.contacts_filtered))
        number_of_new = 0
        self.progressBar.setMaximum(len(self.contacts_filtered) - 1)
        for i, contact in enumerate(self.contacts_filtered):
            self.progressBar.setValue(i)
            if not len(contact['phones']):
                number_of_new += 1
                print(str(number_of_new), contact['fio'])
                try:
                    event4 = service_cal.events().get(calendarId='primary',
                                                             eventId=contact['resourceName']).execute()
                    event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                    event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                    updated_event = service_cal.events().update(calendarId='primary',
                                                eventId=contact['resourceName'], body=event4).execute()
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить событие еще ра - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                    event4 = service_cal.events().get(calendarId='primary',
                                                             eventId=contact['resourceName']).execute()
                    event4['start']['dateTime'] = datetime(2012, 12, 31, 15, 0).isoformat() + 'Z'
                    event4['end']['dateTime'] = datetime(2012, 12, 31, 15, 15).isoformat() + 'Z'
                    updated_event = service_cal.events().update(calendarId='primary',
                                                eventId=contact['resourceName'], body=event4).execute()
                try:
                    resultsc = service.people().deleteContact(resourceName='people/' + contact['resourceName']).execute()
                except errors.HttpError as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить контакт еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                    resultsc = service.people().deleteContact(resourceName='people/' + contact['resourceName']).execute()
        html_x = ''
        self.progressBar.setMaximum(MAX_PAGE)
        for i in range(1, MAX_PAGE):
            self.progressBar.setValue(i)
            if i == 1:
                response = urllib.request.urlopen('https://www.avito.ru/sochi/doma_dachi_kottedzhi/prodam?s=2&user=1')
            else:
                response = urllib.request.urlopen('https://www.avito.ru/sochi/doma_dachi_kottedzhi/prodam?p=' + str(i) +
                                           '&s=2&user=1')
            html_x = response.read().decode('utf-8')
            if len(html_x) < 1000:
                continue
            avitos = []
            avitos_ids = []
            avitos_raw = html_x.split('href="/sochi/doma_dachi_kottedzhi/')
            for i, avito_raw in enumerate(avitos_raw):
                if i == 0:
                    continue
                is_double = False
                if avito_raw[:6] != 'prodam':
                    for avito_id in avitos_ids:
                        avito_x = avito_raw.split('"')[0]
                        for k in range(len(avito_x) - 1, 0, -1):
                            if avito_x[k] not in digits:
                                break
                        if avito_id == avito_x[k+1:]:
                            is_double = True
                    if not is_double:
                        avitos.append('https://www.avito.ru/sochi/doma_dachi_kottedzhi/' + avito_raw.split('"')[0])
                        avito_x = avito_raw.split('"')[0]
                        for k in range(len(avito_x) - 1, 0, -1):
                            if avito_x[k] not in digits:
                                break
                        avitos_ids.append(avito_x[k+1:])
            j = round(random() * 1000000)
            for avito_i, avito_id in enumerate(avitos_ids):
                has_in_db = False
                for contact in self.contacts_filtered:
                    if str(contact.keys()).find('avito') > -1:
                        avito_x = contact['avito']
                        for k in range(len(avito_x) - 1, 0, -1):
                            if avito_x[k] not in digits:
                                break
                        if avito_id == avito_x[k+1:]:
                            has_in_db = True
                if not has_in_db:
# Если возраст объявления меньше месяца - не добавляем
                    html_avito = ''
                    while not html_avito:
                        response = urllib.request.urlopen('https://www.avito.ru/items/stat/' + avito_id + '?step=0')
                        html_avito = response.read().decode('utf-8')
                    avito_date = datetime.strptime((html_avito.split('<strong>')[1].split('</strong>')[0]).strip(),
                                                   '%d %B %Y')
                    if avito_date < datetime.now() - timedelta(days=31):
                        j += 1
                        buf_contact = {}
                        buf_contact['userDefined'] = [{}, {}, {}, {}]
                        buf_contact['userDefined'][0]['value'] = 'пауза'
                        buf_contact['userDefined'][0]['key'] = 'stage'
                        buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
                        buf_contact['userDefined'][1]['key'] = 'calendar'
                        buf_contact['userDefined'][2]['value'] = '0'
                        buf_contact['userDefined'][2]['key'] = 'cost'
                        buf_contact['names'] = [{'givenName': str(j)}]
                        buf_contact['urls'] = {'value': avitos[avito_i]}
                        buf_contact['biographies'] = [{}]
                        buf_contact['biographies'][0]['value'] = '|пауза|' + str(datetime.now().date() +
                                                                                 timedelta(days=14)) + '|0м|\n'
                        # buf_contact['phoneNumbers'] = ['0']
                        # Создаем контакт
                        ok_google = False
                        while not ok_google:
                            try:
                                service = discovery.build('people', 'v1', http=self.http_con,
                                                    discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                                resultsc = service.people().createContact(body=buf_contact).execute()
                                ok_google = True
                            except errors.HttpError as ee:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))

                        # Добавляем в текущую группу
                        ok_google = False
                        while not ok_google:
                            try:
                                group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                                resultsg = service.contactGroups().members().modify(
                                    resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
                                    body=group_body
                                ).execute()
                                ok_google = True
                            except errors.HttpError as ee:
                                print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))

                        # Добавляем событие через 31 день
                        if avito_date.weekday() == 5:
                            avito_date += timedelta(days=2)
                        if avito_date.weekday() == 6:
                            avito_date += timedelta(days=1)
                        event = {}
                        event['id'] = resultsc['resourceName'].split('/')[1]
                        event['start'] = {'dateTime': datetime.combine((avito_date + timedelta(days=31)),
                                            datetime.strptime('19:00', '%H:%M').time()).isoformat() + '+04:00'}
                        event['end'] = {'dateTime': datetime.combine((avito_date + timedelta(days=31)),
                                            datetime.strptime('19:15', '%H:%M').time()).isoformat() + '+04:00'}
                        event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
                        event['description'] = '|пауза|' + str(
                            datetime.now().date() + timedelta(days=14)) + '|0м|\n' + avitos[avito_i]
                        event['summary'] = '- пауза'
                        try:
                            service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                            calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
                        except errors.HttpError as ee:
                            print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить event еще раз - ошибка',
                              ee.resp['status'], ee.args[1].decode("utf-8"))
                            service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                            calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
        self.contacty_syncToken = ''
        self.events_syncToken = ''
        self.google2db4all()  # Перезагружаем ВСЕ контакты из google
        self.setup_twGroups()
        self.progressBar.hide()

    def click_cbStage(self):   # Глючило без костылей self.changed. Убрал вместе с костылями
        if not self.changed:
            return
        self.changed = False # обновляем информацию о контакте
        self.google2db4one()
        self.changed = True
        buf_contact = {}
        buf_contact['userDefined'] = [{},{},{}]
        buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
        buf_contact['userDefined'][1]['key'] = 'calendar'
        try:
            buf_contact['userDefined'][2]['value'] = str(float(self.leCost.text()))
        except ValueError:
            buf_contact['userDefined'][2]['value'] = '0'
        buf_contact['userDefined'][2]['key'] = 'cost'
        buf_contact['biographies'] = [{}]
        buf_contact['biographies'][0]['value'] = self.teNote.toPlainText()
        buf_contact['etag'] = self.contacts_filtered[self.FIO_cur_id]['etag']
        # Обновление контакта
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().updateContact(
                resourceName='people/' + self.FIO_cur_id,
                updatePersonFields='biographies,userDefined',
                body=buf_contact).execute()
        except errors.HttpError as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().updateContact(
                resourceName='people/' + self.FIO_cur_id,
                updatePersonFields='biographies,userDefined',
                body=buf_contact).execute()
        self.changed = False # обновляем информацию о контакте и карточку
        self.google2db4one()
        self.db2form4one()
        self.changed = True
        return

    def click_clbCreateContact(self):  # Ищем дубли и выводим в print()
        for i, contact in enumerate(self.contacty.values()):
            for j, contact2 in enumerate(self.contacty.values()):
                if contact['avito'] != '' and contact['avito'] == contact2['avito'] and i != j:
                    if l(contact['fio']) > l(contact2['fio']):
                        print(contact['iof'],contact2['iof'])
                    else:
                        print(contact2['iof'], contact['iof'])
        
    def click_clbCreateContact(self):
        buf_contact = {}
        buf_contact['biographies'] = [{}]
        buf_contact['biographies'][0]['value'] = self.teNote.toPlainText()
        buf_contact['userDefined'] = [{},{},{}]
        buf_contact['userDefined'][0]['value'] = 'пауза'
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
        buf_contact['userDefined'][1]['key'] = 'calendar'
        try:
            buf_contact['userDefined'][2]['value'] = str(float(self.leCost.text()))
        except ValueError:
            buf_contact['userDefined'][2]['value'] = '0'
        buf_contact['userDefined'][2]['key'] = 'cost'

        givenName = ''
        middleName = ''
        familyName = ''
        if self.leIOF.text():
            if len(self.leIOF.text().strip().split(' ')) > 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                middleName = self.leIOF.text().strip().split(' ')[1]
                for i, name in enumerate(self.leIOF.text().strip().split(' ')):
                    if i > 1:
                        familyName += name + ' '
            elif len(self.leIOF.text().strip().split(' ')) == 2:
                givenName = self.leIOF.text().strip().split(' ')[0]
                familyName = self.leIOF.text().strip().split(' ')[1]
            elif len(self.leIOF.text().strip().split(' ')) == 1:
                givenName = self.leIOF.text().strip().split(' ')[0]
        familyName = familyName.strip()
        buf_contact['names'] = [{'familyName': familyName,
                                  'givenName' : givenName,
                                  'middleName': middleName}]
        if self.leUrls.text():
            buf_contact['urls'] = []
            if len(self.leUrls.text().strip().split(' ')) > 0:
                for i, url in enumerate(self.leUrls.text().strip().split(' ')):
                    if url.strip() != '':
                        buf_contact['urls'].append({'value': url})
        if self.lePhones.text():
            buf_contact['phoneNumbers'] = []
            if len(self.lePhones.text().strip().split(' ')) > 0:
                for i, phone in enumerate(self.lePhones.text().strip().split(' ')):
                    if phone.strip() != '':
                        buf_contact['phoneNumbers'].append({'value': fine_phone(phone)})

        if self.leEmail.text():
            buf_contact['emailAddresses'] = []
            if len(self.leEmail.text().strip().split(' ')) > 0:
                for i, email in enumerate(self.leEmail.text().strip().split(' ')):
                    if email.strip() != '' and len(email.split('@')) > 0:
                        buf_contact['emailAddresses'].append({'value': email})
        if self.leAddress.text():
            if len(self.leAddress.text().strip()) > 0:
                buf_contact['addresses'] = [{'streetAddress': self.leAddress.text().strip()}]

        has_phone = False
        has_phone_names = []
        for phone_new in buf_contact['phoneNumbers']:
            for contact in self.contacts:
                for phone in contact['phones']:
                    if fine_phone(phone) == fine_phone(phone_new['value']):
                        has_phone = True
                        has_phone_names.append(contact['iof'])
        has_phone_names_string = ''
        for has_phone_name in has_phone_names:
            has_phone_names_string += has_phone_name + '\n'
        if has_phone:
            self.teNote.setText('\n!! Уже есть контакт с этим телефоном !!\n!! Уже есть контакт с этим телефоном !!' +
                                '\n!! Уже есть контакт с этим телефоном !!\n\n' + has_phone_names_string +
                                '\n!! Уже есть контакт с этим телефоном !!\n!! Уже есть контакт с этим телефоном !!'
                                '\n!! Уже есть контакт с этим телефоном !!')
            return

        # Создаем контакт
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().createContact(body=buf_contact).execute()
        except errors.HttpError as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().createContact(body=buf_contact).execute()
        self.FIO_saved_id = resultsc['resourceName']
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        # Добавляем в текущую группу и удаляем из myContacts
        group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
        resultsg = service.contactGroups().members().modify(
            resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
            body= group_body
        ).execute()
#        time.sleep(1)
#        resultsg = service.contactGroups().members().modify(
#            resourceName='contactGroups/myContacts',
#            body= {'resourceNamesToAdd': [], 'resourceNamesToRemove': [resultsc['resourceName']]}
#        ).execute()
        self.google2db4all()
        self.setup_twGroups()
        return
    
    def click_gluckGooglePatch(self):  # пересоздаем удаленные контакты (глюки Гугля при удалении)
        try:
            service_cal = discovery.build('calendar', 'v3', http=self.http_cal)         # Считываем глюки календаря
            start = datetime(1999, 12, 31, 0, 0).isoformat() + 'Z' # ('Z' indicates UTC time)
            end = datetime(2017, 12, 31, 0, 0).isoformat() + 'Z'
            calendars_result = service_cal.events().list(
                calendarId='primary',
                showDeleted=True,
                showHiddenInvitations=True,
                timeMin=start,
#                timeMax=end,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        except errors.HttpError as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
            start = datetime(1999, 12, 31, 0, 0).isoformat() + 'Z'  # ('Z' indicates UTC time)
            end = datetime(2017, 12, 31, 0, 0).isoformat() + 'Z'
            calendars_result = service_cal.events().list(
                calendarId='primary',
                showDeleted=True,
                showHiddenInvitations=True,
                timeMin=start,
#                timeMax=end,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        calendars = calendars_result.get('items', [])
        gluck_ids = []
        for calendar in calendars:
            if str(calendar['start'].keys()).find('dateTime') == -1:
                gluck_ids.append(calendar['id'])

        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        try:
            results = service.people().connections() \
                .list(
                resourceName='people/me',
                pageSize=2000,
                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                             'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                             'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                             'residences,skills,taglines,urls,userDefined') \
                .execute()
        except errors.HttpError as ee:
            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
            results = service.people().connections() \
                .list(
                resourceName='people/me',
                pageSize=2000,
                personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                             'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                             'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                             'residences,skills,taglines,urls,userDefined') \
                .execute()
        contacts = results.get('connections', [])
        for contact in contacts:
            if contact['resourceName'].split('/')[1] in gluck_ids:
                groups = ''
                for cont in contact['memberships']:
                    groups += ' ' + self.groups_resourcenames[cont['contactGroupMembership']['contactGroupId']]
                resourceName = contact['resourceName']
                del contact['resourceName']
                del contact['etag']
                del contact['metadata']
                if str(contact.keys()).find('coverPhotos') > -1:
                    del contact['coverPhotos']
                if str(contact.keys()).find('photos') > -1:
                    del contact['photos']
                if str(contact.keys()).find('taglines') > -1:
                    del contact['taglines']
                if str(contact.keys()).find('memberships') > -1:
                    del contact['memberships']
                if str(contact.keys()).find('genders') > -1:
                    if len(contact['genders']) > 1:
                        for i in range(1,len(contact['genders'])):
                            del contact['genders'][i]
                if str(contact.keys()).find('names') > -1:
                    if len(contact['names']) > 1:
                        for i in range(1,len(contact['names'])):
                            del contact['names'][i]
                for infos in contact:
                    for info in contact[infos]:
                        del info['metadata']['source']
                print(contact['names'][0]['displayName'], '-', groups)
                try:
                    contact_res = service.people().createContact(body=contact).execute()
                except errors.HttpError as ee:
                    time.sleep(1)
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать еще раз')
                    try:
                        contact_res = service.people().createContact(body=contact).execute()
                    except errors.HttpError as ee:
                        time.sleep(1)
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать третий раз')
                        contact_res = service.people().createContact(body=contact).execute()
                try:
                    result = service.people().deleteContact(resourceName=resourceName).execute()
                except errors.HttpError as ee:
                    time.sleep(1)
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем удалить еще раз')
                    result = service.people().deleteContact(resourceName=resourceName).execute()
                q=0

    def change_deCalendar(self):                          # выключил из-за глюков deCalendar
#        self.deCalendar.setCalendarPopup(False)
        if not self.changed:
            return
        print(self.deCalendar.date().toString("dd.MM.yyyy"), self.contacts_filtered[self.FIO_cur_id]['calendar'])
        if self.deCalendar.date().toString("dd.MM.yyyy") == self.contacts_filtered[self.FIO_cur_id]['calendar']:
            return
        buf_contact = {}
        buf_contact['userDefined'] = [{},{},{}]
        buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
        buf_contact['userDefined'][1]['key'] = 'calendar'
        try:
            buf_contact['userDefined'][2]['value'] = str(float(self.leCost.text()))
        except ValueError:
            buf_contact['userDefined'][2]['value'] = '0'
        buf_contact['userDefined'][2]['key'] = 'cost'
        buf_contact['biographies'] = [{}]
        buf_contact['biographies'][0]['value'] = self.teNote.toPlainText()
        buf_contact['etag'] = self.contacts_filtered[self.FIO_cur_id]['etag']
        # Обновление контакта
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        resultsc = service.people().updateContact(
            resourceName=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
            updatePersonFields='biographies,userDefined',
            body=buf_contact).execute()
        print(resultsc['userDefined'][0]['value'], resultsc['userDefined'][1]['value'])
        self.changed = False            # обновляем информацию о контакте и карточку
        self.google2db4one()
        self.db2form4one()
        self.changed = True
        return

        
    def click_label_3(self, index=None):
        if index == None or index.row() < 0 or index.row() > 0 or index.column() < 0:
            index = self.tableFotos.model().index(0, 0)
        pixmap = QPixmap('photos/'+ self.mamba_id[self.id_tek] + '_' + s(self.names[self.id_tek]).replace(' ','') +
                         s(self.ages[self.id_tek]) + '_' + '{0:02d}'.format(index.column()+1) + '.jpg')
        self.label_3.setPixmap(pixmap)

    def updateNote(self):
        current = self.teNote.toPlainText()
        if self.histories[self.id_tek] == None:
            past = ''
        else:
            past = self.histories[self.id_tek]
        if current != past:
            self.dbconn.connect()
            write_cursor = self.dbconn.cursor()
            write_cursor.execute('UPDATE peoples SET history = %s WHERE id = %s', (current, self.id_tek))
            self.dbconn.commit()
            self.histories[self.id_tek] = current
        return

    def click_cbLink(self):
        self.dbconn.connect()
        write_cursor = self.dbconn.cursor()
        write_cursor.execute('UPDATE peoples SET t_link = %s WHERE id = %s',
                                  (self.cbLink.currentIndex(), self.id_tek))
        self.dbconn.commit()
        self.t_link[self.id_tek] = self.cbLink.currentIndex()
        if len(s(self.histories[self.id_tek])) > 0:
            self.textEdit.setText(s(self.histories[self.id_tek]) + '\n' + datetime.now().strftime("%d.%m.%y") +
                              ' этап-> ' +  s(self.cbLink.currentText()))
        else:
            self.textEdit.setText(s(self.histories[self.id_tek]) + datetime.now().strftime("%d.%m.%y") +
                              ' этап-> ' +  s(self.cbLink.currentText()))
        self.updateHistory()
        return

    def click_cbPeople(self):
        self.dbconn.connect()
        write_cursor = self.dbconn.cursor()
        write_cursor.execute('UPDATE peoples SET t_people = %s WHERE id = %s',
                                  (self.cbPeople.currentIndex(), self.id_tek))
        self.dbconn.commit()
        self.t_people[self.id_tek] = self.cbPeople.currentIndex()
        if len(s(self.histories[self.id_tek])) > 0:
            self.textEdit.setText(s(self.histories[self.id_tek]) + '\n' + datetime.now().strftime("%d.%m.%y") +
                              ' чел.-> ' +  self.cbPeople.currentText())
        else:
            self.textEdit.setText(s(self.histories[self.id_tek]) + datetime.now().strftime("%d.%m.%y") +
                              ' чел.-> ' +  self.cbPeople.currentText())
        self.updateHistory()
        return

    def click_cbLinkFrom(self):
        self.stLinkFrom = self.cbLinkFrom.currentIndex()
        self.setup_twGroups()
        return

    def click_cbLinkTo(self):
        self.stLinkTo = self.cbLinkTo.currentIndex()
        self.setup_twGroups()
        return

    def click_cbStatus(self):
        self.stStatus = self.cbStatus.currentIndex()
        self.setup_twGroups()
        return

    def click_cbPeopleFrom(self):
        self.stPeopleFrom = self.cbPeopleFrom.currentIndex()
        self.setup_twGroups()
        return

    def click_cbPeopleTo(self):
        self.stPeopleTo = self.cbPeopleTo.currentIndex()
        self.setup_twGroups()

    def convert_mamba_id(self, href):
        a = "".join([k.strip() for k in href]).strip()
        m_id = a[21:].split("?")[0]
        if len(m_id.split('#')) > 1:
            m_id = m_id.split('#')[0]
        if len(m_id.split('&')) > 1:
            m_id = m_id.split('&')[0]
#        print(a, a[21:], m_id)
        return m_id

    def convert_msg_id(self, m_id):
        if m_id[:2] == 'mb':
            return m_id[2:]
        else:
            return None

    def scan(self, html_tek):
        a = crop_tags(html_tek)
        self.chk_educ = False
        self.chk_child = False
        self.chk_home = False
        self.chk_baryg = False
        self.chk_marr = False
        self.chk_dist = False
        if a.find('Образование: среднее') == -1 and a.find('Образование: среднее специальное') == -1 \
                and a.find('Образование: неполное высшее') == -1:
            self.chk_educ = True
        if a.find('Дети: Есть, живём вместе') == -1:
            self.chk_child = True
        if a.find('Проживание: Комната в общежитии, коммуналка') == -1 and \
                        a.find('Проживание: Живу с родителями') == -1 and \
                        a.find('Проживание: Живу с приятелем / с подругой') == -1 and \
                        a.find('Проживание: Нет постоянного жилья') == -1:
            self.chk_home = True
        if a.find('Материальная поддержка: Ищу спонсора') == -1:
            self.chk_baryg = True
        if a.find('Отношения: В браке') == -1 and a.find('Отношения: Есть отношения') == -1:
            self.chk_marr = True
        if a.find('~') > -1:
            if a.find(' км ') > -1:
                dist = int(a[a.find('~') + 1:a.find('км')])
            else:
                dist = 0
            if dist < 20:
                self.chk_dist = True
        else:
            self.chk_dist = True
        return

    def click_pbScan(self):
        if self.refresh_started:
            return
        for id_curr in self.id_all:
            if self.fotos_count[id_curr] == 0:                               # !!!!! Временно !!!!!
                aa = 'https://www.mamba.ru/' + self.mamba_id[id_curr]
                self.drv.get(url=aa)
                wj(self.drv)
                self.click_pbGetHTML()
        return

    def click_pbReLogin(self):
        self.drv.quit()
        self.drv = webdriver.Firefox()  # Инициализация драйвера
        self.drv.implicitly_wait(5)  # Неявное ожидание - ждать ответа на каждый запрос до 5 сек
        authorize(self.drv, **self.webconfig)  # Авторизация
        self.refresh_started = False               # Выключаем автообновление
        self.pbRefresh.setText('Обновить')
        wj(self.drv)
        return

    def click_pbToAnketa(self):
        if self.refresh_started:
            self.drv.switch_to.window(self.drv.window_handles[1])
        aa = 'https://www.mamba.ru/' + self.mamba_id[self.id_tek]
        self.drv.get(url=aa)
        wj(self.drv)
        self.click_pbGetHTML()
        return

    def click_pbToMessage(self):
        if self.refresh_started:
            self.drv.switch_to.window(self.drv.window_handles[1])
        aa = 'https://www.mamba.ru/my/message.phtml?uid=' + self.msg_id[self.id_tek]
        self.drv.get(url=aa)
        return

    def get_html(self):
        html_msg = p(d=self.drv, f='p', **B['anketa-msg'])
        html_favour = p(d=self.drv, f='p', **B['anketa-favour'])
        html_abouts = p(d=self.drv, f='ps', **B['anketa-about'])
        html_locator = p(d=self.drv, f='p', **B['anketa-locator'])
        html = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/' \
               'strict.dtd"><html><head></head><body><p>' + html_msg + '</p><h3>' + html_locator + '</h3><p>'
        html += html_favour.replace('\n', ' | ') + '</p>'
        if len(html_abouts) > 0:
            for html_into in html_abouts:
                html += html_into
        html = html.replace('\n', ' ').replace('\t', ' ').replace('  ', ' ').replace('  ', ' ')
        html = html.replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')
        html = html.replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')
        html += '</body></html>'
        return html
        """


