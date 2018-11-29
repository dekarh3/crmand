from __future__ import print_function

from httplib2 import Http
from subprocess import Popen, PIPE
import os
from string import digits
from random import random
from dateutil.parser import parse
from collections import OrderedDict
from urllib import request

from apiclient import discovery                             # Механизм запроса данных
from googleapiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime, timedelta, time
import time
import pytz
utc=pytz.UTC

from PyQt5.QtCore import QDate, QDateTime, QSize, Qt, QByteArray, QTimer, QUrl, QEventLoop
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QMainWindow, QWidget, QApplication


from crm_win import Ui_Form

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from lib import unique, l, s, fine_phone, format_phone

ALL_STAGES_CONST = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                     'нет на месте', 'недозвон', 'пауза', 'нет объявления', 'недоступен', '---', 'когда получится',
                    'нет контактов', 'не занимаюсь', 'не понимает', 'не интересно', 'мне не интересно', 'уже продали',
                    'не верит', 'дубль', 'рыпу']
WORK_STAGES_CONST = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                     'нет на месте', 'недозвон', 'пауза']
LOST_STAGES_CONST = ['нет объявления']

MAX_PAGE = 20

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/people.googleapis.com-python-quickstart.json
SCOPES_CON = 'https://www.googleapis.com/auth/contacts' #.readonly'       #!!!!!!!!!!!!!!!!!!!!!!!!! read-only !!!!!!!!!!!
SCOPES_CAL = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'People API Python Quickstart'


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

def get_credentials_cal():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES_CAL)
        flow.user_agent = APPLICATION_NAME + 'and test'
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

class MainWindowSlots(Ui_Form):   # Определяем функции, которые будем вызывать в слотах

    def setupUi(self, form):
        Ui_Form.setupUi(self,form)
        self.events_syncToken = ''
        self.contacty_syncToken = ''
        self.show_site = 'avito'
        self.my_html = ''
        self.contacty = []
        self.contacty_filtered = []
        self.contacty_filtered_reverced = {}
        self.groups = []
        self.groups_resourcenames = {}
        self.group_cur = ''
        self.group_cur_id = 0
        self.group_saved_id = None
        self.FIO_cur = ''
        self.FIO_cur_id = 0
        self.FIO_saved_id = 0
        credentials_con = get_credentials_con()
        self.http_con = credentials_con.authorize(Http())
        credentials_cal = get_credentials_cal()
        self.http_cal = credentials_cal.authorize(Http())
        self.google2db4allFull()
        self.all_stages = []
        self.all_stages_reverce = {}
        self.all_events = {}
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
        self.changed = True
        self.clbExport.hide()
        self.progressBar.hide()
        return

    def errMessage(self, err_text): ## Method to open a message box
        infoBox = QMessageBox() ##Message Box that doesn't run
        infoBox.setIcon(QMessageBox.Warning)
        infoBox.setText(err_text)
#        infoBox.setInformativeText("Informative Text")
        infoBox.setWindowTitle(datetime.strftime(datetime.now(), "%H:%M:%S") + ' Ошибка: ')
#        infoBox.setDetailedText("Detailed Text")
#        infoBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        infoBox.setStandardButtons(QMessageBox.Ok)
#        infoBox.setEscapeButton(QMessageBox.Close)
        infoBox.exec_()

    def google2db4allFull(self):                  # Google -> Внутр БД (все контакты) с полным обновлением
        credentials_con = get_credentials_con()
        self.http_con = credentials_con.authorize(Http())
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

