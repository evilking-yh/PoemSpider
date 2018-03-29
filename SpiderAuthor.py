import requests
import requests.cookies
from bs4 import BeautifulSoup
import csv
import os
import re

base_url = 'https://so.gushiwen.org'
author_file_path = 'author.csv'


def init_headers():
    cookies = 'Hm_lvt_04660099568f561a75456483228a9516=1522044920,1522285410; ASP.NET_SessionId=albbasnvcb4sary4ey33igjb; Hm_lpvt_04660099568f561a75456483228a9516=1522286057'
    jar = requests.cookies.RequestsCookieJar()
    for cookie in cookies.split(';'):
        key, value = cookie.split('=', 1)
        jar.set(key, value)

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    return (headers, jar)


def fetch_author_page(p, headers, jar):
    author_url = base_url + '/authors/Default.aspx?p=' + str(p)

    req = requests.get(author_url, headers=headers, cookies=jar, timeout=5)
    do_fail(author_url) if not req.status_code == requests.codes.ok else do_author_success(req.text, author_url)


def fetch_author_page_num(headers, jar):
    author_url = 'https://so.gushiwen.org/authors/'
    req = requests.get(author_url, headers=headers, cookies=jar, timeout=5)
    soup = BeautifulSoup(req.text, 'lxml')
    page_str = soup.select('.main3 .left .pages span')[1].text
    totalCount = re.sub("\D", "", page_str)
    return int(int(totalCount) / 10)


def do_fail(url):
    print('Fetch url is fail !!!', url)
    exit()


def do_author_success(text, url):
    soup = BeautifulSoup(text, 'lxml')
    left_container = soup.select('.main3 .left .sonspic')
    author_dict = []
    for item in left_container:
        item_name = item.select('p')[0]
        author_name = item_name.find(name='b').text
        author_url = item_name.find(name='a').attrs['href']
        item_info = item.select('p')[1].text.replace('► ', '著有')
        author_dict.append({'name': author_name, 'url': author_url, 'info': item_info})
    save_author(author_dict)
    print('已处理: ', url)


def save_author(author_dict):
    with open(author_file_path, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['name', 'url', 'info']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerows(author_dict)


def reset_file(file):
    if os.path.exists(file):
        os.remove(file)


if __name__ == '__main__':
    reset_file('author.csv')
    (headers, jar) = init_headers()
    page_num = fetch_author_page_num(headers, jar)
    for i in range(page_num):
        fetch_author_page(i + 1, headers, jar)
    print('=========(^_^)==========总共', page_num, '页已爬完')
