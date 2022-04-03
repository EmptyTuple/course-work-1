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
    def __init__(self, url: str, token: str, version=''):
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

def clear_tmp():
    '''Функция проверяет есть ли директория с именем VK_TMP,
    для временнего хранения скачанных файлов. Если директории нет, создает ее,
    если директория существует - удаляет ее содержимое.
    '''
    if not os.path.isdir("VK_TMP"):
        os.mkdir('VK_TMP')
    else:
        for root, dirs, files in os.walk('VK_TMP', topdown=False):
            for filename in files:
                os.remove(os.path.join(root, filename))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                
def delete_tmp_dir():
    '''Функция удаляет временные файлы и папки, создаваемые в каталоге программы
       при копировании фотографий
    '''
    print('Удаляю временные файлы и директории.')
    for file in os.listdir('VK_TMP'):
        os.remove('VK_TMP/' + file)
    os.rmdir('VK_TMP')
    print('Временные файлы и директории удалены.')

class VKPhotosDownloader(APIClient):
    """
    Класс для работы с API Вконтакте.
    Создает директорию TMP на локальном диске, сохраняет в нее фото и json-файл.
    """

    def __init__(self, url: str, token: str, version=''):
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
        clear_tmp()

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
        
        with open('VK_TMP/info.json', 'w') as f:
            json.dump(info, f)

        for item in photos_list:
            img_file = requests.get(item['url']).content
            
            with open('VK_TMP/' + item['file_name'], 'wb') as f:
                f.write(img_file)

class YaDiskUpLoader(APIClient):
    """
    Класс для работы с API Yandex Disk
    """
    def __init__(self, url: str, token: str, version=''):
        super().__init__(url, token, version)
        self.headers={"Authorization": self.token}

    def load_to_ydisk(self, folder: str):        
        res = requests.get(self.url, headers=self.headers)
        print('Создание папки на Yandex Disk.')
        res = requests.put(self.url, headers=self.headers, params={"path": folder})
        res = _check_errors(res)
    
        for files in os.listdir('VK_TMP'):
            headers = {"Authorization": self.token}
            params = {"path": folder + '/' + files, 'overwrite':True}
            resp = requests.get(self.url + '/upload', headers=headers, params=params)

            with open('VK_TMP/' + files, 'rb') as f:
                print('Загрузка файла:', files)
                response = requests.post(resp.json()['href'], files={"file": f})
                if response.status_code == 201:
                    print('Файл успешно загружен.')
                else:
                    print('Файл не загружен.')

def is_integer(variable: str) -> int:
    '''Функция проверяет является ли объект ввода целым положительным числом
    '''
    try:
        int(variable)
        return int(variable)
    except ValueError:
        variable = input('Ошибка! Введите целое положительное число: ')
        is_integer(variable)


def main():
    VK_api_version = '5.131'
    VK_API_URL = 'https://api.vk.com/method'
    YD_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
    
    VK_token = str(input('Введите токен для доступа VK: '))
    YD_token = str(input('Введите токен для доступа Yandex Disk: '))
    
    _VK_user_id = int(input('Введите ID пользователя VK: '))
    VK_user_id = is_integer(_VK_user_id)
    _photos_quantity = int(input('Введите количество фотографий: '))
    photos_quantity = is_integer(_photos_quantity)

    

if __name__ == '__main__':
    # Переменная folder_name задаваемая при старте программы будет использоваться при создании имен папок для хранения фотографий
    # Будут использованы в том числе секунды, что позволит избежать конфликтов с одинаковыми названиями папок и написания кода
    # для проверки имен.
    folder_name = datetime.now().strftime("%d-%m-%y_%H-%M-%S")

    VK_token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
    Google_token = ''
    YD_token = ''

    VK_api_version = '5.131'

    VK_user_id = '1'
    photos_quantity = '4'
    album = 'profile'

    VK_API_URL = 'https://api.vk.com/method'

    YD_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources'


    vka = VKPhotosDownloader(VK_API_URL, VK_token, VK_api_version)
    vka.get_photos(VK_user_id, album, photos_quantity)
    yd = YaDiskUpLoader(YD_API_URL, YD_token)
    yd.load_to_ydisk(folder_name)
    delete_tmp_dir()
   