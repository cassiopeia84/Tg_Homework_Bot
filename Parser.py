from datetime import datetime
import requests
import bs4
from bs4 import BeautifulSoup


def get_schedule(date: datetime):

    # Argument error handler
    if date.weekday() > 5:
        return "No lessons on weekends"
    today = datetime.today()
    if (date.month not in [today.month, today.month + 1]) or (date.year != today.year):
        return "Schedule not posted for the selected date"

    # Get soup
    url = 'http://school36.murmansk.su/izmeneniya-v-raspisanii'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Get dates
    dates = [h2.get_text().split()[-2] for h2 in soup.find_all('h2') if "Расписание" in h2.get_text()]
    if str(date.day) not in dates:
        return "Schedule not posted for the selected date"

    # Get schedules in HTML format for date
    tables = [table for table in soup.find_all('tbody') if table.get_text().strip() != '']
    pos = dates.index(str(date.day))
    tables = [tables[pos * 2], tables[pos * 2 + 1]]

    # Get schedule in dict format from tables
    schedule = {}
    for table in tables:
        new_table = []
        for row in table:  # Create table with replaced colspans
            if isinstance(row, bs4.element.Tag):  # There are NavigableStrings in rows
                new_row = []
                for col in row:
                    if isinstance(col, bs4.element.Tag):  # There are NavigableStrings in cols
                        new_row.append(col.get_text().replace('\n', '').replace('\xa0', ''))
                        if 'colspan' in col.attrs:  # Replace all cols with colspan
                            for _ in range(int(col.attrs['colspan']) - 1):
                                new_row.append(col.get_text().replace('\n', '').replace('\xa0', ''))
                new_table.append(new_row)
        new_table = [[new_table[j][i] for j in range(len(new_table))] for i in range(len(new_table[0]))]  # rot90
        for row in new_table[1:]:
            schedule[row[0]] = [lesson.capitalize() for lesson in row[2:]]

    return schedule

