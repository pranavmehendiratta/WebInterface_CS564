#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pprint #delete

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################
import re

# Constant values
# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

# URL mapping for the navigation bar till. Need to figure out what to do
# to the index.html url. It does not show anything as of yet.
urls = (
    # TODO: add additional URLs here
    # first parameter => URL, second parameter => class name
    '/currtime', 'curr_time',
    '/selecttime', 'select_time',
    '/', 'index',
    '/add_bid', 'add_bid',
    '/search', 'search'
)
#Constants
EMPTY_STRING = ""

def createReturnObject(error, msg):
    retObj = dict()
    retObj["error"] = error
    retObj["msg"] = msg
    return retObj

def processTriggerErrors(error):
    trigger1 = re.compile(".*Trigger1_Failed.*", re.IGNORECASE)
    trigger2 = re.compile(".*Trigger2_Failed.*", re.IGNORECASE)
    trigger3 = re.compile(".*Trigger3_Failed.*", re.IGNORECASE)
    trigger4 = re.compile(".*Trigger4_Failed.*", re.IGNORECASE)
    trigger5 = re.compile(".*Trigger5_Failed.*", re.IGNORECASE)
    trigger6 = re.compile(".*Trigger6_Failed.*", re.IGNORECASE)
    trigger7 = re.compile(".*Trigger7_Failed.*", re.IGNORECASE)
    trigger8 = re.compile(".*Trigger8_Failed.*", re.IGNORECASE)

    if trigger1.match(error):
        return createReturnObject(True, "Cannot set currenttime to time that is backward in time")

    if trigger2.match(error):
        return createReturnObject(True, "Bid should always match system time. This should not be thrown ever.")

    if trigger3.match(error):
        return createReturnObject(True, "Any new bid for an item should be greater than previous currently")

    # This error should never be thrown
    if trigger4.match(error):
        return createReturnObject(True, "Unable to update bid count using trigger")

    if trigger5.match(error):
        return createReturnObject(True, "Cannot bid on auction which is not started. Should not be displayed because this is handled differently.")

    if trigger6.match(error):
        return createReturnObject(True, "Cannot bid on auction which is ended. Should not be displayed because this is handled differently.")

    if trigger7.match(error):
        return createReturnObject(True, "User cannot on the item he/she is selling")

    # This error should never be thrown
    if trigger8.match(error):
        return createReturnObject(True, "Unable to update currently to most recent bid using trigger")

    return createReturnObject(False, "Process errors passed successfully")

def processSQLErrors(error):
    no2BidsAtSameTime = re.compile(",*UNIQUE constraint failed: Bids.ItemID, Bids.Time.*", re.IGNORECASE)

    if no2BidsAtSameTime.match(error):
        return createReturnObject(True, "Item cannot have 2 bids at the same time")


    # if unable to figure out the error just throw it
    return createReturnObject(True, error)

def isItemPresent(itemID):
    retObj = None

    query_string = 'SELECT * FROM ITEMS WHERE ITEMID = $itemID'
    values = {
        'itemID': itemID
    }

    result = sqlitedb.query(query_string, values)

    if len(result) == 0:
        retObj = createReturnObject(True, "Item does not exists in the database")
    else:
        retObj = createReturnObject(False, "Item exists in the database")

    return retObj

def isUserPresent(userID):
    retObj = None

    query_string = 'SELECT * FROM USERS WHERE userID = $userID'
    values = {
        'userID': userID
    }

    result = sqlitedb.query(query_string, values)

    if len(result) == 0:
        retObj = createReturnObject(True, "User does not exists in the database")
    else:
        retObj = createReturnObject(False, "User exists in the database")

    return retObj

"""
This check whether 
1. currtime > started
2. currtime < ends
3. buy_price is not met yet
"""
def isAuctionOpenForItem(itemID):
    query_string = 'SELECT Started, ends, Buy_Price, Currently FROM ITEMS WHERE ItemID = $itemID'

    values = {
        'itemID': itemID
    }

    result = sqlitedb.query(query_string, values)

    print("result length is " + str(len(result)))

    started = string_to_time(result[0].Started)
    ends = string_to_time(result[0].Ends)
    buy_price = result[0].Buy_Price
    currently = result[0].Currently
    currTime = string_to_time(sqlitedb.getTime())

    print("currTime: " + str(currTime) + ", startTime: " + str(started) + ", endTime: " + str(ends))
    print("buy_price: " + str(buy_price) + ", currently: " + str(currently))

    if started > currTime:
        return createReturnObject(True, "Cannot bid on an item whose auction has not started yet")

    if ends < currTime:
        return createReturnObject(True, "Cannot bid on an item whose auction has closed")

    # cannot check the condition if buy_price is reached or not if buy_price is None
    if buy_price is not None:
        # compare buy_price and currently here
        buy_price = float(buy_price)
        currently = float(currently)
        if currently >= buy_price:
            return createReturnObject(True, "This item is remove from bidding because buy_price is already been met")

    return createReturnObject(False, "Item is open for bidding")

