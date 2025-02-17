import pandas as pd
import numpy as np
import json
import time
import ast
from routing.plan_route import get_route_info, get_route_duration


# Функция для получения времени маршрута
def get_route_duration_for_place(place, api_key, start_point):
    """
    Вычисляет продолжительность маршрута до ресторана.

    :param place: Строка датафрейма (ресторан).
    :param api_key: API ключ для доступа к сервису 2GIS.
    :param start_point: Начальная точка маршрута (словарь с ключами 'lat' и 'lon').
    :return: Продолжительность маршрута в минутах.
    """
    end_point = ast.literal_eval(place['coordinates'])
    # Получение информации о маршруте
    route_info = get_route_info(api_key, start_point, end_point, transport_mode="walking")
    time.sleep(13)  # Задержка между запросами, чтобы избежать блокировки
    return get_route_duration(route_info)


# Основная функция
def add_route_duration_to_df(df, api_key, start_point):
    """
    Добавляет столбец с продолжительностью маршрута в датафрейм.

    :param df: Исходный датафрейм с колонкой 'coordinates'.
    :param api_key: API ключ для доступа к сервису 2GIS.
    :param start_point: Начальная точка маршрута (словарь с ключами 'lat' и 'lon').
    :return: Датафрейм с добавленным столбцом 'route_duration'.
    """
    df['route_duration'] = df.apply(lambda row: get_route_duration_for_place(row, api_key, start_point), axis=1)
    return df


# Функция для обработки датафрейма частями (из-за лимита запросов на сервис построения маршрутов)
def process_dataframe_in_chunks(df, start_point, chunk_size):
    """
    Обрабатывает датафрейм частями, добавляя столбец с продолжительностью маршрута.

    :param df: Исходный датафрейм.
    :param start_point: Начальная точка маршрута.
    :param chunk_size: Размер части датафрейма (по умолчанию 50 строк).
    :return: Обработанный датафрейм.
    """
    chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]
    processed_chunks = []

    for i, chunk in enumerate(chunks):
        print(f"Обработка части {i + 1} из {len(chunks)}...")

        # API ключ от 2GIS (меняется для каждого чанка)
        with open(f"2gis-key-{i + 1}.json", "r") as file:
            config = json.load(file)
        api_key = config["api_key"]

        processed_chunk = add_route_duration_to_df(chunk, api_key, start_point)
        processed_chunks.append(processed_chunk)

    # Объединение всех частей в один датафрейм
    return pd.concat(processed_chunks, ignore_index=True)


# Основной блок
if __name__ == "__main__":
    # Загрузка данных
    raw_data = pd.read_csv('all_restaurants.csv')
    print(f'Собрано мест: {raw_data.shape[0]}')
    data = raw_data.drop_duplicates()
    print(f'Удалено дубликатов: {raw_data.shape[0] - data.shape[0]}')

    data = data.replace('[]', np.nan)
    data = data.dropna(subset=['name', 'address', 'coordinates', 'rating', 'reviews', 'categories', 'avg_bill',
                               'cuisine'])
    print(f'После удаления строк с пропусками: {data.shape[0]}')

    # Начальная точка маршрута
    START_POINT = {"lat": 59.940289, "lon": 30.369587}

    # Обработка датафрейма частями
    data_with_duration = process_dataframe_in_chunks(data, START_POINT, 50)

    # Сохранение итогового датафрейма в CSV файл
    data_with_duration.to_csv('all_restaurants_with_route_duration.csv', index=False, encoding='utf-8')
    print("Данные успешно сохранены в файл 'all_restaurants_with_route_duration.csv'.")
