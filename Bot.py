import telebot

import Parser
import psycopg2
import os
from datetime import datetime, timedelta

from telebot import types

token = os.environ['TOKEN']
bot = telebot.TeleBot(token)


host = os.environ['HOST']
user = os.environ['USER']
password = os.environ['PASSWORD']
db_name = os.environ['DB_NAME']

connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
connection.autocommit = True

cursor = connection.cursor()



subject = "-"

def rand():
	date_txt = datetime.today().strftime("%y.%m.%d.%H%M%S")
	splitted = date_txt.split(".")
	ran = int(splitted[0] + splitted[1] + splitted[2] + splitted[3])
	return ran



@bot.message_handler(commands=['start'])
def say_hi(message):
	bot.send_message(message.from_user.id, "Здравствуйте! Этот бот создан для записи и просмотра Ваших домашних заданий\nЧтобы узнать как им пользоваться, выберите в меню команду \"Помощь\" или напишите боту /help")
	bot.send_message(message.from_user.id, "Напишите название вашего класса\nПример: 8а\nЕсли у вас профильный класс, следует писать с учётом профиля\nПример: 11м")
	bot.register_next_step_handler(message, new_user)

def new_user(message):
	try:
		course_name = message.text
		cursor.execute(f"SELECT * FROM tg_user WHERE user_id = {message.from_user.id};")
		list = cursor.fetchall()
		if list == []:
			cursor.execute("INSERT INTO tg_user VALUES (%s, %s, %s);", (message.from_user.id, 'NULL', course_name))
		else:
			cursor.execute(f"UPDATE tg_user SET course_name = '{course_name}' WHERE user_id = {message.from_user.id}")
		bot.send_message(message.from_user.id, "Бот готов к работе")
	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Сначала напишите название вашего класса")
		bot.register_next_step_handler(message, new_user)
		#print(f"INFO: {error} in function {message.text}")

@bot.message_handler(commands=['help'])
def help(message):
	bot.send_message(message.from_user.id,
"""•Чтобы записать/посмотреть/стереть домашнее задание, выберите в меню предмет -> Выберите одно из предложенных действий\n
•Чтобы посмотреть все домашние задания на неделю, выберите в меню пункт \"Посмотреть все дз\" или напишите боту /watch_all\n
•Чтобы посмотреть домашнее задание на завтра, выберите в меню пункт \"Посмотреть дз на завтра\" или напишите боту /tomorrow_hw\n
•Чтобы посмотреть расписание на завтра, выберите в меню пункт \"Посмотреть расписание на завтра\" или напишите боту /tomorrow_schedule\n
•Чтобы стереть все домашние задания, выберите в меню пункт \"Стереть все записи\" или напишите боту /delete_all 
""")

