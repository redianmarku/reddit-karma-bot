import praw
import time
from datetime import datetime
import random
import os
import slack

DELAY_TIME = input("Put the delay time in seconds between each comment reply (recomended 80): ")
SUBREDDIT_NAME = input("Put the name of subreddit that you want to comment (default is 'freekarma4u'): ")
sendSlackAlerts = False
mybot = praw.Reddit("bot1")
subreddit_name = "freekarma4u" if SUBREDDIT_NAME == "" else SUBREDDIT_NAME
subreddit = mybot.subreddit(subreddit_name)


if not os.path.isfile("posts_replied_to.txt"):
    with open("posts_replied_to.txt", 'w'):
        pass


def docomment():
    print("Bot started - Commenting every minute")
    randomposts = open("randomposts.txt").read().split('|')
    with open("posts_replied_to.txt", 'r') as done_file:
        done = done_file.read().split(',')

    for submission in subreddit.stream.submissions():
        if submission.id not in done:
            rand = random.randint(0, len(randomposts) - 1)
            randompost = randomposts[rand]
            print("Replying to post:", submission.title)
            submission.reply(randompost)

            for i in range(int(DELAY_TIME)):
                time.sleep(1)
                print(i)

            with open("posts_replied_to.txt", "a") as posts_replied_to:
                posts_replied_to.write(submission.id + ",")

            with open("posts_replied_to.txt", 'r') as done_file:
                done = done_file.read().split(',')


def go():
    try:
        docomment()
    except KeyboardInterrupt:
        print("\nBot stopped.")
        exit(0)
    except Exception as error:
        if not os.path.isfile("logs.txt"):
            open("logs.txt", 'w').write('')

        now = datetime.now()
        date = now.strftime("%m/%d/%Y %H:%M:%S")
        with open("logs.txt", 'a') as log_file:
            log_file.write("\n" + date)
            log_file.write("\n" + str(error))

        print("Unknown error. Check the 'logs.txt' file.")
        print('Waiting for 30 min')
        time.sleep(60 * 30)

        if sendSlackAlerts:
            slacktoken = open("slacktoken.txt").read()
            client = slack.WebClient(token=slacktoken)
            client.chat_postMessage(channel='alerts', text=f"An error has occurred:\n{error}")

        go()


go()
