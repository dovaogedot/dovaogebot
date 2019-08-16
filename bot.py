#!/usr/bin/env python
from __future__ import annotations
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

db = Database('sqlite', 'dovaogebot.db', create_db=False)

class Chats(db.Entity):
	"""telegram chat"""
	id = PrimaryKey(int, size=64)
	title = Required(str)


class Users(db.Entity):
	"""telegram user"""
	id = PrimaryKey(int)
	first_name = Required(str)
	last_name = Optional(str)
	username = Optional(str)\


class Words(db.Entity):
	"""word"""
	name = PrimaryKey(str)
	prevs = Set('Nexts', reverse='next')
	used_first = Required(int, default=0)
	nexts = Set('Nexts', reverse='first')


class Nexts(db.Entity):
	first = Required(Words)
	next = Required(Words)
	count = Required(int, default=0)
	PrimaryKey(first, next)


db.generate_mapping(create_tables=False)
log.debug('Database initialized.')

# ============= #
# D O V A B O T #
# ============= #
virgin_words = [
	'хентай',
	'hentai',
	'аниме',
	'анимэ',
	'аняме',
	'anime',
	'наруто',
	'naruto'
]

virgin_replies = [
	'Мда, блять, я хуею.',
	'Ловите пидораса.',
	'Не позорь человечество.',
	'Кастрируйте его чтоб не размножался.',
	'>аниме\n>2k19'
]

DEV = 205762941
I = 841007205

bot = Bot(token=os.environ['DOVAOGEBOT'])
dp = Dispatcher(bot)


# дикт хранящий инфу о вызовах команд:
# key: функция
# value: time - время последнего успешного вызова команды
#        count - кол-во вызовов команды когда она в куллдауне
spam = dict()


async def on_spam(f, message: types.Message):
	"""
	что делать если тебя начинают заёбывать

	:param f: команда, которую насилуют
	:param message: собсна, сообщение адресованное боту
	"""
	from random import choice
	try:
		await choice([
			[lambda: None] * 85,
			[lambda: message.reply('Я занят.')] * 5 * spam[f][1],
			[lambda: message.reply('Заёбывай другого бота')] * 1 * spam[f][1]
		])[0]()
		spam[f][1] = 0
	except TypeError: # cannot await None
		pass


def cmd(command, cooldown=0):
	"""
	декоратор для предотвращения спама

	:param command: функция-команда
	:param cooldown: время в секундах через которое снова можно будет вызвать команду
	"""
	def wrap(f):
		async def nospam_func(message: types.Message):
			if cooldown:
				import time
				now = time.time()
				if f not in spam or now - spam[f][0] > cooldown:
					spam[f] = [now, 0]
					await f(message)
				else:
					spam[f][1] += 1
					await on_spam(f, message)
			else:
				await f(message)
		dec_f = dp.message_handler(commands=[command])(nospam_func)
		return nospam_func
	return wrap


@cmd('ping')
async def ping(message: types.Message):
	"""
	чисто по-приколу
	"""
	await message.reply('pong')


@cmd('myid')
async def myid(message: types.Message):
	"""
	возвращает ID пользователя
	"""
	await message.reply(message.from_user.id)


@cmd('getlost')
async def getlost(message: types.Message):
	"""
	выгоняет бота из чата
	"""
	await message.reply('My creator is smiling at me, tard. Can you say the same?')
	await bot.leave_chat(message.chat.id)


@cmd('triforce', 5)
async def triforce(message: types.Message):
	"""
	трифорснуть всех ньюфагов в чате
	"""
	await message.reply('\u00a0\u00a0\u25b2\n\u25b2\u25b2')


@cmd('recode', 5)
async def recode(message: types.Message):
	"""
	перекодирует видео в mp4
	"""
	log.info(f'conversion request from {message.from_user.first_name}[{message.from_user.id}].')
	import subprocess as sp
	import asyncio
	import os
	if not message.reply_to_message or not message.reply_to_message.document:
		await message.reply('Что конвертировать?')
		return
	m = await message.reply('Скачиваю...')
	download_task = await message.reply_to_message.document.download(message.reply_to_message.document.file_id)
	await _convert_from_file(m, message.reply_to_message.document.file_id)


async def _convert_from_file(message, filename):
	"""
	перекодирует видео в mp4
	"""
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


@cmd('koksbot')
async def koksbot(message: types.Message):
	"""
	рестартует коксбота
	"""
	if message.from_user.id not in [255295801, DEV]:
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


