import json
import re

from bs4 import BeautifulSoup
import requests
from fake_headers import Headers

class HHParser:

    def __init__(self):
        self.url = 'https://spb.hh.ru/search/vacancy?text=python&area=1&area=2'
        self.headers = Headers(os='windows', browser='chrome').generate()
        self.repl_salary_pattern = re.compile(r'(?<=\d)\s+(?=\d)')
        self.vacancies_list = list()
        self.dollar_vacancies_list = list()

    def parse(self):
        print('Обработка вакансий')
        self.collect_vacancies()
        self.write_files()

    def write_files(self):
        with open('vacancies.json', 'w', encoding='utf-8') as file:
            json.dump(self.vacancies_list, file, ensure_ascii=False)
        with open('dollar_vacancies.json', 'w', encoding='utf-8') as file:
            json.dump(self.dollar_vacancies_list, file, ensure_ascii=False)

    def collect_vacancies(self):
        temp = 0
        for link in self.get_links():
            vacancy = self.get_vacancy(link)
            if vacancy is None:
                continue
            if vacancy['salary'].find('$') != -1:
                self.dollar_vacancies_list.append(vacancy)
            self.vacancies_list.append(vacancy)
            print(temp)
            temp += 1

    def get_links(self):
        links_list = list()
        response = requests.get(url=self.url, headers=self.headers)
        if response.status_code != 200:
            return
        soup = BeautifulSoup(response.content, 'lxml')
        try:
            pages_count = int(soup.find('div', attrs={'class': 'pager'}).find_all('span',recursive=False)[-1].find('a').find('span').text)
        except:
            return
        for page_number in range(pages_count):
            try:
                url = self.url + f'&page={page_number}'
                response = requests.get(url=url, headers=self.headers)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'lxml')
                for link in soup.find_all('a', attrs={'class': 'serp-item__title'}):
                    yield link.attrs['href']
            except Exception as ex:
                print(ex)

    def get_vacancy(self, link):
        response = requests.get(url=link, headers=self.headers)
        if response.status_code != 200:
            return
        soup = BeautifulSoup(response.content, 'lxml')
        try:
            description = soup.find('div', attrs={'class': 'g-user-content', 'data-qa': 'vacancy-description'}).text
            if description.find('Django') == -1 and description.find('Flask') == -1:
                return
        except:
            return
        try:
            name = soup.find('div', attrs={'class': 'vacancy-title'}).find('h1').text
        except:
            name = ''
        try:
            salary = soup.find('div', attrs={'data-qa': 'vacancy-salary'}).find('span', attrs={'class': 'bloko-header-section-2 bloko-header-section-2_lite'}).text
            salary = self.repl_salary_pattern.sub('', salary)
        except:
            salary = ''
        try:
            company = soup.find('a', attrs={'data-qa': 'vacancy-company-name'}).find('span', attrs={'data-qa': 'bloko-header-2'}, recursive=False).text
            company = company.replace('\xa0', ' ')
        except:
            company = ''
        try:
            city = soup.find('p', attrs={'data-qa': 'vacancy-view-location'}).text
        except:
            try:
                city = soup.find('span', attrs={'data-qa': 'vacancy-view-raw-address'}).text
            except:
                city = ''    
        vacancy = {
            'name': name, 
            'salary': salary, 
            'link': link, 
            'company': company,
            'city': city
        }
        return vacancy