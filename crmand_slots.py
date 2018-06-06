from __future__ import print_function

from httplib2 import Http
from subprocess import Popen, PIPE
import os
from string import digits
from dateutil.parser import parse

from apiclient import discovery                             # Механизм запроса данных
from googleapiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime
import time

from PyQt5.QtCore import QDate, QDateTime, QSize, Qt, QByteArray, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QMainWindow, QWidget


from crmand_win import Ui_Form

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from lib import unique, l, s, fine_phone, format_phone

ALL_STAGES_CONST = ['работаем', 'отработали', 'проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча',
                    'диагностика', 'перезвонить', 'нужен e-mail', 'секретарь передаст', 'отправил сообщен',
                    'нет на месте', 'недозвон', 'недоступен', '---', 'когда получится','нет контактов',
                    'не занимаюсь', 'не понимает', 'не интересно', 'не верит', 'рыпу']

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
        self.contacts = []
        self.contacts_filtered = []
        self.contacts_filtered_reverced = {}
        self.groups = []
        self.groups_resourcenames = {}
        self.group_cur = ''
        self.group_cur_id = 0
        self.group_saved_id = None
        self.FIO_cur = ''
        self.FIO_cur_id = 0
        self.FIO_saved_id = 0
        self.refresh_contacts()
        self.all_stages = []
        self.all_stages_reverce = {}
        self.events = {}
        credentials_con = get_credentials_con()
        self.http_con = credentials_con.authorize(Http())
        credentials_cal = get_credentials_cal()
        self.http_cal = credentials_cal.authorize(Http())
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
        self.clbExport.close()
        return

    def refresh_contacts(self):                             # Обновляем все контакты из гугля
        credentials_con = get_credentials_con()
        self.http_con = credentials_con.authorize(Http())
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

        # Вытаскиваем названия групп
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
        self.contacts = []
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
                    memberships.append(self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
            contact['groups'] = memberships
            stage = '---'
            calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
            ostages = connection.get('userDefined', [])
            if len(ostages) > 0:
                for ostage in ostages:
                    if ostage['key'].lower() == 'stage':
                        stage = ostage['value'].lower()
                    if ostage['key'].lower() == 'calendar':
                        calendar = ostage['value']
            contact['stage'] = stage
            contact['calendar'] = calendar
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
            self.contacts.append(contact)
        return

    def refresh_contact(self):                                              # Обновляем текущий контакт из гугля
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        result = service.people().get(
            resourceName=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
            personFields='addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                         'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                         'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                         'residences,skills,taglines,urls,userDefined') \
            .execute()
        connection = result
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
                memberships.append(self.groups_resourcenames[omembership['contactGroupMembership']['contactGroupId']])
        contact['groups'] = memberships
        stage = '---'
        calendar = QDate().currentDate().addDays(-1).toString("dd.MM.yyyy")
        ostages = connection.get('userDefined', [])
        if len(ostages) > 0:
            for ostage in ostages:
                if ostage['key'].lower() == 'stage':
                    stage = ostage['value'].lower()
                if ostage['key'].lower() == 'calendar':
                    calendar = ostage['value']
        contact['stage'] = stage
        contact['calendar'] = calendar
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
        ind = self.contacts_filtered[self.FIO_cur_id]['contact_ind']
        self.contacts_filtered[self.FIO_cur_id] = contact
        self.contacts_filtered[self.FIO_cur_id]['contact_ind'] = ind
        self.contacts[self.contacts_filtered[self.FIO_cur_id]['contact_ind']] = contact
        return

    def refresh_card(self):                                                     # Обновляем поля в карточке
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
        ca = self.contacts_filtered[self.FIO_cur_id]['calendar'].split('.')
        self.deCalendar.setDate(QDate(int(ca[2]),int(ca[1]),int(ca[0])))
        self.setup_twCalls()


    def refresh_stages(self):          # Добавляем в стандатные стадии стадии из контактов
        self.all_stages = ALL_STAGES_CONST
        for i, all_stage in enumerate(self.all_stages):
            self.all_stages_reverce[all_stage] = i
        for i, contact in enumerate(self.contacts):
            has = False
            for all_stage in self.all_stages:
                if all_stage == contact['stage']:
                    has = True
            if not has:
                self.all_stages.append(contact['stage'])
                self.all_stages_reverce[contact['stage']] = len(self.all_stages) - 1
        return

    def click_pbPeopleFilter(self):  # Кнопка фильтр
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
#        self.changed = False  # обновляем информацию о контакте
#        self.refresh_contact()
#        self.changed = True
        self.setup_twGroups()
        return

    def setup_twGroups(self):
        self.twGroups.setColumnCount(0)
        self.twGroups.setRowCount(0)        # Кол-во строк из таблицы
        groups = set()
        for contact in self.contacts:      # !!!!!!!!!!!!!!!! Добавить фильтры !!!!!!!!!!!!!!!
            has_FIO = contact['fio'].lower().find(self.leFIO.text().strip().lower()) > -1
            has_phone = False
            for phone in contact['phones']:
                if str(l(phone)).find(str(l(self.lePhone.text()))) > -1:
                    has_phone = True
            if not self.chbHasPhone.isChecked():
                has_phone = True
            has_note = s(contact['note']).lower().find(self.leNote.text().lower().strip()) > -1
            has_stage = (self.all_stages_reverce[contact['stage']] <= self.cbStageTo.currentIndex())\
                        and (self.all_stages_reverce[contact['stage']] >= self.cbStageFrom.currentIndex())
            if has_FIO and has_phone and has_note and has_stage:
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
        cs = {}
        i = 0
        for ind, contact in enumerate(self.contacts):
            has_FIO = contact['fio'].lower().find(self.leFIO.text().strip().lower()) > -1
            has_phone = False
            tel = self.lePhone.text()
            tel = ''.join([char for char in tel if char in digits])
            for phone in contact['phones']:
                if str(l(phone)).find(tel) > -1:
                    has_phone = True
            if not self.chbHasPhone.isChecked():
                has_phone = True
            has_note = s(contact['note']).lower().find(self.leNote.text().lower().strip()) > -1
            has_group = False
            for group in contact['groups']:
                if group == self.group_cur:
                    has_group = True
            has_stage = (self.all_stages_reverce[contact['stage']] <= self.cbStageTo.currentIndex())\
                        and (self.all_stages_reverce[contact['stage']] >= self.cbStageFrom.currentIndex())
            if has_FIO and has_phone and has_note and has_group and has_stage:
                contacts_f.append(contact)
                contacts_f[i]['contact_ind'] = ind
                cs[contact['fio']] = i
                i += 1
        j = 0
        for kk, i in sorted(cs.items(), key=lambda item: item[0]):  # Хитровычурная сортирвка с исп. sorted()
            self.contacts_filtered.append(contacts_f[i])
            self.contacts_filtered_reverced[contacts_f[i]['resourceName']] = j
            j += 1
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
        self.refresh_contact()
        self.refresh_card()
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

    def click_twCalls(self, index=None):
        audios = ''
        for i, call_id in enumerate(self.calls_ids):
            audios +=  self.calls[call_id] + ' '
        proc = Popen('gnome-mplayer --single_instance ' + audios, shell=True, stdout=PIPE, stderr=PIPE)
        proc.wait()  # дождаться выполнения
        res = proc.communicate()  # получить tuple('stdout', 'stderr')
        if proc.returncode:
            print(res[1])
            print('result:', res[0])

    def click_cbStage(self):
        if not self.changed:
            return
        buf_contact = {}
        buf_contact['userDefined'] = [{},{}]
        buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
        buf_contact['userDefined'][1]['key'] = 'calendar'
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
        self.changed = False # обновляем информацию о контакте и карточку
        self.refresh_contact()
        self.refresh_card()
        self.changed = True
        return

    def click_pbRedo(self):
        self.group_saved_id = self.groups_resourcenames_reversed[self.group_cur]
        self.FIO_saved_id = self.contacts_filtered[self.FIO_cur_id]['resourceName']
        self.refresh_contacts() # Перезагружаем ВСЕ контакты из gmail
        self.setup_twGroups()
        return

    def click_pbSave(self):
        buf_contact = {}
        buf_contact['userDefined'] = [{},{}]
        buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
        buf_contact['userDefined'][1]['key'] = 'calendar'
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
        # Обновление контакта
        service = discovery.build('people', 'v1', http=self.http_con,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        self.changed = False # обновляем информацию о контакте
        self.refresh_contact()
        self.changed = True
        buf_contact['etag'] = self.contacts_filtered[self.FIO_cur_id]['etag']
        resultsc = service.people().updateContact(
            resourceName=self.contacts_filtered[self.FIO_cur_id]['resourceName'],
            updatePersonFields='addresses,biographies,emailAddresses,names,phoneNumbers,urls,userDefined',
            body=buf_contact).execute()
        cal_cancel = False
        if self.contacts_filtered[self.FIO_cur_id]['calendar'] == self.deCalendar.date().toString("dd.MM.yyyy"):  #
            cal_cancel = True
        self.changed = False        # обновляем информацию о контакте и карточку
        self.refresh_contact()
        self.refresh_card()
        self.changed = True
# Календарь
        if cal_cancel or self.deCalendar.date() < datetime.today().date():
            return         # Если Дата не изменилась или поставили дату меньшую сегодняшней - ничего не изменяем

        service_cal = discovery.build('calendar', 'v3', http=self.http_cal)                # Считываем весь календарь
        now = datetime(2016, 1, 1, 0, 0).isoformat() + 'Z' # ('Z' indicates UTC time) с начала работы
        calendars_result = service_cal.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=2000,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        calendars = calendars_result.get('items', [])
        self.events = {}
        for calendar in calendars:                                                          # Переводим в удобную форму
            event = {}
            event['id'] = calendar['id']
            event['start'] = {'dateTime' : datetime.combine(datetime.strptime(self.contacts_filtered[self.FIO_cur_id]['calendar'],
                            '%d.%m.%Y').date(),datetime.strptime('16:00','%H:%M').time()).isoformat() + 'Z'}
            event['end'] = {'dateTime' : datetime.combine(datetime.strptime(self.contacts_filtered[self.FIO_cur_id]['calendar'],
                            '%d.%m.%Y').date(),datetime.strptime('16:15','%H:%M').time()).isoformat() + 'Z'}
            event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
            phones = ''
            if len(self.contacts_filtered[self.FIO_cur_id]['phones']) > 0:
                phones = fine_phone(self.contacts_filtered[self.FIO_cur_id]['phones'][0])
                for i, phone in enumerate(self.contacts_filtered[self.FIO_cur_id]['phones']):
                    if i == 0:
                        continue
                    phones += ', ' + fine_phone(phone)
            event['description'] = phones
            event['summary'] = self.contacts_filtered[self.FIO_cur_id]['fio'] + ' - ' +\
                               self.contacts_filtered[self.FIO_cur_id]['stage']
            self.events[calendar['id']] = event

        try:                                                    # есть такой event - update'им
            event = self.events[self.contacts_filtered[self.FIO_cur_id]['resourceName'].split('/')[1]]
            calendar_result = service_cal.events().update(calendarId='primary', eventId=event['id'], body=event) \
                .execute()
        except KeyError:                                # нет такого event'а - создаем
            event = {}
            event['id'] = self.contacts_filtered[self.FIO_cur_id]['resourceName'].split('/')[1]
            event['start'] = {'dateTime' : datetime.combine(datetime.strptime(self.contacts_filtered[self.FIO_cur_id]['calendar'],
                            '%d.%m.%Y').date(),datetime.strptime('16:00','%H:%M').time()).isoformat() + 'Z'}
            event['end'] = {'dateTime' : datetime.combine(datetime.strptime(self.contacts_filtered[self.FIO_cur_id]['calendar'],
                            '%d.%m.%Y').date(),datetime.strptime('16:15','%H:%M').time()).isoformat() + 'Z'}
            event['reminders'] = {'overrides': [{'method': 'popup', 'minutes': 0}], 'useDefault': False}
            phones = ''
            if len(self.contacts_filtered[self.FIO_cur_id]['phones']) > 0:
                phones = fine_phone(self.contacts_filtered[self.FIO_cur_id]['phones'][0])
                for i, phone in enumerate(self.contacts_filtered[self.FIO_cur_id]['phones']):
                    if i == 0:
                        continue
                    phones += ', ' + fine_phone(phone)
            event['description'] = phones
            event['summary'] = self.contacts_filtered[self.FIO_cur_id]['fio'] + ' - ' +\
                               self.contacts_filtered[self.FIO_cur_id]['stage']
            self.events[self.contacts_filtered[self.FIO_cur_id]['resourceName'].split('/')[1]] = event
            calendar_result = service_cal.events().insert(
                calendarId='primary',
                body=event
            ).execute()
        self.changed = False            # обновляем информацию о контакте и карточку
        self.refresh_contact()
        self.refresh_card()
        self.changed = True
        return

    def change_deCalendar(self):                          # выключил из-за глюков deCalendar
#        self.deCalendar.setCalendarPopup(False)
        if not self.changed:
            return
        print(self.deCalendar.date().toString("dd.MM.yyyy"), self.contacts_filtered[self.FIO_cur_id]['calendar'])
        if self.deCalendar.date().toString("dd.MM.yyyy") == self.contacts_filtered[self.FIO_cur_id]['calendar']:
            return
        buf_contact = {}
        buf_contact['userDefined'] = [{},{}]
        buf_contact['userDefined'][0]['value'] = self.cbStage.currentText()
        buf_contact['userDefined'][0]['key'] = 'stage'
        buf_contact['userDefined'][1]['value'] = self.deCalendar.date().toString("dd.MM.yyyy")
        buf_contact['userDefined'][1]['key'] = 'calendar'
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
        self.refresh_contact()
        self.refresh_card()
        self.changed = True
        return

    def click_clbCreateContact(self):
        buf_contact = {}
        buf_contact['biographies'] = [{}]
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
        self.refresh_contacts()
        self.setup_twGroups()
        return

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

    def click_clbExport(self):          # для создания отчета в Бигль
        q=0

    def qwe(self):
        q4 = """
        
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


