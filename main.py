import logging
import sqlite3

import aiogram.types as types
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token="6701467815:AAH3YpftH8bjOf5N3DPugz3k6uDV94zTRpE")
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

connection = sqlite3.connect("library.db")
cursor = connection.cursor()

back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_btn = types.KeyboardButton("Назад")
back_keyboard.add(back_btn)

main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
my_books = types.KeyboardButton("Мои книги")
library = types.KeyboardButton("Библиотека")
main_keyboard.add(library, my_books)

reading_keyboard = types.InlineKeyboardMarkup(row_width=1)
reading_btn = types.InlineKeyboardButton("Читать книгу", callback_data="reading")
reading_keyboard.add(reading_btn)


def generator(names):
    tmp_keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name in names:
        kb = types.InlineKeyboardButton(name, callback_data=f"book{name}")
        tmp_keyboard.add(kb)
    return tmp_keyboard


def add_user(id, name):
    with connection:
        return cursor.execute("INSERT INTO `users` (`userid`, `username`) VALUES (?, ?)", (id, name,))


def have_user(id):
    with connection:
        result = cursor.execute(f"SELECT * FROM `users` WHERE `userid` = {id}").fetchall()
        return bool(len(result))


def add_book(id, name_book):
    with connection:
        return cursor.execute(f"UPDATE `users` SET `reading` = {name_book} WHERE `userid` = {id}")


def get_book(id):
    with connection:
        result = cursor.execute(f"SELECT `reading` FROM `users` WHERE `userid` = {id}").fetchall()
        for row in result:
            book = row[0]
        return book


def get_books():
    with connection:
        result = cursor.execute(f"SELECT `name` FROM `books`").fetchall()
        books = []
        for row in result:
            book = row[0]
            books.append(book)
        return books

 
def get_book_info(name):
    with connection:
        result = cursor.execute("SELECT * FROM `books` WHERE `name` = ?", (name,)).fetchall()
        return result[0][1:]


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    id = message.from_user.id
    if not have_user(id):
        await bot.send_message(chat_id=id,
                               text="Здравствуйте!\nЯ ваша библиотека книг!",
                               reply_markup=main_keyboard)
        add_user(id, message.from_user.first_name)

    else:
        await bot.send_message(chat_id=id,
                               text=f"Здравствуйте, {message.from_user.first_name}",
                               reply_markup=main_keyboard)


@dp.message_handler(text=["Библиотека"])
async def library(message: types.Message):
    id = message.from_user.id
    await bot.send_message(chat_id=id,
                           text="Для выбора книги нажмите на кнопку",
                           reply_markup=back_keyboard)
    await bot.send_message(chat_id=id,
                           text="Выберите книгу",
                           reply_markup=generator(get_books()))


@dp.message_handler(text=["Мои книги"])
async def my_books(message: types.Message):
    id = message.from_user.id
    if get_book(id):
        await bot.send_message(chat_id=id,
                               text=f"Последняя ваша книга:\n"
                                    f"{get_book(id)}",
                               reply_markup=back_keyboard)
    else:
        await bot.send_message(chat_id=id,
                               text="Вы еще не читали книги",
                               reply_markup=back_keyboard)


@dp.callback_query_handler(lambda mes: mes.data[:4] == "book")
async def send_book(callback_query: types.CallbackQuery):
    id = callback_query.from_user.id
    book_name = callback_query.data[4:]
    book = get_book_info(book_name)
    name = book[0]
    path = book[1]
    info = book[2]
    media = types.MediaGroup()
    media.attach(types.InputMediaDocument(open(path, 'rb')))
    await bot.send_media_group(chat_id=id,
                               media=media)
    await bot.send_message(chat_id=id,
                           text=f"Информация о книге:\n",
                           reply_markup=back_keyboard)
    await bot.send_message(chat_id=id,
                           text=f"Название: {name}\n"
                                f"Описание: {info}",
                           reply_markup=reading_keyboard)


@dp.message_handler(text=["Назад"])
async def back(message: types.Message):
    id = message.from_user.id
    await bot.send_message(chat_id=id,
                           text="Вы вернулись в главное меню",
                           reply_markup=main_keyboard)


@dp.callback_query_handler(lambda mes: mes.data == "reading")
async def reading(callback_query: types.CallbackQuery):
    id = callback_query.from_user.id
    name = callback_query.message.text.split()
    add_book(id, name)
    await bot.send_message(chat_id=id,
                           text=f"Вы читали книгу: {name}",
                           reply_markup=back_keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
