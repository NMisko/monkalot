"""Allows to control the bot via REST calls."""
import json
import logging
import os
import requests
import threading
import urllib.parse

from bottle import ServerAdapter, abort, request, route, run
from jwcrypto import jwk, jws, jwt

from bot.paths import CONFIG_PATH
from bot.paths import OIDC_API, USER_ID_API

# Regarding decoding:
# https://bottlepy.org/docs/dev/tutorial.html#introducing-formsdict
# >>> request.forms['city'] [or request.forms.get('city')]
# 'GÃ¶ttingen' # An utf8 string provisionally decoded as ISO-8859-1 by the server
# >>> request.forms.city
# 'Göttingen'  # The same string correctly re-encoded as utf8 by bottle


class StoppableWSGIRefServer(ServerAdapter):
    """Allows to programmatically shut down bottle server."""

    isRunning = False

    def run(self, handler):
        """Start the server."""
        from wsgiref.simple_server import make_server, WSGIRequestHandler

        if self.quiet:

            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw):
                    pass

            self.options["handler_class"] = QuietHandler
        try:
            self.server = make_server(self.host, self.port, handler, **self.options)
            self.isRunning = True
            self.server.serve_forever()
        except OSError as err:
            if err.errno == 98:  # Address already in use
                self.isRunning = False
                logging.critical(
                    "Port {} already in use. Shutting down web server.".format(
                        self.port
                    )
                )
            else:
                raise

    def stop(self):
        """Stop the server."""
        # self.server.server_close() <--- alternative but causes bad fd exception
        if self.isRunning:
            self.server.shutdown()
        else:
            logging.warning("Server is already shut down.")


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
        api_server = StoppableWSGIRefServer(host="localhost", port=lport)

        global api_port
        api_port = lport

        global api_password
        api_password = password

        global clientID
        with open(CONFIG_PATH.format(bots[0].root), "r", encoding="utf-8") as file:
            CONFIG = json.load(file)
        clientID = str(CONFIG["clientID"])

        threading.Thread(target=run, kwargs=dict(server=api_server,)).start()

    def stop(self):
        """Stop the server."""
        api_server.stop()

    @staticmethod
    @route("/hello")
    def hello():
        """Return hw."""
        return "Hello World!\n"

    @staticmethod
    @route("/bots", method="POST")
    def get_bots():
        """Return list of all bots for given user."""
        WebAPI.check_if_form_exists(["user", "auth"])
        username = urllib.parse.unquote(request.forms.user)
        auth = urllib.parse.unquote(request.forms.auth)

        if not WebAPI.has_user_permission(username, auth):
            abort(403, "Bad authentication")

        logging.info("[API] [User: {}] /bots ".format(username))
        bots = []
        for bot in api_bots:
            if WebAPI.has_bot_permission(username, bot):
                bots.append(bot)

        out = []
        for bot in bots:
            out.append(WebAPI.get_bot_name(bot))
        return json.dumps(out)

    @staticmethod
    @route("/files", method="POST")
    def get_files():
        """Return list of all modifiable files for a given bot."""
        WebAPI.check_if_form_exists(["user", "bot", "auth"])
        username = urllib.parse.unquote(request.forms.user)
        botname = urllib.parse.unquote(request.forms.bot)
        auth = urllib.parse.unquote(request.forms.auth)

        bot = WebAPI.get_bot(botname)

        if not WebAPI.has_user_permission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.has_bot_permission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        logging.info("[API] [#{}] [User: {}] /files ".format(botname, username))

        data = os.listdir(bot.root + "data")
        configs = os.listdir(bot.root + "configs")
        out = []
        for d in data + configs:
            if ".json" in d:
                out.append(d)
        return json.dumps(out)

    @staticmethod
    @route("/file", method="POST")
    def get_file():
        """Return the content of a specific file."""
        WebAPI.check_if_form_exists(["user", "bot", "file", "auth"])
        username = urllib.parse.unquote(request.forms.user)
        botname = urllib.parse.unquote(request.forms.bot)
        filename = urllib.parse.unquote(request.forms.file)
        auth = urllib.parse.unquote(request.forms.auth)

        bot = WebAPI.get_bot(botname)
        if not WebAPI.has_user_permission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.has_bot_permission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        # For security
        filename = os.path.split(filename)[1]

        logging.info(
            "[API] [#{}] [User: {}] /file {} ".format(botname, username, filename)
        )

        path = None
        if os.path.isfile(bot.root + "configs/" + filename):
            path = bot.root + "configs/" + filename
        if os.path.isfile(bot.root + "data/" + filename):
            path = bot.root + "data/" + filename

        if path is None:
            abort(404, 'File "' + filename + '" not found.')

        with open(path) as fp:
            data = json.load(fp)

        return {"content": data}

    @staticmethod
    @route("/setfile", method="POST")
    def set_file():
        """Set the json of a specific file."""
        WebAPI.check_if_form_exists(["user", "bot", "file", "content", "auth"])
        username = urllib.parse.unquote(request.forms.user)
        botname = urllib.parse.unquote(request.forms.bot)
        filename = urllib.parse.unquote(request.forms.file)
        content = urllib.parse.unquote(request.forms.content)
        auth = urllib.parse.unquote(request.forms.auth)

        bot = WebAPI.get_bot(botname)
        if not WebAPI.has_user_permission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.has_bot_permission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        try:
            json_data = json.loads(content)
        except ValueError:
            abort(400, "A json dictionary is required.\n Given:\n" + str(content))

        # For security
        filename = os.path.split(filename)[1]

        logging.info(
            "[API] [#{}] [User: {}] /setfile {} ".format(botname, username, filename)
        )

        path = None
        if os.path.isfile(bot.root + "configs/" + filename):
            path = bot.root + "configs/" + filename
        if os.path.isfile(bot.root + "data/" + filename):
            path = bot.root + "data/" + filename

        if path is None:
            abort(404, 'File "' + filename + '" not found.')

        with open(path, mode="w") as file:
            json.dump(json_data, file, indent=4)

        bot.reload()

    @staticmethod
    @route("/getTwitchUsername", method="POST")
    def get_user_name_i():
        """Get the username based on an id_token. Also verifies token."""
        WebAPI.check_if_form_exists(["auth"])
        auth = urllib.parse.unquote(request.forms.auth)

        username = WebAPI.get_user_name_and_verify_token(auth)
        logging.info("[API] /getTwitchUsername => {} ".format(username))

        return {"username": username}

    @staticmethod
    @route("/pause", method="POST")
    def pause():
        """Pause or unpause a bot."""
        WebAPI.check_if_form_exists(["user", "bot", "auth", "pause"])
        username = urllib.parse.unquote(request.forms.user)
        botname = urllib.parse.unquote(request.forms.bot)
        auth = urllib.parse.unquote(request.forms.auth)
        pause = urllib.parse.unquote(request.forms.pause)

        bot = WebAPI.get_bot(botname)
        if not WebAPI.has_user_permission(username, auth):
            abort(403, "Bad authentication")

        if not WebAPI.has_bot_permission(username, bot):
            abort(403, "User doesn't have access to this bot.")

        logging.info(
            "[API] [#{}] [User: {}] /pause {}".format(botname, username, pause)
        )

        if pause == "true":
            bot.pause = True
        elif pause == "false":
            bot.pause = False
        else:
            abort(400, "pause must be either 'True' or 'False'")

    @staticmethod
    def check_if_form_exists(keys):
        """Get all forms for the given keys."""
        for k in keys:
            if k not in request.forms:
                abort(400, "Bad Request, expecting the following data:\n" + str(keys))

    @staticmethod
    def get_bot(botname):
        """Return the correct bot, based on its directory name."""
        bot = None
        for b in api_bots:
            if WebAPI.get_bot_name(b) == botname:
                bot = b
        if bot is None:
            abort(404, 'Bot "' + botname + '"not found.\n')

        return bot

    @staticmethod
    def get_bot_name(bot):
        """Return the correct bot name, based on its bot."""
        return bot.root.split("/")[len(bot.root.split("/")) - 2]

    @staticmethod
    def has_user_permission(username, auth):
        """Check if the user is authenticated."""
        # Check for password
        if api_password is not None:
            if auth == api_password:
                return True

        # If auth doesn't match password, assume id_token is submitted. Verify it.
        id_token_username = WebAPI.get_user_name_and_verify_token(auth)

        # Compare username from id_token with given username
        return username == id_token_username

    @staticmethod
    def has_bot_permission(username, bot):
        """Check if the user is allowed to access the bot."""
        with open(CONFIG_PATH.format(bot.root), "r", encoding="utf-8") as file:
            CONFIG = json.load(file)
        admins = CONFIG["owner_list"]
        return username in admins

    @staticmethod
    def get_user_name_and_verify_token(auth):
        """Verify id_token and returns the username."""
        r = requests.get(OIDC_API)
        if r.status_code != 200:
            abort(503, "Cannot reach twitch api.")

        # Verify id_token
        k = r.json()["keys"][0]
        key = jwk.JWK(**k)
        try:
            ET = jwt.JWT(key=key, jwt=auth)
        except (jws.InvalidJWSObject, ValueError):
            abort(403, "Token format unrecognized or bad password.")
        except (jwt.JWTExpired):
            abort(403, "Token expired.")
        user_id = json.loads(ET.claims)["sub"]

        # Check that audience in token is same as clientid
        if json.loads(ET.claims)["aud"] != clientID:
            abort(403, "Token not issued to this client.")

        # Get username for id
        headers = {"Client-id": clientID, "Accept": "application/vnd.twitchtv.v5+json"}
        r = requests.get(USER_ID_API.format(user_id), headers=headers)
        if r.status_code != 200:
            abort(503, "Cannot reach twitch api.")

        return r.json()["name"]
