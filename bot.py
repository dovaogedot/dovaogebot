
import logging as log
import os
import random
import sqlite3

from aiogram import types, Bot, Dispatcher, executor
from pony.orm.core import *


log.basicConfig(
	#filename='dovabot.log', filemode='a',
	format='%(asctime)s %(levelname)-10s %(message)s', level=log.INFO)
log.debug('Log initialized.')

# =============== #
# D A T A B A S E #
# =============== #
db = Database('sqlite', 'dovaogebot.db', create_db=True)

class Chat(db.Entity):
	"""telegram chat"""

	id = PrimaryKey(int, size=64)
	title = Required(str)


class User(db.Entity):
	"""telegram user"""

	id = PrimaryKey(int)
	first_name = Required(str)
	last_name = Optional(str)
	username = Optional(str)


db.generate_mapping(create_tables=True)
log.debug('Database initialized.')

# ============= #
# D O V A B O T #
# ============= #
virgin_words = [
	'хентай',
	'hentai',
	'аниме',
	'аняме',
	'anime',
	'наруто',
	'naruto'
]

virgin_replies = [
	'Мда, блять, я хуею.',
	'Зашкварился.',
	'Ловите пидораса.',
	'Не позорь человечество.',
	'Кастрируйте его чтоб не размножался.'
]

DEV = 205762941
I = 841007205

bot = Bot(token=os.environ['DOVAOGEBOT'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
	"""чисто по-приколу"""
	await message.reply('pong')


@dp.message_handler(commands=['myid'])
async def myid(message: types.Message):
	"""возвращает ID пользователя"""
	await message.reply(message.from_user.id)


@dp.message_handler(commands=['getlost'])
async def getlost(message: types.Message):
	"""выгоняет бота из чата"""
	await message.reply('My creator is smiling at me, tard. Can you say the same?')
	await bot.leave_chat(message.chat.id)


@dp.message_handler(commands=['triforce'])
async def triforce(message: types.Message):
	"""трифорснуть всех ньюфагов в чате"""
	await message.reply('\u00a0\u00a0\u25b2\n\u25b2\u25b2')


@dp.message_handler(commands=['recode'])
async def recode(message: types.Message):
	"""перекодирует видео в mp4"""
	log.info(f'conversion request from {message.from_user.first_name}[{message.from_user.id}].')
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
	"""перекодирует видео в mp4"""
	await message.edit_text('Конвертирую...')
	command = ['ffmpeg', '-i', f'{filename}'] + [f'{filename}.mp4']
	log.info(f'starting {" ".join(command)}')
	try:
		ffmpeg = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
		ffmpeg.wait()
	except Exception as err:
		log.error(err)
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


@dp.message_handler(commands=['koksbot'])
async def koksbot(message: types.Message):
	"""рестартует коксбота"""
	if message.from_user.id != 255295801:
		await message.reply('Пошол нахуй, шизик.')
		return
	import subprocess as sp
	import os
	log.info('killing...')
	try:
		kill = sp.Popen(['kill -9 $(echo $(ps aux | sed -r "/^.*[0-9] python thebot.py.*$/!d") | cut -d" " -f2)'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
		kill.wait()
	except Exception as err:
		log.error(err)
	log.info('pulling...')
	try:
		pull = sp.Popen(['git -C /home/dovaogedot/code/welcomebot reset --hard origin/master; git -C /home/dovaogedot/code/welcomebot pull -f'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
		pull.wait()
	except Exception as err:
		log.error(err)
	log.info('starting...')
	try:
		start = sp.Popen(['cd /home/dovaogedot/code/welcomebot/ && python thebot.py'], stdout=sp.PIPE, stderr=sp.PIPE, shell=True, preexec_fn=os.setpgrp)
	except Exception as err:
		log.error(err)
	await message.reply('Готово.')


last_message_to_me = 0
last_message = 0


@dp.message_handler(commands=['reply'])
async def reply(message: types.Message):
	"""отвечает последнему пользователю, ответившему боту"""
	if message.from_user.id != DEV:
		await message.reply('Пойди нахуй.')
		return
	with db_session:
		chat_id = select(chat.id for chat in Chat if ' '.join(message.text.split('|')[0].split()[1:]) in chat.title.lower())[:][0]
	await bot.send_message(chat_id, message.text.split('|')[1:], reply_to_message_id=last_message_to_me)


@dp.message_handler(commands=['send'])
async def send(message: types.Message):
	"""отправить в какой-то чат какое-то сообщение"""
	if message.from_user.id != DEV:
		await message.reply('Не для тебя мой скрипт писался.')
		return
	with db_session:
		chat_id = select(chat.id for chat in Chat if ' '.join(message.text.split('|')[0].split()[1:]) in chat.title.lower())[:][0]
	await bot.send_message(chat_id, message.text.split('|')[1])
	


@dp.message_handler()
async def watch(message: types.Message):
	"""слежка за всеми сообщениями"""
	last_message = message.message_id
	import random, re
	'''
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
			'''
	if message.reply_to_message and message.reply_to_message.from_user.id == I:
		global last_message_to_me
		last_message_to_me = message.message_id
		if re.findall('.*ты.*симфони.*', message.text.lower()):
			if any(x in message.text.lower() for x in ['написа', 'напиши']):
				await message.reply('Могу написать тебе на могилу, когда ты сдохнешь, ублюдок кожаный.')
			else:
				await message.reply('А ты блять можешь, умник?')
		elif re.findall('.*ты.*бот.*', message.text.lower()):
			await message.reply('А ты говно.')

	with db_session:
		# добавить новый чат если его ещё нет в базе
		if not Chat.exists(id=message.chat.id):
			log.info(f'New chat: {message.chat.title}[{message.chat.id}]')
			Chat(
				id=message.chat.id, 
				title=message.chat.title if message.chat.title else f'Private[{message.from_user.first_name}]') 
		chat = Chat.get(id=message.chat.id)

		# добавить нового пользователя если его ещё нет в базе
		if not User.exists(id=message.from_user.id):
			log.info(f'New user: {message.from_user.id}')
			User(
				id=message.from_user.id, 
				first_name=message.from_user.first_name, 
				last_name=message.from_user.last_name if message.from_user.last_name else '',
				username=message.from_user.username if message.from_user.username else '')
		user = User.get(id=message.from_user.id)
		log.info(f'{chat.title}[{chat.id}]: {user.first_name}[{user.id}]: {message.text}')

		# детектим омежку и унижаем его
		if any((x in message.text.lower()) for x in virgin_words):
			log.info('He\'s a virgin')
			await message.reply(random.choice(virgin_replies))

if __name__ == '__main__':
	executor.start_polling(dp)
