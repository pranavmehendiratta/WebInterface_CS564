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

# Constant values
EMPTY_STRING = ""

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
    '/add_bid', 'add_bid'
)

class index:
    def GET(self):
        return render_template('app_base.html')

class add_bid:
    def GET(self):
        return render_template('add_bid.html')

    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        price = post_params['price']
        retObj = self.tryAddingBid(itemID, userID, price)

        #print("This is dummy message. itemID: " + itemID + ", userID: " + userID + ",  price: " + price)
        #update_message = '(This is dummy message. itemID: %s, userID: %s,  price: %s)' % (itemID, userID, price)

        # Replacing dummy msg with something that makes sense
        print("retObj:")
        pprint.pprint(retObj)
        update_message = retObj["msg"]

        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('add_bid.html', message = update_message)

    def tryAddingBid(self, itemID, userID, price):
        retObj = self.validateInput(itemID, userID, price)

        if retObj["error"]:
            return retObj

        transaction = sqlitedb.transaction()
        try:
            query_string = 'INSERT INTO BIDS VALUES ($itemID, $userID, $price, $currtime)'

            values = {
                'itemID': itemID,
                'userID': userID,
                'price': price,
                'currtime': sqlitedb.getTime()
            }
            sqlitedb.executeQuery(query_string, values)

        except Exception as e:
            transaction.rollback()
            print(str(e))
            return self.createReturnObject(True, str(e))
        else:
            transaction.commit()

    def validateInput(self, itemID, userID, price):
        # Check if any of the inputs are None or empty string
        if itemID is None:
            msg = "itemID is None. itemID needs to be an integer"
            return self.createReturnObject(True, msg)

        if userID is None:
            msg = "userID is None. userID cannot be empty"
            return self.createReturnObject(True, msg)

        if price is None:
            msg = "price is None. price needs to be a real value"
            return self.createReturnObject(True, msg)

        if itemID == EMPTY_STRING:
            msg = "itemID is an empty string. itemID needs to be an integer"
            return self.createReturnObject(True, msg)

        if userID == EMPTY_STRING:
            msg = "userID is an empty string. userID cannot be empty"
            return self.createReturnObject(True, msg)

        if price == EMPTY_STRING:
            msg = "price is an empty. price needs to be a real value"
            return self.createReturnObject(True, msg)

        # check if itemID is an integer
        try:
            itemID = int(itemID)
        except:
            msg = "itemID = " + itemID + " is incorrect. itemID needs to be an integer"
            return self.createReturnObject(True, msg)

        # check if price is either float or integer
        if "." not in price:
            print("price is of int type")
            try:
                price = int(price)
            except:
                msg = "price = " + price + " is incorrect. price needs to be either float or int"
                return self.createReturnObject(True, msg)
        else:
            print("price is of float type")
            try:
                price = float(price)
            except:
                msg = "price = " + price + " is incorrect. price needs to be either float or int"
                return self.createReturnObject(True, msg)

        return self.createReturnObject(False, "Inputs are valid")


    def createReturnObject(self, error, msg):
        retObj = dict()
        retObj["error"] = error
        retObj["msg"] = msg
        return retObj


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
        delResult = self.deleteCurrentTime();
        print("delResult is")
        pprint.pprint(delResult)

        # 2. add a new current time
        result = self.addCurrTime(selected_time)

        print("result is")
        pprint.pprint(result)
        print("update_message: " + update_message)

        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('select_time.html', message = update_message)

    # Will delete the current time from the currtime table
    def deleteCurrentTime(self):
        current_time = sqlitedb.getTime()
        query_string = 'delete from currenttime where time = $currenttime'
        result = sqlitedb.executeQuery(query_string, {'currenttime': current_time})
        return result

    def addCurrTime(self, newCurrTime):
        print("newCurrTime in addCurrTime():" + newCurrTime)
        query_string = 'insert into currenttime values ($time)'
        result = sqlitedb.executeQuery(query_string, {'time': newCurrTime})
        return result


###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
