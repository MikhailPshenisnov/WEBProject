import asyncio
import datetime
import random
from discord.ext import commands
import requests
import json

# Различные нужные штуки для работы бота
BOT_TOKEN = ""
WEATHER_URL = "https://api.weather.yandex.ru/v2/forecast/"
WEATHER_API_KEY = "5daaf3dc-2d98-4b4b-bb36-0a4ebb09b9e1"
GEOCODER_URL = "http://geocode-maps.yandex.ru/1.x/"
GEOCODER_API_KEY = "40d1649f-0493-4b70-98ba-98533de7710b"
TRANSLATOR_URL = "https://translated-mymemory---translation-memory.p.rapidapi.com/api/get"
GIPHY_URL = "http://api.giphy.com/v1/gifs/random"
GIPHY_API_KEY = "C9Bd3b8hQiliSq1hsCbFXFzODfG2gf3E"
NASA_URL = "https://api.nasa.gov/planetary/apod?api_key=UcGdVRNdCFPc8feegkidfxyOrZkxTzPfd3ZzHgEe"

# Текстовые реплики бота
with open('texts.json', encoding="utf8") as file:
    TEXTS = json.load(file)


# Вспомогательный бот
class MyBot(commands.Bot):
    def __init__(self, prefix="!!"):
        super().__init__(command_prefix=prefix)

    # Функция здоровается при включении бота
    async def on_ready(self):
        await self.guilds[0].channels[1].send(TEXTS["hello_text"][0])
        await self.guilds[0].channels[1].send(TEXTS["hello_text"][1])