class index:
    def GET(self):
        return render_template('app_base.html')

class search:
    def GET(self):
        return render_template('search.html')

    def POST(self):
        post_params = web.input()
        category = post_params['category']
        description = post_params['description']
        itemID = post_params['itemID']
        minPrice = post_params['minPrice']
        maxPrice = post_params['maxPrice']
        status = post_params['status']

        print("category: " + str(category) + ", description: " + description + ", itemID: " + str(itemID) + ", minPrice: " + str(minPrice) + ", maxPrice: " + str(maxPrice) + ", status: " + str(status))

        inputResults = self.validateInputs(category, description, itemID, minPrice, maxPrice, status)

        if inputResults["error"]:
            message = "Error: " + inputResults["msg"]
            return render_template('search.html', message = message)

        query = self.constructQuery(category, description, itemID, minPrice, maxPrice, status)

        print("Query is")
        pprint.pprint(query)

        pprint.pprint(inputResults)
        return render_template('search.html')

    def constructQuery(self, category, description, itemID, minPrice, maxPrice, status):
        print("Inside constructQuery")

        Select = "SELECT * "
        From = "FROM Items I "
        Where = list()
        values = dict()

        if description != EMPTY_STRING:
            Where.append("I.Description LIKE $description")
            values["description"] = "%" + description + "%"

        if itemID != EMPTY_STRING:
            Where.append("I.itemID = $itemID")
            values["itemID"] = int(itemID)

        if minPrice != EMPTY_STRING:
            Where.append("I.Currently >= $minPrice")
            values["minPrice"] = float(minPrice)

        if maxPrice != EMPTY_STRING:
            Where.append("I.Currently <= $maxPrice")
            values["maxPrice"] = float(maxPrice)

        if status != "all":
            if status == "open":
                Where.append("I.Started > $currtime")
                Where.append("I.Ends < $currtime")
                Where.append("I.Buy_Price > I.Currently")
            elif status == "close":
                Where.append("(I.Ends < $currtime OR I.Buy_Price == I.Currently")
            elif status == "notStarted":
                Where.append("I.Ends < $currtime")

            values["currtime"] = sqlitedb.getTime()

        if category != EMPTY_STRING:
            # Join Condition - Don't have to worry about mutiple because each item belong to each category only once
            Where.append("C.ItemID == I.ItemID")
            From = From + ", Categories C "

        query = {
            "query_string": Select + From + "WHERE " + (" AND ").join(Where) + ";",
            "values": values
        }

        return query




    def validateInputs(self, category, description, itemID, minPrice, maxPrice, status):
        count = 0
        NUM_SEARCH_PARAMS = 6

        # Check if userID is valid
        if category == EMPTY_STRING:
            count += 1

        if description == EMPTY_STRING:
            count += 1

        # Check if itemID is valid
        if itemID == EMPTY_STRING:
            count += 1
        else:
            try:
                itemID = int(itemID)
                itemResults = isItemPresent(itemID)
                if itemResults["error"]:
                    return itemResults
            except:
                msg = "itemID = " + itemID + " is incorrect. itemID needs to be an integer"
                return createReturnObject(True, msg)

        # Check if min price is either Empty or int or float
        if minPrice == EMPTY_STRING:
            count += 1
        else:
            if "." not in minPrice:
                try:
                    minPrice = int(minPrice)
                except:
                    msg = "minPrice = " + minPrice + " is incorrect. minPrice needs to be either float or int"
                    return createReturnObject(True, msg)
            else:
                try:
                    minPrice = float(minPrice)
                except:
                    msg = "minPrice = " + minPrice + " is incorrect. minPrice needs to be either float or int"
                    return createReturnObject(True, msg)

        # Check if max price is either Empty or int or float
        if maxPrice == EMPTY_STRING:
            count += 1
        else:
            if "." not in maxPrice:
                try:
                    maxPrice = int(maxPrice)
                except:
                    msg = "maxPrice = " + maxPrice + " is incorrect. maxPrice needs to be either float or int"
                    return createReturnObject(True, msg)
            else:
                try:
                    maxPrice = float(maxPrice)
                except:
                    msg = "maxPrice = " + maxPrice + " is incorrect. minPrice needs to be either float or int"
                    return createReturnObject(True, msg)

        if status == "all":
            count += 1

        print("count: " + str(count))

        if count == NUM_SEARCH_PARAMS:
            return createReturnObject(True, "Everything is empty. Please enter something to search")

        return createReturnObject(False, "Inputs validated")

