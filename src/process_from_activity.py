# =============================================================================
# 
# PROCESS FROM ACTIVITY
# 
# This is an outdated version from before October 2024, when I discovered that
# there was a discrepancy between the data from the main panel and the data
# from the activity panel. The main panel always has the same or more.
# Duolingo support, while coy, suggested that the main panel captured more
# data and was more up-to-date, yet only authentic data. Hence, this version
# is now "abandoned".
# 
# =============================================================================

from __future__ import annotations
import re
import datetime
from pathlib import Path
from typing import TextIO
from functools import total_ordering

PATH_VARIABLES = Path(__file__).parent / 'config/variables.txt'
PATH_INPUT = Path(__file__).parent / 'input'

FMT_DT_INPUT1 = '%b %d, %Y %H h %M'
FMT_DT_INPUT2 = '%b %d, %Y %I:%M %p'
FMT_DT_OUTPUT = '%Y-%m-%d %H-%M'
FMT_DT_OUTPUT_NICE = '%Y-%m-%d %H:%M'
FMT_DATE_OUTPUT = '%Y-%m-%d (%a)'

RE_NAME = r'^([-_a-z\(\)\. ]+) (completed|practiced|tested)'
RE_XP = r'^\+(\d+) xp'
RE_DATE1 = r'^([a-z]+) (\d+), (\d+) (\d+) h (\d+)'
RE_DATE2 = r'([a-z]+) (\d+), (\d+) (\d+):(\d+) (a\.m\.|p\.m\.)'

# Classes

class Student:
    name: str
    practices: set[Practice]

    def __init__(self: Student, name: str) -> None:
        self.name = name
        self.practices = set()

    def practices_between(self: Student, start: datetime.datetime, end: datetime.datetime) -> set[Practice]:
        return set(filter(lambda p: p.is_between(start, end), self.practices))
    
    def practices_between_date(self: Student, start: datetime.date, end: datetime.date) -> set[Practice]:
        return self.practices_between(date_to_dt(start), date_to_dt(end, end=True))
    
    def xp_between(self: Student, start: datetime.datetime, end: datetime.datetime) -> int:
        return sum(p.xp for p in self.practices_between(start, end))
    
    def xp_between_date(self: Student, start: datetime.date, end: datetime.date) -> int:
        return self.xp_between(date_to_dt(start), date_to_dt(end, end=True))

    def __hash__(self: Student) -> int:
        return hash(self.name)

    def __repr__(self: Student) -> str:
        return self.name

@total_ordering
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
        return f'{self.date.strftime("%a")}, {self.date.strftime(FMT_DT_OUTPUT_NICE)} : {self.xp} ({self.desc})'
    
    def format_detailed_report(self: Practice) -> str:
        return f'{self.date.strftime(FMT_DT_OUTPUT)}'

    
    def __lt__(self: Practice, other: Practice) -> bool:
        if not(isinstance(other, Practice)):
            raise TypeError('Cannot compare Practice to non-Practice')
        
        return self.date < other.date
    
    def __eq__(self: Practice, other: object) -> bool:
        if not(isinstance(other, Practice)):
            return False
        
        return self.date == other.date

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
        paths = PATH_INPUT.glob('*.txt')
        for path in paths:
            if path.stem.startswith('_'):
                continue

            self.parse_input_file(path)

    def parse_input_file(self: DuolingoMarker, path: Path) -> None:

        with open(path, 'r') as f:

            state = 0
            for line in clean_lines(f):

                if state == 0:
                    m = re.search(RE_NAME, line)
                    if m:
                        alias = m.group(1).strip()
                        desc = m.group(2).strip()
                        student = self.aliases[alias]
                        state = 1

                elif state == 1:
                    m = re.search(RE_XP, line)
                    if m:
                        xp = int(m.group(1))
                        state = 2

                elif state == 2:
                    m1 = re.search(RE_DATE1, line)
                    m2 = re.search(RE_DATE2, line)
                    if (m1 or m2):

                        if m1:
                            m = m1
                            fmt = FMT_DT_INPUT1
                        else:
                            m = m2
                            fmt = FMT_DT_INPUT2
                        
                        dt = datetime.datetime.strptime(m.group(0).capitalize().replace('.', ''), fmt)
                        date = datetime.date(dt.year, dt.month, dt.day)
                        self.dates.add(date)

                        practice = Practice(student, desc, xp, dt)
                        student.practices.add(practice)
                        
                        state = 0


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

            # print(i)
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
        if label:
            label += ' '

        s = f'{label}{start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}\n'

        for stu in sorted(self.students.values(), key=lambda s: s.name):
            xp = stu.xp_between_date(start, end)

            name = stu.name.title().ljust(20)
            full = str(xp).ljust(4)
            capt = str(min(self.goal, xp)).ljust(3)

            s += '\n' + ' : '.join([name, full, capt])
        
        return s
    
# Helpers
    
def date_to_dt(date: datetime.date, end: bool=False) -> datetime.datetime:
    if end:
        h, m = 23, 59
    else:
        h, m = 0, 0

    return datetime.datetime(date.year, date.month, date.day, h, m)

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

    print(sorted(s.practices, reverse=True))

    weeks = d.get_weeks()
    numbers = d.get_week_numbers(weeks)

    for (week, number) in reversed(list(zip(weeks, numbers))):
        start, end = week
        header = f'{number} {start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}'
        xp = s.xp_between_date(start, end)
        print(f'{header}: {xp}')

def mark_student_detailed() -> None:
    print('Detailed student report')
    d = make_marker()
    s = pick_student(d)
    
    print(s)  
    print()

    weeks = d.get_weeks()
    numbers = d.get_week_numbers(weeks)

    for (week, number) in reversed(list(zip(weeks, numbers))):      
        start, end = week
        
        if number.strip().isdigit():
            label = f'Week {number:>2}   '
        else:
            label = f'Bonus Week'

        print(f'{label} ({start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}) : {s.xp_between_date(start, end):>4} XP')
        print()

        for p in sorted(s.practices_between_date(start, end), reverse=True):
            print(f'\t{p}')
        
        print()

# Go

if __name__ == '__main__':
    mark_class()
    # mark_student()
    # mark_student_detailed()