# Вытаскиваем названия групп
            serviceg = discovery.build('contactGroups', 'v1', http=self.http_con,
                                       discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsg = serviceg.contactGroups().list(pageSize=200).execute()
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

            serviceg = discovery.build('contactGroups', 'v1', http=self.http_con,
                                       discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsg = serviceg.contactGroups().list(pageSize=200).execute()
        self.groups_resourcenames = {}
        self.groups_resourcenames_reversed = {}
        contactGroups = resultsg.get('contactGroups', [])
        for i, contactGroup in enumerate(contactGroups):
            self.groups_resourcenames[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
            self.groups_resourcenames_reversed[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]
# Контакты
        connections = []
        results = {'nextPageToken':''}
        while str(results.keys()).find('nextPageToken') > -1:
            if results['nextPageToken'] == '':
                try:
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageSize=2000,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageSize=2000,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
            else:
                try:
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageToken=results['nextPageToken'],
                        pageSize=2000,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageToken=results['nextPageToken'],
                        pageSize=2000,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
            connections.extend(results.get('connections', []))
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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

        self.all_events = {}
        for calendar in calendars:
            event = {}
            event['id'] = calendar['id']
            if str(calendar['start'].keys()).find('dateTime') > -1:
                event['start'] = calendar['start']['dateTime']
            else:
                event['start'] = str(utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00', "%Y-%m-%d %H:%M")))
            if str(calendar.keys()).find('htmlLink') > -1:
                event['www'] =calendar['htmlLink']
            else:
                event['www'] = ''
            self.all_events[calendar['id']] = event

        self.contacty = {}
        events4delete = []
        number_of_new = 0
        for i, connection in enumerate(connections):
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
            try:  # есть такой event - берем
                eventn = self.all_events[contact['resourceName']]
                contact['event'] = parse(eventn['start'])
                contact['event-www'] = eventn['www']
            except KeyError:  # нет такого event'а - ставим дряхлую дату
                contact['event'] = utc.localize(datetime(2012, 12, 31, 0, 0))
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
            contact['avito'] = ''                           # Фильтруем все ссылки на avito в поле 'avito'
            contact['instagram'] = ''                       # а ссылки на instagram в поле 'instagram'
            urls = []
            ourls = connection.get('urls', [])
            if len(ourls) > 0:
                for ourl in ourls:
                    urls.append(ourl['value'])
                    if ourl['value'].find('www.avito.ru') > -1:
                        contact['avito'] = ourl['value']
                    if ourl['value'].find('instagram.com') > -1:
                        contact['instagram'] = ourl['value']
            contact['urls'] = urls
            self.contacty[contact['resourceName']] = contact
            if contact['event'] > utc.localize(datetime(2013, 1, 1, 0, 0)) \
                    and contact['stage'] not in WORK_STAGES_CONST and contact['stage'] not in LOST_STAGES_CONST:
                events4delete.append(contact['resourceName'])
        for event4delete in events4delete:
            event4 = service_cal.events().get(calendarId='primary', eventId=event4delete).execute()
            event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
            event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
            updated_event = service_cal.events().update(calendarId='primary', eventId=event4delete, body=event4).execute()
        return

    def google2db4allPart(self):  # Google -> Внутр БД (все контакты) с частичным обновлением
        credentials_con = get_credentials_con()
        self.http_con = credentials_con.authorize(Http())
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

            # Вытаскиваем названия групп
            serviceg = discovery.build('contactGroups', 'v1', http=self.http_con,
                                       discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsg = serviceg.contactGroups().list(pageSize=200).execute()
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

            serviceg = discovery.build('contactGroups', 'v1', http=self.http_con,
                                       discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsg = serviceg.contactGroups().list(pageSize=200).execute()
        self.groups_resourcenames = {}
        self.groups_resourcenames_reversed = {}
        contactGroups = resultsg.get('contactGroups', [])
        for i, contactGroup in enumerate(contactGroups):
            self.groups_resourcenames[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
            self.groups_resourcenames_reversed[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]
        # Контакты
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
                        syncToken=self.contacty_syncToken,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageSize=2000,
                        requestSyncToken=True,
                        syncToken=self.contacty_syncToken,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
            else:
                try:
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageToken=results['nextPageToken'],
                        pageSize=2000,
                        requestSyncToken=True,
                        syncToken=self.contacty_syncToken,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем еще раз')
                    results = service.people().connections() \
                        .list(
                        resourceName='people/me',
                        pageToken=results['nextPageToken'],
                        pageSize=2000,
                        requestSyncToken=True,
                        syncToken=self.contacty_syncToken,
                        personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,'
                                     'emailAddresses,events,genders,imClients,interests,locales,memberships,metadata,'
                                     'names,nicknames,occupations,organizations,phoneNumbers,photos,relations,'
                                     'relationshipInterests,relationshipStatuses,residences,skills,taglines,urls,'
                                     'userDefined') \
                        .execute()
            connections.extend(results.get('connections', []))
            self.contacty_syncToken = results['nextSyncToken']

        # Календарь
        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
        calendars = []
        calendars_result = {'nextPageToken': ''}
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                eventd['start'] = str(
                    utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00', "%Y-%m-%d %H:%M")))
            if str(calendar.keys()).find('htmlLink') > -1:
                eventd['www'] = calendar['htmlLink']
            else:
                eventd['www'] = ''
            eventds[calendar['id']] = eventd

        self.contacty = {}
        events4delete = []
        number_of_new = 0
        for i, connection in enumerate(connections):
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
            try:  # есть такой event - берем
                eventn = eventds[contact['resourceName']]
                contact['event'] = parse(eventn['start'])
                contact['event-www'] = eventn['www']
            except KeyError:  # нет такого event'а - ставим дряхлую дату
                contact['event'] = utc.localize(datetime(2012, 12, 31, 0, 0))
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
                        contact['instagram'] = ourl['value']
            contact['urls'] = urls
            self.contacty[contact['resourceName']] = contact
            if contact['event'] > utc.localize(datetime(2013, 1, 1, 0, 0)) \
                    and contact['stage'] not in WORK_STAGES_CONST and contact['stage'] not in LOST_STAGES_CONST:
                events4delete.append(contact['resourceName'])
        for event4delete in events4delete:
            event4 = service_cal.events().get(calendarId='primary', eventId=event4delete).execute()
            event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
            event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
            updated_event = service_cal.events().update(calendarId='primary', eventId=event4delete,
                                                        body=event4).execute()
        return

    def google2db4one(self):               # Google -> Внутр БД (текущий контакт)
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            result = service.people().get(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,'
                             'events,genders,imClients,interests,locales,memberships,metadata,names,nicknames,'
                             'occupations,organizations,phoneNumbers,photos,relations,relationshipInterests,'
                             'relationshipStatuses,residences,skills,taglines,urls,userDefined') \
            .execute()
            connection = result
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            result = service.people().get(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,'
                             'events,genders,imClients,interests,locales,memberships,metadata,names,nicknames,'
                             'occupations,organizations,phoneNumbers,photos,relations,relationshipInterests,'
                             'relationshipStatuses,residences,skills,taglines,urls,userDefined') \
            .execute()
            connection = result
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                eventd['start'] = str(utc.localize(datetime.strptime(calendar['start']['date'] + ' 12:00', "%Y-%m-%d %H:%M")))
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
        try:  # есть такой event - берем
            eventn = eventds[contact['resourceName']]
            contact['event'] = parse(eventn['start'])
            contact['event-www'] = eventn['www']
        except KeyError:  # нет такого event'а - ставим дряхлую дату
            contact['event'] = utc.localize(datetime(2012, 12, 31, 0, 0))
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
                    contact['instagram'] = ourl['value']
        contact['urls'] = urls
        ind = self.contacts_filtered[self.FIO_cur_id]['contact_ind']
        self.contacts_filtered[self.FIO_cur_id] = contact
        self.contacts_filtered[self.FIO_cur_id]['contact_ind'] = ind
        self.contacty[self.contacts_filtered[self.FIO_cur_id]['contact_ind']] = contact
        return

    def google2db4etag(self):  # Google -> etag внутр БД (текущий контакт)
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            result = service.people().get(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                             'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                             'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                             'residences,skills,taglines,urls,userDefined') \
                .execute()
            connection = result
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            result = service.people().get(
                resourceName='people/' + elf.contacts_filtered[self.FIO_cur_id]['resourceName'],
                personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                             'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                             'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                             'residences,skills,taglines,urls,userDefined') \
                .execute()
            connection = result
        self.contacts_filtered[self.FIO_cur_id]['etag'] = connection['etag']
        return

    def db2form4one(self):              #  внутр. БД -> Форма
        self.teNote.setText(self.contacts_filtered[self.FIO_cur_id]['note'])
        self.cbStage.setCurrentIndex(self.all_stages_reverce[self.contacts_filtered[self.FIO_cur_id]['stage']])
        phones = ''
        if len(self.contacts_filtered[self.FIO_cur_id]['phones']) > 0:
            phones = fine_phone(self.contacts_filtered[self.FIO_cur_id]['phones'][0])
            for i, phone in enumerate(self.contacts_filtered[self.FIO_cur_id]['phones']):
                if i == 0:
                    continue
                phones += ' ' + fine_phone(phone)
        self.lePhones.setText(phones)
        self.FIO_cur = self.contacts_filtered[self.FIO_cur_id]['fio']
        self.calls_ids = []
        for i, call in enumerate(self.calls):
            for phone in self.contacts_filtered[self.FIO_cur_id]['phones']:
                if format_phone(call.split(']_[')[1]) == format_phone(phone):
                    self.calls_ids.append(i)
        self.leTown.setText(self.contacts_filtered[self.FIO_cur_id]['town'])
        self.leEmail.setText(self.contacts_filtered[self.FIO_cur_id]['email'])
        self.leIOF.setText(self.contacts_filtered[self.FIO_cur_id]['iof'])
        urls = ''
        for url in self.contacts_filtered[self.FIO_cur_id]['urls']:
            urls += url + ' '
        self.leUrls.setText(urls)
#        ca = self.contacts_filtered[self.FIO_cur_id]['calendar'].split('.')
#        self.deCalendar.setDate(QDate(int(ca[2]),int(ca[1]),int(ca[0])))
        self.deCalendar.setDate(self.contacts_filtered[self.FIO_cur_id]['event'])
        self.cbTime.setTime(self.contacts_filtered[self.FIO_cur_id]['event'].time())
        self.leCost.setText(str(round(self.contacts_filtered[self.FIO_cur_id]['cost'], 4)))
        if len(self.contacts_filtered[self.FIO_cur_id]['avito']) > 10 and self.show_site == 'avito':
            self.preview.load(QUrl(self.contacts_filtered[self.FIO_cur_id]['avito']))
            self.preview.show()
            avito_x = self.contacts_filtered[self.FIO_cur_id]['avito'].strip()
            for i in range(len(avito_x)-1,0,-1):
                if avito_x[i] not in digits:
                    break
            response = request.urlopen('https://www.avito.ru/items/stat/' + avito_x[i+1:] + '?step=0')
            html_x = response.read().decode('utf-8')
            self.leDateStart.setText(html_x.split('<strong>')[1].split('</strong>')[0])
        elif len(self.contacts_filtered[self.FIO_cur_id]['instagram']) > 10 and self.show_site == 'instagram':
            self.preview.load(QUrl(self.contacts_filtered[self.FIO_cur_id]['instagram']))
            self.preview.show()
        self.setup_twCalls()

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
        self.contacts_filtered[self.FIO_cur_id]['cost'] = float(self.leCost.text()) + random() * 1e-5
        self.contacts_filtered[self.FIO_cur_id]['town'] = self.leTown.text().strip()
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

    def refresh_stages(self):          # Добавляем в стандатные стадии стадии из контактов
        self.all_stages = ALL_STAGES_CONST
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
            self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
            self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
        except IndexError:
            q=0
#        self.changed = False  # обновляем информацию о контакте
#        self.google2db4one()
#        self.changed = True
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
                has_to_today = contact['event'] <= to_today
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
        self.contacts_filtered = []
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
                    contacts_f_event[i] = contacts_f[i]['event']
                    contacts_f_fio[i] = contacts_f[i]['fio']
                    contacts_f_cost[i] = contacts_f[i]['cost']
                    i += 1
        else:
            for ind, contact in enumerate(self.contacty.values()):
                if self.chbToToday.isChecked():
                    to_today = utc.localize(datetime.now())
                else:
                    to_today = utc.localize(datetime(2100,12,31,0,0))
                has_to_today = contact['event'] <= to_today
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
                    contacts_f_event[i] = contacts_f[i]['event']
                    contacts_f_fio[i] = contacts_f[i]['fio']
                    contacts_f_cost[i] = contacts_f[i]['cost']
                    i += 1
        if self.chbDateSort.isChecked():                                        # Сортировка по дате
            contacts_f_event_sorted = OrderedDict(sorted(contacts_f_event.items(), reverse = True, key=lambda t: t[1]))
            for j, contact_f_event_sorted in enumerate(contacts_f_event_sorted):
                self.contacts_filtered.append(contacts_f[contact_f_event_sorted])
                self.contacts_filtered_reverced[contacts_f[contact_f_event_sorted]['resourceName']] = j
        elif self.chbCostSort.isChecked():                                      # Сортировка по цене
            contacts_f_cost_sorted = OrderedDict(sorted(contacts_f_cost.items(), reverse = True, key=lambda t: t[1]))
            for j, contact_f_cost_sorted in enumerate(contacts_f_cost_sorted):
                self.contacts_filtered.append(contacts_f[contact_f_cost_sorted])
                self.contacts_filtered_reverced[contacts_f[contact_f_cost_sorted]['resourceName']] = j
        else:                                                                   # Сортировка по фамилии
            contacts_f_fio_sorted = OrderedDict(sorted(contacts_f_fio.items(), key=lambda t: t[1]))
            for j, contact_f_fio_sorted in enumerate(contacts_f_fio_sorted):
                self.contacts_filtered.append(contacts_f[contact_f_fio_sorted])
                self.contacts_filtered_reverced[contacts_f[contact_f_fio_sorted]['resourceName']] = j
        self.twFIO.setColumnCount(1)                                # Устанавливаем кол-во колонок
        self.twFIO.setRowCount(len(self.contacts_filtered))         # Кол-во строк из таблицы
        for i, contact in enumerate(self.contacts_filtered):
            self.twFIO.setItem(i-1, 1, QTableWidgetItem(contact['fio']))
        # Устанавливаем заголовки таблицы
        self.twFIO.setHorizontalHeaderLabels(["Ф.И.О."])
        # Устанавливаем выравнивание на заголовки
        self.twFIO.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        # делаем ресайз колонок по содержимому
        self.twFIO.resizeColumnsToContents()
        self.click_twFIO()
        return

    def click_twFIO(self, index=None):
        if index == None:
            index = self.twFIO.model().index(0, 0)
            self.twFIO.setCurrentIndex(index)
        if self.FIO_saved_id:
            try:
                index = self.twFIO.model().index(self.contacts_filtered_reverced[self.FIO_saved_id], 0)
            except KeyError:
                index = self.twFIO.model().index(0, 0)
            self.twFIO.setCurrentIndex(index)
            self.FIO_saved_id = 0
        if index.row() < 0:
            return None
        self.changed = False # обновляем информацию о контакте и карточку
        self.FIO_cur_id = index.row()
        self.google2db4one()
        self.db2form4one()
        self.changed = True
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

    def click_cbStage(self):                                            # !!!!!! Пока что выключили !!!!!!!!!
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
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                updatePersonFields='biographies,userDefined',
                body=buf_contact).execute()
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().updateContact(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                updatePersonFields='biographies,userDefined',
                body=buf_contact).execute()
        self.changed = False # обновляем информацию о контакте и карточку
        self.google2db4one()
        self.db2form4one()
        self.changed = True
        return

    def click_clbRedo(self):
        try:
            self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
            self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
        except IndexError:
            q=0
        self.google2db4all() # Перезагружаем ВСЕ контакты из gmail
        self.setup_twGroups()
        return

    def click_clbSave(self):
        pred_cal = self.contacts_filtered[self.FIO_cur_id]['event']
        pred_stage = self.contacts_filtered[self.FIO_cur_id]['stage']
        self.form2db4one()
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
        if self.leTown.text():
            if len(self.leTown.text().strip()) > 0:
                buf_contact['addresses'] = [{'streetAddress': self.leTown.text().strip()}]
        time.sleep(5)
        self.changed = False # обновляем информацию о контакте
        self.google2db4etag()
        self.changed = True
        buf_contact['etag'] = self.contacts_filtered[self.FIO_cur_id]['etag']
        # Обновление контакта
        try:
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().updateContact(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                updatePersonFields='addresses,biographies,emailAddresses,names,phoneNumbers,urls,userDefined',
                body=buf_contact).execute()
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем еще раз')
            time.sleep(1)
            service = discovery.build('people', 'v1', http=self.http_con,
                                      discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
            resultsc = service.people().updateContact(
                resourceName='people/' + self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                updatePersonFields='addresses,biographies,emailAddresses,names,phoneNumbers,urls,userDefined',
                body=buf_contact).execute()

        cal_cancel = False
        if pred_cal.date() == self.deCalendar.date(): #.toString("dd.MM.yyyy"):  #
            cal_cancel = True
#        self.changed = False        # обновляем информацию о контакте
#        self.google2db4one()
#        self.changed = True
# Календарь
#        if cal_cancel or self.deCalendar.date() < datetime.today().date():
#            return         # Если Дата не изменилась или поставили дату меньшую сегодняшней - ничего не изменяем
        if self.cbStage.currentText() not in WORK_STAGES_CONST and self.cbStage.currentText() not in LOST_STAGES_CONST:  # Если стадия не рабочая, уходим поставив прошлую дату
            try:
                service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
                event4 = service_cal.events().get(calendarId='primary',
                         eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName']).execute()
                event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
                event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
                updated_event = service_cal.events().update(calendarId='primary',
                                eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                                body=event4).execute()
            except Exception as ee:
                print(datetime.now().strftime("%H:%M:%S") + ' попробуем поставить прошлую дату еще раз')
                time.sleep(1)
                service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
                event4 = service_cal.events().get(calendarId='primary',
                         eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName']).execute()
                event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
                event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
                updated_event = service_cal.events().update(calendarId='primary',
                                eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                                body=event4).execute()
            self.contacts_filtered[self.FIO_cur_id]['event'] = utc.localize(datetime(2012, 12, 31, 0, 0))
            return
        if self.cbStage.currentText() not in WORK_STAGES_CONST:   # Если нет объявления, ставим ближайшую субботу
            lost_date = datetime(2012, 1, 7)
            try:
                service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
                event4 = service_cal.events().get(calendarId='primary',
                         eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName']).execute()
                event4_date = parse(event4['start']['dateTime'])
                lost_date = datetime(2012, 1, 7)
                while lost_date.year == datetime.now().year:
                    if event4_date < utc.localize(lost_date):
                        event4['start']['dateTime'] = (lost_date + timedelta(hours=19)).isoformat() + '+04:00'
                        event4['end']['dateTime'] = (lost_date + timedelta(hours=19,minutes=15)).isoformat() + '+04:00'
                        break
                    else:
                        lost_date += timedelta(days=7)
                updated_event = service_cal.events().update(calendarId='primary',
                                eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                                body=event4).execute()
            except Exception as ee:
                print(datetime.now().strftime("%H:%M:%S") + ' попробуем поставить прошлую дату еще раз')
                time.sleep(1)
                service_cal = discovery.build('calendar', 'v3', http=self.http_cal)  # Считываем весь календарь
                event4 = service_cal.events().get(calendarId='primary',
                         eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName']).execute()
                event4_date = parse(event4['start']['dateTime'])
                lost_date = datetime(2012, 1, 7)
                while lost_date.year == datetime.now().year:
                    if event4_date < utc.localize(lost_date):
                        event4['start']['dateTime'] = (lost_date + timedelta(hours=19)).isoformat() + '+04:00'
                        event4['end']['dateTime'] = (lost_date + timedelta(hours=19,minutes=15)).isoformat() + '+04:00'
                        break
                    else:
                        lost_date += timedelta(days=7)
                updated_event = service_cal.events().update(calendarId='primary',
                                eventId=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
                                body=event4).execute()
            self.contacts_filtered[self.FIO_cur_id]['event'] = utc.localize(lost_date)
            return

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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем считать весь календарь еще раз')
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
        self.events = {}
        for calendar in calendars:                                                          # Переводим в удобную форму
            event = {}
            event['id'] = calendar['id']
            event['start'] = calendar['start']
            event['end'] = calendar['end']
#            event['start'] = {'dateTime' : datetime.combine(datetime.strptime(buf_contact['userDefined'][1]['value'],
#                            '%d.%m.%Y').date(),datetime.strptime('15:00','%H:%M').time()).isoformat() + 'Z'}
#            event['end'] = {'dateTime' : datetime.combine(datetime.strptime(buf_contact['userDefined'][1]['value'],
#                            '%d.%m.%Y').date(),datetime.strptime('15:15','%H:%M').time()).isoformat() + 'Z'}
            event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
            phones = ''
            memos = ''
            if len(self.contacts_filtered[self.FIO_cur_id]['phones']) > 0:
                phones = fine_phone(self.contacts_filtered[self.FIO_cur_id]['phones'][0])
                for i, phone in enumerate(self.contacts_filtered[self.FIO_cur_id]['phones']):
                    if i == 0:
                        continue
                    phones += ', ' + fine_phone(phone)
            if len(self.contacts_filtered[self.FIO_cur_id]['urls']):
                memos = self.contacts_filtered[self.FIO_cur_id]['urls'][0] + '\n'
                for i, memo in enumerate(self.contacts_filtered[self.FIO_cur_id]['urls']):
                    if i == 0:
                        continue
                    memos += memo + '\n'
            event['description'] = phones + '\n' + memos + '\n' + self.contacts_filtered[self.FIO_cur_id]['note']
            event['summary'] = self.contacts_filtered[self.FIO_cur_id]['fio'] + ' - ' +\
                               self.contacts_filtered[self.FIO_cur_id]['stage']
            self.events[calendar['id']] = event
        has_event = False
        try:                                                    # есть такой event - update'им
            event = self.events[self.contacts_filtered[self.FIO_cur_id]['resourceName']]
            has_event = True
        except KeyError:  # нет такого event'а - создаем
            has_event = False

        if not has_event:
            event = {}
            event['id'] = self.contacts_filtered[self.FIO_cur_id]['resourceName']

        event['start'] = {'dateTime' : datetime.combine(self.deCalendar.date().toPyDate(),
                                        self.cbTime.time().toPyTime()).isoformat() + '+04:00'}

        event['end'] = {'dateTime' : (datetime.combine(self.deCalendar.date().toPyDate(),
                                        self.cbTime.time().toPyTime()) + timedelta(minutes=15)).isoformat() + '+04:00'}
        event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
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
        event['description'] = phones + '\n' + memos + '\n' \
                               + self.contacts_filtered[self.FIO_cur_id]['note']
        event['summary'] = self.contacts_filtered[self.FIO_cur_id]['fio'] + ' - ' +\
                           self.contacts_filtered[self.FIO_cur_id]['stage']
        self.events[self.contacts_filtered[self.FIO_cur_id]['resourceName']] = event

        try:
            if has_event:
                calendar_result = service_cal.events().update(calendarId='primary', eventId=event['id'], body=event) \
                    .execute()
            else:
                calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
        except Exception as ee:
            print(datetime.now().strftime("%H:%M:%S") +' попробуем добавить event еще раз')
            time.sleep(1)
            if has_event:
                calendar_result = service_cal.events().update(calendarId='primary', eventId=event['id'], body=event) \
                    .execute()
            else:
                calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
        self.changed = False            # обновляем информацию о контакте
        self.google2db4one()
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

    def click_clbGoURL1(self):
        if len(self.contacts_filtered[self.FIO_cur_id]['urls']) > 0:
            if len(self.contacts_filtered[self.FIO_cur_id]['urls'][0]) > 5:
                proc = Popen('firefox --new-tab ' + self.contacts_filtered[self.FIO_cur_id]['urls'][0],
                             shell=True, stdout=PIPE, stderr=PIPE)
                proc.wait()  # дождаться выполнения
                res = proc.communicate()  # получить tuple('stdout', 'stderr')
                if proc.returncode:
                    print(res[1])
                    print('result:', res[0])

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
        str_ = text
        if str_.find(' на участке ') > -1:
            str_ = str_.replace(' на участке ', '+')
        if str_.find(' м²') > -1:
            str_ = str_.replace(' м²', 'м²')
        if str_.find(' сот') > -1:
            str_ = str_.replace(' сот', 'сот')
        if str_.find(' га') > -1:
            str_ = str_.replace(' га', 'га')
        if str_.find('.') > -1:
            str_ = str_.replace('.', '_')
        self.leIOF.setText(str_)

    def click_clbAvito(self):                       # Переключение с календаря на карточку avito или instagram
        if self.show_site == 'instagram':
            self.clbAvito.setIcon(QIcon('avito.png'))
            self.show_site = 'avito'
            if len(self.contacts_filtered[self.FIO_cur_id]['avito']) > 10:
                self.preview.load(QUrl(self.contacts_filtered[self.FIO_cur_id]['avito']))
                self.preview.show()
        elif self.show_site == 'calendar':
            self.clbAvito.setIcon(QIcon('instagram.png'))
            self.show_site = 'instagram'
            if len(self.contacts_filtered[self.FIO_cur_id]['instagram']) > 10:
                self.preview.load(QUrl(self.contacts_filtered[self.FIO_cur_id]['instagram']))
                self.preview.show()
        else:
            self.clbAvito.setIcon(QIcon('gcal.png'))
            self.show_site = 'calendar'
            self.preview.load(QUrl('https://calendar.google.com'))
            self.preview.show()

    def click_clbGCal(self):
        q=0
        self.clbExport.show()

    def preview_loading(self):
        self.clbPreviewLoading.setIcon(QIcon('load.gif'))

    def preview_loaded(self):
        self.clbPreviewLoading.setIcon(QIcon('plus.png'))

    def click_clbPreviewLoading(self):
        self.preview.page().toHtml(self.processHtml)
        self.teNote.setPlainText(self.my_html)

    def processHtml(self, html_x):
        self.my_html = str(html_x)
        return

    def click_clbTrashLoad(self):
        if self.group_cur != '_КоттеджиСочи':
            return
        self.progressBar.show()
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
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
                    event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
                    event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
                    updated_event = service_cal.events().update(calendarId='primary',
                                                eventId=contact['resourceName'], body=event4).execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить событие еще раз')
                    event4 = service_cal.events().get(calendarId='primary',
                                                             eventId=contact['resourceName']).execute()
                    event4['start']['dateTime'] = datetime(2012, 12, 31, 0, 0).isoformat() + 'Z'
                    event4['end']['dateTime'] = datetime(2012, 12, 31, 0, 15).isoformat() + 'Z'
                    updated_event = service_cal.events().update(calendarId='primary',
                                                eventId=contact['resourceName'], body=event4).execute()
                try:
                    resultsc = service.people().deleteContact(resourceName='people/' + contact['resourceName']).execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") +' попробуем удалить контакт еще раз')
                    resultsc = service.people().deleteContact(resourceName='people/' + contact['resourceName']).execute()
        html_x = ''
        self.progressBar.setMaximum(MAX_PAGE)
        for i in range(1, MAX_PAGE):
            self.progressBar.setValue(i)
            if i == 1:
                response = request.urlopen('https://www.avito.ru/sochi/doma_dachi_kottedzhi/prodam?s=2&user=1')
            else:
                response = request.urlopen('https://www.avito.ru/sochi/doma_dachi_kottedzhi/prodam?p=' + str(i) +
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
                    j += 1
                    buf_contact = {}
                    buf_contact['userDefined'] = [{}, {}, {}]
                    buf_contact['userDefined'][0]['value'] = 'пауза'
                    buf_contact['userDefined'][0]['key'] = 'stage'
                    buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
                    buf_contact['userDefined'][1]['key'] = 'calendar'
                    buf_contact['userDefined'][2]['value'] = '0'
                    buf_contact['userDefined'][2]['key'] = 'cost'
                    buf_contact['names'] = [{'givenName': str(j)}]
                    buf_contact['urls'] = {'value': avitos[avito_i]}
                    buf_contact['biographies'] = [{}]
                    buf_contact['biographies'][0]['value'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) \
                                                             + '|0м|\n'
                    # buf_contact['phoneNumbers'] = ['0']
                    # Создаем контакт
                    try:
                        service = discovery.build('people', 'v1', http=self.http_con,
                                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                        resultsc = service.people().createContact(body=buf_contact).execute()
                    except Exception as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз')
                        time.sleep(1)
                        service = discovery.build('people', 'v1', http=self.http_con,
                                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                        resultsc = service.people().createContact(body=buf_contact).execute()
                    # Добавляем в текущую группу
                    try:
                        group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                        resultsg = service.contactGroups().members().modify(
                            resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
                            body=group_body
                        ).execute()
                    except Exception as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз')
                        time.sleep(1)
                        group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                        resultsg = service.contactGroups().members().modify(
                            resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
                            body=group_body
                        ).execute()
                    # Добавляем событие через 14 дней
                    event = {}
                    event['id'] = resultsc['resourceName'].split('/')[1]
                    event['start'] = {'dateTime': datetime.combine((datetime.now().date() + timedelta(days=14)),
                                                                   datetime.strptime('19:00',
                                                                                     '%H:%M').time()).isoformat() + '+04:00'}
                    event['end'] = {'dateTime': datetime.combine((datetime.now().date() + timedelta(days=14)),
                                                                 datetime.strptime('19:15',
                                                                                   '%H:%M').time()).isoformat() + '+04:00'}
                    event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
                    event['description'] = '|пауза|' + str(
                        datetime.now().date() + timedelta(days=14)) + '|0м|\n' + avitos[avito_i]
                    event['summary'] = '- пауза'
                    try:
                        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                        calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
                    except Exception as ee:
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить event еще раз')
                        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                        calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
        self.google2db4allFull()  # Перезагружаем ВСЕ контакты из gmail
        self.setup_twGroups()
        self.progressBar.hide()

    def click_clbExport(self):                     # ищем на странице отсутствующие в БД ссылки avito и создаем карточки
        #print(self.preview.page().url().url())
        self.preview.page().toHtml(self.processHtml)
        if len(self.my_html) < 1000:
            return
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
        avitos = []
        avitos_raw = self.my_html.split('href="/sochi/doma_dachi_kottedzhi/')
        for i, avito_raw in enumerate(avitos_raw):
            if i == 0:
                continue
            is_double = False
            if avito_raw[:6] != 'prodam':
                for davito in avitos:
                    if davito == 'https://www.avito.ru/sochi/doma_dachi_kottedzhi/' + avito_raw.split('"')[0]:
                        is_double = True
                if not is_double:
                    avitos.append('https://www.avito.ru/sochi/doma_dachi_kottedzhi/' + avito_raw.split('"')[0])
        j = round(random()*1000000)
        for avito in avitos:
            has_in_db = False
            for contact in self.contacty.values():
                if str(contact.keys()).find('avito') > -1:
                    if contact['avito'] == avito:
                        has_in_db = True
            if not has_in_db:
                j += 1
                buf_contact = {}
                buf_contact['userDefined'] = [{}, {}, {}]
                buf_contact['userDefined'][0]['value'] = 'пауза'
                buf_contact['userDefined'][0]['key'] = 'stage'
                buf_contact['userDefined'][1]['value'] = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")
                buf_contact['userDefined'][1]['key'] = 'calendar'
                buf_contact['userDefined'][2]['value'] = '0'
                buf_contact['userDefined'][2]['key'] = 'cost'
                buf_contact['names'] = [{'givenName': str(j)}]
                buf_contact['urls'] = {'value': avito}
                buf_contact['biographies'] = [{}]
                buf_contact['biographies'][0]['value'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) \
                                                          + '|0м|\n'
                #buf_contact['phoneNumbers'] = ['0']
                # Создаем контакт
                try:
                    service = discovery.build('people', 'v1', http=self.http_con,
                                              discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                    resultsc = service.people().createContact(body=buf_contact).execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать контакт еще раз')
                    time.sleep(1)
                    service = discovery.build('people', 'v1', http=self.http_con,
                                              discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
                    resultsc = service.people().createContact(body=buf_contact).execute()
                # Добавляем в текущую группу
                try:
                    group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                    resultsg = service.contactGroups().members().modify(
                        resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
                        body=group_body
                    ).execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить в группу еще раз')
                    time.sleep(1)
                    group_body = {'resourceNamesToAdd': [resultsc['resourceName']], 'resourceNamesToRemove': []}
                    resultsg = service.contactGroups().members().modify(
                        resourceName='contactGroups/' + self.groups_resourcenames_reversed[self.group_cur],
                        body=group_body
                    ).execute()
                # Добавляем событие через 14 дней
                event = {}
                event['id'] = resultsc['resourceName'].split('/')[1]
                event['start'] = {'dateTime' : datetime.combine((datetime.now().date() + timedelta(days=14)),
                                          datetime.strptime('19:00','%H:%M').time()).isoformat() + '+04:00'}
                event['end'] = {'dateTime' : datetime.combine((datetime.now().date() + timedelta(days=14)),
                                          datetime.strptime('19:15','%H:%M').time()).isoformat() + '+04:00'}
                event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
                event['description'] = '|пауза|' + str(datetime.now().date() + timedelta(days=14)) + '|0м|\n' + avito
                event['summary'] = '- пауза'
                try:
                    service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                    calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
                except Exception as ee:
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем добавить event еще раз')
                    service_cal = discovery.build('calendar', 'v3', http=self.http_cal)
                    calendar_result = service_cal.events().insert(calendarId='primary', body=event).execute()
        self.google2db4allFull() # Перезагружаем ВСЕ контакты из gmail
        self.setup_twGroups()
        q=0

    def qwe(self):
        q4 = """
        
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
        if self.leTown.text():
            if len(self.leTown.text().strip()) > 0:
                buf_contact['addresses'] = [{'streetAddress': self.leTown.text().strip()}]

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
        except Exception as ee:
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
        except Exception as ee:
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
        except Exception as ee:
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
                except Exception as ee:
                    time.sleep(1)
                    print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать еще раз')
                    try:
                        contact_res = service.people().createContact(body=contact).execute()
                    except Exception as ee:
                        time.sleep(1)
                        print(datetime.now().strftime("%H:%M:%S") + ' попробуем создать третий раз')
                        contact_res = service.people().createContact(body=contact).execute()
                try:
                    result = service.people().deleteContact(resourceName=resourceName).execute()
                except Exception as ee:
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


