from twisted.web.client import Agent
from twisted.web.client import FileBodyProducer
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.http_headers import Headers
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from StringIO import StringIO
from urllib import urlencode
from datetime import datetime
import optparse


agent = Agent(reactor)

usage = """usage: %prog --key --port

This small twisted server handles POST requests from Rackspace Cloud Monitoring
(or anything) and forwards it to Prowl http://www.prowlapp.com/ via your API key.
"""

parser = optparse.OptionParser(usage)
parser.add_option("-k", "--key", dest="prowl_api_key")
parser.add_option("-p", "--port", dest="port")
(options, args) = parser.parse_args()


class webhook(Resource):

    def render_POST(self, request):
        maasalert = request.content.getvalue()
        post_alert(options.prowl_api_key, maasalert)
        return ""


class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print "Prowl notification fired at " + datetime.now()
            self.remaining -= len(display)

    def connectionLost(self, reason):
        self.finished.callback(None)


def post_alert(APIKEY, description):

    post = {"apikey": APIKEY,
            "application": "Rackspace Cloud Monitoring",
            "description": description}

    body = FileBodyProducer(StringIO(""))

    d = agent.request(
        'POST',
        'https://api.prowlapp.com/publicapi/add?' + urlencode(post),
        Headers({'Content-Type': ['application/json']}),
        body)

    def cbRequest(response):
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        return finished
    d.addCallback(cbRequest)


root = Resource()
root.putChild("webhook", webhook())
factory = Site(root)
reactor.listenTCP(options.port, factory)
reactor.run()
