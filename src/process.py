from __future__ import annotations
import re
import datetime as dt
from pathlib import Path
from typing import TextIO

PATH_VARIABLES = Path('src/variables.txt')
PATH_INPUT = Path('src/input')
PATH_OUTPUT = Path('src/output')

FMT_DT_INPUT = '%b %d, %Y %H h %M'
FMT_DT_OUTPUT = '%Y-%m-%d %H-%M'

RE_NAME = r'^([-_a-z\(\) ]+) (completed|practiced|tested)'
RE_XP = r'^\+(\d+) xp'
RE_DATE = r'^([a-z]+) (\d+), (\d+) (\d+) h (\d+)'

# Classes

class Student:
    alias: str
    name: str
    practices: set[Practice]

    def __init__(self: Student, alias: str, name: str) -> None:
        self.alias = alias
        self.name = name
        self.practices = set()

    def practices_between(self: Student, start: dt.datetime, end: dt.datetime) -> set[Practice]:
        return set(filter(lambda p: p.is_between(start, end), self.practices))
    
    def xp_between(self: Student, start: dt.datetime, end: dt.datetime) -> int:
        return sum(p.xp for p in self.practices_between(start, end))

    def __hash__(self: Student) -> int:
        return hash((self.alias, self.name))

    def __repr__(self: Student) -> str:
        return self.name

class Practice:
    student: Student
    desc: str
    xp: int
    date: dt.datetime

    def __init__(self: Practice, student: Student, desc: str, xp: int, date: dt.datetime) -> None:
        self.student = student
        self.desc = desc
        self.xp = xp
        self.date = date

    def is_between(self: Practice, start: dt.datetime, end: dt.datetime) -> bool:
        return start <= self.date <= end

    def __hash__(self: Practice) -> int:
        return hash((self.student, self.desc, self.xp, self.date.strftime(FMT_DT_OUTPUT)))
    
    def __repr__(self: Practice) -> str:
        return f'{self.student} : {self.xp} @ {self.date.strftime(FMT_DT_OUTPUT)}'

class DuolingoMarker:
    students: dict[str, Student]
    goal: int
    first_sunday: dt.date

    def __init__(self: DuolingoMarker) -> None:
        self.students = {}
        self.goal: 0
        self.first_sunday = None

    def parse_variables(self: DuolingoMarker):
        with open(PATH_VARIABLES, 'r') as f:

            lines = list(filter(None, map(str.strip, f.readlines())))
            i = 0

            while i < len(lines):
                line = lines[i]

                k, v = map(str.strip, line.split('::'))
                
                if k == 'goal':
                    self.goal = int(v)
                
                elif k == 'first sunday':
                    y, m, d = map(int, v.split('-'))
                    self.first_sunday = dt.date(y, m, d)

                elif k == 'students':
                    n = int(v)
                    for j in range(i + 1, n + i + 1):
                        line = lines[j]

                        alias, real = map(lambda s: s.strip().lower(), line.split('::'))

                        if not real:
                            real = alias

                        elif real == '-':
                            continue

                        s = Student(alias, real)
                        self.students[alias] = s
                    
                    i += n

                i += 1

    def parse_files(self: DuolingoMarker) -> None:        
        paths = PATH_INPUT.glob('*.txt')
        for path in paths:
            if path.stem.startswith('_'):
                continue

            self.parse_file(path)

    def parse_file(self: DuolingoMarker, path: Path) -> None:

        with open(path, 'r') as f:

            state = 0
            for line in clean_lines(f):

                if state == 0:
                    m = re.search(RE_NAME, line)
                    if m:
                        alias = m.group(1).strip()
                        desc = m.group(2).strip()
                        student = self.students[alias]
                        state = 1

                elif state == 1:
                    m = re.search(RE_XP, line)
                    if m:
                        xp = int(m.group(1))
                        state = 2

                elif state == 2:
                    m = re.search(RE_DATE, line)
                    if m:
                        date = dt.datetime.strptime(m.group(0).capitalize(), FMT_DT_INPUT)
                        practice = Practice(student, desc, xp, date)
                        student.practices.add(practice)
                        
                        state = 0

    def create_outputs(self: DuolingoMarker) -> None:
        for student in self.students.values():
            print(student)
            for practice in student.practices:
                print(practice)

    def create_output(self: DuolingoMarker) -> None:
        pass
    
# Functions
    
def clean_lines(f: TextIO) -> str:
    return map(str.lower, filter(None, map(str.strip, f.readlines())))

def mark() -> None:
    d = DuolingoMarker()
    d.parse_variables()
    d.parse_files()
    d.create_outputs()            

# Rewritten up to here

# output = ''
# for name in sorted(d.student_xps):
#     j_name = name.ljust(20)
#     j_full = str(d.student_xps[name]).ljust(4)
#     j_capt = str(min(d.goal, d.student_xps[name])).ljust(3)
#     output += ' : '.join([j_name, j_full, j_capt]) + '\n'

# output = '\n' + output[:-1]

# out_file = open(out_filename, 'w')
# out_file.write(output)
# out_file.close()

# print(output)
# input(f'\nSaved to {out_filename}\n\nEnter to quit')

# Run

def run() -> None:
    mark()

if __name__ == '__main__':
    run()
