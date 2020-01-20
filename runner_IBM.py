import pymongo
from bson.objectid import ObjectId
import tornado.ioloop
import tornado.web 
import tornado.websocket
import threading
import logging
import os
import sys
from bson.json_util import dumps
import configparser
import json
from datetime import datetime
from watson_developer_cloud import VisualRecognitionV3

# global variables
_WEBSETTINGS = { "static_path": os.path.join(os.path.dirname(__file__)+"Web/", "static") }
_clients = []

# get config file settings
cfg = configparser.ConfigParser()
cfg.read('settings.cfg')

# configure connection to mongodb
conn = pymongo.MongoClient(cfg['DEFAULT']['_URI'])
try:
    conn.server_info()
except Exception as e:
    logging.error("Unable to connect to {s}".format(s=cfg['DEFAULT']['_URI']))
    conn = None
    sys.exit(1)

handle = conn[cfg['DEFAULT']['_DBNAME']][cfg['DEFAULT']['_COLNAME']]
print("Connected to Atlas!")


# configure connection to watson VisualRecognitionV3 api
visual_recognition = VisualRecognitionV3(
    '2018-03-19',
    iam_apikey='IBMkey')



#########
# configure web interface
#########
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("Web/index.html", title="Welcome")

class WebSockHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("New client connected")
        _clients.append(self)
        self.write_message("You are connected")

    def on_message(self, msg):
        print(msg)
        #self.write_message(msg)
        # oh man this is bad practice
        handle.insert_one({"url":msg, "created":datetime.now()})

    def on_close(self):
        print("Client disconnected")

    def check_origin(self, origin):
        # who cares about security
        return True


###########
# Main loop
##########
if __name__ == "__main__":
    # start up the web servers as tornado applications
    application = tornado.web.Application([(r"/", MainHandler),], **_WEBSETTINGS)
    appsoc = tornado.web.Application([(r"/", WebSockHandler),],)

    # start a web server for sockets
    appsoc.listen(cfg['DEFAULT']['_WEBSOCKPORT'])
    
    # start a web server for index.html and run in background thread
    application.listen(cfg['DEFAULT']['_WEBPORT'])
    t = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
    t.daemon = True
    t.start()

    print("Listening...")

    # connect to a change stream
    change_stream = handle.watch()
    # every change in the db
    for change in change_stream:
        # can be insert, update, replace (Compass)
        if change["operationType"] == "insert":
            # make sure it had a URL attribute
            if "url" in change["fullDocument"]:
                # boilerplate to prep watson api request
                image_url=change["fullDocument"]["url"]
                resp = visual_recognition.classify(
                    url=image_url,
                    threshold='0.1',
                    classifier_ids='default').get_result()
                # If image does not exist then, send message on co
                if resp['images_processed'] == 1 :
                    # odd formatting i dont have time for right now so just process it first
                    labels = []
                    for label in resp:
                        obj = {}
                        obj['description'] = label['class']
                        obj['score'] = label['score']
                        labels.append(obj)

                    # update mongodb record with response from IBM watson
                    handle.update_one({'_id':ObjectId(change["fullDocument"]["_id"])}, {"$set": {"watsonlabels":labels}})
                else:
                    logging.warning("API error on URl: {a}".format(a=resp.error.message))
                    logging.warning(change["fullDocument"]["url"])

        # print to screen
        print(dumps(change))
        print("")

        for c in _clients:
            # fix disconnecting clients symptom rather than fixings
            try:
                c.write_message(dumps(change))
            except:
                pass
