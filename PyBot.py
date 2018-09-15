import time
import re
import praw
from slackclient import SlackClient

# Read credentials from file
f = open("auth.txt", 'r')
lines = f.read().splitlines()
SLACK_OAUTH = lines[1]
REDDIT_USERNAME = lines[4]
REDDIT_PASSWORD = lines[5]
REDDIT_API_USERNAME = lines[8]
REDDIT_API_PASSWORD = lines[9]
f.close()

# Instantiate Slack Client
slack_client = SlackClient(SLACK_OAUTH)

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "creator"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

# Creator's user ID
request = slack_client.api_call("users.list")
if request['ok']:
    for item in request['members']:
        if item['name'] == 'liam.hinzman':
            creatorID = item['id']

# Setup PRAW variables
reddit = praw.Reddit(client_id=REDDIT_API_USERNAME,
                     client_secret=REDDIT_API_PASSWORD,
                     password=REDDIT_PASSWORD,
                     username=REDDIT_USERNAME,
                     user_agent='RedditDigest')

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        # Filter events to only consider messages
        if event["type"] == "message" and not "subtype" in event:
            print(event)
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"], event["user"], event["event_ts"]
    return None, None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # First group contains the username, Second group contains the remaining message
    if matches:
        return (matches.group(1), matches.group(2).strip())
    else:
        return (None, None)

def handle_command(command, channel, user, eventThread):
    """
        Execute bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "I'm not sure what you mean. Try *{}*".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    command = command.lower()
    response = None

    if ("suggestion" in command) or ("suggest" in command):
        # Get username of suggestion sender
        request = slack_client.api_call("users.list")
        if request['ok']:
            for item in request['members']:
                if item['id'] == user:
                    suggestion_sender = item['name']

        response = "Your suggestion was sent to to Liam Hinzman!"
        suggestion = "@{}'s suggestion for PyBot: \n {}".format(suggestion_sender, command)

        slack_client.api_call(
            "chat.postMessage",
            channel=creatorID,
            text=suggestion or default_response
        )

    elif "creator" in command:
        response = "I was created by Liam Hinzman"

    elif ("source code" in command) or ("repo" in command):
        response = "My github repo is hosted at https://github.com/LiamHz/PyBot"

    elif "resources" in command:
        if "programming" in command:
            response = []
            response.append("*Learn Python on CodeCademy*: https://www.codecademy.com/learn/learn-python")
            response.append("*WebDev Course*: https://www.theodinproject.com/")
            response = "\n".join(response)
        elif ("machine learning" in command) or ("ml" in command):
            response = []
            response.append("Note: ML stands for Machine Learning")
            response.append("*Google's ML Crash Course*: https://developers.google.com/machine-learning/crash-course/prereqs-and-prework")
            response.append("*ML with Andrew Ng*: https://www.coursera.org/learn/machine-learning")
            response.append("*TensorFlow Tutorials*: https://www.tensorflow.org/tutorials/")
            response = "\n".join(response)
        elif ("cryptocurrency" in command) or ("crypto" in command) or ("bitcoin" in command):
            response = []
            response.append("*How Cyrptocurrencies Work*: https://youtu.be/bBC-nXj3Ng4")
            response.append("*The Original Bitcon Whitepaper*: https://www.bitcoin.com/bitcoin.pdf")
            response = "\n".join(response)
        elif "fitness" in command:
            response = []
            response.append("*Intro to Weight Lifting*: https://docs.google.com/document/d/1l3TxRVjwqNGNpa1m0V_aRuIa_ZMujhYpsmBA653IIT4/edit?usp=sharing")
            response.append("*No Gym? Bodyweight Fitness Routine*: https://www.reddit.com/r/bodyweightfitness/wiki/kb/recommended_routine")
            response.append("*Exercise's Benfits to Mental Health*: https://www.helpguide.org/articles/healthy-living/the-mental-health-benefits-of-exercise.htm")
            response = "\n".join(response)
        else:
            response = "type 'resources' plus a category such as: programming / machine learning / crypto / fitness"

    # Respond with the top 3 posts of the day from r/WorldNews
    elif "news" in command:
        submissions = []
        subreddit = reddit.subreddit('WorldNews')
        subredditLimit = 3

        for submission in subreddit.top(time_filter='day', limit=subredditLimit):
            submissions.append("*{}*: {}".format(submission.title, submission.url))

        response = []
        response.append("The top 3 stories of today on r/WorldNews are:")
        for i in range(len(submissions)):
            response.append(submissions[i])
        response = "\n".join(response)

    elif ("commands" in command) or ("list" in command):
        response = []
        response.append("Here's a list of my available commands")
        response.append("*suggest* -- Suggest a feature request to Liam (bot creator)")
        response.append("*repo* -- Send a link to the github repo for PyBot")
        response.append("*resources* -- Send a list of resources for a supported topic")
        response.append("*news* -- Send the top 3 news stories of the day")
        response = "\n".join(response)

    if ("send public" in command):
        eventThread = 'nil'

    if eventThread != 'nil':
        # Send the response back in thread
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response,
            thread_ts=eventThread
        )
    else:
        # Send the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response,
        )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("PyBot connected and running!")
        # Read bot's user ID by calling Web API method 'auth.test'
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, user, eventThread = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, user, eventThread)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above")
