import xml.dom.minidom
import requests
import json

# Адрес вашего Torrserver
host = 'http://192.168.1.62:8090/torrents'
# Можно использовать RSS для чтения, чтобы подгрузить постеры напрямую из RSS
url = 'http://litr.cc/rss/d02e7a69357c64210a8aa8d932e1cd64'
RssText = requests.get(url).text

doc = xml.dom.minidom.parseString(RssText)
torrents = doc.getElementsByTagName('item')
for torrent in torrents:
    Torrent_Title = ''
    Torrent_Link = '' 
    Torrent_Poster = ''       
    for childTitle in torrent.getElementsByTagName('title'):
        for childName in childTitle.childNodes:
            Torrent_Title = childName.data
    for childLink in torrent.getElementsByTagName('link'):
        for childName in childLink.childNodes:
            Torrent_Link = childName.data

    if (len(Torrent_Link)==0) or (Torrent_Link[0:4]=='http'):
        #значит это RSS для чтения, находим магнет ссылку и постер в html содержимом
        img_tag = 'img src="'
        start_img = RssText.find(img_tag)
        if start_img>0:
            end_img = RssText.find('" alt="',start_img)
            Torrent_Poster = RssText[start_img+len(img_tag):end_img]
        start_link = RssText.find('magnet:')
        if start_link>0:
            end_link = RssText.find('&',start_link)
            Torrent_Link = RssText[start_link:end_link]

    print(Torrent_Title) 
    print(Torrent_Link) 
    print(Torrent_Poster) 

    
    json = {
        'action': 'add',
        'link': Torrent_Link,
        'title': Torrent_Title,
        'poster': Torrent_Poster,                
        'save_to_db': True
        }
    response = requests.post(host,'',json)
    # 200 - значит всё ОК
    print("Status code: ", response.status_code)