@bot.message_handler(commands=['mathematics', 'physics', 'biology', 'chemistry', 'it', 'geography', 'russian', 'literature', 'history', 'english', 'law', 'social_sciense', 'economics', 'psychology', 'lsf'])
def subject(message):

	global subject
	subject = message.text
	subject = str(subject)[1:]

	keyboard = types.InlineKeyboardMarkup()
	watch = types.InlineKeyboardButton(text="Посмотреть дз", callback_data="watch")
	keyboard.add(watch)
	write = types.InlineKeyboardButton(text="Записать дз", callback_data="write")
	keyboard.add(write)
	delete = types.InlineKeyboardButton(text="Стереть запись", callback_data="delete")
	keyboard.add(delete)

	bot.send_message(message.from_user.id, "Выберите действие", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def buttons(call):
	global subject

	if call.data == "write":
		bot.send_message(call.message.chat.id, "Запишите дз, указав дату:")
		bot.register_next_step_handler(call.message, write_subject)
	elif call.data == "watch":
		bot.send_message(call.message.chat.id, "Напишите дату, на которую вы хотите посмотреть дз:")
		bot.register_next_step_handler(call.message, watch_subject)
	elif call.data == "delete":
		bot.send_message(call.message.chat.id, "Напишите дату, на которую было записано домашнее задание по выбранному предмету:")
		bot.register_next_step_handler(call.message, delete_subject)

def watch_subject(message):

	try:
		date = datetime.strptime(message.text, "%d.%m.%y").date()
		cursor.execute(f"SELECT homework_id FROM tg_homework WHERE user_Id = %s", [message.from_user.id])
		all_hw_id_list = cursor.fetchall()

		hw_text = []
		for hw_id_1 in all_hw_id_list:
			for hw_id in hw_id_1:
				cursor.execute(f"""SELECT hw_text FROM homework WHERE homework_id = %s AND lesson_name = %s AND hw_date = %s""", [hw_id, subject, date])
				hw_text.append(cursor.fetchall())

		while [] in hw_text:
			hw_text.remove([])

		if hw_text == []:
			bot.send_message(message.from_user.id, "Ничего не задано")
		else:
			bot.send_message(message.from_user.id, f"Дз на {date}:")
			for text in hw_text:
				bot.send_message(message.from_user.id, text[0])
	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Вы ввели данные в неверном формате\nПример правильной записи: 01.01.22\nВозможно, вы нажали кнопку на старой панели. Для корректной работы, вызовите команду ещё раз")
		print(f"INFO: {error} in function watch_subject")


def write_subject(message):

	homework_id = rand()
	try:
		splitted = message.text.split(" ", 1)
		date_txt, text = splitted[0], splitted[1]
		date = datetime.strptime(date_txt, "%d.%m.%y").date()

		cursor.execute("SELECT homework_id FROM homework WHERE lesson_name = %s AND hw_date = %s", [subject, date])
		curs = cursor.fetchall()
		if curs != []:
			hw_id = curs[0][0]
			cursor.execute("SELECT hw_text FROM homework WHERE lesson_name = %s AND hw_date = %s", [subject, date])
			hw_txt = cursor.fetchall()[0][0]

			text = hw_txt + ", " + text
			cursor.execute("DELETE FROM homework WHERE lesson_name = %s AND hw_date = %s", [subject, date])
			cursor.execute("DELETE FROM tg_homework WHERE homework_id = %s", [hw_id])

		cursor.execute("INSERT INTO homework VALUES (%s, %s, %s, %s);", [homework_id, subject, date, text])

		cursor.execute("INSERT INTO tg_homework VALUES (%s, %s);", [message.from_user.id, homework_id])
		bot.send_message(message.from_user.id, "Дз записано")

	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Вы ввели данные в неверном формате\nПример правильной записи: 01.01.22 №1,2,3")
		print(f"INFO: {error} in function write_subject")

def delete_subject(message):
	try:
		date = datetime.strptime(message.text, "%d.%m.%y").date()
		cursor.execute("SELECT homework_id FROM homework WHERE lesson_name = %s AND hw_date = %s;", [subject, date])
		homework_id = cursor.fetchall()
		cursor.execute("DELETE FROM homework WHERE lesson_name = %s AND hw_date = %s;", [subject, date])
		for hw_id in homework_id:
			cursor.execute("DELETE FROM tg_homework WHERE homework_id = %s;", [hw_id])
		bot.send_message(message.from_user.id, "Данные удалены")

	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Вы ввели данные в неверном формате\nПример правильной записи: 01.01.22 №1,2,3\nВозможно, на данную дату не записано домашнее задание")
		print(f"INFO: {error} in function delete_subject")

@bot.message_handler(commands=['watch_all'])
def show_all(message):
	names = {'mathematics': "Математика", 'physics': "Физика", 'biology': "Биология", 'chemistry': "Химия",
			 'it': "Информатика", 'geography': "География", 'russian': "Русский язык", 'literature': "Литература",
			 'history': "История", 'english': "Английский язык", 'law': "Право", 'social_sciense': "Обществознание",
			 'economics': "Экономика", 'psychology': "Психология", 'lsf': "ОБЖ"}
	dates = []
	start = 1
	today = datetime.today().date().weekday()
	if today == 6:
		for_range = 7
	elif today == 5:
		for_range, start = 8, 2
	elif today == 4:
		for_range, start = 9, 3
	else:
		for_range = 6 - today

	for plus in range(start, for_range):
		dates.append(datetime.today().date() + timedelta(days=plus))

	try:
		send = ""
		for date in dates:
			cursor.execute("SELECT homework_id FROM tg_homework WHERE user_Id = %s;", [message.from_user.id])
			with_tuples = cursor.fetchall()
			ids = tuple(tup_date[0] for tup_date in with_tuples)
			if ids != ():
				cursor.execute("SELECT lesson_name, hw_text FROM homework WHERE hw_date = %s AND homework_id IN %s;", [date, ids])
				homeworks = cursor.fetchall()
			else:
				homeworks = []
			send += f"Дз на {date}:\n"
			for lesson_hw in homeworks:
				send += f"\t\t\t•{names[lesson_hw[0]]}: {lesson_hw[1]}\n"
			if homeworks == []:
				send += "\t\t\tНичего не задано\n"
			send += "\n"
		bot.send_message(message.from_user.id, send)

	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Упс... Что-то пошло не так 	😕")
		print(f"INFO: {error} in function {message.text}")

@bot.message_handler(commands=['delete_all'])
def del_all(message):
	try:
		cursor.execute("SELECT homework_id FROM tg_homework WHERE user_Id = %s;", [message.from_user.id])
		homework_ids = cursor.fetchall()
		for homework_id in homework_ids:
			cursor.execute("DELETE FROM homework WHERE homework_id = %s;", [homework_id])
		cursor.execute("DELETE FROM tg_homework WHERE user_Id = %s;", [message.from_user.id])
		bot.send_message(message.from_user.id, "Все домашние задания удалены")
	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Упс... Что-то пошло не так 	😕")
		print(f"INFO: {error} in function {message.text}")

@bot.message_handler(commands=['tomorrow_hw'])
def watch_tomorrow_hw(message):
	try:
		names = {'mathematics': "Математика", 'physics': "Физика", 'biology': "Биология", 'chemistry': "Химия",
				 'it': "Информатика", 'geography': "География", 'russian': "Русский язык", 'literature': "Литература",
				 'history': "История", 'english': "Английский язык", 'law': "Право", 'social_sciense': "Обществознание",
				 'economics': "Экономика", 'psychology': "Психология", 'lsf': "ОБЖ"}

		date = datetime.today().date() + timedelta(days=1)
		if date.day == 6:
			date = date + timedelta(days=1)
		elif date.day == 5:
			date = date + timedelta(days=2)

		cursor.execute("SELECT homework_id FROM tg_homework WHERE user_Id = %s;", [message.from_user.id])
		bad_homework_ids = cursor.fetchall()
		homework_ids = tuple(hw_id[0] for hw_id in bad_homework_ids)

		if homework_ids == ():
			bot.send_message(message.from_user.id, f"На {date} ничего не задано")
		else:
			cursor.execute("SELECT (lesson_name, hw_text) FROM homework WHERE homework_id IN %s AND hw_date = %s;", [homework_ids, date])
			bad_tomorrow_homework = cursor.fetchall()
			tomorrow_homework = tuple(hw[0] for hw in bad_tomorrow_homework)

			send = f"Дз на {date}:\n\n"
			for homework in tomorrow_homework:
				homework = homework[1:-1]
				lesson = homework.split(',', 1)[0]
				text = homework.split(',', 1)[1]

				send += f"{names[lesson]}: {text}\n"
			if send == f"Дз на {date}:\n\n":
				send = "На завтра ничего не задано"
			bot.send_message(message.from_user.id, send)

	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Упс... Что-то пошло не так 	😕")
		print(f"INFO: {error} in function {message.text}")

@bot.message_handler(commands=['tomorrow_schedule'])
def watch_tomorrow_schedule(message):
	try:
		tom_date = datetime.today() + timedelta(days=1)
		if tom_date.weekday() == 6:
			tom_date = tom_date + timedelta(days=1)
		elif tom_date.weekday() == 5:
			tom_date = tom_date + timedelta(days=2)

		schedule = Parser.get_schedule(tom_date)
		tom_date = tom_date.date()
		if schedule != "Schedule not posted for the selected date" and schedule != "No lessons on weekends":
			cursor.execute("SELECT course_name FROM tg_user WHERE user_id = %s;", [message.from_user.id])
			course = cursor.fetchall()
			tom_sched = schedule[str(course[0][0])]

			bot.send_message(message.from_user.id, f"Расписание на {tom_date}")
			k, for_send = 1, ""
			while "" in tom_sched:
				tom_sched.remove("")
			for lesson in tom_sched:
				for_send += f"{k}. {lesson}" + "\n"
				k += 1
			bot.send_message(message.from_user.id, for_send)
		else:
			bot.send_message(message.from_user.id, "На завтра расписание не выложено")
	except(Exception, psycopg2.Error) as error:
		bot.send_message(message.from_user.id, "Упс... Что-то пошло не так 	😕 \nВозможно, вы неверно указали название вашего класса при регистрации. В таком случае выберите команду /start и укажите верное название класса")
		print(f"INFO: {error} IN FUNCTION {message.text}")


@bot.message_handler(func = lambda message: True)
def sender(message):
	mes = message.text.split('\n')
	send = ""
	if mes[0] == "Лере":
		id = 478903479
		send = mes[1]
	elif mes[0] == "Димасу":
		id = 799395562
		send = mes[1]
	elif mes[0] == "Матвею":
		id = 867731219
		send = mes[1]
	elif message.from_user.id != 813519084:
		id = 813519084
		send = str(message.from_user.id) + ": " + message.text
		bot.send_message(message.from_user.id, "Бот реагирует только на команды и кнопки")
	else:
		return 0

	bot.send_message(id, send)

"""
id-шники:
	799395562 - Димас
	478903479 - Лерчик
	867731219 - Матвей
	813519084 - Я
"""

bot.polling(none_stop=True)