# Основной бот
class AnatolyBot(commands.Cog):
    # Флаги разделов и параметры по умолчанию
    def __init__(self, bot):
        self.bot = bot
        self.main_flag = True
        self.entertainment_flag = False
        self.useful_things_flag = False
        self.clock_flag = False
        self.translator_flag = False
        self.weather_flag = False
        self.maps_flag = False
        self.poet_flag = False
        self.nasa_flag = False
        self.gif_flag = False
        self.magic_of_numbers_flag = False
        self.quotes_flag = False
        self.translator_lang = "ru|en"
        self.weather_cur_place = "Москва"
        self.weather_cur_coords = self.get_coords(self.weather_cur_place)
        self.map_zoom = 15

    # Возвращает координаты по адресу, если ничего не нашлось возвращается ошибка
    def get_coords(self, place):
        params = {"apikey": GEOCODER_API_KEY,
                  "geocode": place,
                  "format": "json"}
        response = requests.get(GEOCODER_URL, params=params)
        if response:
            json_response = response.json()
            if json_response["response"]["GeoObjectCollection"]["featureMember"]:
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                if toponym:
                    coords = [float(x) for x in toponym["Point"]["pos"].split()]
                    return coords.copy()
        return ValueError

    # Возвращает фотографию карты по адресу или сообщение об ошибке если ничего не нашлось
    def get_map(self, place):
        try:
            place_coords = self.get_coords(place)
            if place_coords == ValueError:
                raise ValueError
            map_request = f"https://static-maps.yandex.ru/1.x/?ll={place_coords[0]},{place_coords[1]}&" \
                          f"l=map&pt={place_coords[0]},{place_coords[1]},pm2rdm&z={self.map_zoom}"
            return map_request
        except Exception:
            return "Что-то пошло не так, повторите снова :confused:"

    # Возвращает краткую информацию о месте и карту по адресу или сообщение об ошибке если ничего не нашлось
    def get_place_info(self, place):
        try:
            params = {"apikey": GEOCODER_API_KEY,
                      "geocode": place,
                      "format": "json"}
            response = requests.get(GEOCODER_URL, params=params)
            if response:
                json_response = response.json()
                if json_response["response"]["GeoObjectCollection"]["featureMember"]:
                    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                    if toponym:
                        try:
                            name = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                        except Exception:
                            name = "*Не найдено*"
                        try:
                            postalcode = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                        except Exception:
                            postalcode = "*Не найдено*"
                        try:
                            coords = " ".join(reversed(toponym["Point"]["pos"].split()))
                        except Exception:
                            coords = "*Не найдено*"
                        place_map = self.get_map(name)
                        if place_map == "Что-то пошло не так, повторите снова :confused:":
                            place_map = "Карта не найдена"
                        return f"Место: {name} (Почтовый индекс: {postalcode})\n" \
                               f"Координаты: {coords}\n{place_map}"
            raise ValueError
        except Exception:
            return "Ничего не нашось :confused:"

    # Возвращает прогноз погоды на days дней
    def get_weather_info(self, days=1):
        params = {"lat": self.weather_cur_coords[1],
                  "lon": self.weather_cur_coords[0],
                  "lang": "ru_RU",
                  "limit": days,
                  "hours": False,
                  "extra": False}
        headers = {"X-Yandex-API-Key": WEATHER_API_KEY}
        response = requests.get(WEATHER_URL, headers=headers, params=params).json()
        return response

    # Возвращает переведенный текст, есть 2 режима работы, при использовании функции
    # переводчиком язык задается параметром, в остальных случаях используется лишь en|ru
    def translate_text(self, text, lang=None):
        if not lang:
            lang = self.translator_lang
        try:
            querystring = {"langpair": lang,
                           "q": text}
            headers = {'x-rapidapi-key': "76f8b82787msha96867be9203970p19bcbbjsn63c7162fa51f",
                       'x-rapidapi-host': "translated-mymemory---translation-memory.p.rapidapi.com"}
            response = requests.request("GET", TRANSLATOR_URL, headers=headers, params=querystring).json()
            return response["matches"][0]["translation"]
        except Exception:
            return None

    # Команда !!info печатает в чат информацию о текущей функции или разделе
    @commands.command(name="info")
    async def info(self, ctx):
        if self.main_flag:
            await ctx.send(TEXTS["info"]["main_info"][0])
            await ctx.send(TEXTS["info"]["main_info"][1])
        elif self.useful_things_flag:
            await ctx.send(TEXTS["info"]["useful_things_info"][0])
        elif self.entertainment_flag:
            await ctx.send(TEXTS["info"]["entertainment_info"][0])
        elif self.clock_flag:
            await ctx.send(TEXTS["info"]["clock_info"][0])
        elif self.translator_flag:
            await ctx.send(TEXTS["info"]["translator_info"][0])
        elif self.weather_flag:
            await ctx.send(TEXTS["info"]["weather_info"][0])
        elif self.maps_flag:
            await ctx.send(TEXTS["info"]["maps_info"][0])
        elif self.poet_flag:
            await ctx.send(TEXTS["info"]["poet_info"][0])
        elif self.nasa_flag:
            await ctx.send(TEXTS["info"]["nasa_info"][0])
        elif self.magic_of_numbers_flag:
            await ctx.send(TEXTS["info"]["magic_of_numbers_info"][0])
        elif self.quotes_flag:
            await ctx.send(TEXTS["info"]["quotes_info"][0])
        elif self.gif_flag:
            await ctx.send(TEXTS["info"]["gif_info"][0])

    # Команда !!about_us печатает в чат общую информацию о боте и разработчиках
    @commands.command(name="about_us")
    async def about_us(self, ctx):
        if self.main_flag:
            await ctx.send(TEXTS["about_us"][0])

    # Возвращает пользователя в главное меню из разделов Полезных Полезностей и Развлечений
    @commands.command(name="main_menu")
    async def main_menu(self, ctx):
        if self.useful_things_flag:
            self.useful_things_flag = False
            self.main_flag = True
            await ctx.send('Вы вернулись в главное меню.')
            await self.info(ctx)
        if self.entertainment_flag:
            self.entertainment_flag = False
            self.main_flag = True
            await ctx.send('Вы вернулись в главное меню.')
            await self.info(ctx)

    # Перемещает пользователя в раздел Полезных Полезностей из главного меню
    # или возвращает в него из других подразделов раздела
    @commands.command(name="useful_things")
    async def useful_things(self, ctx):
        if self.main_flag:
            self.main_flag = False
            self.useful_things_flag = True
            await ctx.send('Вы перешли в раздел полезных полезностей.')
            await self.info(ctx)
        if self.clock_flag:
            self.clock_flag = False
            self.useful_things_flag = True
            await ctx.send('Вы вернулись в раздел полезных полезностей.')
            await self.info(ctx)
        if self.translator_flag:
            self.translator_flag = False
            self.useful_things_flag = True
            await ctx.send('Вы вернулись в раздел полезных полезностей.')
            await self.info(ctx)
        if self.weather_flag:
            self.weather_flag = False
            self.useful_things_flag = True
            await ctx.send('Вы вернулись в раздел полезных полезностей.')
            await self.info(ctx)
        if self.maps_flag:
            self.maps_flag = False
            self.useful_things_flag = True
            await ctx.send('Вы вернулись в раздел полезных полезностей.')
            await self.info(ctx)

    # Перемещает пользователя в подраздел "Часы"
    @commands.command(name="clock")
    async def clock(self, ctx):
        if self.useful_things_flag:
            self.clock_flag = True
            self.useful_things_flag = False
            await ctx.send('Вы перешли в функцию "Часы"')
            await self.info(ctx)

    # Заводит таймер на N минут M секунд, не мешает работоспособности бота,
    # в конце пишет сообщение об окончании таймера
    @commands.command(name="set_timer")
    async def set_timer(self, ctx, time):
        if self.clock_flag:
            try:
                minutes = int(time.split(":")[0])
                seconds = int(time.split(":")[1])
                if minutes < 0:
                    minutes = 0
                if seconds < 0:
                    seconds = 0
                if seconds > 59:
                    seconds = 59
                if minutes == 0 and seconds == 0:
                    raise ValueError
                time = minutes * 60 + seconds
                await ctx.send(f"Таймер сработает через {minutes} минут и {seconds} секунд.")
                await asyncio.sleep(time)
                await ctx.send(f":alarm_clock: Динь! Динь! Динь! Таймер завершен :alarm_clock:")
            except Exception:
                await ctx.send("Таймер не может быть установлен - что-то пошло не так :confused:")

    # Печатает текущую дату
    @commands.command(name="current_date")
    async def current_date(self, ctx):
        if self.clock_flag:
            current_date = datetime.datetime.now().date()
            year = current_date.year
            month = current_date.month
            day = current_date.day
            await ctx.send(f"Сегодня {day}.{month}.{year}")

    # Печатает текущее время
    @commands.command(name="current_time")
    async def current_time(self, ctx):
        if self.clock_flag:
            current_time = datetime.datetime.now().time()
            hours = current_time.hour
            minutes = current_time.minute
            seconds = current_time.second
            await ctx.send(f"Сейчас {hours}:{minutes}:{seconds}")

    # Определяет день недели по дате и печатает его
    @commands.command(name="day_of_week")
    async def day_of_week(self, ctx, date):
        if self.clock_flag:
            week_days = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
                         4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
            try:
                date = date.split(".")
                if not (len(date[0]) == 2 and len(date[1]) == 2 and len(date[2]) >= 4) or len(date) > 3:
                    raise ValueError
                day = int(date[0])
                month = int(date[1])
                year = int(date[2])
                week_day = datetime.datetime(year=year, month=month, day=day).weekday()
                await ctx.send(week_days[week_day])
            except Exception:
                await ctx.send("Что-то пошло не так, попробуйте снова :confused:")

    # Перемещает пользователя в подраздел "Переводчик"
    @commands.command(name="translator")
    async def translator(self, ctx):
        if self.useful_things_flag:
            self.translator_flag = True
            self.useful_things_flag = False
            await ctx.send('Вы перешли в функцию "Переводчик"')
            await self.info(ctx)

    # Изменяет язык перевода (Доступны ru, en, fr, de, но не один и тот же)
    @commands.command(name="set_lang")
    async def set_lang(self, ctx, lang):
        if self.translator_flag:
            try:
                langs = ["en", "ru", "de", "fr"]
                lang = lang.split("|")
                if len(lang) != 2:
                    raise ValueError
                lang1 = lang[0]
                lang2 = lang[1]
                if lang1 not in langs or lang2 not in langs or lang1 == lang2:
                    raise ValueError
                self.translator_lang = f"{lang1}|{lang2}"
                await ctx.send(f"Язык перевода {self.translator_lang}")
            except Exception:
                await ctx.send("Что-то пошло не так, попробуйте снова :confused:")

    # Переводит текст пользователя
    @commands.command(name="translate")
    async def translate(self, ctx, *text):
        if self.translator_flag:
            translated_text = self.translate_text(" ".join(text))
            if translated_text:
                await ctx.send(translated_text)
            else:
                await ctx.send("Что-то пошло не так, попробуйте снова :confused:")

    # Перемещает пользователя в подраздел "Переводчик"
    @commands.command(name="weather")
    async def weather(self, ctx):
        if self.useful_things_flag:
            self.weather_flag = True
            self.useful_things_flag = False
            await ctx.send('Вы перешли в функцию "Погода"')
            await self.info(ctx)

    # Устанавливает место прогноза (По умолчанию установлена Москва)
    @commands.command(name="set_place")
    async def set_place(self, ctx, *place):
        if self.weather_flag:
            try:
                coords = self.get_coords(" ".join(place))
                if coords == ValueError:
                    raise ValueError
                self.weather_cur_place = " ".join(place)
                self.weather_cur_coords = coords
                await ctx.send(f"Место изменено на {self.weather_cur_place}")
            except Exception:
                await ctx.send(f"Что-то пошло не так :confused:")

    # Выводит информацию о погоде в заданном месте
    @commands.command(name="current_weather")
    async def current_weather(self, ctx):
        if self.weather_flag:
            try:
                response = self.get_weather_info()['fact']
                temp = response['temp']
                pressure = response['pressure_mm']
                humidity = response['humidity']
                condition = response['condition']
                wind_dir = response['wind_dir']
                wind_seed = response['wind_speed']
                await ctx.send(f"Погода в '{self.weather_cur_place}' сейчас:\n"
                               f"Температура: {temp} °C;\n"
                               f"Давление: {pressure} мм рт. ст.;\n"
                               f"Влажность воздуха: {humidity} %;\n"
                               f"Состояние: {condition};\n"
                               f"Ветер: {wind_dir}, {wind_seed} м/с.")
            except Exception:
                await ctx.send(f"Что-то пошло не так :confused:")

    # Выводит информацию о погоде на N дней (От 1 до 7)
    @commands.command(name="forecast")
    async def forecast(self, ctx, days):
        if self.weather_flag:
            try:
                if len(days) != 1:
                    raise ValueError
                days = int(days[0])
                if days < 1 or days > 7:
                    raise ValueError
                answer = []
                response = self.get_weather_info(days=days)['forecasts']
                for forecast in response:
                    date = forecast['date']
                    day = forecast['parts']['day']
                    temp = day['temp_avg']
                    pressure = day['pressure_mm']
                    humidity = day['humidity']
                    condition = day['condition']
                    wind_dir = day['wind_dir']
                    wind_seed = day['wind_speed']
                    answer.append(f"Погода в '{self.weather_cur_place}' {date} днём:\n"
                                  f"Температура: {temp} °C;\n"
                                  f"Давление: {pressure} мм рт. ст.;\n"
                                  f"Влажность воздуха: {humidity} %;\n"
                                  f"Состояние: {condition};\n"
                                  f"Ветер: {wind_dir}, {wind_seed} м/с.")
                await ctx.send("\n\n".join(answer))
            except Exception:
                await ctx.send(f"Что-то пошло не так, количество дней должно "
                               f"быть от 1 до 7 включительно, попробуйте сновы :confused:")

    # Перемещает пользователя в подраздел "Карты"
    @commands.command(name="maps")
    async def maps(self, ctx):
        if self.useful_things_flag:
            self.maps_flag = True
            self.useful_things_flag = False
            await ctx.send('Вы перешли в функцию "Карты"')
            await self.info(ctx)

    # Устанавливает коэф увеличения для карты (число от 1 до 18) (по умолчанию 15)
    @commands.command(name="set_map_zoom")
    async def set_map_zoom(self, ctx, zoom):
        if self.maps_flag:
            try:
                if self.maps_flag:
                    zoom = int(zoom)
                    if not (1 <= zoom <= 18):
                        raise ValueError
                    self.map_zoom = zoom
                    await ctx.send(f"Значение Zoom установлено на {self.map_zoom}.")
            except Exception:
                await ctx.send("Значение Zoom должно быть целочисленным числом от 1 до 18 включительно.")

    # Выводит пользователю карту места по адресу
    @commands.command(name="show_place")
    async def show_place(self, ctx, *place):
        if self.maps_flag:
            await ctx.send(self.get_map(" ".join(place)))

    # Выводит краткую информацию о месте и карту по адресу
    @commands.command(name="get_info")
    async def get_info(self, ctx, *place):
        if self.maps_flag:
            await ctx.send(self.get_place_info(" ".join(place)))

    # Перемещает пользователя в раздел Развлечений из главного меню или
    # возвращает в него из других подразделов раздела
    @commands.command(name="entertainment")
    async def entertainment(self, ctx):
        if self.main_flag:
            self.main_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы перешли в раздел развлечений.')
            await self.info(ctx)
        if self.poet_flag:
            self.poet_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы вернулись в раздел развлечений.')
            await self.info(ctx)
        if self.nasa_flag:
            self.nasa_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы вернулись в раздел развлечений.')
            await self.info(ctx)
        if self.magic_of_numbers_flag:
            self.magic_of_numbers_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы вернулись в раздел развлечений.')
            await self.info(ctx)
        if self.quotes_flag:
            self.quotes_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы вернулись в раздел развлечений.')
            await self.info(ctx)
        if self.gif_flag:
            self.gif_flag = False
            self.entertainment_flag = True
            await ctx.send('Вы вернулись в раздел развлечений.')
            await self.info(ctx)

    # Перемещает пользователя в подраздел "Поэт"
    @commands.command(name="poet")
    async def poet(self, ctx):
        if self.entertainment_flag:
            self.poet_flag = True
            self.entertainment_flag = False
            await ctx.send('Вы перешли в функцию "Поэт"')
            await self.info(ctx)

    # Зачитывает пользователю случайный стих из предложенных (построчно)
    @commands.command(name="read_random_verse")
    async def read_random_verse(self, ctx):
        if self.poet_flag:
            verse = random.choice(["stih1", "stih2", "stih3"])
            await ctx.send(TEXTS["stihi"][verse]["name"])
            await asyncio.sleep(1)
            for string in TEXTS["stihi"][verse]["text"]:
                await ctx.send(string)
                await asyncio.sleep(2)

    # Зачитывает пользователю конкретный стих из предложенных (построчно)
    @commands.command(name="read_verse")
    async def read_verse(self, ctx, n):
        if self.poet_flag:
            try:
                n = int(n)
                if n < 1 or n > 3:
                    raise ValueError
                verse = ["stih1", "stih2", "stih3"][n - 1]
                await ctx.send(TEXTS["stihi"][verse]["name"])
                await asyncio.sleep(1)
                for string in TEXTS["stihi"][verse]["text"]:
                    await ctx.send(string)
                    await asyncio.sleep(2)
            except Exception:
                await ctx.send("Некорректный номер стиха")

    # Перемещает пользователя в подраздел "NASA"
    @commands.command(name="NASA")
    async def nasa(self, ctx):
        if self.entertainment_flag:
            self.nasa_flag = True
            self.entertainment_flag = False
            await ctx.send('Вы перешли в функцию "NASA"')
            await self.info(ctx)

    # Показывает пользователю космическую картинку дня, ее название, описание, автора и дату
    @commands.command(name="photo_of_the_day")
    async def photo_of_the_day(self, ctx):
        if self.nasa_flag:
            try:
                response = requests.get(NASA_URL).json()
                try:
                    name = self.translate_text(response["title"], "en|ru")
                    if name:
                        name += f' ({response["title"]})'
                    if not name:
                        name = response["title"]
                except Exception:
                    name = "-----"
                try:
                    discription = self.translate_text(response["explanation"], "en|ru")
                    if discription:
                        discription += f' ({response["explanation"]})'
                    else:
                        discription = response["explanation"]
                except Exception:
                    discription = "-----"
                try:
                    author = response["copyright"]
                except Exception:
                    author = "-----"
                try:
                    date = response["date"]
                except Exception:
                    date = "-----"
                try:
                    photo = response["url"]
                except Exception:
                    photo = "-----"
                await ctx.send(f"{name}")
                await ctx.send(f"{photo}")
                await ctx.send(f"Описание: {discription}\nАвтор: {author}, {date}")
            except Exception:
                await ctx.send("NASA опять там что-то сломали, приходите позже :confused:")

    # Бросает кости и выводит результат (дополнительно можно указать число бросков (от 1 до 10))
    @commands.command(name="dice")
    async def dice(self, ctx, n=""):
        if self.entertainment_flag:
            try:
                if not n:
                    n = "1"
                n = int(n)
                if n < 1 or n > 10:
                    raise ValueError
                for i in range(n):
                    num = random.choice([1, 2, 3, 4, 5, 6])
                    await ctx.send(f"Выпало {num}")
            except Exception:
                await ctx.send("Значение числа кубиков должно быть целым числом от 1 до 10")

    # Бросает монетку и выводит результат (дополнительно можно указать число бросков (от 1 до 10))
    @commands.command(name="coin")
    async def coin(self, ctx, n=""):
        if self.entertainment_flag:
            try:
                if not n:
                    n = "1"
                n = int(n)
                if n < 1 or n > 10:
                    raise ValueError
                for i in range(n):
                    result = random.choice(["орёл", "решка"])
                    await ctx.send(f"Выпал(-а) {result}")
            except Exception:
                await ctx.send("Значение числа бросков должно быть целым числом от 1 до 10")

    # Перемещает пользователя в подраздел "Магия чисел"
    @commands.command(name="magic_of_numbers")
    async def magic_of_numbers(self, ctx):
        if self.entertainment_flag:
            self.magic_of_numbers_flag = True
            self.entertainment_flag = False
            await ctx.send('Вы перешли в функцию "Магия чисел"')
            await self.info(ctx)

    # Выводит интересный факт о числе
    @commands.command(name="math")
    async def random_math(self, ctx):
        if self.magic_of_numbers_flag:
            request = requests.get("http://numbersapi.com/random/math?json").json()
            text = request["text"]
            new_text = self.translate_text(text, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            await ctx.send(new_text)

    # Выводит интересный факт о мелочи
    @commands.command(name="trivia")
    async def random_trivia(self, ctx):
        if self.magic_of_numbers_flag:
            request = requests.get("http://numbersapi.com/random/trivia?json").json()
            text = request["text"]
            new_text = self.translate_text(text, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            await ctx.send(new_text)

    # Выводит интересный факт о годе
    @commands.command(name="year")
    async def random_year(self, ctx):
        if self.magic_of_numbers_flag:
            request = requests.get("http://numbersapi.com/random/year?json").json()
            text = request["text"]
            new_text = self.translate_text(text, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            await ctx.send(new_text)

    # Выводит интересный факт о дате
    @commands.command(name="date")
    async def random_date(self, ctx):
        if self.magic_of_numbers_flag:
            request = requests.get("http://numbersapi.com/random/date?json").json()
            text = request["text"]
            new_text = self.translate_text(text, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            await ctx.send(new_text)

    # Перемещает пользователя в подраздел "Цитаты"
    @commands.command(name="quotes")
    async def quotes(self, ctx):
        if self.entertainment_flag:
            self.quotes_flag = True
            self.entertainment_flag = False
            await ctx.send('Вы перешли в функцию "Цитаты"')
            await self.info(ctx)

    # Выводит пользователю цитату дня
    @commands.command(name="quote_of_the_day")
    async def quote_of_the_day(self, ctx):
        if self.quotes_flag:
            request = requests.get("https://favqs.com/api/qotd").json()
            text = request["quote"]["body"]
            author = request["quote"]["author"]
            new_text = self.translate_text(text, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            await ctx.send(new_text + f" Автор: {author}.")

    # Выводит пользователю цитату из "Во все тяжкие"
    @commands.command(name="quote_breaking_bad")
    async def quote_breaking_bad(self, ctx):
        if self.quotes_flag:
            request = requests.get("https://www.breakingbadapi.com/api/quote/random").json()
            text = request[0]["quote"]
            author = request[0]["author"]
            series = request[0]["series"]
            new_text = self.translate_text(text, "en|ru")
            new_series = self.translate_text(series, "en|ru")
            if new_text:
                new_text += f' ({text})'
            else:
                new_text = text
            if new_series:
                new_series += f' ({series})'
            else:
                new_series = series
            await ctx.send(f"{new_text} (Автор: {author}, выпуск: {new_series})")

    # Перемещает пользователя в подраздел "GIF"
    @commands.command(name="gif")
    async def gif(self, ctx):
        if self.entertainment_flag:
            self.gif_flag = True
            self.entertainment_flag = False
            await ctx.send('Вы перешли в функцию "GIF"')
            await self.info(ctx)

    # Выводит пользователю рандомную гифку
    @commands.command(name="random_gif")
    async def random_gif(self, ctx):
        if self.gif_flag:
            try:
                params = {'api_key': GIPHY_API_KEY}
                response = requests.request("GET", GIPHY_URL, params=params).json()
                gif_url = response["data"]["image_url"]
                await ctx.send(gif_url)
            except Exception:
                await ctx.send("Что-то пошло не так, попробуйте снова :confused:")

    # Ищет пользователю гифку по фразе и выводит ее
    @commands.command(name="search_gif")
    async def search_gif(self, ctx, *text):
        if self.gif_flag:
            try:
                text = " ".join(text)
                params = {'api_key': GIPHY_API_KEY,
                          'tag': text}
                response = requests.request("GET", GIPHY_URL, params=params).json()
                gif_url = response["data"]["image_url"]
                await ctx.send(gif_url)
            except Exception:
                await ctx.send("Что-то пошло не так, попробуйте снова :confused:")


bot = MyBot(prefix="!!")
bot.add_cog(AnatolyBot(bot))
bot.run(BOT_TOKEN)
