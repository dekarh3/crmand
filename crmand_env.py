# -*- coding: utf-8 -*-

B = {
    'select_in' : {'t': 'x', 's': '//A[@class="changeBoxContainer"][text()="Вход"]'},
    'login'     : {'t': 'x', 's': '//INPUT[@id="inputLogin"]'},
    'password'  : {'t': 'x', 's': '//INPUT[@id="inputPassword"]'},
    'a-button'  : {'t': 'x', 's': '//INPUT[@name="submit_login"]'},
    'tiles'     : {'t': 'x', 's': '//DIV[@class="b-tile__item-slot"]/A[@href]'},
    'tiles-name': {'t': 'x', 's': '//DIV[@class="b-tile__details"]/DIV[1]', 'a': 'text'},
    'tiles-href': {'t': 'x', 's': '//DIV[@class="b-tile__item-slot"]/A[@href]', 'a': 'href'},
    'tiles-img' : {'t': 'x', 's': '//IMG[@class="b-tile__image"][@src]', 'a': 'src'},
#    'tiles-offl': {'t': 'x', 's': '//I[@class="icn icn-circleOnline-small icn-small info-online js-info-online"]'
#                                  '/..', 'a': 'href'},
    'tiles-onln': {'t': 'x', 's': '//DIV[@class="b-tile__is-online"]/../DIV/A[@href]', 'a': 'href'},
  'anketa-about': {'t': 'x', 's': '//DIV[@class="b-anketa_inset b-anketa_inset-info"]', 'a': 'outerHTML'},
   'anketa-msg' : {'t': 'x', 's': '//DIV[@class="b-profile-cloud-inner__message alien"]', 'a': 'text'},
 'anketa-favour': {'t': 'x', 's': '//DIV[@class="in clearFix"]', 'a': 'text'},
    'anketa-btn': {'t': 'x', 's': '//A[@class="button button-blue first  _openChateg "]', 'a': 'href'},
'anketa-locator': {'t': 'x', 's': '//SPAN[@class="info info-misc__distance"]', 'a': 'text'},
'anketa-deleted': {'t': 'x', 's': '//H2[text()="Анкета удалена, заблокирована или не существует"]'},

    'back-find' : {'t': 'x', 's': '//A[@class="widget-title js-widget-title"][text()="Результаты поиска"]'},

    'open-fotos': {'t': 'x', 's': '//DIV[@class="anketa-photo"]/IMG'},
    'no-fotos': {'t': 'x', 's': '//DIV[text()="Нет фото :("]'},
    'big-foto'  : {'t': 'x', 's': '//IMG[@class="photo-image"]', 'a': 'src'},
    'all-fotos' : {'t': 'x', 's': '//IMG[@class="album-image"]'},
   'close-fotos': {'t': 'x', 's': '//DIV[@class="close-button close-button-hovered"]|//DIV[@class="close-button"]'},
}



#   'okved-listA': {'t': 'x', 's': '//DIV[@sbisname="okvedSelector"]//TR[@data-id]//DIV[@title]', 'a': 'title'},
#   'okved-listD': {'t': 'x', 's': '//DIV[@sbisname="okvedSelector"]//TR[@data-id]//DIV[@title="'},


LINK = [
    'Нет интереса',
    'Пара',
    'Не начинал',
    'Мой интерес',
    'Переписка',
    'Взаимная симп.',
    'Встреча',
    'Доверие',
]

PEOPLE = [
    'Упырь',
    'Животное',
    'Барыга',
    'Недалекая',
    'Нет КПД',
    'Не верит',
    'Нет места',
    'Неизвестная',
    'Услышала',
    'Проводник',
]

ONLINE = [
    'Сейчас',
    'Сегодня',
    '3 дня',
    'Неделя',
    'пофиг'
]

ISHTML = [
    'Нет',
    'Есть',
    'пофиг'
]

