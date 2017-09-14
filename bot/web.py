"""Allows to control the bot via REST calls."""

from bottle import route, run, ServerAdapter, request, abort
from os import listdir
import threading
import json
import os


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


class Singleton(type):
    """Singleton, allows a class to be initiated only once."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class WebAPI(object):
    """Create a REST API that allows control over a list of bots."""

    __metaclass = Singleton

    def __init__(self, bots, lport):
        """Initiate Web API."""
        global api_bots
        api_bots = bots
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

    @route('/bots', method='POST')
    def getBots():
        """Return list of all bots for given user."""
        WebAPI.checkIfFormExists(['user'])
        username = request.forms.get('user').replace('"', '')
        auth = ""

        bots = []
        for bot in api_bots:
            if WebAPI.hasPermission(username, WebAPI.getBotName(bot), auth):
                bots.append(bot)

        out = []
        for bot in bots:
            out.append(WebAPI.getBotName(bot))
        return json.dumps(out)

    @route('/files', method='POST')
    def getFiles():
        """Return list of all modifiable files for a given bot."""
        WebAPI.checkIfFormExists(['user', 'bot'])
        username = request.forms.get('user').replace('"', '')
        botname = request.forms.get('bot').replace('"', '')
        auth = ""

        bot = WebAPI.getBot(botname)
        if not WebAPI.hasPermission(username, botname, auth):
            abort(403, "User doesn't have access to this bot.")

        print(bot.root)
        data = listdir(bot.root + 'data')
        configs = listdir(bot.root + 'configs')
        out = []
        for d in data + configs:
            if '.json' in d:
                out.append(d)
        return json.dumps(out)

    @route('/file', method='POST')
    def getFile():
        """Return the json of a specific file."""
        WebAPI.checkIfFormExists(['user', 'bot', 'file'])
        username = request.forms.get('user').replace('"', '')
        botname = request.forms.get('bot').replace('"', '')
        filename = request.forms.get('file').replace('"', '')
        auth = ""

        bot = WebAPI.getBot(botname)
        if not WebAPI.hasPermission(username, botname, auth):
            abort(403, "User doesn't have access to this bot.")

        path = None
        if os.path.isfile(bot.root + 'config/' + filename):
            path = bot.root + 'config/' + filename
        if os.path.isfile(bot.root + 'data/' + filename):
            path = bot.root + 'data/' + filename

        if path is None:
            abort(404, "File not found.")

        with open(path) as fp:
            data = json.load(fp)
        return data

    @route('/setfile', method='POST')
    def setFile():
        """Set the json of a specific file."""
        WebAPI.checkIfFormExists(['user', 'bot', 'file', 'content'])
        username = request.forms.get('user').replace('"', '')
        botname = request.forms.get('bot').replace('"', '')
        filename = request.forms.get('file').replace('"', '')
        content = request.forms.get('content')
        auth = ""

        print(content)
        bot = WebAPI.getBot(botname)
        if not WebAPI.hasPermission(username, botname, auth):
            abort(403, "User doesn't have access to this bot.")

        try:
            json_data = json.loads(content)
        except ValueError:
            abort(400, "A json dictionary is required.\n Given:\n" + str(content))

        path = None
        if os.path.isfile(bot.root + 'config/' + filename):
            path = bot.root + 'config/' + filename
        if os.path.isfile(bot.root + 'data/' + filename):
            path = bot.root + 'data/' + filename

        if path is None:
            abort(404, "File not found.")

        with open(path, mode='w') as file:
            json.dump(json_data, file, indent=4)

        bot.reloadConfig()

    def checkIfFormExists(keys):
        """Get all forms for the given keys."""
        for k in keys:
            if k not in request.forms:
                abort(400, "Bad Request, expecting the following data:\n" + str(keys))

    def getBot(botname):
        """Return the correct bot, based on its directory name."""
        bot = None
        for b in api_bots:
            if WebAPI.getBotName(b) == botname:
                bot = b
        if bot is None:
            abort(404, "Bot not found.\n")

        return bot

    def getBotName(bot):
        """Return the correct bot name, based on its bot."""
        return bot.root.split('/')[len(bot.root.split('/')) - 2]

    def hasPermission(username, botname, auth):
        """True. (temp)."""
        return True
