import requests
import json
import datetime
import sys
from dateutil.relativedelta import *
from time import sleep
from lxml import html

class Downloader:
    session = requests.Session()
    hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    def get_page(self, url, cookies={}):
        sleep(2)
        r = self.session.get(url, cookies=cookies, headers=self.hdr, timeout=60)
        r.encoding = "UTF-8"
        return r.text
    
    def post_page(self, url, cookies={}, data={}):
        sleep(2)
        r = self.session.post(url, cookies=cookies, data=data, headers=self.hdr, timeout=60)
        r.encoding = "UTF-8"
        return r.text

class Parser:
    api_url = '''http://cobranza.poderjudicial.cl/SITCOPORWEB/AtPublicoDAction.do?TIP_Consulta=3&TIP_Lengueta=tdDos&SeleccionL=0&RUC_Tribunal=3&FEC_Desde={date_from}&FEC_Hasta={date_to}&COD_Tribunal={type_id}&irAccionAtPublico=Consulta'''
    downloader = Downloader()

    def parse(self, months_count=12):
        initial_page_content = self.downloader.get_page('http://cobranza.poderjudicial.cl/SITCOPORWEB/')
        initial_page_content = self.downloader.get_page('http://cobranza.poderjudicial.cl/SITCOPORWEB/AtPublicoViewAccion.do?tipoMenuATP=1')
        tree = html.fromstring(initial_page_content)
        type_ids = tree.xpath('//*[@name="COD_Tribunal"]/option[not(@disabled)]/@value')
        j = 0
        count = len(type_ids)
        for type_id in type_ids:
            j+=1
            print('Dowloading: [{0}/{1}]\r'.format(j, count))
            sys.stdout.write("\033[F")
            type_id = str(type_id)
            date_from = datetime.datetime.now()
            date_to = datetime.datetime.now() + relativedelta(months=+1)
            items = []
            for i in range(0, months_count):
                date_to = date_to - relativedelta(months=+1)
                date_from = date_from - relativedelta(months=+1)
                items.extend(self.parse_by_type_id(type_id, date_from, date_to))
            self.save_items(type_id, items)
    
    def parse_by_type_id(self, type_id, date_from, date_to):
        items = []
        date_from = date_from.strftime('%d/%m/%Y').replace('/', '%2F')
        date_to = date_to.strftime('%d/%m/%Y').replace('/', '%2F')
        post_url = self.api_url.format(date_from=date_from, date_to=date_to, type_id=type_id)
        page_content = self.downloader.post_page(post_url)
        page_tree = html.fromstring(page_content)
        for table_row in page_tree.xpath('//*[@id="divRecursos"]//tr[position()>1]'):
            tree = html.fromstring(html.tostring(table_row))
            items.append({
                'url': 'http://cobranza.poderjudicial.cl/' + next(iter(tree.xpath('//td[1]/a/@href')), ''),
                'rit': next(iter(tree.xpath('//td[1]/a/text()')), '').strip(),
                'ruc': next(iter(tree.xpath('//td[2]/text()')), '').strip(),
                'fecha': next(iter(tree.xpath('//td[3]/text()')), '').strip(),
                'caratulado': next(iter(tree.xpath('//td[4]/text()')), '').strip(),
                'tribunal': next(iter(tree.xpath('//td[5]/text()')), '').strip()
            })
        return items

    def save_items(self, type_id, items):
        if len(items) > 0:
            text_items = json.dumps(items)
            with open('result/{type_id}.json'.format(type_id=type_id), 'w') as the_file:
                the_file.write(text_items)

p = Parser()
p.parse(input('Enter count of months to download: '))