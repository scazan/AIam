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

    if message == "shutdown":
      print (message)
      subprocess.call(['/usr/bin/osascript', '-e','tell app "System Events" to shut down'])
    else:
      # self.write_message(u"You Said: " + message)
      print (message)
      writeFile(message);
   
     #self.write_message("re")

  def on_close(self):
    print 'connection closed'
    listeners.remove(self)

def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([(r'/ws', WSHandler),])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

def writeFile(content):
  with io.open("/Users/eom-terkep/Google Drive/log/terkep/terkep_log.csv", 'a', encoding='utf-8') as myfile:
  # test locally
  # with io.open('/Users/gase12/Documents/xorxor_projects/evangelikus/terkep/log/test.csv', 'a', encoding='utf-8') as myfile:
    myfile.write(content)

if __name__ == "__main__":
    main()