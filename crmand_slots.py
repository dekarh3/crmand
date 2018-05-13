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


def refresh():
    """Shows basic usage of the People API.

    Creates a People API service object and outputs the name if
    available of 10 connections.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('people', 'v1', http=http,
                              discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')

# Вытаскиваем названия групп
    serviceg = discovery.build('contactGroups', 'v1', http=http,
                               discoveryServiceUrl='https://people.googleapis.com/$discovery/rest')
    resultsg = serviceg.contactGroups().list(pageSize=200).execute()
    groups = {}
    groups_reverse = {}
    contactGroups = resultsg.get('contactGroups', [])
    for i, contactGroup in enumerate(contactGroups):
        groups[contactGroup['resourceName'].split('/')[1]] = contactGroup['name']
        groups_reverse[contactGroup['name']] = contactGroup['resourceName'].split('/')[1]

# Контакты
    results = service.people().connections()\
        .list(
            resourceName='people/me',
            pageSize=200,
            personFields=',addresses,ageRanges,biographies,birthdays,braggingRights,coverPhotos,emailAddresses,events,'
                         'genders,imClients,interests,locales,memberships,metadata,names,nicknames,occupations,'
                         'organizations,phoneNumbers,photos,relations,relationshipInterests,relationshipStatuses,'
                         'residences,skills,taglines,urls,userDefined')\
        .execute()
    connections = results.get('connections', [])
    contacts = []
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

        contacts.append(contact)
    return contacts

# Добавляем массив стадий из контактов
def refresh_stages():
    all_stages = ALL_STAGES_CONST
    for i, contact in enumerate(contacts):
        has = False
        for all_stage in all_stages:
            if all_stage == contact['stage']:
                has = True
        if not has:
            all_stages.append(contact['stage'])
    return all_stages


class MainWindowSlots(Ui_Form):   # Определяем функции, которые будем вызывать в слотах

    def setupUi(self, form):
        Ui_Form.setupUi(self,form)

        self.fillconfig = read_config(filename='mNote.ini', section='fill')
        self.messages = read_config(filename='mNote.ini', section='messages')
        self.webconfig = read_config(filename='mNote.ini', section='web')

        self.drv = webdriver.Firefox()  # Инициализация драйвера
        self.drv.implicitly_wait(5)  # Неявное ожидание - ждать ответа на каждый запрос до 5 сек

        dbconfig = read_config(filename='mNote.ini', section='mysql')
        self.dbconn = MySQLConnection(**dbconfig)  # Открываем БД из конфиг-файла
        self.id_all = []
        self.id_tek = 0
        self.mamba_id = {}
#        self.mamba_id_tek = ''
        self.msg_id = {}
#        self.msg_id_tek = ''
        self.t_people = {}
        self.t_link = {}
        self.html = {}
        self.foto = {}
        self.fotos_count = {}
        self.names = {}
        self.ages = {}
        self.chk_educ = False
        self.chk_child = False
        self.chk_home = False
        self.chk_baryg = False
        self.chk_marr = False
        self.chk_dist = False
        self.history = ''
        self.histories = {}
        self.stLinkFrom = 2
        self.cbLinkFrom.addItems(LINK)
        self.cbLinkFrom.setCurrentIndex(self.stLinkFrom)
        self.stLinkTo = 7
        self.cbLinkTo.addItems(LINK)
        self.cbLinkTo.setCurrentIndex(self.stLinkTo)
        self.stPeopleFrom = 6
        self.cbPeopleFrom.addItems(PEOPLE)
        self.cbPeopleFrom.setCurrentIndex(self.stPeopleFrom)
        self.stPeopleTo = 9
        self.cbPeopleTo.addItems(PEOPLE)
        self.cbPeopleTo.setCurrentIndex(self.stPeopleTo)
        self.stStatus = 0
        self.cbStatus.addItems(ONLINE)
        self.cbStatus.setCurrentIndex(self.stStatus)
        self.cbPeople.addItems(PEOPLE)
        self.cbPeople.setCurrentIndex(0)
        self.cbLink.addItems(LINK)
        self.cbLink.setCurrentIndex(6)
        self.cbHTML.addItems(ISHTML)
        self.cbHTML.setCurrentIndex(2)
        self.setup_tableWidget()
        self.myTimer = QTimer()
        self.myTimer.start(300000)
        self.refresh_started = False

        return

    def click_pbPeopleFilter(self):  # Применить фильтр
        a = self.leFilter.text()
        if a[:4] == 'http':
            self.leFilter.setText(self.convert_mamba_id(a))
        self.setup_tableWidget()
        return

    def click_cbHTML(self):
        self.setup_tableWidget()
        return

    def setup_tableWidget(self):
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)        # Кол-во строк из таблицы
        self.dbconn.connect()
        read_cursor = self.dbconn.cursor()
        sql_append = ''
        if self.stStatus == 0:
            sql_append = 'AND status > 0 '
        elif self.stStatus == 1:
            sql_append = 'AND DATE(access_date) >= DATE_SUB(NOW(), INTERVAL 24 HOUR) '
        elif self.stStatus == 2:
            sql_append = 'AND DATE(access_date) >= DATE_SUB(NOW(), INTERVAL 3 DAY) '
        elif self.stStatus == 3:
            sql_append = 'AND DATE(access_date) >= DATE_SUB(NOW(), INTERVAL 7 DAY) '
        if self.cbHTML.currentIndex() == 1:
            sql_append += 'AND html IS NOT NULL ORDER BY age DESC;'# сообщения не показывает, с...
        elif self.cbHTML.currentIndex() == 0:
            sql_append += 'AND html IS NULL ORDER BY age DESC;'
        else:
            sql_append += 'ORDER BY age DESC;'
        if len(s(self.leFilter.text())) > 4:
            sql = 'SELECT DATE_FORMAT(access_date,"%d.%m %H:%i"), her_name, age, msg, fotos_count, id, msg_id, mamba_id,' \
                  ' t_people, t_link, html, foto, history FROM peoples WHERE (age > 33 OR age = 0) AND ' \
                  't_link >= %s AND t_link <= %s AND t_people >= %s  AND t_people <= %s AND mamba_id = %s ' + sql_append
            read_cursor.execute(sql, (self.stLinkFrom, self.stLinkTo, self.stPeopleFrom, self.stPeopleTo,
                                      s(self.leFilter.text())))
        else:
            sql = 'SELECT DATE_FORMAT(access_date,"%d.%m %H:%i"), her_name, age, msg, fotos_count, id, msg_id, mamba_id, ' \
                  't_people, t_link, html, foto, history FROM peoples WHERE (age > 33 OR age = 0) AND ' \
                  't_link >= %s AND t_link <= %s AND t_people >= %s AND t_people <= %s ' + sql_append
            read_cursor.execute(sql, (self.stLinkFrom, self.stLinkTo, self.stPeopleFrom, self.stPeopleTo))

        rows = read_cursor.fetchall()
        self.tableWidget.setColumnCount(3)             # Устанавливаем кол-во колонок
        self.tableWidget.setRowCount(len(rows))        # Кол-во строк из таблицы
        self.id_all = []
        self.histories = {}
        self.foto = {}
        self.html = {}
        self.t_link = {}
        self.t_people = {}
        self.mamba_id = {}
        self.msg_id = {}
        i = 0
        for row in rows:
            html_tek = row[len(row)-3]
            self.scan(html_tek)
            show = True
            if self.chb_mar.isChecked():
                if not self.chk_marr:
                    show = False
            if self.chb_baryg.isChecked():
                if not self.chk_baryg:
                    show = False
            if self.chb_child.isChecked():
                if not self.chk_child:
                    show = False
            if self.chb_dist.isChecked():
                if not self.chk_dist:
                    show = False
            if self.chb_edu.isChecked():
                if not self.chk_educ:
                    show = False
            if self.chb_home.isChecked():
                if not self.chk_home:
                    show = False
            if not show:
                continue
            self.id_all.append(int(row[len(row)-8]))
            self.id_tek = int(row[len(row)-8])
            for j, cell in enumerate(row):
                if j == len(row) - 8:
                    q = 0
                elif j == len(row) - 1:
                    self.histories[self.id_tek] = cell
                elif j == len(row) - 2:
                    self.foto[self.id_tek] = cell
                elif j == len(row) - 3:
                    self.html[self.id_tek] = cell
                    self.scan(cell)
                elif j == len(row) - 4:
                    self.t_link[self.id_tek] = cell
                elif j == len(row) - 5:
                    self.t_people[self.id_tek] = cell
                elif j == len(row) - 6:
                    self.mamba_id[self.id_tek] = cell
                elif j == len(row) - 7:
                    self.msg_id[self.id_tek] = cell
                elif j == len(row) - 9:                        # Количество загруженных фоток
                    self.fotos_count[self.id_tek] = cell
                elif j == len(row) - 10:
                    q = 0                                     # сообщения не показывает, с...
                elif j == len(row) - 11:
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(cell)))
                    self.ages[self.id_tek] = str(cell)
                elif j == len(row) - 12:
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(cell)))
                    self.names[self.id_tek] = str(cell)
                else:
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(cell)))
            i += 1
        self.tableWidget.setRowCount(len(self.id_all))        # Обрезаем кол-во строк с учетом фильтров

        if len(self.id_all) > 0:
            self.id_tek = self.id_all[0]
#        self.mamba_id_tek = self.mamba_id[self.id_tek]
#        self.msg_id_tek = self.msg_id[self.id_tek]
        # Устанавливаем заголовки таблицы
        self.tableWidget.setHorizontalHeaderLabels(["Активность", "Имя", "Возраст"])

        # Устанавливаем выравнивание на заголовки
        self.tableWidget.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        self.tableWidget.horizontalHeaderItem(1).setTextAlignment(Qt.AlignCenter)
        self.tableWidget.horizontalHeaderItem(2).setTextAlignment(Qt.AlignCenter)

        # делаем ресайз колонок по содержимому
        self.tableWidget.resizeColumnsToContents()
        self.click_tableWidget()
        return

    def click_tableWidget(self, index=None):
        if index == None:
            index = self.tableWidget.model().index(0, 0)
        else:
            self.updateHistory()
        if index.row() < 0:
            return None
        self.id_tek = self.id_all[index.row()]
        self.textEdit.setText(self.histories[self.id_tek])
        self.cbLink.setCurrentIndex(self.t_link[self.id_tek])
        self.cbPeople.setCurrentIndex(self.t_people[self.id_tek])
        pixmap = QPixmap()
        pixmap.loadFromData(self.foto[self.id_tek],'JPG')
        self.label_3.setPixmap(pixmap)
        self.anketa_html.setHtml(self.html[self.id_tek])
#        try:
#            self.chb_baryg.setChecked(self.chk_baryg[self.id_tek])
#            self.chb_child.setChecked(self.chk_child[self.id_tek])
#            self.chb_dist.setChecked(self.chk_dist[self.id_tek])
#            self.chb_edu.setChecked(self.chk_educ[self.id_tek])
#            self.chb_home.setChecked(self.chk_home[self.id_tek])
#            self.chb_mar.setChecked(self.chk_marr[self.id_tek])
#        except:
#            a = crop_tags(self.html[self.id_tek])

        self.setup_tableFotos()
        if self.msg_id[self.id_tek] == None:
            self.pbToMessage.setEnabled(False)
        else:
            self.pbToMessage.setEnabled(True)
        return None

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

    def setup_tableFotos(self):
        mamba_id = self.mamba_id[self.id_tek]
        name = self.names[self.id_tek]
        count = self.fotos_count[self.id_tek]
        self.tableFotos.setColumnCount(0)
        self.tableFotos.setRowCount(1)
        self.tableFotos.setColumnCount(count)
        for i in range(1, count + 1):
            self.tableFotos.setItem(0, i-1, QTableWidgetItem(str(i)))
        self.tableFotos.resizeColumnsToContents()

    def click_label_3(self, index=None):
        if index == None or index.row() < 0 or index.row() > 0 or index.column() < 0:
            index = self.tableFotos.model().index(0, 0)
        pixmap = QPixmap('photos/'+ self.mamba_id[self.id_tek] + '_' + s(self.names[self.id_tek]).replace(' ','') +
                         s(self.ages[self.id_tek]) + '_' + '{0:02d}'.format(index.column()+1) + '.jpg')
        self.label_3.setPixmap(pixmap)

    def click_tableFotos(self, index=None):
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
        self.setup_tableWidget()
        return

    def click_cbLinkTo(self):
        self.stLinkTo = self.cbLinkTo.currentIndex()
        self.setup_tableWidget()
        return

    def click_cbStatus(self):
        self.stStatus = self.cbStatus.currentIndex()
        self.setup_tableWidget()
        return

    def click_cbPeopleFrom(self):
        self.stPeopleFrom = self.cbPeopleFrom.currentIndex()
        self.setup_tableWidget()
        return

    def click_cbPeopleTo(self):
        self.stPeopleTo = self.cbPeopleTo.currentIndex()
        self.setup_tableWidget()

    def updateHistory(self):
        current = self.textEdit.toPlainText()
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


    def deep_old_scan(self):        # старое глубокое сканирование
        self.drv.get(**self.fillconfig)  # Открытие страницы где поиск
        page = 1
        standart = len(p(d=self.drv, f='ps', **B['tiles']))
        while len(p(d=self.drv, f='ps', **B['tiles'])) == standart:
            if page > 1:
                wj(self.drv)
                page_link = self.drv.find_element_by_xpath('//DIV[@class="pager wrap"]//LI[text()="' + str(page) + '"]')
                wj(self.drv)
                page_link.click()
                wj(self.drv)
            tiles = []
            tiles = p(d=self.drv, f='ps', **B['tiles'])
            hrefs = []
            hrefs = p(d=self.drv, f='ps', **B['tiles-href'])
            for i, mamba_href in enumerate(hrefs):
                mamba_id = self.convert_mamba_id(mamba_href)
                row_ch = []
                self.dbconn.connect()
                read_cursor = self.dbconn.cursor()
                read_cursor.execute('SELECT id, html FROM peoples WHERE mamba_id = %s', (mamba_id,))
                row_ch = read_cursor.fetchall()
                refresh_html = False  # анкета сохранена в базе?
                if len(row_ch) > 0:
                    if row_ch[0][1] == None:
                        refresh_html = True
                    elif len(row_ch[0][1]) < 10:
                        refresh_html = True
                else:
                    refresh_html = True
                if len(row_ch) < 1:  # такой записи нет в базе
                    continue
                elif refresh_html:  # запись есть, а анкеты нет
                    tiles[i].click()
                    wj(self.drv)
                    html_msg = p(d=self.drv, f='p', **B['anketa-msg'])
                    html_favour = p(d=self.drv, f='p', **B['anketa-favour'])
                    html_locator = p(d=self.drv, f='p', **B['anketa-locator'])
                    html_abouts = p(d=self.drv, f='ps', **B['anketa-about'])
                    html = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/' \
                           'strict.dtd"><html><head></head><body><p>' + html_msg + '</p><h3>' + html_locator + '</h3><p>'
                    html += html_favour.replace('\n',' | ') + '</p>'
                    if len(html_abouts) > 0:
                        for html_into in html_abouts:
                            html += html_into
                    html = html.replace('\n',' ').replace('\t',' ').replace('  ',' ').replace('  ',' ')
                    html = html.replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
                    html = html.replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
                    html += '</body></html>'
                    read_cursor = self.dbconn.cursor()
                    read_cursor.execute('SELECT msg_id FROM peoples WHERE mamba_id = %s', (mamba_id,))
                    self.html[row_ch[0][0]] = html
                    row_msg = read_cursor.fetchall()
                    if len(row_msg) > 0:
                        if row_msg[0][0] == None:
                            sql = 'UPDATE peoples SET msg_id = %s WHERE mamba_id = %s'
                            write_cursor = self.dbconn.cursor()
                            aa = p(d=self.drv, f='p', **B['anketa-btn'])
                            ab = aa.split('uid=')[1]
                            write_cursor.execute(sql, (ab, mamba_id))
                            self.dbconn.commit()
                    wj(self.drv)
                    wr()
                    back = p(d=self.drv, f='c', **B['back-find'])
                    wj(self.drv)
                    sql = 'UPDATE peoples SET html = %s WHERE mamba_id = %s'
                    write_cursor = self.dbconn.cursor()
                    write_cursor.execute(sql, (html, mamba_id))
                    self.dbconn.commit()
                    back.click()
                    wj(self.drv)
                    break
                else:                                               # есть и запись и анкета
                    continue
            page += 1
            q = 0
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


    def click_pbRefresh(self):                     # Включение автообновления
        if self.refresh_started == False:
            if len(self.drv.window_handles) < 2:
                self.drv.execute_script('''window.open("about:blank", "_blank");''')
                self.drv.switch_to.window(self.drv.window_handles[1])
                self.drv.get(**self.messages)  # Открытие страницы где сообщения
                self.drv.switch_to.window(self.drv.window_handles[0])
            self.refresh_started = True
            self.pbRefresh.setText('ОБНОВЛЯЮ')
            self.myTimer.stop()
            self.myTimer.start(3)
        else:
            self.refresh_started = False
            self.pbRefresh.setText('Обновить')
        wj(self.drv)

    def refreshing(self):                           # Обновление статусов
        if not self.refresh_started:
            return
        self.myTimer.stop()
        self.drv.switch_to.window(self.drv.window_handles[0])
        sql = 'UPDATE peoples SET status = 0 WHERE status != 0'     # Сначала всех в оффлайн
        self.dbconn.connect()
        write_cursor = self.dbconn.cursor()
        write_cursor.execute(sql)
        self.dbconn.commit()
        self.drv.get(**self.fillconfig)  # Открытие страницы где поиск
        page = 0
#        standart = len(p(d=self.drv, f='ps', **B['tiles']))
        i_tek = 0
        outs = []
        updates = []
        statuses = []
        has_new = True
        loaded_mamba_ids = []
        while has_new:
#            page_link = self.drv.find_element_by_xpath('//DIV[@class="pager wrap"]//LI[text()="' + str(page) + '"]')
#            page_link.click()
            self.drv.execute_script("window.scrollTo(0, " + str(page*3000) + ");")
            tiles = []
            tiles = p(d=self.drv, f='ps', **B['tiles'])
            names = []
            names = p(d=self.drv, f='ps', **B['tiles-name'])
            hrefs = []
            hrefs = p(d=self.drv, f='ps', **B['tiles-href'])
            fotos_hrefs = []
            fotos_hrefs = p(d=self.drv, f='ps', **B['tiles-img'])
            hrefs_onln = []
            hrefs_onln = p(d=self.drv, f='ps', **B['tiles-onln'])
            has_new = False
            reload = False
            q = len(tiles)
            if len(names) != q or len(hrefs) != q or len(fotos_hrefs) != q:
                print('Обновление: Количество в массивах не совпадает')
                break
#            tiles[0].location_once_scrolled_into_view
            for i, mamba_href in enumerate(hrefs):
                nextload = False
                mamba_id = self.convert_mamba_id(mamba_href)
                for loaded_mamba_id in loaded_mamba_ids:
                    if loaded_mamba_id == mamba_id:
                        nextload = True
                if nextload:
                    continue
                has_new = True
                row_ch = []
                read_cursor = self.dbconn.cursor()
                read_cursor.execute('SELECT id, html FROM peoples WHERE mamba_id = %s',(mamba_id,))
                row_ch = read_cursor.fetchall()
                if len(row_ch) < 1: # карточки (записи в БД) нет
                    out = tuple()
                    html = None
                    age = 0
                    if len(names[i].split(',')) > 1:
                        age = l(names[i].split(',')[1].strip())
                    out += (mamba_id, ) + (self.convert_msg_id(mamba_id), ) + (names[i].split(',')[0].strip(), ) + (age,)
                    status = 0
                    try:
                        foto = urllib.request.urlopen(fotos_hrefs[i], timeout=10).read()
                    except:
                        foto = BREAKED_MAMBA
                    for status_href in hrefs_onln:
                        if self.convert_mamba_id(status_href) == mamba_id:
                            status = 1
                            statuses.append((status, foto, mamba_id))
                    try:
                        tiles[i].click()
                    except:
                        q = 0
                    else:
                        try:
                            wj(self.drv)
                            html = self.get_html()
                            back = p(d=self.drv, f='c', **B['back-find'])
                            wj(self.drv)
                            back.click()
                            wj(self.drv)
                        except:
                            q = 0
                    out += (status, ) + (foto, ) + (html, )
                    outs.append(out)
#                    i_tek += 1
                    reload = True
                elif not row_ch[0][1]:  # html нет а карточка (запись в БД) есть
                    update = tuple()
                    html = None
                    try:
                        foto = urllib.request.urlopen(fotos_hrefs[i], timeout=10).read()
                    except:
                        foto = BREAKED_MAMBA
                    status = 0
                    for status_href in hrefs_onln:
                        if self.convert_mamba_id(status_href) == mamba_id:
                            status = 1
                            statuses.append((status, foto, mamba_id))
                    try:
                        tiles[i].click()
                    except:
                        q = 0
                    else:
                        try:
                            wj(self.drv)
                            html = self.get_html()
                            try:
                                foto = urllib.request.urlopen(fotos_hrefs[i], timeout=10).read()
                            except:
                                foto = BREAKED_MAMBA
                            back = p(d=self.drv, f='c', **B['back-find'])
                            wj(self.drv)
                            back.click()
                            wj(self.drv)
                        except:
                            q = 0
                    update += (html,) + (status,) + (foto, ) + (row_ch[0][0],)
#                    update += (status,) + (row_ch[0][0],)
                    updates.append(update)
                    reload = True
#                    i_tek += 1
                else:                   # есть и html и карточка
                    status = 0
                    try:

                        foto = urllib.request.urlopen(fotos_hrefs[i], timeout=10).read()
                    except:
                        foto = BREAKED_MAMBA
                    for status_href in hrefs_onln:
                        if self.convert_mamba_id(status_href) == mamba_id:
                            status = 1
                            statuses.append((status, foto, mamba_id))
                loaded_mamba_ids.append(mamba_id)
                if reload:
                    break
            if len(outs) > 0:
                sql = 'INSERT INTO peoples(mamba_id, msg_id, her_name, age, status, foto, html) ' \
                      'VALUES (%s,%s,%s,%s,%s,%s,%s)'
                write_cursor = self.dbconn.cursor()
                write_cursor.executemany(sql, outs)
                self.dbconn.commit()
            if len(updates) > 0:
                sql = 'UPDATE peoples set html = %s, status = %s, foto = %s WHERE id = %s'
                write_cursor = self.dbconn.cursor()
                write_cursor.executemany(sql, updates)
                self.dbconn.commit()
            if len(statuses) > 0:
                sql = 'UPDATE peoples SET status = %s, foto = %s, access_date = NOW() WHERE mamba_id = %s'
                write_cursor = self.dbconn.cursor()
                write_cursor.executemany(sql, statuses)
                self.dbconn.commit()
            else:                              # Если нет ни одного в онлайне - выходим
                self.setup_tableWidget()
                self.myTimer.start(300000)
                return
            outs = []
            updates = []
            statuses = []
            if (not reload) or (i == len(hrefs)-1):
#                self.drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.drv.execute_script("window.scrollTo(0, 3000);")
                page += 1

#            if i_tek >= len(hrefs) - 1:
#                page += 1
#                i_tek = 0
            q=0
        q = 0
        self.setup_tableWidget()
        self.myTimer.start(300000)
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

    def click_pbGetHTML(self):
        if self.refresh_started:
            self.drv.switch_to.window(self.drv.window_handles[1])
        mamba_id_there = self.convert_mamba_id(self.drv.current_url)
        if len(mamba_id_there.split('#')) > 1:
            mamba_id_there = mamba_id_there.split('#')[0]
        if len(mamba_id_there.split('&')) > 1:
            mamba_id_there = mamba_id_there.split('&')[0]
        if len(mamba_id_there.split('?')) > 1:
            mamba_id_there = mamba_id_there.split('?')[0]
        self.dbconn.connect()
        read_cursor = self.dbconn.cursor()
        read_cursor.execute('SELECT id, her_name, age FROM peoples WHERE mamba_id = %s', (mamba_id_there,))
        row_row = read_cursor.fetchall()
        if len(row_row) > 0:
            id_there = row_row[0][0]
            anketa_deleted = p(d=self.drv, f='p', **B['anketa-deleted'])
            if anketa_deleted != None:
                sql = 'UPDATE peoples SET t_link = 0 WHERE mamba_id = %s'
                write_cursor = self.dbconn.cursor()
                write_cursor.execute(sql, (mamba_id_there,))
                self.dbconn.commit()
                return
            her_name = row_row[0][1]
            age = row_row[0][2]
            wj(self.drv)
            no_fotos = p(d=self.drv, f='p', **B['no-fotos'])
            wj(self.drv)
            if no_fotos == None:
                open_fotos = p(d=self.drv, f='c', **B['open-fotos'])
                wj(self.drv)
                open_fotos.click()
                time.sleep(1)
                all_fotos = p(d=self.drv, f='ps', **B['all-fotos'])
                wj(self.drv)
                if all_fotos != None:                           # Грузим все фотки
                    if len(all_fotos) > self.fotos_count[id_there] :
                        for i, all_foto in enumerate(all_fotos):
                            if all_foto.is_displayed():
                                all_foto.click()
                            wj(self.drv)
                            big_foto = p(d=self.drv, f='p', **B['big-foto'])
                            try:
                                foto = urllib.request.urlopen(big_foto, timeout=10).read()
                            except:
                                foto = BREAKED_MAMBA
                            f = open('./photos/'+ mamba_id_there + '_' + s(her_name).replace(' ','').replace('\n','')
                                     + s(age) + '_' + '{0:02d}'.format(i+1) + '.jpg', 'wb')
                            f.write(foto)
                            f.close()
                        self.fotos_count[id_there] = len(all_fotos)
                else:
                    if 1 > self.fotos_count[id_there]:
                        big_foto = p(d=self.drv, f='p', **B['big-foto'])
                        try:
                            foto = urllib.request.urlopen(big_foto, timeout=10).read()
                        except:
                            foto = BREAKED_MAMBA
                        f = open('./fotos/' + mamba_id_there + '_' + s(her_name).replace(' ','') + s(age) + '_01' +
                                 '.jpg', 'wb')
                        f.write(foto)
                        f.close()
                    self.fotos_count[id_there] = 1
                close_fotos = p(d=self.drv, f='ps', **B['close-fotos'])
                wj(self.drv)
                close_fotos[0].click()
            wj(self.drv)
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
            self.html[id_there] = html
            self.anketa_html.setHtml(html)
            sql = 'UPDATE peoples SET html = %s, fotos_count = %s WHERE mamba_id = %s'
            write_cursor = self.dbconn.cursor()
            write_cursor.execute(sql, (html, self.fotos_count[id_there], mamba_id_there))
            self.dbconn.commit()
            read_cursor = self.dbconn.cursor()
            read_cursor.execute('SELECT msg_id FROM peoples WHERE mamba_id = %s', (mamba_id_there,))
            row_msg = read_cursor.fetchall()
            if len(row_msg) > 0:
                if row_msg[0][0] == None:
                    sql = 'UPDATE peoples SET msg_id = %s WHERE mamba_id = %s'
                    write_cursor = self.dbconn.cursor()
                    aa = p(d=self.drv, f='p', **B['anketa-btn'])
                    ab = aa.split('uid=')[1]
                    write_cursor.execute(sql, (ab, mamba_id_there))
                    self.dbconn.commit()
                    self.msg_id[mamba_id_there] = ab
            wj(self.drv)
        return


