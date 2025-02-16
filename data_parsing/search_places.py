import requests
import pandas as pd
import json
import time


# API ключ от 2GIS
with open("2gis-key.json", "r") as file:
    config = json.load(file)
API_KEY = config["api_key"]

# Основной URL для API 2GIS
BASE_URL = 'https://catalog.api.2gis.com/3.0/items'


def search_places(api_key, base_url, query, location, radius=2000, page=1):
    """
    Функция для поиска заведений через API 2GIS.

    :param api_key: API ключ
    :param base_url: Базовый URL API
    :param query: Поисковый запрос
    :param location: Координаты точки (долгота, широта)
    :param radius: Радиус поиска в метрах
    :param page: Номер страницы
    :return: JSON-ответ от API или None в случае ошибки
    """
    params = {
        'q': query,
        'point': location,
        'radius': radius,
        'fields': 'items.point,items.address,items.rubrics,items.reviews,items.context',
        'key': api_key,
        'page': page
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def extract_place_info(place):
    """
    Функция для извлечения информации о заведении из JSON-ответа.

    :param place: JSON-объект с информацией о заведении
    :return: Словарь с ключевой информацией о заведении
    """
    stop_factors = place.get('context', {}).get('stop_factors', [])

    # Проверяем, что stop_factors существует и является списком
    if not isinstance(stop_factors, list):
        stop_factors = []

    # Ищем средний счет
    avg_price_dict = next(
        (item for item in stop_factors if isinstance(item, dict) and item.get('tag') == 'food_service_avg_price'), None)

    # Ищем информацию о кухне
    cuisine_dicts = [item for item in stop_factors if
                     isinstance(item, dict) and 'food_service_food' in item.get('tag', '')]

    # Ищем информацию о ассортименте
    assortment_dicts = [item for item in stop_factors if
                        isinstance(item, dict) and 'food_service_assortment' in item.get('tag', '')]

    # Формируем информацию о заведении
    info = {
        "name": place.get('name'),
        "address": place.get('address_name'),
        "coordinates": place.get('point'),
        "rating": place.get('reviews', {}).get('general_rating'),
        "reviews": place.get('reviews', {}).get('general_review_count'),
        "categories": [rubric.get('name') for rubric in place.get('rubrics', [])],
        "avg_bill": avg_price_dict.get('name') if avg_price_dict else None,
        "cuisine": [cuisine.get('name') for cuisine in cuisine_dicts if cuisine.get('name')],
        "assortment": [assortment.get('name') for assortment in assortment_dicts if assortment.get('name')],
    }
    return info


def fetch_places_for_category(category, location, radius=2000):
    """
    Функция для получения всех заведений по указанной категории.

    :param category: Категория заведений (например, "ресторан", "кафе")
    :param location: Координаты точки (долгота, широта)
    :param radius: Радиус поиска в метрах
    :return: DataFrame с информацией о заведениях
    """
    page = 1
    all_places = []

    while True:
        data = search_places(API_KEY, BASE_URL, category, location, radius=radius, page=page)
        if data and data.get("result"):
            places = data["result"].get("items", [])
            all_places.extend(places)
            page += 1
        else:
            print(f"Данные для категории '{category}' закончились или отсутствуют.")
            break

        time.sleep(1)  # Задержка между запросами, чтобы избежать блокировки

    # Создаем DataFrame для текущей категории
    df = pd.DataFrame(
        columns=["name", "address", "coordinates", "rating", "reviews", "categories", "avg_bill", "cuisine",
                 "assortment"])

    for place in all_places:
        place_info = extract_place_info(place)
        df.loc[len(df)] = place_info

    return df


def main():
    """
    Основная функция для выполнения поиска и вывода информации о заведениях.
    """
    categories = ["ресторан", "кафе", "бар", "пиццерия", "кофейня", "фастфуд"]  # Список категорий
    location = "30.369587,59.940289"  # Координаты точки (долгота и широта)
    radius = 5000  # Радиус поиска в метрах

    all_dfs = []  # Список для хранения DataFrame по каждой категории

    for category in categories:
        print(f"Поиск заведений для категории: {category}")
        df = fetch_places_for_category(category, location, radius)
        all_dfs.append(df)

    # Объединяем все DataFrame в один
    final_df = pd.concat(all_dfs, ignore_index=True)

    # Сохраняем итоговый DataFrame в CSV файл
    final_df.to_csv('all_restaurants.csv', index=False, encoding='utf-8')
    print("Данные сохранены в файл 'all_restaurants.csv'")


if __name__ == "__main__":
    main()
