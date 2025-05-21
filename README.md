# Duolingo Marker

A couple of scripts for summing student XP records in a Duolingo classroom.

There are two methods. Originally, Duolingo's export function was not great, and the most reliable method was to copy and paste the text from the Activity panel. This is `process_from_activity.py`. However, now a CSV export from the main panel in the student view is usable and reliable.

To set up (once):

1. Create a file called `variables.txt` under `config`. An example has been provided to copy.
2. Supply the XP goal, any bonus weeks (where all XP is treated as extra, e.g. over Christmas holidays), and student names and aliases (since they can choose their own usernames...).

To add data (on a regular basis):

2. Go to the student view.
3. Select a custom date range for the period you want to mark (e.g. Monday to Sunday). Export the CSV.
4. Save it with a title that has two datestamps for the start and end, e.g. `2024-09-01 2024-09-07.csv`. Note that it will be interpreted as the start of the first date to the end of the second date (midnight to midnight).
5. Place that file under `input`.

Then just run the script. It always runs from the latest file to the earliest.
