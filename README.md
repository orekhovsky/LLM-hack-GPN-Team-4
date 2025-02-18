
# 🍽️ Dorcia: Рекомендательный телеграм-бот для выбора заведений

**Dorcia** — это телеграм-бот, который помогает пользователям находить наиболее подходящие заведения (рестораны, кафе и т.д.) на основе их вкусовых предпочтений. Бот использует рекомендательную систему, основанную на правилах и взвешивании параметров, чтобы предложить пользователю топ-5 заведений, которые лучше всего соответствуют его запросам.

---

### Функциональные требования 
- хранение данных о пользователе
- использование группирующей переменной "комната" для реализации коллективного посещения обеда:
   - ветвление на создание комнаты и выбор комнаты
   - реализация прав модератора для создателя комнаты:
      - получение оповещения о том, что все присоединившиеся к комнате закончили заполнение предпочтений: вывод списка присоединившихся с пометкой (стик галочки) о завершении заполнения предпочтений.
- реализация рекомендательной системы, основанной на правилах

---

## 🚀 Основные функции

1. **Опрос пользователя**:
   - Бот задаёт вопросы для уточнения вкусовых предпочтений.
   - На основе ответов формируется список кухонь с баллами, отражающими их релевантность.

2. **Рекомендации для одного пользователя**:
   - После опроса пользователь может получить топ-5 рекомендованных заведений.
   - Бот учитывает время до встречи и желательный средний чек.

3. **Режим комнаты**:
   - Пользователь может создать комнату (стать модератором) или присоединиться к существующей.
   - У каждого участника комнаты запрашиваются предпочтения (время до встречи, средний чек).
   - Бот формирует общий топ-5 заведений для всех участников комнаты.

---

## 🛠️ Составляющие проекта

### 1. **Телеграм-бот**
   - Основной интерфейс для взаимодействия с пользователем.
   - Реализован с использованием библиотеки `python-telegram-bot`.
   - **Файлы**:
     - `bot.py`: Основной скрипт для работы бота.
     - `firebase_bd/`: Папка с кодом для инициализации и работы с базой данных Firebase.
       - `db.py`: Логика взаимодействия с базой данных.
     - `qstns.py`: Вопросы для опроса пользователей.

### 2. **Парсинг данных**
   - Используется API 2GIS для получения актуальной информации о заведениях.
   - Данные включают название, адрес, рейтинг, средний чек и другие параметры.
   - **Файлы**:
     - `search_places.py`: Алгоритм для работы парсера.
     - `all_restaurants_with_route_duration.csv`: Собранные данные о ресторанах, включая время в пути.
     - `process_parsed_data.ipynb`: Обработка данных, полученных от парсера.

### 3. **Рекомендательная система**
   - Ранжирует заведения на основе предпочтений пользователя.
   - Учитывает время до встречи, средний чек и другие параметры.
   - **Файлы**:
     - `demo_recsys/`: Папка с рекомендательным алгоритмом.
       - Алгоритм выставляет бальную оценку каждому заведению и ранжирует их.

### 4. **Маршрутизация**
   - Алгоритм для сбора данных о времени пути до ресторана.
   - **Файлы**:
     - `routing/`: Папка с алгоритмом для сбора данных о времени пути.

---

## 🖥️ Как запустить проект

### 1. Запуск бота
1. Перейдите в Telegram и найдите бота **Dorcia**.
2. Начните диалог с ботом, нажав кнопку **Start**.

### 2. Прохождение опроса
1. Ответьте на несколько вопросов, чтобы уточнить ваши вкусовые предпочтения.
2. После завершения опроса вы увидите список кухонь с баллами, отражающими их релевантность.

### 3. Получение рекомендаций
- **Для одного пользователя**:
  1. Укажите время до встречи и желательный средний чек.
  2. Получите топ-5 рекомендованных заведений.

- **Для группы пользователей (режим комнаты)**:
  1. Создайте комнату или присоединитесь к существующей.
  2. Укажите время до встречи и средний чек.
  3. Получите общий топ-5 заведений для всех участников комнаты.

---

## 🛠️ Технические детали

### 1. **Телеграм-бот**
   - **Используемые технологии**:
     - **Telegram Bot API**: Для взаимодействия с пользователем через Telegram. Используется библиотека `python-telegram-bot`, которая упрощает создание и управление ботом.
     - **Firebase**: Для хранения данных о пользователях, их предпочтениях и комнатах. Используется библиотека `firebase_admin` для работы с Firestore и Realtime Database.
     - **Pandas**: Для обработки данных, таких как списки заведений и предпочтений пользователей.
     - **Модуль `qstns`**: Содержит вопросы для опроса пользователей, список кухонь и тестовые данные о заведениях.

### 2. **Парсинг данных**
   - **Используемые технологии**:
     - **API 2GIS**: Для получения актуальной информации о заведениях, включая название, адрес, рейтинг и средний чек.
     - **Requests**: Для выполнения HTTP-запросов к API 2GIS и получения данных в формате JSON.
     - **Pandas**: Для обработки и сохранения данных в формате CSV.
     - **Time**: Для управления задержками между запросами, чтобы избежать превышения лимитов API.

### 3. **Рекомендательная система**
   - **Используемые технологии**:
     - **Pandas**: Для обработки данных и ранжирования заведений на основе предпочтений пользователя. Алгоритм учитывает такие параметры, как время до встречи, средний чек и релевантность кухни.
     - **Взвешивание параметров**: Для расчёта баллов, которые определяют, насколько заведение подходит пользователю.

### 4. **Маршрутизация**
   - **Используемые технологии**:
     - **API маршрутизации**: Для сбора данных о времени пути до заведений. Используется библиотека `requests` для выполнения запросов.
     - **Folium**: Для визуализации маршрутов на карте (планируется в будущем).

## 📦 Установка и запуск

### 1. Клонируйте репозиторий
bash
git clone (https://github.com/orekhovsky/LLM-hack-GPN-Team-4)
cd dorcia-bot 
### 2. Установите зависимости
pip install -r requirements.txt
### 3. Настройте Firebase
Создайте проект в Firebase.
Скачайте файл конфигурации (serviceAccountKey.json) и поместите его в папку bot/firebase_bd.
Укажите путь к файлу в bot/firebase_bd/db.py.
### 4. Настройте API 2GIS
Получите API-ключ на сайте 2GIS.
Укажите ключ в файле data_parsing/search_places.py.
### 5. Запустите бота
python bot/bot.py
