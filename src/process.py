# =============================================================================
# 
# PROCESS FROM MAIN PANEL
# 
# Make sure to set the custom date range and to save the exported csv with
# a start and end date (inclusive) like this: yyyy-mm-dd yyyy-mm-dd.csv
# 
# =============================================================================

from __future__ import annotations
import datetime as datetime
from pathlib import Path
from typing import TextIO
import csv

PATH_VARIABLES = Path(__file__).parent / 'config/variables.txt'
PATH_INPUT = Path(__file__).parent / 'input'

FMT_DT_INPUT = '%Y-%m-%d %H-%M'
FMT_DT_OUTPUT = '%Y-%m-%d %H-%M'
FMT_DATE_OUTPUT = '%Y-%m-%d (%a)'

# Classes

class Student:
    name: str
    practices: set[Practice]

    def __init__(self: Student, name: str) -> None:
        self.name = name
        self.practices = set()

    def practices_between(self: Student, start: datetime.datetime, end: datetime.datetime) -> set[Practice]:
        return set(filter(lambda p: p.is_between(start, end), self.practices))
    
    def xp_between(self: Student, start: datetime.datetime, end: datetime.datetime) -> int:
        return sum(p.xp for p in self.practices_between(start, end))

    def __hash__(self: Student) -> int:
        return hash(self.name)

    def __repr__(self: Student) -> str:
        return self.name

class Practice:
    student: Student
    desc: str
    xp: int
    date: datetime.datetime

    def __init__(self: Practice, student: Student, desc: str, xp: int, date: datetime.datetime) -> None:
        self.student = student
        self.desc = desc
        self.xp = xp
        self.date = date

    def is_between(self: Practice, start: datetime.datetime, end: datetime.datetime) -> bool:
        return start <= self.date <= end

    def __hash__(self: Practice) -> int:
        return hash((self.student, self.desc, self.xp, self.date.strftime(FMT_DT_OUTPUT)))
    
    def __repr__(self: Practice) -> str:
        return f'{self.student} : {self.xp} @ {self.date.strftime(FMT_DT_OUTPUT)}'

