from __future__ import annotations
import re
import os
import datetime

FNAME_VARIABLES = './variables.txt'

class DuolingoMarker:
    students: dict[str, Student]
    student_aliases: dict[str, str]
    student_xps: dict[str, int]
    goal: int
    first_sunday: datetime.date

    def __init__(self: DuolingoMarker) -> None:
        self.students = {}
        self.student_aliases = {}
        self.student_xps = {}
        self.goal: 0
        self.first_sunday = None

        self.parse_variables()

        for student in self.student_aliases.values():
            self.student_xps[student] = 0

    def parse_variables(self: DuolingoMarker):
        with open(FNAME_VARIABLES, 'r') as f:

            lines = list(filter(None, map(str.strip, f.readlines())))
            i = 0

            while i < len(lines):
                line = lines[i]

                k, v = map(str.strip, line.split('::'))
                
                if k == 'goal':
                    self.goal = int(v)
                
                elif k == 'first sunday':
                    y, m, d = map(int, v.split('-'))
                    self.first_sunday = datetime.date(y, m, d)

                elif k == 'students':
                    n = int(v)
                    for j in range(i + 1, n + i + 1):
                        line = lines[j]

                        duo, canonical = map(lambda s: s.strip().lower(), line.split('::'))

                        if not canonical:
                            canonical = duo

                        elif canonical == '-':
                            continue

                        self.student_aliases[duo] = canonical
                    
                    i += n

                i += 1

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
    date: datetime.datetime

    def __init__(self: Practice, student: Student, desc: str, xp: int, ds: str) -> None:
        self.student = student
        self.desc = desc
        self.xp = xp

        y, mo, d, h, mi = 0, 0, 0, 0, 0, 0 # TODO
        self.date = datetime.datetime(y, mo, d, h, mi)

        self.student.practices.add(self)

    def __hash__(self: Practice) -> int:
        return hash((self.student, self.desc, self.xp, str(datetime)))
    
# Begin

d = DuolingoMarker()

# Rewritten up to here

fnames = list(os.walk('input'))[0][2]
fnames = list(filter(lambda s: not s.startswith('_') and not s.endswith('ini'), fnames))
latest_in_filename = fnames[-1]

in_filename = input(f'Enter input filename or blank to use latest ({latest_in_filename}): ').strip()
if not in_filename:
    in_filename = latest_in_filename
    
print(f'Using {in_filename}')
in_file = open(f'input/{in_filename}', 'r')

# in_filename
out_filename = f'output/res_{in_filename}'

reg_name = r'^([-_a-z\(\) ]+) (completed|practiced|tested)'
reg_xp = r'^\+(\d+) xp'
reg_date = r'^([a-z]+) (\d+), (\d+)'

state = 0
for line in in_file.readlines():
    line = line.strip().lower()

    if state == 0:
        m = re.search(reg_name, line)
        if m:
            name = m.group(1).strip()
            name = d.student_aliases[name]
            state = 1

    elif state == 1:
        m = re.search(reg_xp, line)
        if m:
            xp = int(m.group(1))
            state = 2

    elif state == 2:
        m = re.search(reg_date, line)
        if m:
            mo, day, year = list(m.groups())

            # if date...
            d.student_xps[name] += xp
            
            state = 0

in_file.close()

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
