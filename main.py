from aiogram import types, Dispatcher, Bot
import asyncio
import requests
from bs4 import BeautifulSoup
import datetime
from aiogram.types import ReplyKeyboardMarkup
from dotenv import load_dotenv
import os

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot)

cities = {}
previous_searches = {}


def get_keyboard(buttons_to_add, main_city='', columns=3):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    counter = 1
    if main_city in previous_searches.values() and main_city:
        keyboard.insert(main_city.strip())
        keyboard.row()
    for button in buttons_to_add:
        keyboard.insert(button)
        if not counter % columns:
            keyboard.row()
        counter += 1
    return keyboard


def get_cities():
    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    }

    response = requests.get('http://www.pro-vreme.net/index.php', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    all_cities = soup.find_all('option')
    cities = {}
    for item in all_cities:
        if '...' in item.text or '----' in item.text:
            continue
        cities[item.text] = item.get('value')

    return cities


@dp.message_handler(commands='start')
async def start(message: types.Message) -> None:
    global cities
    cities = get_cities()
    global previous_searches
    main_city = ''
    if message.chat.id in previous_searches:
        main_city = previous_searches[message.chat.id]
    keyboard = get_keyboard(buttons_to_add=cities.keys(), main_city=main_city)
    await message.answer(text="Poiskal vam bom vremensko napoved, prosim izberite mesto", reply_markup=keyboard)


@dp.message_handler(content_types='text')
async def get_data(message: types.Message) -> None:
    global cities
    text = message.text.strip()
    if not text in cities.keys():
        keyboard = get_keyboard(cities.keys())
        await message.answer(text=f"Mesto {text} žal nisem našel, prosim preverite podatke",
                             reply_markup=keyboard)
    else:
        citi_code = cities[text]
        url = 'https://www.pro-vreme.net/index.php?id=2000&m=' + citi_code

        headers = {
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        }

        response = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        title_soup = soup.find_all('p', class_='prvi')
        title_soup_2 = BeautifulSoup(str(title_soup), 'html.parser')
        titles = title_soup_2.find_all('span')
        title = 'Napoved za ' + titles[1].text

        first_int_index = -1
        for index, ch in enumerate(title):
            if ch.isdigit():
                first_int_index = index
                break
        date = datetime.date
        if not first_int_index < 0:
            day = int(title[first_int_index] + title[first_int_index + 1])
            month = int(title[first_int_index + 3] + title[first_int_index + 4])
            year = int(title[first_int_index + 6: first_int_index + 10])

            date = datetime.date(year=year, month=month, day=day)

        all_days = soup.find_all('td', class_='prikaziDan')
        days = []
        links = []
        for day in all_days:
            days.append(day.text)

        all_links = BeautifulSoup(str(all_days), 'html.parser').find_all('a')

        for link in all_links:
            link_to_add = link['href']

            link_to_add = 'https://www.pro-vreme.net' + link_to_add[1:]
            links.append(link_to_add)

        all_images = soup.find_all('img', class_='prikaziDanIcon')
        images = []

        for image in all_images:
            images.append('https://www.pro-vreme.net/' + image.get('src'))

        all_temperatures = soup.find_all('td')

        temperatures_am = []
        temperatures_pm = []
        counter = 0
        for temp in all_temperatures:
            if counter == len(links) * 2:
                break
            truth1 = len(temp.text) < 7
            truth2 = '°C' in temp.text
            truth3 = temp.text == '-'
            truth4 = truth1 and truth2
            if truth4 or truth3:
                if counter < len(links):
                    temperatures_am.append(temp.text)
                else:
                    temperatures_pm.append(temp.text)
                counter += 1

        if not len(links) == len(temperatures_pm) == len(temperatures_am) == len(images) == len(days):
            await bot.send_message(message.chat.id, "Prišlo je do napake, prosim, poskusite kasneje")
        else:
            # await bot.delete_message(message.chat.id, wait_message.id)
            await message.answer(title, reply_markup=types.ReplyKeyboardRemove())
            for i in range(len(links)):
                await bot.send_photo(message.chat.id, images[i],
                                     caption=days[i] + f", {date.day}.{date.month}\n" + "<b>" +
                                             temperatures_am[i] + " / " + temperatures_pm[i] +
                                             f"</b>\n<a href='{links[i]}'>Podrobnosti</a>\n", parse_mode="html")
                i += 1
                date = date + datetime.timedelta(days=1)

            global previous_searches
            previous_searches[message.chat.id] = text



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
