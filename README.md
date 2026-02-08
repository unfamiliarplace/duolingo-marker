# Duolingo Marker

A couple of scripts for summing student XP records in a Duolingo classroom.

To set up (once):

1. Create a file called `variables.txt` under `config`. An example has been provided to copy and modify.
1. Supply the XP goal, any bonus weeks (where all XP is treated as extra, e.g. over Christmas holidays), the week start day if desired, and student names and aliases (since they can choose their own usernames...).

To add data (on a regular basis):

1. Go to the student view.
1. Select a custom date range for the period you want to mark (e.g. Monday to Sunday). Export the CSV.
1. Save it with a title that has two datestamps for the start and end, e.g. `2024-09-01 2024-09-07.csv`. Note that it will be interpreted as the start of the first date to the end of the second date (midnight to midnight).
1. Place that file under `input`.

Then just run the script. It always runs from the latest file to the earliest.
