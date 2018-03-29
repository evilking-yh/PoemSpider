import requests
import requests.cookies
from bs4 import BeautifulSoup
import csv
import os
import re

base_url = 'https://www.gushiwen.org'
poem_file_path = 'poem.csv'

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

def fetch_poem_page(p, headers, jar):
    poem_url = base_url + '/shiwen/default_0A0A' + str(p) + '.aspx'
    req = requests.get(poem_url, headers=headers, cookies=jar, timeout=5)
    do_fail(poem_url) if not req.status_code == requests.codes.ok else do_poem_success(req.text, poem_url)

def fetch_poem_page_num(headers, jar):
    author_url = base_url + '/shiwen/'
    req = requests.get(author_url, headers=headers, cookies=jar, timeout=5)
    soup = BeautifulSoup(req.text, 'lxml')
    page_str = soup.select('.main3 .left .pages span')[1].text
    totalCount = re.sub("\D", "", page_str)
    return int(int(totalCount) / 10)


def do_fail(url):
    print('Fetch url is fail !!!', url)
    exit()

def do_poem_success(text, url):
    soup = BeautifulSoup(text, 'lxml')
    sons_container = soup.select('.main3 .left .sons')
    for item in sons_container:
        son_link = item.select_one('a').attrs['href']
        do_parse_poem_page(son_link)
    # print("已处理完: ", url)

def do_parse_poem_page(poem_detail_url):
    print(poem_detail_url)
    req = requests.get(poem_detail_url, headers=headers, cookies=jar, timeout=5)
    soup = BeautifulSoup(req.text, 'lxml')
    container = soup.select('.main3 .left .sons')
    # 处理 诗歌
    peom_c = container[0].select_one('.cont')
    peom_h1 = peom_c.select_one('h1').text
    peom_p = peom_c.select_one('p').text
    peom_body = peom_c.select_one('.contson').text

    peom_tag = container[0].select('.tag a')
    peom_tag_list = list(set([tag.text for tag in peom_tag]))

    # 处理译文及注释
    fanyi_id_str = None
    try:
        fanyi_id_str = container[1].attrs['id']
    except:
        try:
            fanyi_id_str = container[2].attrs['id']
        except:
            pass
    if fanyi_id_str != None:
        fanyi_id = re.sub("\D", "", fanyi_id_str)
        (yiwen, zhushi) = parse_fanyi(fanyi_id)
    else:
        fanyi_container = container[1].select('.contyishang p')
        (yiwen, zhushi) = parse_fanyi_content(fanyi_container)

    # 处理主题
    shangxi = ''
    fenxi_siblings = container[3].fetchNextSiblings()
    for item in fenxi_siblings:
        if item.get('id') != None and item.get('id').startswith('shangxi'):
            shangxi_id = re.sub("\D", "", item.attrs['id'])
            # 处理赏析消失
            x_s = item.select('.contyishang p')
            x_s_list = []
            for x_item in x_s:
                x_s_list.append(x_item.text)
            shangxi = parser_shangxi(shangxi_id, '\n'.join(x_s_list))
            break
    save_poem_info(peom_h1, peom_p, peom_body, peom_tag_list, yiwen, zhushi, shangxi)

def save_poem_info(name, author_p, body, tag_list, yiwen, zhushi, shangxi):
    author = author_p.split('：')[1].strip()
    period = author_p.split('：')[0].strip()
    with open(poem_file_path, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['name', 'author', 'period', 'body', 'tag_list', 'yiwen', 'zhushi', 'shangxi']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'name': name, 'author': author, 'period': period, 'body': body, 'tag_list': tag_list, 'yiwen': yiwen, 'zhushi': zhushi, 'shangxi': shangxi})


def parser_shangxi(id, x_text):
    shangxi_url = 'https://so.gushiwen.org/shiwen2017/ajaxshangxi.aspx?id=' + id
    # print(shangxi_url)
    req = requests.get(shangxi_url, headers=headers, cookies=jar, timeout=5)
    soup = BeautifulSoup(req.text, 'lxml')
    shangxi_container = soup.select_one('.contyishang')
    shangxi = ''
    try:
        shangxi = shangxi_container.text
    except:
        shangxi = x_text
    return shangxi

def parse_fanyi(id):
    fanyi_url = 'https://so.gushiwen.org/shiwen2017/ajaxfanyi.aspx?id=' + id
    req = requests.get(fanyi_url, headers=headers, cookies=jar, timeout=5)
    soup = BeautifulSoup(req.text, 'lxml')
    fanyi_container = soup.select('.contyishang p')
    return parse_fanyi_content(fanyi_container)

def parse_fanyi_content(fanyi_container):
    yiwen = []
    zhushi = []
    flag = True
    for item in fanyi_container:
        if item.text.startswith('译文'):
            flag = True
        if item.text.startswith('直译'):
            flag = True
        if item.text.startswith('注释'):
            flag = False

        if flag:
            yiwen.append(item.text)
        else:
            zhushi.append(item.text)

    return ('\n'.join(yiwen), '\n'.join(zhushi))

def save_author(author_dict):
    with open(poem_file_path, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['name', 'url', 'info']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerows(author_dict)


def reset_file(file):
    if os.path.exists(file):
        os.remove(file)


if __name__ == '__main__':
    reset_file(poem_file_path)
    (headers, jar) = init_headers()
    page_num = fetch_poem_page_num(headers, jar)
    # page_num = 2
    for i in range(1, page_num):
        fetch_poem_page(i + 1, headers, jar)
    print('=========(^_^)==========总共', page_num, '页已爬完')