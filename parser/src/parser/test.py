import datetime

res = '7 марта 12:53 2021'
if res[-4:].isdigit() and len(res[-4:]) == 4:
    year = int(res[-4:])
    date = datetime.datetime.now().year - year
    print(date)
else:
    print("The string does not contain a valid year at the end.")
