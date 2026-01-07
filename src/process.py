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

PLACEHOLDER_SKIP = '-'
NUMBER_BONUS = '--'

WEIGHT_XP = 1
WEIGHT_CONSISTENCY = 1
MAX_BONUS = 120

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
    skips: set[str]
    goal: int
    bonus_weeks: set[datetime.date]
    dates: set[datetime.date]

    def __init__(self: DuolingoMarker) -> None:
        self.students = {}
        self.aliases = {}
        self.skips = set()
        self.goal: 0
        self.bonus_weeks = set()
        self.dates = set()

    def parse_variables(self: DuolingoMarker):
        with open(PATH_VARIABLES, 'r') as f:
            lines = list(filter(lambda L: L and not L.startswith(';'), map(str.strip, f.readlines())))

            for line in lines:
                k, v = map(str.strip, line.split('::'))
                
                if k == 'goal':
                    self.goal = int(v)

                elif k == 'bonus week end':
                    y, m, d = map(int, v.split('-'))
                    sunday = datetime.date(y, m, d)
                    self.bonus_weeks.add(sunday) 

                elif k == 'alias':

                    alias, real = map(lambda s: s.strip().lower(), v.split('=='))

                    if not real:
                        real = alias

                    elif real == PLACEHOLDER_SKIP:
                        self.skips.add(alias)
                        continue

                    s = self.students.setdefault(real, Student(real))
                    self.aliases[alias] = s

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
                # Name, Username, Email, ..., ..., ..., ..., ..., ..., Total XP, ...rest

                alias = row[1]
                xp = int(row[10])
                dt = dt_start

                if alias.lower() in self.skips:
                    continue
                
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
                    numbers.append(NUMBER_BONUS)
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

        s = f'Week {label}: {start.strftime(FMT_DATE_OUTPUT)} to {end.strftime(FMT_DATE_OUTPUT)}'

        s += "\n\nName".ljust(22) + ' : ' + "XP   : Counted\n"
        s += "=" * 37

        for stu in sorted(self.students.values(), key=lambda s: s.name):
            xp = stu.xp_between(start_dt, end_dt)

            name = stu.name.title().ljust(20)
            full = str(xp).ljust(4)
            capt = str(min(self.goal, xp)).ljust(3)

            s += '\n' + ' : '.join([name, full, capt])
        
        return s
    
    def calculate_final_report(self: DuolingoMarker) -> dict[str]:
        report = {
            'totals': {
                'xp': 0,
                'weeks': 0,
            },
            'averages': {
                'total xp': 0,
                'weekly xp': 0,
                '100% weeks': 0,
                '50% weeks': 0,
                'xp mark': 0,
                'consistency mark': 0,
            },
            'students': {}
        }

        weeks = self.get_weeks()
        numbers = self.get_week_numbers(weeks)

        report['totals']['weeks'] = sum(n is not NUMBER_BONUS for n in numbers)
        report['totals']['xp'] = self.goal * report['totals']['weeks']

        # Convert week dates to dts for practice comparisons...
        # Can't be done earlier because bonus uses dates...
        # TODO reconcile
        weeks = list((date_to_dt(s), date_to_dt(e)) for (s, e) in weeks)

        for stu in self.students.values():
            xps = []
            for (start_d, end_d) in weeks:
                xps.append(stu.xp_between(start_d, end_d))
            
            report['students'][stu.name] = self.get_student_stats(stu, xps)

        n = len(self.students)
        for key in report['averages']:
            report['averages'][key] = round(sum(s[key] for s in report['students'].values()) / n)

        return report
    
    def get_student_stats(self: DuolingoMarker, student: Student, xps: list[int]) -> dict[str, int]:
        """
        total xp, average xp per week, # of weeks w/ full xp, # of weeks w/ half xp
        final XP mark, final consistency mark
        comment
        """
        d = {}

        # Bases
        xp_goal = self.goal * len(xps)
        xp = sum(xps)
        wk = len(xps)

        # Stats
        d['total xp'] = xp
        d['weekly xp'] = xp / wk
        d['100% weeks'] = sum(x >= self.goal for x in xps)
        d['50% weeks'] = sum(x >= (self.goal / 2) for x in xps) - d['100% weeks']

        # Marks
        # =MIN($B$5 / 100, MIN(I2 / $F$2, 1) + ((MAX(I2, $F$2) - $F$2) / ($B$2 * 100)))
        d['xp mark'] = min(
            MAX_BONUS / 100,
            min(xp / xp_goal, 1) + (max(xp, xp_goal) - xp_goal) / (self.goal * 100)
        )
        d['xp mark'] = round(100 * d['xp mark'])

        # =MIN($B$5 / 100, ( (I4/$F4) + (I5/$F5) ) / 2)
        d['consistency mark'] = min(
            MAX_BONUS / 100,
            (d['100% weeks'] / wk) + ((d['50% weeks'] / wk) / 2)
        )
        d['consistency mark'] = round(100 * d['consistency mark'])

        # Comments
        d['xp comment'] = f"Of the overall goal of {xp_goal} XP, you earned {xp}."
        d['consistency comment'] = self.format_consistency_comment(wk, d['100% weeks'], d['50% weeks'])

        return d
    
    def format_consistency_comment(self: DuolingoMarker, n: int, full: int, half: int) -> str:
        s = ""
        s += f"Of the overall goal of {n} weeks of practice: "

        if full == 0:
            s += "You did not earn the full XP goal in any week."
        elif full == 1:
            s += "You earned the full XP goal in one of them."
        elif 1 < full < n:
            s += f"You earned the full XP goal in {full} of them."
        else:
            s += "You earned the full XP goal in all of them."
        
        if half == 1:
            s += "You also earned half the XP goal in one of the weeks."
        elif 1 < half < n:
            s += f"You also earned half the XP goal in {half} of the weeks."
        else:
            s += "You earned half or more of the XP goal in all of the weeks."
        
        if (full + half) > n:
            s += " (The total is higher than {n} because you also earned XP during weeks when it was not required.)"

        return s

    def format_final_report(self: DuolingoMarker) -> str:
        s = ""

        report = self.calculate_final_report()

        # Totals
        totals = report['totals']
        s += '\nTOTALS\n'
        s += f"\nXP goal:      {totals['xp']} ({round(totals['xp'] / totals['weeks'])} per week)"
        s += f"\n# weeks goal: {totals['weeks']}"

        # Averages
        averages = report['averages']
        s += '\n\nAVERAGES\n'

        s += f"\nTotal XP earned:  {averages['total xp']}"
        s += f"\nWeekly XP earned: {averages['weekly xp']}"
        s += f"\n100% weeks:       {averages['100% weeks']}"
        s += f"\n50% weeks:        {averages['50% weeks']}"
        s += f"\nXP mark:          {averages['xp mark']}%"
        s += f"\nConsistency mark: {averages['consistency mark']}%"

        # Student XP marks
        s += "\n\nSTUDENT XP MARKS"
  
        for stu in sorted(self.students.values(), key=lambda s: s.name):
            stats = None

        # Student consistency marks
        s += "\n\nSTUDENT CONSISTENCY MARKS"
  
        for stu in sorted(self.students.values(), key=lambda s: s.name):
            stats = None

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

def do_final_report() -> None:
    print('Final report')
    d = make_marker()
    print(d.format_final_report())
    input('\nPress Enter to exit')

def do_weekly_class_report() -> None:
    print('Weekly class report')
    d = make_marker()
    d.show_weeks()
    input('\nPress Enter to exit')

def do_weekly_student_report() -> None:
    print('Weekly student report')
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
    # do_weekly_class_report()
    # do_weekly_student_report()
    do_final_report()
