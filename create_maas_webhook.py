import optparse
import httplib2
import simplejson

usage = """usage: %prog --username --key [options]

This script adds a webhook to your Rackspace Cloud Montioring account.
Each request requires your username and key.
If you type just your username and key you will list all current notifications.

Add a webhoook_url to add a webhook.
To test your webhooks type --test [webhook_id]

Also, look into using the full raxmon_cli: https://github.com/racker/rackspace-monitoring-cli
"""

parser = optparse.OptionParser(usage)
parser.add_option("-u", "--username", dest="username", help="Rackspace Username")
parser.add_option("-k", "--key", dest="key", help="Rackspace API Key")
parser.add_option("--webhook_url", dest="webhook_url")
parser.add_option("--test", dest="test_webhook_id")
(options, args) = parser.parse_args()


def get(url, headers=None):
    h = httplib2.Http()
    if headers == None:
        headers = {'Content-Type': 'application/json'}
    response, content = h.request(url,
                              'GET',
                              headers=headers)

    return response, content


def post(data, url, headers=None):
    jsondata = simplejson.dumps(data)
    h = httplib2.Http()
    if headers == None:
        headers = {'Content-Type': 'application/json'}
    response, content = h.request(url,
                              'POST',
                              headers=headers,
                              body=jsondata)

    return response, content


def auth(username, key):
    POSTDATA = {
        "credentials": {
            "username": username,
            "key": key
        }
    }
    URL = 'https://identity.api.rackspacecloud.com/v1.1/auth'
    reply = post(POSTDATA, URL)

    if reply[0]['status'] == '200':
        auth_response = simplejson.loads(reply[1])
        auth_token = auth_response['auth']['token']['id']
        cm_url = auth_response['auth']['serviceCatalog']['cloudMonitoring'][0]['publicURL']

        print auth_token
        print cm_url

        if options.webhook_url:
            create_webhook("webhook", options.webhook_url, cm_url, auth_token)
        if options.test_webhook_id:
            test_webhook(options.test_webhook_id, cm_url, auth_token)
        else:
            list_notifications(cm_url, auth_token)


def test_webhook(test_webhook_id, cm_url, auth_token):
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': auth_token,
        'X-Auth-User': options.username
    }
    notifications_url = cm_url + "/notifications/" + test_webhook_id + "/test"
    reply = post("", notifications_url, headers)
    print reply[0]
    print reply[1]


def list_notifications(cm_url, auth_token):
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': auth_token,
        'X-Auth-User': options.username
    }
    notifications_url = cm_url + "/notifications"
    reply = get(notifications_url, headers)
    print reply[0]
    print reply[1]


def create_webhook(label, webhook_url, cm_url, auth_token):
    POSTDATA = {
        "label": label,
        "type": "webhook",
        "details": {
            "url": webhook_url
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': auth_token,
        'X-Auth-User': options.username
    }
    notifications_url = cm_url + "/notifications"

    reply = post(POSTDATA, notifications_url, headers)
    print reply[0]
    print reply[1]

if options.username:
    auth(options.username, options.key)
