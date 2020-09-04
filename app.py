#!/usr/bin/env python3.6

# Title: Py-Air-Quality
# Created by: Braeden Richards
# Created on: September 3rd, 2020
# Last Edited: September 3rd, 2020


###########
# Imports #
###########
import requests     # For querying the API
import json         # Make the API response usable
import time         # For grabbing local time
import threading    # To create worker threads
import logging      # For logging during development (now set to critical only)


#########################
# YOUR CREDENTIALS HERE #
#########################
# Add your token for the API here
api_token = ''
# Add your latitude here
lat = ''

# Add your longitude here
lon = ''


####################
# Global Variables #
####################
c = threading.Condition()   # Lock for shared variables
localTime = 0               # To hold localtime of each AQI update
aqius = 0                   # Air quality
updated = True              # True if air quality has been updated since last console print


#############
# Functions #
#############

# Name: main
# Def: Main loop of the application. Creates the threads and manages them.
# Arg: None
# Ret: None
def main():
    logging.basicConfig(
        level=logging.CRITICAL,
        format="%(relativeCreated)6d %(threadName)s %(message)s",
    )
    event = threading.Event()

    thread_Query = threading.Thread(target=workerQuery, args=(event,))
    thread_Print = threading.Thread(target=workerPrint, args=(event,))

    thread_Query.start()
    event.wait(10)
    thread_Print.start()

    while not event.isSet():
        try:
            logging.debug("Checking in from main thread")
            event.wait(1)
        except KeyboardInterrupt:
            event.set()
            break

# Name: workerQuery
# Def: Thread function. Requests from the AirVisual API and updates global variables with the info. 
#       Queries every 45 min if last query was successful. Otherwise every 30 min.
# Arg: <threading.Event> event: Used to close thread once application is quit
# Ret: None
def workerQuery(event):
    successfulQuery = False
    global updated
    global aqius
    global localTime
    while not event.isSet():
        logging.debug("query thread checking in")
        logging.debug("query thread querying api")
        try:
            results = json.loads(requests.get('http://api.airvisual.com/v2/nearest_city?lat=' + lat + '&lon=' + lon + '&key=' + api_token).text)
            logging.debug("query successful") 
            successfulQuery = True
        except:
            logging.debug("query unsuccessful")
            successfulQuery = False
        
        if successfulQuery:
            c.acquire()
            logging.debug("updating aqius") 
            aqius = results["data"]["current"]["pollution"]["aqius"]
            localTime = time.asctime(time.localtime(time.time()))
            updated = True
            logging.debug("update successful") 
            c.notify_all()
            c.release()
            event.wait(2700)
        else:
            event.wait(1800)
        

# Name: workerPrint
# Def: Thread function. Prints updated air quality information to the console.
#       Checks for updated information every 45 seconds
# Arg: <threading.Event> event: Used to close thread once application is quit
# Ret: None
def workerPrint(event):
    global aqius
    global localTime
    global updated
    while not event.isSet():
        c.acquire()
        if updated:
            if aqius >= 0 and aqius <= 51:
                quality = 'Good'
            elif aqius >= 51 and aqius <= 100:
                quality = 'Moderate'
            elif aqius >= 101 and aqius <= 150:
                quality = 'Unhealthy for Sensitive Groups'
            elif aqius >= 151 and aqius <= 200:
                quality = 'Unhealthy'
            elif aqius >= 201 and aqius <= 300:
                quality = 'Very Unhealthy'
            elif aqius >= 301 and aqius <= 500:
                quality = 'Moderate'
            else:
                quality = '\{\{ERROR\}\}'
            
            print("\n\nCURRENT AIR QUALITY")
            print(localTime)
            print("AQI:", aqius)
            print("Status: " + quality)

            updated = False

        c.notify_all()
        c.release()
    
        event.wait(45)
        

# Application loop
if __name__ == "__main__":
    main()