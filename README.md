**Monkalot**
===============
A bot for [Zetalot's Twitch stream](https://twitch.tv/zetalot). 

![monkaS](http://i3.kym-cdn.com/entries/icons/original/000/022/713/4.png)

Uses [SimpleTwitchBot](https://github.com/EhsanKia/SimpleTwitchBot) by [EhsanKia](https://github.com/EhsanKia/) as base.

# Installation and usage
All you should need is Python 3.6+ with [Twisted](https://twistedmatrix.com/trac/) installed.
You then copy this project in a folder, configure the bot and run `twitch_irc.py`.

#### Configuration:
Make sure to modify the following values in `bot_config.json`:
- `channel`: Twitch channel which the bot will run on
- `username`: The bot's Twitch user
- `oauth_key`: IRC oauth_key for the bot user (from [here](http://twitchapps.com/tmi/))
- `owner_list`: List of Twitch users which have admin powers on bot
- `ignore_list`: List of Twitch users which will be ignored by the bot

**Warning**: Make sure all channel and user names above are in lowercase.

#### Usage:
The main command-line window will show chat log and other extra messsages.
You can enter commands by pressing CTRL+C on the command line:
- `q`: Closes the bot
- `r`: Reloads the code in `bot.py` and reconnects
- `ra`: reloads the code in `commands.py` and reloads commands
- `p`: Pauses bot, ignoring commands from non-admins
- `t <msg>`: Runs a test command with the bot's reply not being sent to the channel
- `s <msg>`: Say something as the bot in the channel

As you can see, the bot was made to be easy to modify live.
You can simply modify most of the code and quickly reload it.
The bot will also auto-reconnect if the connection is lost.

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
| `!active`             | Return the amount of active viewers in chat. | - |
| `!smorc`              | Send a random SMOrc quote. | - |
| `!quote [<number>]`   | Send a random quote. Optional a number can be given to call a specific quote. | `!quote` , `!quote 2` |
| `!pjsalt`             | Send a pjsalt pyramid in chat.      | - |
| `!call <emote> <text>`| Sends a call interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!call Kappa a nice stream` |
| `!any <emote> <text>` | Sends any sentence interlaced by an emote. All Twitch- and BTTV-emotes and emojis are supported. | `!any Jebaited Long have we waited, now we Jebaited` |
| `!word <emote> <text>`| Sends a word with an emote interlaced between letters. All Twitch- and BTTV-emotes and emojis are supported. | `!word monkaS dragons` |
| `!rank [<username>]`  | Return the current spam-rank and -points for the chatter or optional for a specific <username>. | `!rank` , `!rank monkalot` |
| `!topspammers`        | Return the five highest ranked spammers. | - |
| `!kpm`                | Send out the amount of Kappas per minute in channel. | - |
| `!tkp`                | Send out the total amount of Kappas in channel. | - |
| `!minute <emote>`     | Send out the amount of a specific emote per minute in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!minute BabyRage` |
| `!total <emote>`      | Send out the total amount of a specific emote in channel. All Twitch- and BTTV-emotes and emojis are supported. | `!total EleGiggle` |
| `!oralpleasure on / off`  | Turn oralpleasure on or off. | - |
| `!calc <formula>`       | A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry. | `!calc (5+7)/2` , `!calc log(5^2) + sin(pi/4)` |
| `<botname> <text>`      | Talk to the bot. Questions can be asked or a conversation can be started with the native speech engine. | `Hey Monkalot, how are you doing?`, `What's 2Head + 2Head? @Monkalot` |

### Chat games:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!kstart`             | Start the *KappaGame*. Guess the right amount of Kappas to win. Type Kappas to start playing. | - |
| `!estart`, `[!emotes]`| Start the *GuessEmoteGame*. Guess the right emote from the list. Type emotes to start playing. While the game is active `!emotes` shows all possible emotes. | - |
| `!mstart`             | Start the *GuessMinionGame*. Guess the right minion card. Type minion names to play. After a short time the game will give clues to the chat. | - |
| `<emote>-pyramids`    | Build emote pyramids to gain spampoints. All Twitch- and BTTV-emotes and emojis are supported. | `Kappa` <br> `Kappa Kappa` <br> `Kappa` |

### Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addquote <quote>`   | Add a quote to the *quotelist*. | `!addquote "Priest in 2k17 LUL"` |
| `!delquote <quote>`   | Delete a quote from the *quotelist*. | `!delquote "Priest in 2k17 LUL"` |
| `!block on / off`     | Turn pyramidblock on or off. If on, pyramids will be interupted by the bot. | - |
| `!games on / off`     | Turn automatic games on or off. If on, *chatgames* will start automaticly after a certain amount of time. | - |

### Trusted-Moderator commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!addmod <username>`  | Add a mod to the list of *trusted mods*. | `!addmod Monkalot` |
| `!delmod <username>`  | Delete a mod from the list of *trusted mods*. | `!delmod Monkalot` |
| `!addcommand <command> <response>` | Add a command to the *simplereply*-list. | `!addcommand !ping pong` |
| `!delcommand <command>`| Delete a command from the *simplereply*-list. | `!delcommand !ping` |
| `!replylist`          | Return all available commands from the *simplereply*-list. | - |

### Admin commands:

| Command               | Description           | Examples  |
| --------------------- | --------------------- | --------- |
| `!sleep`    			| Puts the bot in *sleepmode*. All games will be disabled and the bot only responses to admins | - |
| `!wakeup`    			| Puts the in normal mode again. | - |
| `!g <username> <pronouns>` | Allows changing gender pronouns for a user. Three pronouns have to be given. | `!g monkalot she her hers` |