@cmd('reply_last')
async def reply_last(message: types.Message):
	"""
	отвечает последнему пользователю, написавшему в чат
	"""
	if message.from_ser.id != DEV:
		await message.reply('Пойди нахуй.')
		return
	with db_session:
		chat_id = select(chat.id for chat in Chats if ' '.join(message.text.split('|')[0].split()[1:]) in chat.title.lower())[:][0]
	await bot.send_message(chat_id, ''.join(message.text.split('|')[1:]), reply_to_message_id=last_message)


@cmd('reply')
async def reply(message: types.Message):
	"""
	отвечает последнему пользователю, ответившему боту
	"""
	if message.from_user.id != DEV:
		await message.reply('Пойди нахуй.')
		return
	with db_session:
		chat_id = select(chat.id for chat in Chats if ' '.join(message.text.split('|')[0].split()[1:]) in chat.title.lower())[:][0]
	await bot.send_message(chat_id, ''.join(message.text.split('|')[1:]), reply_to_message_id=last_message_to_me)


@cmd('send')
async def send(message: types.Message):
	"""
	отправить в какой-то чат какое-то сообщение
	"""
	if message.from_user.id != DEV:
		await message.reply('Не для тебя мой скрипт писался.')
		return
	with db_session:
		chat_id = select(chat.id for chat in Chats if ' '.join(message.text.split('|')[0].split()[1:]) in chat.title.lower())[:][0]
	await bot.send_message(chat_id, message.text.split('|')[1])


story_length = 10

@cmd('story_length')
async def _story_length(message: types.Message):
	"""
	определяет кол-во слов в генерируемых историях
	"""
	global story_length
	try:
		story_length = int(message.text.split()[1])
		await message.reply('Как скажешь.')
	except:
		await message.reply('Додик?')


@cmd('story')
async def story(message: types.Message):
	"""
	время охуительных историй
	"""
	import numpy as np, itertools as it, operator as op
	from collections import defaultdict
	with db_session:
		words = select((word.name, word.used_first, next.next.name, next.count) for word in Words for next in Nexts if word==next.first)[:]
		#vocab = dict(list((i, sum(j, tuple())) for i,j in it.groupby(words, key=op.itemgetter(0))))
		vocab = defaultdict(dict)
		for word, used_first, next, count in words:
			vocab[word]['used_first'] = used_first
			if 'nexts' not in vocab[word]:
				vocab[word]['nexts'] = dict()
			vocab[word]['nexts'][next] = count
	def make_sentence(sentence=''):
		if len(sentence.split()) > story_length:
			return sentence
		if not sentence:
			return make_sentence(np.random.choice([x for x in vocab.keys()], 1)[0])
		try:
			nexts = vocab[sentence.split()[-1]]['nexts']
		except KeyError:
			return sentence
		sum_p = sum(nexts.values())
		return make_sentence(sentence + ' ' + np.random.choice([word for word in nexts.keys()], p=[weight/sum_p for weight in nexts.values()]))
			
	await message.reply(make_sentence())



@dp.message_handler()
async def watch(message: types.Message):
	"""
	слежка за всеми сообщениями
	"""
	import random, re

	global last_message
	last_message = message.message_id

	with db_session:
		words = re.sub(r'[^\w0-9 ]+', '', message.text.lower()).split()
		for i in range(len(words)):
			if not Words.exists(lambda x: x.name==words[i]):
				Words(name=words[i])
			word = Words[words[i]]
			if i == 0:
				word.used_first += 1
			if i > 0:
				if not Nexts.exists(lambda x: x.first==Words[words[i-1]] and x.next==word):
					Nexts(first=Words[words[i-1]], next=word, count=0)
					commit()
				Nexts.get(first=Words[words[i-1]], next=word).count += 1
	
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
		if not Chats.exists(id=message.chat.id):
			log.info(f'New chat: {message.chat.title}[{message.chat.id}]')
			Chats(
				id=message.chat.id, 
				title=message.chat.title if message.chat.title else f'Private[{message.from_user.first_name}]') 
		chat = Chats[message.chat.id]

		# добавить нового пользователя если его ещё нет в базе
		if not Users.exists(id=message.from_user.id):
			log.info(f'New user: {message.from_user.id}')
			Users(
				id=message.from_user.id, 
				first_name=message.from_user.first_name, 
				last_name=message.from_user.last_name if message.from_user.last_name else '',
				username=message.from_user.username if message.from_user.username else '')
		user = Users[message.from_user.id]
		log.info(f'{chat.title}[{chat.id}]: {user.first_name}[{user.id}]: {message.text}')

		# детектим омежку и унижаем его
		if any((x in message.text.lower()) for x in virgin_words):
			log.info('He\'s a virgin')
			await message.reply(random.choice(virgin_replies))


if __name__ == '__main__':
	from asyncio import get_event_loop
	loop = get_event_loop()
	executor.start_polling(dp, loop=loop, skip_updates=True)
