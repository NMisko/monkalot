**Monkalot**
===============

Subjectively the best twitch bot. 

Easy to get running, highly modular and [fast to extend](#adding-a-new-custom-command), 
monkalot is almost fully configurable on a channel by channel basis. 
Fully modifiable texts allow for full localization on each channel (if you have the patience to translate).
These configurations can also be controlled via [REST api](#rest-api) or through a [Web Interface](https://github.com/NMisko/monkalot-ui).

## Quick Start
Clone this project.  
`$ git clone https://github.com/NMisko/monkalot.git`

Switch into it.  
`$ cd monkalot`

Install all necessary packages.  
`$ pip install -r requirements.txt`

Copy the `template` folder in `channels`, rename it to whatever channel 
the bot needs to run on.  
`$ cp -r channels/template channels/<your_channel>`

Set the configuration parameters in `channels/<your_channel/configs/bot_config.json` (see configuration section).

Then start the bot.  
`$ python3 monkalot.py`

Multiple bots can be started by adding more folders with different configurations to `channels`.

#### Configuration:
Make sure to modify the following values in `bot_config.json`:
- `channel`: Twitch channel which the bot will run on
- `username`: The bot's Twitch user
- `clientID`: Twitch ClientID for API calls.
- `oauth_key`: IRC oauth_key for the bot user (from [here](http://twitchapps.com/tmi/))
- `access_token`: access token for the bot user (see [here](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow))
- `owner_list`: List of Twitch users which have admin powers on bot
- `ignore_list`: List of Twitch users which will be ignored by the bot

**Warning**: Make sure all channel and user names above are in lowercase.

#### Additional Configuration Parameters:
- `points`: Various parameters that balance point-distribution for the different games.
- `ranking`: Ranking System Point Distribution -> Rank_n = base * factor^n
- `auto_game_interval`: Time between automaticly started games while AutoGames are on.
- `pleb_cooldown`: Time between normal chat user commands.
- `pleb_gametimer`: Time between games started by normal chat users.
- `EmoteGame`: Preset of emotes used in the `!estart`- command.


# Commands

All commands that can be called from chat via different calls. Note that some commands can only be called by Moderators, Trusted-Moderators or Bot-Admins. Chat games can also be started by regular users, if they have spam points to pay for it.

### All-User commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!any <emote> <text>` | Sends out any sentence interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!any Jebaited Long have we waited, now we Jebaited` |
| `!bttv`               | Returns all bttv emotes on this channel (messy) | - |
| `!calc <formula>`     | A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry. | `!calc (5+7)/2` , <br>`!calc log(5^2) + sin(pi/4)` |
| `!call <emote> <text>`| Sends a call interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!call Kappa a nice stream` |
| `!fps`                | Returns the fps of the stream | - |
| `!hug <user>`         | Sends a hug to another user. | `!hug Monkalot` |
| `!kpm`                | Returns the amount of Kappas per minute in channel. | - |
| `!minute <emote>`     | Returns the amount of a specific emote per minute in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!minute BabyRage` |
| `!oralpleasure on/off`| Turns oralpleasure on or off. | - |
| `!penta <emote>`      | Quintuples an emote | `!penta PunOko` |
| `!pjsalt`             | Sends a pjsalt pyramid in chat.      | - |
| `!quote [<number>]`   | Returns a random quote. Optional a number can be given to call a specific quote. | `!quote` , `!quote 2` |
| `!rank [<username>]`  | Returns the current spam-rank and -points for the chatter or optional for a specific <username>. | `!rank` , `!rank monkalot` |
| `!slap <user>`        | Sends a slap to another user. | `!slap Monkalot` |
| `!smorc`              | Returns a random SMOrc quote. | - |
| `!tenta <emote>`      | Gives an emote some tentacles | `!tenta WutFace` |
| `!tip <user> <amount>`| Transfers an amount of channel points to another user. | `!tip Keepo 500` |
| `!tkp`                | Returns the total amount of Kappas in channel. | - |
| `!topspammers`        | Returns the five highest ranked spammers. | - |
| `!total <emote>`      | Returns the total amount of a specific emote in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!total EleGiggle` |
| `!uptime`             | Returns how long this stream has been on | - | 
| `!word <emote> <text>`| Sends a word with an emote interlaced between letters. All Twitch- and BTTV-emotes and emojis are supported. | `!word monkaS dragons` |
| `<botname> <text>`    | Talk to the bot. Questions can be asked or a conversation can be started with the native speech engine. | `Hey Monkalot, how are you doing?`, `What's 2Head + 2Head? @Monkalot` |
| `@monkalot ban me`    | Users can ask the bot to get banned (they will get banned and unbanned immediately) | `@monkalot ban me please :)` |
| `[<hearthstone card>]`| Get some information about a hearthstone card. Allows up to two spelling mistakes. | `[Malganis]` |


### Chat games:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!estart`, `[!estop]`, `[!emotes]`| Starts the *GuessEmoteGame*. Guess the right emote from the list. Type emotes to start playing. While the game is active `!emotes` shows all possible emotes. | - |
| `!kstart`, `[!pstop]` | Starts the *KappaGame*. Guess the right amount of Kappas to win. Type Kappas to start playing. | - |
| `!mstart`, `[!mstop]` | Starts the *GuessMinionGame*. Guess the right minion card. Type minion names to play. After a short time the game will give clues to the chat. | - |
| `!pstart`, `[!pstop]` | Starts the *MonkalotParty*. A Minigames tournament with 7 games by default. | - |
| `<emote>-pyramids`    | Build emote pyramids to gain spampoints. All Twitch- and BTTV-emotes and emojis are supported. | `Kappa`<br/>`Kappa`&nbsp;`Kappa`<br/>`Kappa` |

All games can be canceled by their respected `!stop` command.

### Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addnotification <msg>` | Adds a message to the notification message rotation | `!addnotification Please remember to drink water. :)` |
| `!delnotification <msg>` | Removes a message from the notification message rotation | `!delnotification wheeeeee` |
| `!addquote <quote>`   | Adds a quote to the *quotelist*. | `!addquote "Priest in 2k17 LUL"` |
| `!delquote <quote>`   | Deletes a quote from the *quotelist*. | `!delquote "Priest in 2k17 LUL"` |
| `!block on/off`       | Turns pyramidblock on or off. If on, pyramids will be interupted by the bot. | - |
| `!games on/off`       | Turns automatic games on or off. If on, *chatgames* will start automaticly after a certain amount of time. | - |
| `!notifications on/off`   | Enables or disables notifications. Notifications are messages that get sent out in regular intervals. | - |

### Trusted-Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addcommand <command> <response>` | Adds a command to the *simplereply*-list. | `!addcommand !ping pong` |
| `!clearcache`         | Clears the cache. Use this e.g. to load newly released twitch emotes | - |
| `!delcommand <command>`| Deletes a command from the *simplereply*-list. | `!delcommand !ping` |
| `!ignore <user>`      | Makes the bot ignore a user. Please enter the username in lowercase. | - |
| `!unignore <user>`    | Makes the bot no longer ignore a user. Please enter the username in lowercase. | - |
| `!replylist`          | Returns all available commands from the *simplereply*-list. | - |
| `!sleep`    			| Puts the bot in *sleepmode*. All games will be disabled and the bot only responses to admins | - |
| `!wakeup`    			| Puts the in normal mode again. | - |


### Admin commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addmod <username>`  | Adds a mod to the list of *trusted mods*. | `!addmod Monkalot` |
| `!delmod <username>`  | Deletes a mod from the list of *trusted mods*. | `!delmod Monkalot` |
| `!g <username> <pronouns>` | Allows changing gender pronouns for a user. Three pronouns have to be given. | `!g monkalot she her hers` |


# Adding a new custom command
Create a command which inherits from [command.py](/bot/commands/abstract/command.py) in a new file and add it to the [commands](/bot/commands/) folder.
Then import your new class into [\_\_init\_\_.py](/bot/commands/__init__.py) and add it to one of the command arrays, depending on its priority.

# REST Api
The REST Api allows to control the bot via POST requests. It must be enabled by setting the port using the `-p` flag. You can set a password using the `-s` flag. Using a password gives access to all the bots. Alternatively pass a twitch id token, which gives access to the bots of the owner of the id token.

Example:
Run bot with: `./monkalot.py -p 8080 -s Kappa`. Assume there is one bot called *Monkalot*, owned by *Alice*.

---

```bash
curl --data 'user=alice&auth=Kappa' localhost:8080/bots
```

Returns every bot *Alice* is admin of.

\=\> `["monkalot"]`

---

```bash
curl --data 'user=alice&bot=monkalot&auth=Kappa' localhost:8080/files
```

Returns all configurable files of *Monkalot*.

\=\> `\["ignored_users.json", "sreply_cmds.json", "quotes.json", "pronouns.json", "smorc.json", "notifications.json", "emote_stats.json", "monkalot_party.json", "slaphug.json", "trusted_mods.json", "bot_config.json", "responses.json"]`

---

```bash
curl --data 'user=alice&bot=monkalot&file=ignored_users.json&auth=Kappa' localhost:8080/file
```

Returns the content of *ignored_users.json*.

\=\> `{"content": ['bob']}`

---

```bash
curl --data 'user=alice&bot=monkalot&file=ignored_users.json&content=["Bob","Carl"]&auth=Kappa' localhost:8080/setfile```
```

Sets the content of *ignored_users.json* to *["Bob","Carl"]*.

---


```bash
curl --data 'auth=xyz' localhost:8080/getTwitchUsername
```

Utility function. Takes a twitch id token and returns the username associated to it. Also ensures the token is valid.

---

```bash
curl --data 'user=alice&bot=monkalot&pause=True&auth=Kappa' localhost:8080/pause
```

Pauses the bot. Set pause = false to unpause the bot.

---

*(Based on [SimpleTwitchBot](https://github.com/EhsanKia/SimpleTwitchBot) by [EhsanKia](https://github.com/EhsanKia/).)*
