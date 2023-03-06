import argparse
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import random
import os
import praw
import time
import re
from requests import get
from slack_sdk.webhook import WebhookClient

def loadArguments():
    global args, postsRepliedToFile, logsFile
    parser = argparse.ArgumentParser(
        prog='karma-farm.py', description='A bot that farms karma on reddit')
    parser.add_argument('username', help='The username of the bot')
    parser.add_argument("-s", "--sendSlackAlerts",
                        help="Send slack alerts when an error occurs", action="store_true")
    args = parser.parse_args()
    postsRepliedToFile = "posts_replied_to-" + str(args.username) + ".txt"
    logsFile = "logs-" + str(args.username) + ".txt"

def setup():
    global ipAddress, begginningOfMessage
    if not os.path.isfile(postsRepliedToFile):
        file = open(postsRepliedToFile, 'w')
        file.write('')
        file.close()
    if not os.path.isfile(logsFile):
        file = open(logsFile, 'w')
        file.write('')
        file.close()
    ipAddress = get('https://ipecho.net/plain').text
    begginningOfMessage = f"{ipAddress} - {args.username} - "

def loadRedditBot():
    global redditBot, slackToken
    redditBot = praw.Reddit(args.username)
    printTo("Logged in as: "+redditBot.user.me().name)
    getKarma()

def getKarma():
    redditBot.user.me().refresh()
    printTo("Karma: "+str(redditBot.user.me().comment_karma))


def loadScheduler():
    global sched
    sched=BackgroundScheduler()
    sched.add_job(getKarma, 'interval', minutes=30)
    sched.start()

def slackAlert(message):
    if args.sendSlackAlerts:
        try:
            slacktoken = open("slackWebHook.txt").read()
            client = WebhookClient(slacktoken)
            response=client.send(text=message)
            assert response.status_code == 200
            assert response.body == "ok"
        except Exception as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            printTo("Error sending slack alert: "+e.response["error"], slack=False, error=True)


def doComment():
    subreddit = redditBot.subreddit("freekarma4u")
    randomposts = open("randomposts.txt").read()
    randomposts = randomposts.split('\n')
    for submission in subreddit.stream.submissions():
        done = open(postsRepliedToFile, 'r').read().split(',')
        if submission.id not in done:
            rand = random.randint(0, len(randomposts)-1)
            randompost = randomposts[rand]
            printTo("Replying to post: "+submission.title, slack=False)
            submission.reply(randompost)
            time.sleep(80)
            with open(postsRepliedToFile, "a") as posts_replied_to:
                posts_replied_to.write(submission.id+",")
            done = open(postsRepliedToFile, 'r').read().split(',')

def printTo(message, slack=True, error=False):
    if not error:
        message = begginningOfMessage + message
    else:
        message = begginningOfMessage + f"*ERROR*: {message}"
    date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    with open(logsFile, "a") as file:
        file.write(date +" - " + message + "\n")
    if slack:
        slackAlert(message)

def go():
    global isInit
    try:
        if not isInit:
            isInit = True
            loadArguments()
            setup()
            loadRedditBot()
            loadScheduler()
            printTo("Bot started - Commenting every minute")
        doComment()
    except KeyboardInterrupt:
        sched.shutdown()
        printTo("Stopping Bot...")
        exit(0)
    except Exception as error:
        breakTime = int(re.search(r"\d+", str(error))) + 2
        printTo(error, error=True)

        printTo(f"Restarting Bot in {breakTime} minutes...", slack=False)
        time.sleep(60*breakTime)
        go()

isInit = False
go()
