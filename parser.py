from dataclasses import replace
from datetime import datetime
import requests
import json
import os
import sys
import telegram

# Адрес ваших Torrserver
hosts = [
    'http://192.168.1.83:8090'
    ]
# Адрес RSS. Можно использовать RSS для чтения, чтобы подгрузить постеры напрямую из RSS
url = 'https://litr.cc/feed/15efba36-7b07-4112-ad51-dcf9b8fa5057/rss/magnet'
# для загрузки постеров на imgur
imgur_token = ''
# интеграция в telegram, если не заполнять токен то не отправлять сообщения не будет
token = ""
bot = None
# для отправки в групповой чат (уведомления о новых сериях)
chat_id_group = [0,]
# для отправки в личный чат (уведомления о ошибках)
chat_id_my = [0,]
if len(token)>0:
    bot = telegram.Bot(token)


def main():
    global url
    url = url.replace('/rss/magnet','')
    url = url.replace('/rss/read','')
    url = url.replace('/rss','')
    url = url + '/json'

    JsonText = requests.get(url).text
    print('Дата отправки запроса '+str(datetime.now()))
    print('')

    otkaz = False
    pathOldJson = os.path.basename(sys.argv[0])+'_old.json'
    print(pathOldJson)
    try:
        old_json = open(pathOldJson, 'r').read()
        if (JsonText==old_json):
            print('Без изменений. Пропущено')
            print('Для перезапуска удалите файл '+pathOldJson)
            otkaz = True
    except Exception as e:
        print('Ошибка открытия json '+str(e))
       
    if otkaz:
        exit()


    my_file = open(pathOldJson, 'w')
    my_file.write(JsonText)
    my_file.close()

    for host in hosts:
        print('-------------------------------------------')
        print(host)
        print('-------------------------------------------')
        json_list=[]
        json1 = {
            'action': 'list'
            }
        try:
            response = requests.post(host+'/torrents','',json1,timeout=10)
            # 200 - значит всё ОК
            json_list = json.loads(response.text)
        except:
            print('Ошибка подключения к хосту '+host)  
            send_message_bot('Ошибка подключения torserve_parser ' + str(datetime.now()))
            continue   

        doc = json.loads(JsonText)

        torrents = doc.get('items',[])
        for torrent in torrents:
            
            Torrent_Title = ''
            Torrent_Link = '' 
            Torrent_Poster = ''
            Torrent_Guid = ''
            
            Torrent_Title = torrent.get('title','')
            Torrent_Poster = torrent.get('image','')
            Torrent_Hash = torrent.get('id','').lower()
            Torrent_attachments = torrent.get('attachments',[])
            if len(Torrent_attachments)>0:
                Torrent_Guid = Torrent_attachments[0].get('url','')
            Torrent_Link = 'magnet:?xt=urn:btih:'+Torrent_Hash 

               
            if len(imgur_token)>0 and len(Torrent_Poster)>0:
                api = 'https://api.imgur.com/3/image'

                params = dict(
                    client_id=imgur_token
                )

                files123 = dict(
                    image=(None, Torrent_Poster),
                    name=(None, ''),
                    type=(None, 'URL'),
                )
                r_imgur = requests.post(api, files=files123, params=params)
                if r_imgur.status_code==200:
                    try:
                        Torrent_Poster = r_imgur.json()['data']['link']    
                    except:()      

            print(Torrent_Title) 
            print(Torrent_Guid)
            print(Torrent_Link) 
            print('')
            print(Torrent_Hash)     
            print('')
            print(Torrent_Poster) 

            # Проверяем добавляли ли торрент с таким хэшем ранее, если да, то ничего не делаем
            json1 = {
                'action': 'get',
                'hash': Torrent_Hash
                }
            try:
                response = requests.post(host+'/torrents','',json1,timeout=10)
                # 200 - значит торрент уже добавлен
                if response.status_code == 200:
                    print('Уже добавлен')
                    print('')
                    continue
            except:
                print('Ошибка подключения')
                send_message_bot('Ошибка подключения torserve_parser ' + str(datetime.now()))
                continue    

            # Добавляем новый торрент
            json1 = {
                'action': 'add',
                'link': Torrent_Link,
                'title': Torrent_Title,
                'poster': Torrent_Poster,                
                'save_to_db': True,
                'data': Torrent_Guid
                }
            try:
                response = requests.post(host+'/torrents','',json1,timeout=10)
                # 200 - значит всё ОК
                if response.status_code==200:
                    print('Новый торрент добавлен')
                    send_message_bot('Добавлен новый торрент ' + Torrent_Title, True)
                else:
                    send_message_bot('Ошибка добавления торрента ' + Torrent_Title+' . Сервер вернул код ' + str(response.status_code))
                    continue
            except:
                print('Ошибка подключения')  
                send_message_bot('Ошибка подключения torserve_parser')               
                continue

            # Ищем старые торрренты, ищем просмотренные серии и удаляем
            search_limit = 100
            OldHash = ''
            current_torrent=0
            for old_torrent in json_list:
                if Torrent_Hash == Torrent_Guid or Torrent_Guid == '':
                    break
                current_torrent+=1
                if current_torrent>search_limit:
                    break
                if not 'data' in old_torrent or not 'hash' in old_torrent:
                    continue
                if old_torrent['data']==Torrent_Guid and old_torrent['hash']!=Torrent_Hash:
                    OldHash = old_torrent['hash']
                    break

            if OldHash=='':
                # старый хэш не нашли
                print('')
                continue

            #запоминаем просмотренные серии из старого торрента
            viewed_list = []
            json1 = {
                'action': 'list',
                'hash': OldHash
                }
            try:
                response = requests.post(host+'/viewed','',json1,timeout=10)
                # 200 - значит всё ОК
                viewed_list = json.loads(response.text)
            except:
                print('Ошибка подключения')  
                continue   
        
            set_viewed_complete = False
            for viewed_index in viewed_list:
                json1 = {
                    'action': 'set',
                    'hash': Torrent_Hash,
                    'file_index': viewed_index['file_index']
                    }
                try:
                    response = requests.post(host+'/viewed','',json1,timeout=10)
                    # 200 - значит всё ОК
                    if response.status_code == 200:
                        set_viewed_complete = True
                        continue
                except:
                    print('Ошибка подключения')  
                    send_message_bot('Ошибка подключения torserve_parser')
                    continue   
            if set_viewed_complete:
                print('Просмотренные серии загружены')
                send_message_bot('Просмотренные серии загружены torserve_parser')
            json1 = {
                'action': 'rem',
                'hash': OldHash
                }
            try:
                response = requests.post(host+'/torrents','',json1,timeout=10)
                # 200 - значит всё ОК
                if response.status_code == 200:
                    print('Старый торрент удален')
                    send_message_bot('Старый торрент удален torserve_parser')
            except:
                print('Ошибка подключения')  
                send_message_bot('Ошибка подключения torserve_parser ')
                continue   

            print('')
        
def send_message_bot(text, group=False):
    if group:
        chat_id_array = chat_id_group
    else:
        chat_id_array = chat_id_my
    if bot is None or len(chat_id_array)==0:
        return   
    for i in chat_id_array:
        bot.send_message(i, text=text, parse_mode="Markdown")

    
if __name__ == '__main__':
    main()
