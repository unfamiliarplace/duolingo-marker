from __future__ import annotations
import re
import os
import datetime as dt
from pathlib import Path

PATH_VARIABLES = Path('variables.txt')
PATH_INPUT = Path('input')
PATH_OUTPUT = Path('output')

FMT_DT_INPUT = '%b %d, %Y %H h %M'
FMT_DT_OUTPUT = '%Y-%m-%d %H-%M'

RE_NAME = r'^([-_a-z\(\) ]+) (completed|practiced|tested)'
RE_XP = r'^\+(\d+) xp'
RE_DATE = r'^([a-z]+) (\d+), (\d+)'

# Classes

class Student:
    alias: str
    name: str
    practices: set[Practice]

    def __init__(self: Student, alias: str, name: str) -> None:
        self.alias = alias
        self.name = name
        self.practices = set()

    def __hash__(self: Student) -> int:
        return hash((self.alias, self.name))

class Practice:
    student: Student
    desc: str
    xp: int
    date: dt.datetime

    def __init__(self: Practice, student: Student, desc: str, xp: int, ds: str) -> None:
        self.student = student
        self.desc = desc
        self.xp = xp
        self.date = dt.strptime(ds, FMT_DT_INPUT)
        self.student.practices.add(self)

    def __hash__(self: Practice) -> int:
        return hash((self.student, self.desc, self.xp, dt.strftime(FMT_DT_OUTPUT)))

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
        state = 0
        for line in in_file.readlines():
            line = line.strip().lower()

            if state == 0:
                m = re.search(RE_NAME, line)
                if m:
                    name = m.group(1).strip()
                    name = d.student_aliases[name]
                    state = 1

            elif state == 1:
                m = re.search(RE_XP, line)
                if m:
                    xp = int(m.group(1))
                    state = 2

            elif state == 2:
                m = re.search(RE_DATE, line)
                if m:
                    mo, day, year = list(m.groups())

                    # if date...
                    d.student_xps[name] += xp
                    
                    state = 0

        in_file.close()

    def create_outputs(self: DuolingoMarker) -> None:
        pass

    def create_output(self: DuolingoMarker) -> None:
        pass

    
# Functions

def mark() -> None:
    d = DuolingoMarker()
    d.parse_variables()
    d.parse_files()
    d.create_outputs()            

# Rewritten up to here

output = ''
for name in sorted(d.student_xps):
    j_name = name.ljust(20)
    j_full = str(d.student_xps[name]).ljust(4)
    j_capt = str(min(d.goal, d.student_xps[name])).ljust(3)
    output += ' : '.join([j_name, j_full, j_capt]) + '\n'

output = '\n' + output[:-1]

out_file = open(out_filename, 'w')
out_file.write(output)
out_file.close()

print(output)
input(f'\nSaved to {out_filename}\n\nEnter to quit')

# Run

def run() -> None:
    mark()

if __name__ == '__main__':
    run()
