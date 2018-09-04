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
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

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

def handle_command(command, channel):
    """
        Execute bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "I'm not sure what you mean. Try *{}*".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    command = command.lower()
    response = None

    if "creator" in command:
        response = "I was created by Liam Hinzman"

    if "source code" in command:
        response = "My github repo is hosted at https://github.com/LiamHz/PyBot"

    if "news" in command:
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

    # Send the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("PyBot connected and running!")
        # Read bot's user ID by calling Web API method 'auth.test'
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above")