class DuolingoMarker:
    students: dict[str, Student]
    aliases: dict[str, Student]
    goal: int
    bonus_weeks: set[datetime.date]
    dates: set[datetime.date]

    def __init__(self: DuolingoMarker) -> None:
        self.students = {}
        self.aliases = {}
        self.goal: 0
        self.bonus_weeks = set()
        self.dates = set()

    def parse_variables(self: DuolingoMarker):
        with open(PATH_VARIABLES, 'r') as f:

            lines = list(filter(lambda L: L and not L.startswith(';'), map(str.strip, f.readlines())))
            i = 0

            while i < len(lines):
                line = lines[i]

                k, v = map(str.strip, line.split('::'))
                
                if k == 'goal':
                    self.goal = int(v)

                elif k == 'bonus weeks':
                    n = int(v)
                    for j in range(i + 1, n + i + 1):
                        line = lines[j]
                        y, m, d = map(int, line.split('-'))
                        sunday = datetime.date(y, m, d)
                        self.bonus_weeks.add(sunday)                        
                    
                    i += n

                elif k == 'students':
                    n = int(v)
                    for j in range(i + 1, n + i + 1):
                        line = lines[j]

                        alias, real = map(lambda s: s.strip().lower(), line.split('::'))

                        if not real:
                            real = alias

                        elif real == '-':
                            continue

                        s = self.students.setdefault(real, Student(real))
                        self.aliases[alias] = s
                    
                    i += n

                i += 1

    def parse_input_files(self: DuolingoMarker) -> None:        
        paths = PATH_INPUT.glob('*.csv')
        for path in paths:
            if path.stem.startswith('_'):
                continue

            self.parse_input_file(path)

    def parse_input_file(self: DuolingoMarker, path: Path) -> None:

        ts_start, ts_end = path.stem.split()
        dt_start = datetime.datetime.strptime(f'{ts_start} 00-00', FMT_DT_INPUT)
        dt_end = datetime.datetime.strptime(f'{ts_end} 11-59', FMT_DT_INPUT)

        self.dates.add(datetime.date(dt_start.year, dt_start.month, dt_start.day))
        self.dates.add(datetime.date(dt_end.year, dt_end.month, dt_end.day))

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)

            for row in reader:
                alias = row[0]
                xp = int(row[10])
                dt = dt_start
                
                student = self.aliases[alias.lower()]
                desc = f'Main panel week summary {ts_start} to {ts_end}'

                practice = Practice(student, desc, xp, dt)
                student.practices.add(practice)
 
    def show_weeks(self: DuolingoMarker) -> None:
        weeks = self.get_weeks()
        if not weeks:
            print('No data found')
            return
        
        numbers = self.get_week_numbers(weeks)

        for i in range(1, len(weeks) + 1):
            week = weeks[-i]
            number = numbers[-i]
            print()
            print(self.format_week(*week, number))

            if i < len(weeks):
                choice = input('\nEnter to show another week or Q to quit: ').strip().upper()

                if choice == 'Q':
                    break
        
        print('\nFinished')

    def get_weeks(self: DuolingoMarker) -> list[tuple[datetime.date]]:
        if not self.dates:
            return
        
        weeks = []

        start = None

        for date in sorted(self.dates):

            # Started week?
            if start is None:
                start = date
                end = None

            # Sunday?
            if date.strftime('%w') == '0':
                end = date
                weeks.append((start, end))
                start = None
        
        # Didn't end on a Sunday?
        if end is None:
            end = date
            weeks.append((start, end))

        return weeks
    
    def get_week_numbers(self: DuolingoMarker, weeks: list[tuple[datetime.date]]) -> list[str]:
        n = 1
        numbers = []

        boni = self.bonus_weeks.copy()

        for (start, end) in weeks:
            for bonus in boni:
                if start <= bonus <= end:
                    numbers.append('--')
                    boni.remove(bonus)
                    break

            else:
                numbers.append(f'{n:>2}')
                n += 1
        
        return numbers

    def format_week(self: DuolingoMarker, start: datetime.date, end: datetime.date, label: str='') -> None:
        start_dt = date_to_dt(start)
        end_dt = date_to_dt(end)

        if label:
            label += ' '

        s = f'{label}{start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}\n'

        for stu in sorted(self.students.values(), key=lambda s: s.name):
            xp = stu.xp_between(start_dt, end_dt)

            name = stu.name.title().ljust(20)
            full = str(xp).ljust(4)
            capt = str(min(self.goal, xp)).ljust(3)

            s += '\n' + ' : '.join([name, full, capt])
        
        return s
    
# Helpers
    
def date_to_dt(date: datetime.date) -> datetime.datetime:
    return datetime.datetime(date.year, date.month, date.day, 0, 0)

def dt_to_date(dt: datetime.datetime) -> datetime.date:
    return datetime.date(dt.year, dt.month, dt.day)
    
def clean_lines(f: TextIO) -> str:
    return map(str.lower, filter(None, map(str.strip, f.readlines())))

# Operations

def pick_student(d: DuolingoMarker) -> Student:
    choices = sorted(d.students)
    choice_str = ''
    for (i, name) in enumerate(choices):
        choice_str += f'{i + 1:>2}: {name}\n'
        
    print(f'Students:\n\n{choice_str}')
    number = int(input('Selection (enter number): '))
    return d.students[choices[number - 1]]

def make_marker() -> DuolingoMarker:
    d = DuolingoMarker()
    d.parse_variables()
    d.parse_input_files()
    return d

# Programs

def mark_class() -> None:
    print('Class report')
    d = make_marker()
    d.show_weeks()
    input('\nPress Enter to exit')

def mark_student() -> None:
    print('Student report')
    d = make_marker()
    s = pick_student(d)
    
    print(s)

    weeks = d.get_weeks()
    numbers = d.get_week_numbers(weeks)

    for (week, number) in reversed(list(zip(weeks, numbers))):
        start, end = week
        header = f'{number} {start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}'
        xp = s.xp_between(date_to_dt(start), date_to_dt(end))
        print(f'{header}: {xp}')

# Go

if __name__ == '__main__':
    mark_class()
    # mark_student()
