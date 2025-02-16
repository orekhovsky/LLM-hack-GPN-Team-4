import requests
import json
import folium


def get_route_info(api_key, start_point, end_point, transport_mode="walking"):
    """
    Получает информацию о маршруте между двумя точками с использованием API 2GIS.

    :param api_key: API ключ для доступа к сервису 2GIS.
    :param start_point: Словарь с координатами начальной точки (ключи: 'lon', 'lat').
    :param end_point: Словарь с координатами конечной точки (ключи: 'lon', 'lat').
    :param transport_mode: Режим транспорта ('walking', 'driving' и т.д.).
    :return: Ответ от API в формате JSON.
    """
    # URL для запроса маршрута
    url = f"http://routing.api.2gis.com/routing/7.0.0/global?key={api_key}"

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json"
    }

    # Данные для запроса
    data = {
        "points": [
            {
                "type": transport_mode,
                "lon": start_point['lon'],
                "lat": start_point['lat']
            },
            {
                "type": transport_mode,
                "lon": end_point['lon'],
                "lat": end_point['lat']
            }
        ],
        "transport": transport_mode
    }

    # Отправка POST-запроса к API
    response = requests.post(url, headers=headers, json=data)

    # Возврат ответа в формате JSON
    return response.json()


def extract_route_coordinates(route_data):
    """
    Извлекает координаты маршрута из ответа API 2GIS.

    :param route_data: JSON-ответ от API 2GIS.
    :return: Список координат маршрута в формате [[lat1, lon1], [lat2, lon2], ...].
    """
    coordinates = []

    # Проверяем, есть ли данные о маршруте
    if not route_data.get('result'):
        raise ValueError("Нет данных о маршруте в ответе API.")

    # Извлекаем данные о маршруте
    maneuvers = route_data['result'][0]['maneuvers']
    for maneuver in maneuvers:
        if 'outcoming_path' in maneuver and 'geometry' in maneuver['outcoming_path']:
            for segment in maneuver['outcoming_path']['geometry']:
                # Разбираем строку с координатами (LINESTRING)
                linestring = segment['selection'].replace('LINESTRING(', '').replace(')', '')
                points = linestring.split(', ')
                for point in points:
                    lon, lat = map(float, point.split())
                    coordinates.append([lat, lon])

    return coordinates


def get_route_duration(route_data):
    """
    Извлекает продолжительность маршрута в минутах из ответа API 2GIS.

    :param route_data: JSON-ответ от API 2GIS.
    :return: Продолжительность маршрута в минутах.
    """
    if not route_data.get('result'):
        raise ValueError("Нет данных о маршруте в ответе API.")

    # Извлекаем общее время маршрута в секундах
    total_duration_seconds = route_data['result'][0]['total_duration']

    # Преобразуем секунды в минуты
    total_duration_minutes = total_duration_seconds / 60
    return round(total_duration_minutes, 1)  # Округляем до одного знака после запятой


def draw_route_on_map(route_info, start_point, end_point):
    """
    Отрисовывает маршрут на карте с использованием библиотеки folium.

    :param route_info: Данные о маршруте, полученные от API.
    :param start_point: Словарь с координатами начальной точки (ключи: 'lon', 'lat').
    :param end_point: Словарь с координатами конечной точки (ключи: 'lon', 'lat').
    """
    # Извлечение координат маршрута из ответа API
    route_coordinates = extract_route_coordinates(route_info)
    # Извлекаем продолжительность маршрута в минутах
    duration_minutes = get_route_duration(route_info)

    # Создание карты с центром в начальной точке
    map_center = [start_point['lat'], start_point['lon']]
    route_map = folium.Map(location=map_center, zoom_start=14)

    # Добавление маркеров для начальной и конечной точек
    folium.Marker(
        location=[start_point['lat'], start_point['lon']],
        popup=f"Начало маршрута\nВремя: {duration_minutes} мин",
        icon=folium.Icon(color="green")
    ).add_to(route_map)

    folium.Marker(
        location=[end_point['lat'], end_point['lon']],
        popup=f"Конец маршрута\nВремя: {duration_minutes} мин",
        icon=folium.Icon(color="red")
    ).add_to(route_map)

    # Отрисовка маршрута на карте
    folium.PolyLine(
        locations=route_coordinates,
        color="blue",
        weight=5,
        opacity=0.7
    ).add_to(route_map)

    # Сохранение карты в HTML-файл
    route_map.save("route_map.html")
    print("Карта сохранена в файл 'route_map.html'. Откройте этот файл в браузере.")


def main():
    # API ключ для доступа к сервису 2GIS
    with open("2gis-key.json", "r") as file:
        config = json.load(file)
    api_key = config["api_key"]

    # Координаты начальной и конечной точек
    start_point = {"lon": 30.369587, "lat": 59.940289}
    end_point = {"lon": 30.350266, "lat": 59.932201}

    # Получение информации о маршруте
    route_info = get_route_info(api_key, start_point, end_point, transport_mode="walking")

    # Отрисовка маршрута на карте
    draw_route_on_map(route_info, start_point, end_point)


if __name__ == "__main__":
    main()
