import sqlite3
import time

conct = sqlite3.connect('twitter2.db', check_same_thread=False)
cur = conct.cursor()

daysToKeep = 2
currentMsTime = time.time()*1000
msInDay = 86400 * 1000
delTill = int(currentMsTime - (daysToKeep*msInDay))

sqlt = "DELETE FROM tweet WHERE UnixTime < {}".format(delTill)
cur.execute(sqlt)

#to rebuild and optimize the database
#cur.execute("VACUUM") 
conct.commit()
conct.close()