"""Allows to control the bot via REST calls."""

import json
import os
import threading
import requests
import urllib.parse

from bottle import ServerAdapter, abort, request, route, run
from jwcrypto import jwk, jwt, jws

CONFIG_PATH = '{}configs/bot_config.json'


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

    def __init__(self, bots, lport, password=None):
        """Initiate Web API."""
        global api_bots
        api_bots = bots

        global api_server
        api_server = StoppableWSGIRefServer(host='localhost', port=lport)

        global api_port
        api_port = lport

        global api_password
        api_password = password

        global clientID
        with open(CONFIG_PATH.format(bots[0].root), 'r', encoding="utf-8") as file:
            CONFIG = json.load(file)
        clientID = str(CONFIG['clientID'])

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
        WebAPI.checkIfFormExists(['user', 'auth'])
        username = urllib.parse.unquote(str(request.forms.get('user')))
        auth = urllib.parse.unquote(request.forms.get('auth'))

        if not WebAPI.hasUserPermission(username, auth):
            abort(403, "Bad authentication")

        bots = []
        for bot in api_bots:
            if WebAPI.hasBotPermission(username, bot):
                bots.append(bot)

        out = []
        for bot in bots:
            out.append(WebAPI.getBotName(bot))
        return json.dumps(out)

    @route('/files', method='POST')
    def getFiles():
        """Return list of all modifiable files for a given bot."""
        WebAPI.checkIfFormExists(['user', 'bot', 'auth'])
        username = urllib.parse.unquote(request.forms.get('user'))
        botname = urllib.parse.unquote(request.forms.get('bot'))
        auth = urllib.parse.unquote(request.forms.get('auth'))

        bot = WebAPI.getBot(botname)

        if not WebAPI.hasUserPermission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.hasBotPermission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        data = os.listdir(bot.root + 'data')
        configs = os.listdir(bot.root + 'configs')
        out = []
        for d in data + configs:
            if '.json' in d:
                out.append(d)
        return json.dumps(out)

    @route('/file', method='POST')
    def getFile():
        """Return the content of a specific file."""
        WebAPI.checkIfFormExists(['user', 'bot', 'file', 'auth'])
        username = urllib.parse.unquote(request.forms.get('user'))
        botname = urllib.parse.unquote(request.forms.get('bot'))
        filename = urllib.parse.unquote(request.forms.get('file'))
        auth = urllib.parse.unquote(request.forms.get('auth'))

        bot = WebAPI.getBot(botname)
        if not WebAPI.hasUserPermission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.hasBotPermission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        # For security
        filename = os.path.split(filename)[1]

        path = None
        if os.path.isfile(bot.root + 'configs/' + filename):
            path = bot.root + 'configs/' + filename
        if os.path.isfile(bot.root + 'data/' + filename):
            path = bot.root + 'data/' + filename

        if path is None:
            abort(404, "File \"" + filename + "\" not found.")

        with open(path) as fp:
            data = json.load(fp)

        return {'content': data}

    @route('/setfile', method='POST')
    def setFile():
        """Set the json of a specific file."""
        WebAPI.checkIfFormExists(['user', 'bot', 'file', 'content', 'auth'])
        username = urllib.parse.unquote(request.forms.get('user'))
        botname = urllib.parse.unquote(request.forms.get('bot'))
        filename = urllib.parse.unquote(request.forms.get('file'))
        content = urllib.parse.unquote(request.forms.get('content'))
        auth = urllib.parse.unquote(request.forms.get('auth'))

        bot = WebAPI.getBot(botname)
        if not WebAPI.hasUserPermission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.hasBotPermission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        try:
            json_data = json.loads(content)
        except ValueError:
            abort(400, "A json dictionary is required.\n Given:\n" + str(content))

        # For security
        filename = os.path.split(filename)[1]

        path = None
        if os.path.isfile(bot.root + 'configs/' + filename):
            path = bot.root + 'configs/' + filename
        if os.path.isfile(bot.root + 'data/' + filename):
            path = bot.root + 'data/' + filename

        if path is None:
            abort(404, "File \"" + filename + "\" not found.")

        with open(path, mode='w') as file:
            json.dump(json_data, file, indent=4)

        bot.reloadConfig()

    @route('/getTwitchUsername', method='POST')
    def getUserNameI():
        """Get the username based on an id_token. Also verifies token."""
        WebAPI.checkIfFormExists(['auth'])
        auth = urllib.parse.unquote(request.forms.get('auth'))
        return {"username": WebAPI.getUserNameAndVerifyToken(auth)}

    @route('/pause', method='POST')
    def pause():
        """Pause or unpause a bot."""
        WebAPI.checkIfFormExists(['user', 'bot', 'auth', 'pause'])
        username = urllib.parse.unquote(request.forms.get('user'))
        botname = urllib.parse.unquote(request.forms.get('bot'))
        auth = urllib.parse.unquote(request.forms.get('auth'))
        pause = urllib.parse.unquote(request.forms.get('pause'))

        bot = WebAPI.getBot(botname)
        if not WebAPI.hasUserPermission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.hasBotPermission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        if pause == 'true':
            bot.pause = True
        elif pause == 'false':
            bot.pause = False
        else:
            abort(400, "pause must be either 'True' or 'False'")

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
            abort(404, "Bot \"" + botname + "\"not found.\n")

        return bot

    def getBotName(bot):
        """Return the correct bot name, based on its bot."""
        return bot.root.split('/')[len(bot.root.split('/')) - 2]

    def hasUserPermission(username, auth):
        """Check if the user is authenticated."""
        # Check for password
        if api_password is not None:
            if auth == api_password:
                return True

        # If auth doesn't match password, assume id_token is submitted. Verify it.
        id_token_username = WebAPI.getUserNameAndVerifyToken(auth)

        # Compare username from id_token with given username
        return username == id_token_username

    def hasBotPermission(username, bot):
        """Check if the user is allowed to access the bot."""
        with open(CONFIG_PATH.format(bot.root), 'r', encoding="utf-8") as file:
            CONFIG = json.load(file)
        admins = CONFIG['owner_list']
        return username in admins

    def getUserNameAndVerifyToken(auth):
        """Verify id_token and returns the username."""
        r = requests.get('https://api.twitch.tv/api/oidc/keys')
        if r.status_code != 200:
            abort(503, "Cannot reach twitch api.")

        # Verify id_token
        k = r.json()['keys'][0]
        key = jwk.JWK(**k)
        try:
            ET = jwt.JWT(key=key, jwt=auth)
        except (jws.InvalidJWSObject, ValueError):
            abort(403, "Token format unrecognized or bad password.")
        except (jwt.JWTExpired):
            abort(403, "Token expired.")
        user_id = json.loads(ET.claims)['sub']

        # Check that audience in token is same as clientid
        if json.loads(ET.claims)['aud'] != clientID:
            abort(403, "Token not issued to this client.")

        # Get username for id
        headers = {'Client-id': clientID, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get('https://api.twitch.tv/kraken/users/{}'.format(user_id), headers=headers)
        if r.status_code != 200:
            abort(503, "Cannot reach twitch api.")

        return r.json()['name']
