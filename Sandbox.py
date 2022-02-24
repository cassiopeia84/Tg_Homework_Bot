import os
import Parser
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import Error

host = os.environ['HOST']
user = os.environ['USER']
password = os.environ['PASSWORD']
db_name = os.environ['DB_NAME']

connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
connection.autocommit = True

cursor = connection.cursor()

try:
	names = {'mathematics': "Математика", 'physics': "Физика", 'biology': "Биология", 'chemistry': "Химия",
			 'it': "Информатика", 'geography': "География", 'russian': "Русский язык", 'literature': "Литература",
			 'history': "История", 'english': "Английский язык", 'law': "Право", 'social_sciense': "Обществознание",
			 'economics': "Экономика", 'psychology': "Психология", 'lsf': "ОБЖ"}

	date = datetime.today().date() + timedelta(days=1)

	cursor.execute("SELECT homework_id FROM tg_homework WHERE user_id = %s;", [813519084])
	bad_homework_ids = cursor.fetchall()
	homework_ids = tuple(hw_id[0] for hw_id in bad_homework_ids)
	cursor.execute("SELECT (lesson_name, hw_text) FROM homework WHERE homework_id IN %s AND hw_date = %s;", [homework_ids, date])
	bad_tomorrow_homework = cursor.fetchall()
	tomorrow_homework = tuple(hw[0] for hw in bad_tomorrow_homework)
	print(tomorrow_homework)

	s = f"Дз на {date}:\n\n"
	for homework in tomorrow_homework:
		homework = homework[1:-1]
		lesson = homework.split(',')[0]
		text = homework.split(',')[1]

		s += f"{names[lesson]}: {text}\n"
	print(s)

except(Exception, Error) as error:
	print(error)

cursor.close()
connection.close()