class add_bid:
    def GET(self):
        return render_template('add_bid.html')

    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        price = post_params['price']
        retObj = self.tryAddingBid(itemID, userID, price)

        # Replacing dummy msg with something that makes sense
        print("retObj:")
        pprint.pprint(retObj)

        if retObj["error"]:
            return render_template('add_bid.html', message = retObj["msg"])
        else:
            return render_template('add_bid.html', add_result = retObj["msg"])

    def tryAddingBid(self, itemID, userID, price):

        # Check if inputs exists and are valid
        inputResult = self.validateInput(itemID, userID, price)
        if inputResult["error"]:
            return inputResult

        # Check if the itemID exists in the database
        itemResult = isItemPresent(itemID)
        if itemResult["error"]:
            return itemResult

        # check if the user exits in the database
        userResult = isUserPresent(userID)
        if userResult["error"]:
            return userResult

        # check if the bid is open
        bidOpen = isAuctionOpenForItem(itemID)
        if bidOpen["error"]:
            return bidOpen

        transaction = sqlitedb.transaction()
        try:
            query_string = 'INSERT INTO BIDS VALUES ($itemID, $userID, $price, $currtime)'

            values = {
                'itemID': itemID,
                'userID': userID,
                'price': price,
                'currtime': sqlitedb.getTime()
            }
            sqlitedb.executeInsertionOrDeletionQuery(query_string, values)

        except Exception as e:
            transaction.rollback()
            print(str(e))
            triggerErrors = processTriggerErrors(str(e))

            if (triggerErrors["error"]):
                return triggerErrors

            return processSQLErrors(str(e))
        else:
            transaction.commit()
            return createReturnObject(False, "Bid successfully placed")

    def validateInput(self, itemID, userID, price):
        # Check if any of the inputs are None or empty string
        if itemID is None:
            msg = "itemID is None. itemID needs to be an integer"
            return createReturnObject(True, msg)

        if userID is None:
            msg = "userID is None. userID cannot be empty"
            return createReturnObject(True, msg)

        if price is None:
            msg = "price is None. price needs to be a real value"
            return createReturnObject(True, msg)

        if itemID == EMPTY_STRING:
            msg = "itemID is an empty string. itemID needs to be an integer"
            return createReturnObject(True, msg)

        if userID == EMPTY_STRING:
            msg = "userID is an empty string. userID cannot be empty"
            return createReturnObject(True, msg)

        if price == EMPTY_STRING:
            msg = "price is an empty. price needs to be a real value"
            return createReturnObject(True, msg)

        # check if itemID is an integer
        try:
            itemID = int(itemID)
        except:
            msg = "itemID = " + itemID + " is incorrect. itemID needs to be an integer"
            return createReturnObject(True, msg)

        # check if price is either float or integer
        if "." not in price:
            print("price is of int type")
            try:
                price = int(price)
            except:
                msg = "price = " + price + " is incorrect. price needs to be either float or int"
                return createReturnObject(True, msg)
        else:
            print("price is of float type")
            try:
                price = float(price)
            except:
                msg = "price = " + price + " is incorrect. price needs to be either float or int"
                return createReturnObject(True, msg)

        return createReturnObject(False, "Inputs are valid")

class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests

    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        enter_name = post_params['entername']

        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)

        # TODO: save the selected time as the current time in the database
        # 1. Delete the current time
        #delResult = self.deleteCurrentTime();
        #print("delResult is")
        #pprint.pprint(delResult)

        # 2. add a new current time
        #result = self.addCurrTime(selected_time)

        #print("result is")
        #pprint.pprint(result)
        #print("update_message: " + update_message)



        transaction = sqlitedb.transaction()
        try:
            query_string = "UPDATE CurrentTime SET time = $selected_time where time = $current_time"

            values = {
                "selected_time": selected_time,
                "current_time": sqlitedb.getTime()
            }

            sqlitedb.executeInsertionOrDeletionQuery(query_string, values)

        except Exception as e:
            transaction.rollback()
            print(str(e))
            triggerErrors = processTriggerErrors(str(e))
            update_message = "Error: " + triggerErrors["msg"]
        else:
            transaction.commit()

        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('select_time.html', message = update_message)

    # Will delete the current time from the currtime table
    #def deleteCurrentTime(self):
    #    current_time = sqlitedb.getTime()
    #    query_string = 'delete from currenttime where time = $currenttime'
    #    result = sqlitedb.executeInsertionOrDeletionQuery(query_string, {'currenttime': current_time})
    #    return result

    #def addCurrTime(self, newCurrTime):
    #    print("newCurrTime in addCurrTime():" + newCurrTime)
    #    query_string = 'insert into currenttime values ($time)'
    #    result = sqlitedb.executeInsertionOrDeletionQuery(query_string, {'time': newCurrTime})
    #    return result


###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
