import pandas as pd


# Загрузка данных
df = pd.read_csv('../data_parsing/preprocessed_data.csv')
print(df.shape[0])

# Имитация предпочтений пользователей
users = {
    'user_1_id': {'Испанская кухня': 4.5, 'Японская кухня': 4.5, 'Средиземноморская кухня': 3.5, 'Вьетнамская кухня': 3,
                  'Греческая кухня': 3, 'Тайская кухня': 3, 'Авторская кухня': 2, 'Веганская кухня': 2,
                  'Израильская кухня': 2, 'Итальянская кухня': 2, 'Китайская кухня': 2},
    'user_2_id': {'Испанская кухня': 2, 'Японская кухня': .5, 'Средиземноморская кухня': 2, 'Вьетнамская кухня': 4,
                  'Греческая кухня': 2, 'Тайская кухня': 1, 'Авторская кухня': 2, 'Веганская кухня': 2,
                  'Израильская кухня': 3, 'Итальянская кухня': 5, 'Китайская кухня': 3}
}


def apply_user_preferences(data, user_preferences):
    """
    Применяет предпочтения пользователя к данным.
    Умножает значения столбцов, соответствующих кухням, на вес предпочтений пользователя.
    """
    for cuisine, weight in user_preferences.items():
        data[cuisine] *= weight
    return data


def calculate_rate(data):
    """
    Вычисляет рейтинг на основе предпочтений пользователя.
    Возвращает максимальное значение среди всех кухонь для каждого заведения.
    """
    cuisines_ohe = data.columns[11:]  # Столбцы с кухнями начинаются с 11-го индекса
    data['rate'] = data[cuisines_ohe].max(axis=1)
    data.drop(cuisines_ohe, axis=1, inplace=True)  # Удаляем столбцы с кухнями после вычисления рейтинга
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
    data['final_score'] = data['rating'] * data['reviews_coef'] / 2 + data['rate']
    return data


def filter_by_avg_bill(data, min_bill=500, max_bill=1000):
    """
    Фильтрует данные по среднему чеку.
    """
    data = data[(data['avg_bill'] > min_bill) & (data['avg_bill'] < max_bill)]
    print(f'После фильтррации по чеку: {data.shape[0]}')
    return data


def filter_by_route_duration(data, time_before_meet=90):
    """
    Фильтрует данные по времени до встречи.
    """
    data = data[data['route_duration'] * 2 + 45 < time_before_meet]
    print(f'После фильтрации по времени: {data.shape[0]}')
    return data


def recommend_restaurants(data, user_id, users_dict, time_before_meet=90, min_bill=500, max_bill=1000, top_n=7):
    """
    Основная функция для рекомендации ресторанов.
    """
    user_preferences = users_dict.get(user_id)

    # Применяем предпочтения пользователя
    data = apply_user_preferences(data, user_preferences)

    # Вычисляем рейтинг на основе предпочтений
    data = calculate_rate(data)

    # Вычисляем коэффициент на основе отзывов
    data = calculate_reviews_coefficient(data)

    # Вычисляем итоговый рейтинг
    data = calculate_final_score(data)

    # Фильтруем по среднему чеку
    data = filter_by_avg_bill(data, min_bill, max_bill)

    # Фильтруем по времени до встречи
    data = filter_by_route_duration(data, time_before_meet)

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
    # Пример использования
    user = 'user_1_id'
    recommendations = recommend_restaurants(df, user, users)

    # Форматируем рекомендации в виде словаря
    recommendations = format_recommendations(recommendations)

    # Выводим результат
    print(recommendations)
