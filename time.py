from datetime import date

# calling the today
# function of date class
today = date.today().strftime('%d %B,%Y')

print("Today's date is", today)
