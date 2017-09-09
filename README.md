**Monkalot**
===============
A bot for [Zetalot's Twitch stream](https://twitch.tv/zetalot).

![monkaS](http://i3.kym-cdn.com/entries/icons/original/000/022/713/4.png)

Uses [SimpleTwitchBot](https://github.com/EhsanKia/SimpleTwitchBot) by [EhsanKia](https://github.com/EhsanKia/) as base.

# Installation and usage
Clone this project and install all necessary packages in `requirements.txt`.
Copy the `template` folder in `channels`, rename it and fill in the values in `bot_config.json`.
Then start the bot by starting `monkalot.py`.

Multiple bots can be started by adding more folders with different configurations to `channels`.

#### Configuration:
Make sure to modify the following values in `bot_config.json`:
- `channel`: Twitch channel which the bot will run on
- `username`: The bot's Twitch user
- `clientID`: Twitch ClientID for API calls.
- `oauth_key`: IRC oauth_key for the bot user (from [here](http://twitchapps.com/tmi/))
- `owner_list`: List of Twitch users which have admin powers on bot
- `ignore_list`: List of Twitch users which will be ignored by the bot
- `cleverbot_key`: Cleverbot API Key for native speech.

**Warning**: Make sure all channel and user names above are in lowercase.

#### Additional Configuration Parameters:
- `points`: Various parameters that balance point-distribution for the different games.
- `ranking`: Ranking System Point Distribution -> Rank_n = base * factor^n
- `auto_game_interval`: Time between automaticly started games while AutoGames are on.
- `pleb_cooldown`: Time between normal chat user commands.
- `pleb_gametimer`: Time between games started by normal chat users.
- `EmoteGame`: Preset of emotes used in the `!estart`- command.

# Code Overview

#####`monkalot.py`
This is the file that you run. It just starts up a Twisted IRC connection with the bot protocol.
The bot is currently built to only run in one channel, but you can still open all the files over
to another folder with a different config and run it in parallel.

#####`bot.py`
Contains the bot IRC protocol. The main guts of the bot are here.

#####`commands.py`
This is where the commands are stored. The code is built to be modular.
Each "Command" class has:
- `perm` variable from the Permission Enum to set access level
- `__init__` function that initializes the command
- `match` function that checks if this command needs to run
- `run` function which actually runs the command
- `close` function which is used to cleanup and save things

All commands are passed the bot instance where they can get list of mods, subs and active users.
`match` and `run` are also passed the name of the user issuing the command and the message.

# Chat Command List

All commands that can be called from chat via different calls. Note that some commands can only be called by Moderators, Trusted-Moderators or Bot-Admins. Chat games can also be started by regular users, if they have spam points to pay for it.

### All-User commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!active`             | Returns the amount of active viewers in chat. | - |
| `!smorc`              | Returns a random SMOrc quote. | - |
| `!quote [<number>]`   | Returns a random quote. Optional a number can be given to call a specific quote. | `!quote` , `!quote 2` |
| `!slap <user>`        | Sends a slap to another user. | `!slap Monkalot` |
| `!hug <user>`         | Sends a hug to another user. | `!hug Monkalot` |
| `!pjsalt`             | Sends a pjsalt pyramid in chat.      | - |
| `!call <emote> <text>`| Sends a call interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!call Kappa a nice stream` |
| `!any <emote> <text>` | Sends out any sentence interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!any Jebaited Long have we waited, now we Jebaited` |
| `!word <emote> <text>`| Sends a word with an emote interlaced between letters. All Twitch- and BTTV-emotes and emojis are supported. | `!word monkaS dragons` |
| `!rank [<username>]`  | Returns the current spam-rank and -points for the chatter or optional for a specific <username>. | `!rank` , `!rank monkalot` |
| `!topspammers`        | Returns the five highest ranked spammers. | - |
| `!kpm`                | Returns the amount of Kappas per minute in channel. | - |
| `!tkp`                | Returns the total amount of Kappas in channel. | - |
| `!minute <emote>`     | Returns the amount of a specific emote per minute in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!minute BabyRage` |
| `!total <emote>`      | Returns the total amount of a specific emote in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!total EleGiggle` |
| `!oralpleasure on/off`  | Turns oralpleasure on or off. | - |
| `!calc <formula>`       | A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry. | `!calc (5+7)/2` , <br>`!calc log(5^2) + sin(pi/4)` |
| `<botname> <text>`      | Talk to the bot. Questions can be asked or a conversation can be started with the native speech engine. | `Hey Monkalot, how are you doing?`, `What's 2Head + 2Head? @Monkalot` |

### Chat games:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!kstart`, `[!pstop]` | Starts the *KappaGame*. Guess the right amount of Kappas to win. Type Kappas to start playing. | - |
| `!estart`, `[!estop]`, `[!emotes]`| Starts the *GuessEmoteGame*. Guess the right emote from the list. Type emotes to start playing. While the game is active `!emotes` shows all possible emotes. | - |
| `!mstart`, `[!mstop]` | Starts the *GuessMinionGame*. Guess the right minion card. Type minion names to play. After a short time the game will give clues to the chat. | - |
| `!pstart`, `[!pstop]` | Starts the *MonkalotParty*. A Minigames tournament with 7 games by default. | - |
| `<emote>-pyramids`    | Build emote pyramids to gain spampoints. All Twitch- and BTTV-emotes and emojis are supported. | `Kappa`<br/>`Kappa`&nbsp;`Kappa`<br/>`Kappa` |

All games can be canceled by their respected `!stop` command.

### Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addquote <quote>`   | Adds a quote to the *quotelist*. | `!addquote "Priest in 2k17 LUL"` |
| `!delquote <quote>`   | Deletes a quote from the *quotelist*. | `!delquote "Priest in 2k17 LUL"` |
| <nobr>`!block on/off`</nobr>     | Turns pyramidblock on or off. If on, pyramids will be interupted by the bot. | - |
| <nobr>`!games on/off`</nobr>     | Turns automatic games on or off. If on, *chatgames* will start automaticly after a certain amount of time. | - |

### Trusted-Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!sleep`    			| Puts the bot in *sleepmode*. All games will be disabled and the bot only responses to admins | - |
| `!wakeup`    			| Puts the in normal mode again. | - |
| `!addcommand <command> <response>` | Adds a command to the *simplereply*-list. | `!addcommand !ping pong` |
| `!delcommand <command>`| Deletes a command from the *simplereply*-list. | `!delcommand !ping` |
| `!replylist`          | Returns all available commands from the *simplereply*-list. | - |

### Admin commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addmod <username>`  | Adds a mod to the list of *trusted mods*. | `!addmod Monkalot` |
| `!delmod <username>`  | Deletes a mod from the list of *trusted mods*. | `!delmod Monkalot` |
| `!g <username> <pronouns>` | Allows changing gender pronouns for a user. Three pronouns have to be given. | `!g monkalot she her hers` |
