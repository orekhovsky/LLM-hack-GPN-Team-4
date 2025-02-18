import pandas as pd


# Загрузка данных
df = pd.read_csv('../data_parsing/preprocessed_data.csv')

# Имитация предпочтений пользователей
users = {
    'user_1_id': {
        'cuisines': {'Авторская кухня': 4.5, 'Азиатская кухня': 4.5, 'Американская кухня': 3.5,
                     'Веганская кухня': 3, 'Вегетарианская кухня': 3, 'Восточная кухня': 3, 'Вьетнамская кухня': 2,
                     'Греческая кухня': 2, 'Грузинская кухня': 2, 'Домашняя кухня': 2, 'Европейская кухня': 2},
        'avg_bill': '500-1000',
        'time_before_meet': 90
    },
    'user_2_id': {
        'cuisines': {'Испанская кухня': 2, 'Японская кухня': 1, 'Средиземноморская кухня': 4.5,
                     'Вьетнамская кухня': 1, 'Греческая кухня': 3, 'Тайская кухня': 2, 'Авторская кухня': 4,
                     'Веганская кухня': 1, 'Израильская кухня': 2, 'Итальянская кухня': 5, 'Китайская кухня': 2},
        'avg_bill': '1000-1500',
        'time_before_meet': 60
    },
    'user_3_id': {
        'cuisines': {'Испанская кухня': 3.5, 'Японская кухня': 2.5, 'Средиземноморская кухня': 2,
                     'Вьетнамская кухня': 3, 'Греческая кухня': 3, 'Тайская кухня': 3, 'Авторская кухня': 5,
                     'Веганская кухня': 4, 'Израильская кухня': 1, 'Итальянская кухня': 3, 'Китайская кухня': 3},
        'avg_bill': '1500-2000',
        'time_before_meet': 120
    }
}

# Имитация комнат с пользователями
rooms = {
    'room_1_id': ['user_1_id', 'user_2_id', 'user_3_id'],
    'room_2_id': ['user_3_id', 'user_1_id']
}


def calculate_room_preferences(room_users_list, users_dict):
    """
    Рассчитывает средние предпочтения для комнаты.
    Возвращает средние предпочтения по кухням, средний диапазон чека и минимальное время до встречи.
    """
    cuisines_avg = {}
    avg_bill_ranges = []
    time_before_meet_list = []

    # Собираем данные от всех пользователей в комнате
    for user_ID in room_users_list:
        user = users_dict.get(user_ID)
        if user:
            # Считаем средние предпочтения по кухням
            for cuisine, weight in user['cuisines'].items():
                if cuisine in cuisines_avg:
                    cuisines_avg[cuisine].append(weight)
                else:
                    cuisines_avg[cuisine] = [weight]

            # Собираем диапазоны среднего чека
            if 'avg_bill' in user and user['avg_bill']:
                avg_bill_range = user['avg_bill'].split('-')
                if len(avg_bill_range) == 2:
                    avg_bill_ranges.append((int(avg_bill_range[0]), int(avg_bill_range[1])))

            # Собираем время до встречи
            if 'time_before_meet' in user and user['time_before_meet'] is not None:
                time_before_meet_list.append(user['time_before_meet'])

    # Рассчитываем средние значения для кухонь
    for cuisine in cuisines_avg:
        cuisines_avg[cuisine] = sum(cuisines_avg[cuisine]) / len(cuisines_avg[cuisine])

    # Рассчитываем средний диапазон чека
    if avg_bill_ranges:  # Если список не пустой
        avg_bill_min = sum([x[0] for x in avg_bill_ranges]) / len(avg_bill_ranges)
        avg_bill_max = sum([x[1] for x in avg_bill_ranges]) / len(avg_bill_ranges)
    else:
        # Значения по умолчанию, если данные отсутствуют
        avg_bill_min, avg_bill_max = 500, 1000  # Пример диапазона по умолчанию

    # Минимальное время до встречи
    if time_before_meet_list:  # Если список не пустой
        time_before_meet_min = min(time_before_meet_list)
    else:
        # Значение по умолчанию, если данные отсутствуют
        time_before_meet_min = 60  # Пример времени по умолчанию

    return {
        'cuisines': cuisines_avg,
        'avg_bill': f"{int(avg_bill_min)}-{int(avg_bill_max)}",
        'time_before_meet': time_before_meet_min
    }


