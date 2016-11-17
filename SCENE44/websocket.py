import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import io
from tornado.options import define, options
import subprocess


print("scs")
listeners = []

class WSHandler(tornado.websocket.WebSocketHandler):

  def check_origin(self, origin):
    return True
  
  def open(self):
    print "opened a new websocket"
    listeners.append(self)
    print listeners
   
  def on_message(self, message):
    print message

    # self.write_message(u"You Said: " + message)
  
  def send(self,msg):
    self.write_message(msg)

  def on_close(self):
    print 'connection closed'
    listeners.remove(self)

def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([(r'/ws', WSHandler),])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()