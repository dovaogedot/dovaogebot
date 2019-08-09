#!/usr/bin/env python
import logging as log
import os
import random
import sqlite3

from aiogram import types, Bot, Dispatcher, executor
from pony.orm.core import *


log.basicConfig(
	#filename='dovabot.log', filemode='a',
	format='%(asctime)s %(levelname)-10s %(message)s', level=log.INFO)
log.info('Log initialized.')

# =============== #
# D A T A B A S E #
# =============== #
db = Database('sqlite', 'dovaogebot.db', create_db=True)


class User(db.Entity):
	"""Telegram user."""

	id = PrimaryKey(int)
	first_name = Required(str)
	last_name = Optional(str)
	username = Optional(str)
	dick_length = Required(float, default=0)


db.generate_mapping(create_tables=True)
log.info('Database initialized.')

# ============= #
# D O V A B O T #
# ============= #
# Загрузка слов-триггеров для уменьшения писоса.
with open('virgin_words.txt', 'r', encoding='utf-8') as f:
	virgin_words = f.read().splitlines()
	log.info(f'virgin words: {", ".join(virgin_words)}')

# Загрузка ответов на слова-триггеры.
with open('virgin_replies.txt', 'r', encoding='utf-8') as f:
	virgin_replies = f.read().splitlines()
	log.info(f'virgin replies: {", ".join(virgin_replies)}')

# ID юзеров способных менять размер челнока.
authorized_dickchangers = [205762941, 185500059, ]

bot = Bot(token=os.environ['DOVAOGEBOT'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
	"""Чисто по-приколу."""
	await message.reply('pong')

@dp.message_handler(commands=['dick'])
async def hui(message: types.Message):
	"""Отвечает пользователю размером его члена."""
	with db_session:
		if User.exists(id=message.from_user.id):
			await message.reply(f'Твой писос размером %.2f см.' % User.get(id=message.from_user.id).dick_length)


@dp.message_handler(commands=['set_dick'])
async def set_dick(message: types.Message):
	"""Устанавливает размер члена пользователю, которому адресовано сообщение."""
	with db_session:
		sender = User.get(id=message.from_user.id)
		if sender.id not in authorized_dickchangers:
			await message.reply('Пошол нахуй.')
		else:
			if message.reply_to_message is None:
				target = sender
			else:
				target = User.get(id=message.reply_to_message.from_user.id) 
			try:
				target.dick_length = message.text.split()[1]
			except:
				await message.reply('Не понял. Какой размер? Можешь не мямлить?')


@dp.message_handler(commands=['myid'])
async def myid(message: types.Message):
	"""Возвращает ID пользователя."""
	await message.reply(message.from_user.id)


@dp.message_handler(commands=['top'])
async def top(message: types.Message):
	"""Показывает глобальный топ членов."""
	with db_session:
		await message.reply('\n'.join(f'{pos+1}. {user.first_name} - {"%.2f" % user.dick_length}' \
			for pos, user in enumerate(
				select(user for user in User).order_by(desc(User.dick_length))[:15])))


@dp.message_handler(commands=['getlost'])
async def top(message: types.Message):
	"""Выгоняет бота из чата."""
	await message.reply('My creator is smiling at me, tard. Can you say the same?')
	await bot.leave_chat(message.chat.id)


@dp.message_handler(commands=['triforce'])
async def triforce(message: types.Message):
	"""Трифорснуть всех ньюфагов в чате."""
	await message.reply('\u00a0\u00a0\u25b2\n\u25b2\u25b2')


@dp.message_handler(commands=['recode'])
async def recode(message: types.Message):
	"""Перекодирует видео в mp4."""
	log.info(f'Conversion request from {message.from_user.first_name}[{message.from_user.id}].')
	import subprocess as sp
	import asyncio
	import os
	if not message.reply_to_message.document:
		await message.reply('Что конвертировать?')
		return
	m = await message.reply('Скачиваю...')
	download_task = await message.reply_to_message.document.download(message.reply_to_message.document.file_id)
	await convert(m, message.reply_to_message.document.file_id)


async def convert(message, filename):
	await message.edit_text('Конвертирую...')
	command = ['ffmpeg', '-i', f'{filename}'] + [f'{filename}.mp4']
	log.info(f'Starting {" ".join(command)}')
	ffmpeg = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
	ffmpeg.wait()
	log.info('ffmpeg finished conversion.')
	await message.delete()
	with open(filename + '.mp4', 'rb') as v:
		await message.reply_to_message.reply_video(v.read())
	try:
		os.remove(filename + '.mp4')
	except Exception as err:
		log.error(err)
	try:
		os.remove(filename)
	except Exception as err:
		log.error(err)


@dp.message_handler(commands=['koks'])
async def koks(message: types.Message):
	import subprocess as sp
	import os
	start = sp.Popen(['cd /home/dovaogedot/code/welcomebot/ && python thebot.py'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True, preexec_fn=os.setpgrp)


@dp.message_handler(commands=['koksbot'])
async def koksbot(message: types.Message):
	"""Останавливает коксбота."""
	import subprocess as sp
	import os
	log.info('Killing...')
	try:
		kill = sp.Popen(['kill -9 $(echo $(ps aux | sed -r "/^.*[0-9] python thebot.py.*$/!d") | cut -d" " -f2)'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
		kill.wait()
	except Exception as err:
		log.error(err)
	log.info('Pulling...')
	try:
		pull = sp.Popen(['git -C /home/dovaogedot/code/welcomebot reset --hard origin/master; git -C /home/dovaogedot/code/welcomebot pull -f'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
		pull.wait()
	except Exception as err:
		log.error(err)
	log.info('Starting...')
	try:
		start = sp.Popen(['cd /home/dovaogedot/code/welcomebot/ && python thebot.py'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True, preexec_fn=os.setpgrp)
	except Exception as err:
		log.error(err)
	await message.reply('Готово.')


@dp.message_handler()
async def watch(message: types.Message):
	"""Слежка за всеми сообщениями."""
	import re
	urls = re.findall('https?:\/\/.+\/.*\.webm', message.text)
	if urls:
		log.info(f'URL to webm found: {urls[0]}')
		try:
			from urllib.request import urlretrieve
			from time import time
			m = await message.reply('Ща позырим чет там.')
			name = str(time()) + '.webm'
			urlretrieve(urls[0], name)
			await convert(m, name)
		except Exception as err:
			log.error(f'Could not download file from {urls[0]}. Reason: {err}')
			err.stacktrace()
	with db_session:
		# Добавить нового пользователя если его ещё нет в базе.
		if not User.exists(id=message.from_user.id):
			log.info(f'New user: {message.from_user.id}')
			User(
				id=message.from_user.id, 
				first_name=message.from_user.first_name, 
				last_name=message.from_user.last_name if message.from_user.last_name else '',
				username=message.from_user.username if message.from_user.username else '',
				dick_length=0)
		user = User.get(id=message.from_user.id)
		log.info(f'{user.first_name}[{user.id}]: {message.text}')

		# Детектим омежку и оберзаем дик, иначе увеличиваем его.
		if any((x in message.text.lower()) for x in virgin_words):
			log.info('He\'s a virgin')
			await message.reply(random.choice(virgin_replies))
			user.dick_length -= 1
			if user.dick_length < 0:
				user.dick_length = 0
		else:
			log.info(f'Increased dick of {user}.')
			user.dick_length += 0.01


executor.start_polling(dp)