def apply_preferences(data, preferences):
    """
    Применяет предпочтения (от пользователя или комнаты) к данным.
    Умножает значения столбцов, соответствующих кухням, на вес предпочтений.
    """
    for cuisine, weight in preferences['cuisines'].items():
        if cuisine in data.columns:  # Проверяем, существует ли столбец
            data[cuisine] *= weight
        else:
            print(f"Предупреждение: столбец '{cuisine}' отсутствует в данных.")
    return data


def calculate_rate(data):
    """
    Вычисляет рейтинг на основе предпочтений.
    Возвращает максимальное значение среди всех кухонь для каждого заведения.
    """
    cuisines_ohe = [col for col in data.columns if 'кухня' in col]
    data['rate'] = data[cuisines_ohe].max(axis=1)
    return data


def calculate_reviews_coefficient(data):
    """
    Вычисляет коэффициент на основе количества отзывов.
    """
    def count_to_rate(x):
        if x < 200:
            return 0.8
        elif x > 1000:
            return 1
        else:
            return 0.9

    data['reviews_coef'] = data['reviews'].apply(count_to_rate)
    return data


def calculate_final_score(data):
    """
    Вычисляет итоговый рейтинг для каждого заведения.
    """
    # Рейтинг заведения делится на 2, чтобы уменьшить влияние на итоговый скор
    data['final_score'] = data['rating'] * data['reviews_coef'] / 2 + data['rate']
    return data


def filter_by_avg_bill(data, avg_bill_range):
    """
    Фильтрует данные по среднему чеку.
    """
    min_bill, max_bill = map(int, avg_bill_range.split('-'))
    return data[(data['avg_bill'] > min_bill) & (data['avg_bill'] < max_bill)]


def filter_by_route_duration(data, time_before_meet):
    """
    Фильтрует данные по времени до встречи.
    """
    return data[data['route_duration'] * 2 + 45 < time_before_meet]  # Путь туда-обратно и 45 минут на обед


def recommend_restaurants(data, preferences, top_n=7):
    """
    Основная функция для рекомендации ресторанов.
    Работает как для одного пользователя, так и для комнаты.
    """
    # Применяем предпочтения
    data = apply_preferences(data, preferences)

    # Вычисляем рейтинг на основе предпочтений
    data = calculate_rate(data)

    # Вычисляем коэффициент на основе отзывов
    data = calculate_reviews_coefficient(data)

    # Вычисляем итоговый рейтинг
    data = calculate_final_score(data)

    # Фильтруем по среднему чеку
    data = filter_by_avg_bill(data, preferences['avg_bill'])

    # Фильтруем по времени до встречи
    data = filter_by_route_duration(data, preferences['time_before_meet'])

    # Сортируем по итоговому рейтингу и возвращаем топ-N ресторанов
    return data.sort_values(by=['final_score'], ascending=False).head(top_n)


def format_recommendations(recommended_restaurants):
    """
    Форматирует рекомендации в виде словаря.
    """
    recommendations_dict = {}
    for idx, row in recommended_restaurants.iterrows():
        recommendations_dict[idx] = {
            'name': row['name'],
            'address': row['address'],
            'coordinates': row['coordinates'],
            'rating': row['rating'],
            'reviews': row['reviews'],
            'categories': row['categories'],
            'avg_bill': row['avg_bill'],
            'cuisine': row['cuisine'],
            'assortment': row['assortment'],
            'photo_url': row['photo_url'],
            'route_duration': row['route_duration'],
            'final_score': row['final_score']
        }
    return recommendations_dict


if __name__ == "__main__":
    # Пример использования для одного пользователя
    user_id = 'user_1_id'
    user_preferences = {
        'cuisines': users[user_id]['cuisines'],
        'avg_bill': users[user_id]['avg_bill'],
        'time_before_meet': users[user_id]['time_before_meet']
    }
    recommendations = recommend_restaurants(df, user_preferences)
    recommendations = format_recommendations(recommendations)
    print(f"Рекомендации для пользователя {user_id}:")
    print(recommendations)

    # Пример использования для комнаты
    room_id = 'room_1_id'
    room_users = rooms[room_id]
    room_preferences = calculate_room_preferences(room_users, users)
    recommendations = recommend_restaurants(df, room_preferences)
    recommendations = format_recommendations(recommendations)
    print(f"Рекомендации для комнаты {room_id}:")
    print(recommendations)
