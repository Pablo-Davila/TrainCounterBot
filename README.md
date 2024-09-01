

# TrainCounterBot

Have you ever wanted to set a daily/weekly training objective? Maybe just a simple +1/-1 counter? This bot makes it easier by keeping track of your collection of counters and increasing them with the frequency you want.

It is based on [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI"), a Python interface for the [Telegram Bot API](https://core.telegram.org/bots/api).

**Try it in Telegram**: [TrainCounterBot](https://t.me/TrainCounterBot)


## Usage

To run your own instance of this bot you must first [register a new Telegram bot](https://core.telegram.org/bots#6-botfather). Once you have a token for your bot, you may proceed with options 1 or 2.


### Option 1: Manual execution

First, you have to create the necessary environment variables:
  - `BOT_TOKEN`: The token you obtained in the previous step.
  - `DATA_DIR_PATH`: The path for the data directory.

After that, you only need to execute the following terminal command:

```Bash
python ./src/train_counter_bot.py
```

This will run the bot attached to your current terminal. If you want it to stay in the background you should have a look at tools like [`tmux`](https://github.com/tmux/tmux).


### Option 2: Docker container (recommended)

First, you have to create a ".env" file in the repository root with the following format:

```
DATA_DIR_PATH=pat_to_the_data_directory
BOT_TOKEN=your_bot_token_here
```

Now, you can run the bot with a single `docker` command:

```Bash
docker compose up -d --build
```

This will run the bot as a Docker container in the background.
