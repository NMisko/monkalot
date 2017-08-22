"""Allows to control the bot via REST calls."""

from bottle import route, run, ServerAdapter, request, abort
from os import listdir
import threading
import json


class StoppableWSGIRefServer(ServerAdapter):
    """Allows to programmatically shut down bottle server."""

    def run(self, handler):
        """Start the server."""
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        """Stop the server."""
        # self.server.server_close() <--- alternative but causes bad fd exception
        self.server.shutdown()


class WebAPI(object):
    """Create a REST API that allows control over the bot."""

    def __init__(self, bot, lport):
        """Initiate Web API."""
        global api_bot
        api_bot = bot
        global api_server
        api_server = StoppableWSGIRefServer(host='localhost', port=lport)
        global api_port
        api_port = lport
        threading.Thread(target=run, kwargs=dict(server=api_server,)).start()

    def stop(self):
        """Stop the server."""
        api_server.stop()

    @route('/hello')
    def hello():
        """Return hw."""
        return "Hello World!\n"

    @route('/config')
    def getconfig():
        """Return the config."""
        return api_bot.config

    @route('/setconfig', method='POST')
    def setconfig():
        """Set the config."""
        config = request.forms.get('config')

        try:
            json_config = json.loads(config)
            api_bot.setConfig(json_config)
            return "Successfully set configuration.\n"
        except ValueError:
            abort(400, "A json dictionary is required.\n")

    @route('/datafiles')
    def getDataFiles():
        """Return list of all data files."""
        data = listdir('data')
        out = []
        for d in data:
            if '.json' in d:
                out.append(d)
        return json.dumps(out)

    @route('/data', method='POST')
    def getData():
        """Return the json of a specific file."""
        name = request.forms.get('name')
        name = name.replace('"', '')

        with open('data/' + name) as fp:
            data = json.load(fp)
        return data

    @route('/setdata', method='POST')
    def setData():
        """Set the json of a specific file."""
        name = request.forms.get('name')
        name = name.replace('"', '')
        data = request.forms.get('data')
        try:
            json_data = json.loads(data)
        except ValueError:
            abort(400, "A json dictionary is required.\n")

        with open('data/' + name, 'w') as file:
            json.dump(json_data, file, indent=4)
        api_bot.reloadConfig()
