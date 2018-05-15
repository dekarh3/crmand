from __future__ import print_function

import httplib2
import os

from apiclient import discovery                             # Механизм запроса данных
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime
import time

from PyQt5.QtCore import QDate, QDateTime, QSize, Qt, QByteArray, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QTableWidget, QTableWidgetItem


from crmand_win import Ui_Form

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from lib import unique

ALL_STAGES_CONST = ['проводник', 'своим скажет', 'доверие', 'услышал', 'нужна встреча', 'перезвонить', 'нужен e-mail',
                    'секретарь передаст', 'отправил сообщен', 'нет на месте', 'недозвон', 'недоступен', '---',
                    'нет контактов', 'не занимаюсь', 'не понимает', 'не верит', 'рыпу']

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/people.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/contacts.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'People API Python Quickstart'


def get_credentials():
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
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
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
        self.groups = []
        self.group_cur = ''
        self.group_cur_id = 0
        self.FIO_cur = ''
        self.FIO_cur_id = 0
        self.refresh_contacts()
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
        self.setup_twGroups()

        return

    def refresh_contacts(self):
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('people', 'v1', http=http,
                                  discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

        # Вытаскиваем названия групп
        serviceg = discovery.build('contactGroups', 'v1', http=http,
                                   discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
        resultsg = serviceg.contactGroups().list(pageSize=200).execute()
        groups = {}
        contactGroups = resultsg.get('contactGroups', [])
        for i, contactGroup in enumerate(contactGroups):
            groups[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']

        # Контакты
        results = service.people().connections() \
            .list(
            resourceName='people/me',
            pageSize=200,
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
            onames = connection.get('names', [])
            if len(onames) > 0:
                name = onames[0].get('displayName')
            contact['fio'] = name
            biographie = ''
            obiographies = connection.get('biographies', [])
            if len(obiographies) > 0:
                biographie = obiographies[0].get('value')
            contact['note'] = biographie
            phones = []
            ophones = connection.get('phoneNumbers', [])
            if len(ophones) > 0:
                for ophone in ophones:
                    phones.append(ophone.get('canonicalForm'))
            contact['phones'] = phones
            memberships = []
            omemberships = connection.get('memberships', [])
            if len(omemberships) > 0:
                for omembership in omemberships:
                    memberships.append(groups[omembership['contactGroupMembership']['contactGroupId']])
            contact['groups'] = memberships
            stage = '---'
            ostages = connection.get('userDefined', [])
            if len(ostages) > 0:
                for ostage in ostages:
                    if ostage['key'].lower() == 'stage':
                        stage = ostage['value'].lower()
            contact['stage'] = stage
            self.contacts.append(contact)
        return

    # Добавляем массив стадий из контактов
    def refresh_stages(self):
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
        self.setup_twGroups()
        return

    def setup_twGroups(self):
        self.twGroups.setColumnCount(0)
        self.twGroups.setRowCount(0)        # Кол-во строк из таблицы
        groups = []
        for contact in self.contacts:      # !!!!!!!!!!!!!!!! Добавить фильтры !!!!!!!!!!!!!!!
            for group in contact['groups']:
                groups.append(group)
        self.groups = sorted(unique(groups))

        self.twGroups.setColumnCount(1)             # Устанавливаем кол-во колонок
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
        if index.row() < 0:
            return None
        self.group_cur = self.groups[index.row()]
        self.group_cur_id = index.row()
        self.setup_twFIO()
        return

    def setup_twFIO(self):
        self.contacts_filtered = []
        for contact in self.contacts:      # !!!!!!!!!!!!!!!! Добавить фильтры !!!!!!!!!!!!!!!
            for group in contact['groups']:
                if group == self.group_cur:
                    self.contacts_filtered.append(contact)
                    break
        self.twFIO.setColumnCount(1)                              # Устанавливаем кол-во колонок
        self.twFIO.setRowCount(len(self.contacts_filtered))        # Кол-во строк из таблицы
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
        if index.row() < 0:
            return None
        self.teNote.setText(self.contacts_filtered[index.row()]['note'])
        self.cbStage.setCurrentIndex(self.all_stages_reverce[self.contacts_filtered[index.row()]['stage']])
        self.FIO_cur = self.contacts_filtered[index.row()]['fio']
        self.FIO_cur_id = index.row()
        self.setup_twCalls()
        return

    def setup_twCalls(self):
        q1 = """
        mamba_id = self.mamba_id[self.id_tek]
        name = self.names[self.id_tek]
        count = self.fotos_count[self.id_tek]
        self.tableFotos.setColumnCount(0)
        self.tableFotos.setRowCount(1)
        self.tableFotos.setColumnCount(count)
        for i in range(1, count + 1):
            self.tableFotos.setItem(0, i-1, QtwGroupsItem(str(i)))
        self.tableFotos.resizeColumnsToContents()
        """

    def click_twCalls(self, index=None):
        q2 = """ 
        if index == None or index.row() < 0 or index.row() > 0 or index.column() < 0:
            index = self.tableFotos.model().index(0, 0)
        proc = Popen('nomacs ' + 'photos/'+ self.mamba_id[self.id_tek] + '_' + s(self.names[self.id_tek]).replace(' ','') +
                     s(self.ages[self.id_tek]) + '_' + '{0:02d}'.format(index.column()+1) + '.jpg', shell=True,
                     stdout=PIPE, stderr=PIPE)
        proc.wait()  # дождаться выполнения
        res = proc.communicate()  # получить tuple('stdout', 'stderr')
        if proc.returncode:
            print(res[1])
            print('result:', res[0])
        """
    def click_cbStage(self):
        q=0

    def click_pbRedo(self):
        q=0
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


