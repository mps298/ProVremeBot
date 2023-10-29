from telebot.async_telebot import AsyncTeleBot, asyncio_helper
import asyncio
import requests
from bs4 import BeautifulSoup


TOKEN = "6752614576:AAFLvb09hR2C5irvagqid_G_RCGTRT1EJtI"
bot = AsyncTeleBot(TOKEN)


@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id,
                           "Pozdravljeni, poiskal vam bom vremensko napoved za Ljutomer, prosim počakajte...")

    url = 'https://www.pro-vreme.net/index.php?id=2000&m=76'
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
        # print(image.text)
        images.append('pro-vreme.net/' + image.get('src'))

    all_temperatures = soup.find_all('td')

    temperatures_am = []
    temperatures_pm = []
    counter = 0
    for temp in all_temperatures:
        if '°C' in temp.text and len(temp.text) < 7:
            if counter < 6:
                temperatures_am.append(temp.text)
            else:
                temperatures_pm.append(temp.text)
            counter += 1

    if not len(links) == len(temperatures_pm) == len(temperatures_am) == len(images) == len(days):
        await bot.send_message(message.chat.id, "Prišlo je do napake, prosim, poskusite kasneje")
    else:
        await bot.send_message(message.chat.id, title)
        for i in range(len(links)):
            await bot.send_photo(message.chat.id, images[i],
                                 caption=days[i] + "\n" + "<b>" + temperatures_am[i] + " / " + temperatures_pm[i]
                                         + f"</b>\n<a href='{links[i]}'>Podrobnosti</a>\n", parse_mode="html")
            i += 1


if __name__ == '__main__':
    asyncio.run(bot.polling())
