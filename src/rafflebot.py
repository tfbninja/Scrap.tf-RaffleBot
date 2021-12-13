import chromiumdl
import pickle
from selenium import webdriver
import sys
import os
import requests
from bs4 import BeautifulSoup
import time
import random


class RaffleBot:
    allraffles = []
    unenteredraffles = []

    def __init__(self, path):
        self.path = path
        self.cookiefile = os.path.join(path, 'cookie.pkl')
        iscookie = self.checkCookie()
        if iscookie:
            self.cookie = pickle.load(open(self.cookiefile, 'rb'))  # if we have cookie use it
        else:
            self.generateCookie()  # if not ask user to login using selenium to generate one
        self.session = requests.Session()
        self.csrf, self.name = self.getCsrfAndName()  # gets csrf token
        print('Hello {}'.format(self.name), end='\n\n')
        self.getRaffles()
        print('Total raffles: {}'.format(len(self.allraffles)))
        print('Unentered raffles: {}'.format(len(self.unenteredraffles)), end='\n\n')
        self.enterAllRaffles()
        print('Finished all raffles')

    def checkCookie(self):
        if os.path.isfile(self.cookiefile):  # check cookiefile existence
            while True:  # loops until valid user input
                print('Cookie detected, use it? (Y/N)')
                choice = input().lower()
                if choice == 'n' or choice == 'y':
                    break
                else:
                    print('Invalid input.\n\'Y\' for yes\n\'N\' for no')
            if choice == 'y':  # if using existing cookie file return 1
                return 1
            else:  # if not using existing cookie file remove it
                os.remove(self.cookiefile)
        return 0  # return 0 to signal we don't have a cookie file

    def generateCookie(self):  # uses selenium to get login information
        webdriver_path, chromium_path = chromiumdl.chromiumdl(path)  # download chromium and get binary locations
        options = webdriver.ChromeOptions()
        options.binary_location = chromium_path
        driver = webdriver.Chrome(webdriver_path, options=options)
        driver.get('https://scrap.tf/')
        print('Write \'ready\' after logging into scrap.tf')
        while True:
            userinput = input().lower()
            if userinput == 'ready':
                break
        driver.get('https://scrap.tf/')
        self.cookie = driver.get_cookie('scr_session')
        pickle.dump(self.cookie, open(self.cookiefile, 'wb'))
        driver.quit()

    def getCsrfAndName(self):
        self.session.cookies.set('scr_session', self.cookie['value'], domain='.scrap.tf')
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Connection": "close",
            "Referer": "https://scrap.tf/", "Upgrade-Insecure-Requests": "1"}
        mainpage = self.session.get('https://scrap.tf')
        soup = BeautifulSoup(mainpage.content, 'html.parser')
        csrf = soup.find('input', attrs={'type': 'hidden', 'name': 'csrf'})['value']
        name = soup.find('li', attrs={'class': 'dropdown nav-userinfo'})['title']
        return csrf, name

    def getRaffles(self):
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://scrap.tf", "Connection": "close", "Referer": "https://scrap.tf/raffles"}

        data = {"start": "", "sort": "0", "puzzle": "0", "csrf": self.csrf}
        url = "https://scrap.tf:443/ajax/raffles/Paginate"
        lid=[];
        while True:
            response = self.session.post(url, data=data).json()
            print(response['lastid'])
            if response['lastid'] in lid:
                break
            self.parseRaffles(response['html'])
            data['start'] = response['lastid']
            lid.append(response['lastid'])

    def parseRaffles(self, htmldata):
        soup = BeautifulSoup(htmldata, 'html.parser')
        raffles = soup.find_all('div', attrs={'class': 'panel-raffle'})
        for raffle in raffles:
            raffledata = {}
            raffledata['title'] = raffle.find('div', attrs={'class': 'raffle-name'}).a.text
            raffledata['relative_url'] = raffle.find('div', attrs={'class': 'raffle-name'}).a['href']
            raffledata['id'] = raffledata['relative_url'].split('/')[-1]
            raffledata['entered'] = True if raffle['class'] == ['panel-raffle', 'raffle-entered'] else False
            raffledata['absurl'] = 'https://scrap.tf' + raffledata['relative_url']
            if raffledata['absurl'] in [x['absurl'] for x in self.allraffles]:
                continue
            self.allraffles.append(raffledata)
            if raffledata['entered'] == False:
                self.unenteredraffles.append(raffledata)

    def enterOneRaffle(self, raffle):
        response = self.session.get(raffle['absurl'])
        soup = BeautifulSoup(response.content, 'html.parser')
        onclick_data = \
            soup.find('button', attrs={'class': 'btn btn-embossed btn-info btn-lg', 'rel': 'tooltip-free',
                                       'data-placement': 'top'})['onclick']
        hash = onclick_data.split('(')[1].split(',')[1].strip('\' ')  # there are multiple ways to get the hash.
        url = "https://scrap.tf:443/ajax/viewraffle/EnterRaffle"
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
            "Accept": "application/json, text/javascript, */*; q=0.01", "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate", "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest", "Origin": "https://scrap.tf", "Connection": "close",
            "Referer": raffle['absurl']}
        data = {"raffle": raffle['id'], "captcha": '',
                "hash": hash, "flag": "false",
                "csrf": self.csrf}
        resp = self.session.post(url, data=data, verify=False)
        return resp.json()

    def enterAllRaffles(self, verbose=True):
        rafflecount = len(self.unenteredraffles)
        currentraffle = 1
        for raffle in self.unenteredraffles:
            response = self.enterOneRaffle(raffle)
            if verbose:
                if response['success']:
                    print('Entered raffle {}/{}'.format(currentraffle, rafflecount))
                    print('TITLE:{}'.format(raffle['title']))
                    print('ID:{}'.format(raffle['id']))
                    print('URL:{}'.format(raffle['absurl']),end='\n\n')
                    currentraffle += 1
                else:
                    print('Raffle enter failed, stopping script')
                    print(response)
                    break
            time.sleep(random.uniform(4, 6))


if __name__ == '__main__':
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    RaffleBot(path)
