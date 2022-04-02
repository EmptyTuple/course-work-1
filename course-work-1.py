from json5 import dumps
import requests
from datetime import datetime
import json
import os
import sys

from pprint import pprint

class APIClient(object):
    """
    Базовый класс для всех API-клиентов.
    """

    def __init__(self, url, token, version=''):
        self.url = url
        self.token = token
        self.version = version

def _check_errors(res):
    """
    Функция обрабатывает ошибки, записывает ошибки в словарь,
    печатает словарь, завершает программу.
    Если ошибок нет возвращает json.
    """
    try:
        res.raise_for_status()
        res = res.json()
        if 'error' in res:
            error_dict = {
                'error_code': f'{res["error"].get("error_code")}',
                'error_msg': res["error"].get("error_msg")
            }
            sys.exit(f'Обнаружены ошибки:\n{error_dict}')
        elif 'error_message' in res:
            error_dict = {
                'error_code': f'{res["error_message"].get("code")} - '
                              f'{res["error_message"].get("error_type")}',
                'error_msg': res['error_message']
            }
            sys.exit(f'Обнаружены ошибки:\n{error_dict}')
    
    except Exception as Ex:
        error_dict = {
            'error_msg': Ex
        }
        sys.exit(f'Обнаружены ошибки:\n{error_dict}')
    return res


class VKPhotosDownloader(APIClient):
    """
    Класс для работы с API Вконтакте.
    Создает директорию TMP на локальном диске, сохраняет в нее фото и json-файл.
    """

    def __init__(self, url, token, version=''):
        super().__init__(url, token, version)
        self.params = {
            'access_token': token,
            'v': version,
        }        

    def get_photos(self, owner_id, album_id='profile', counter=5):
        photos_url = self.url + '/photos.get'
        photos_params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'extended': '1',
            'photo_sizes': '1',
            'count': counter
        }
        res = requests.get(photos_url, params={**self.params, **photos_params})
        res = _check_errors(res)
        
        photos_list = []
        os.mkdir('TMP')

        for value in res['response']['items']:
            # Определение самой большой фотографии в items: сортировка по высоте и ширине
            max_size = sorted(value['sizes'], key=lambda x: x['height'] + x['width'], reverse=True)[0]
    
            # Присваиваем файлу имя в формате: idxxx_likesxxx.jpg, что позволит избежать конфликта
            # при одинаковом количестве лайков.
            max_size['file_name'] = 'id' + str(value['id']) + '_likes' + str(value['likes']['count']) + '.jpg'
            photos_list.append(max_size)

        info = []

        for item in photos_list:
            file_info = {'file name': item['file_name'], 'size': item['type']}
            info.append(file_info)           
        
        with open('TMP/info.json', 'w') as f:
            json.dump(info, f)

        for item in photos_list:
            img_file = requests.get(item['url']).content
            
            with open('TMP/' + item['file_name'], 'wb') as f:
                f.write(img_file)


class YaDiskUpLoader(APIClient):
    """
    Класс для работы с API Yandex Disk
    """

    def __init__(self, url, token, version=''):
        super().__init__(url, token, version)
        self.headers={"Authorization": self.token}

    def create_folder(self, folder):
        
        res = requests.get(self.url, headers=self.headers)
        print('Создание папки на яндекс диске.')
        res = requests.put(self.url, headers=self.headers, params={"path": folder})
        
        # print(res.json()['href'])

        
    def _get_upload_link(self, folder):
        params = {"path": folder, "overwrite": "true"}
        headers = self.headers
        response = requests.get(url=self.url, headers=headers, params=params)

        print(response.json())

        return response.json()
        
    
    def upload_files(self, folder):
        for files in os.listdir('TMP'):

            resp = self._get_upload_link(folder)
            
            with open('TMP/' + files, 'rb') as f:
                print('Загрузка файла:', files)
                response = requests.put(resp['href'], files={"file": f})
                if response.status_code == 201:
                    print('Файл успешно загружен.')
                else:
                    print('Файл не загружен.')

            # res = requests.get(self.url, headers=self.headers, params={"path": files})
            # print(res.json())
            
            # print('Загрузка файла:', files)
            # response = requests.post(res.json()['href'], data=open('TMP/' + files, 'rb'))
           
            # if response.status_code == 201:
            #     print('Файл успешно загружен.')
            # else:
            #     print('Файл не загружен.')
    
    
    
    
    # def upload(self):
    #     """Загрузка файлов из папки TMP на Яндекс Диск"""
    #     # Сохранение файлов в папку
    #     headers = self.headers
    #     # file_list = []
    #     for file_path in os.listdir('TMP'):
    #         if file_path.endswith(".jpg"):
    #             d = {}
    #             d['file_name'] = file_path
    #             d['size'] = int(os.path.getsize(self.folder + file_path))
    #             # file_list.append(d)

    #         def myfunc(file):
    #             return int(os.path.getsize(self.folder + file))
    #         if d['file_name'] in sorted(os.listdir(self.directory), key=myfunc, reverse=True)[:quantity]:
    #             params = {"path": self.folder + file_path}
    #             resp = requests.get(self.api_url + '/upload', headers=headers, params=params)

    #             with open(self.folder + file_path, 'rb') as f:
    #                 print('Загрузка файла:', file_path)
    #                 response = requests.post(resp.json()['href'], files={"file": f})
    #                 if response.status_code == 201:
    #                     print('Файл успешно загружен.')
    #                 else:
    #                     print('Файл не загружен.')

    #             with open(self.folder + 'file_list.json', 'a') as f:
    #                 json.dump(d, f)

    #         print('Загрузка файла json с названиями и размерами файлов')
    #         params = {"path": self.folder + 'file_list.json'}
    #         resp = requests.get(self.api_url + '/upload', headers=headers, params=params)

    #         with open(self.folder + 'file_list.json', 'rb') as f:
    #             response = requests.post(resp.json()['href'], files={"file": f})
    #             if response.status_code == 201:
    #                 print('Файл успешно загружен.')
    #             else:
    #                 print('Файл не загружен.')

    #         print('Загрузка выполнена.')


if __name__ == '__main__':
    # Переменная folder_name задаваемая при старте программы будет использоваться при создании имен папок для хранения фотографий
    # Будут использованы в том числе секунды, что позволит избежать конфликтов с одинаковыми названиями папок и написания кода
    # для проверки имен.
    folder_name = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    

    VK_token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
    Yandex_token = ''
    Google_token = ''

    VK_api_version = '5.131'

    VK_user_id = '1'
    photos_quantity = '4'
    album = 'profile'

    VK_API_URL = 'https://api.vk.com/method'

    YD_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    YD_token = 'AQAAAABewBoFAADLW-SEUZ3sE07CsV2Xgo43Fdo'

    vka = VKPhotosDownloader(VK_API_URL, VK_token, VK_api_version)
    vka.get_photos(VK_user_id, album, photos_quantity)
    yd = YaDiskUpLoader(YD_API_URL, YD_token)
    yd.create_folder(folder_name)
    yd._get_upload_link(folder_name)







