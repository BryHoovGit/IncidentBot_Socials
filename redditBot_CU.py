import praw
import datetime
import pytz
import requests
import dotenv
import os
import logging

# Load the environment variables
dotenv.load_dotenv()

# Get the webhook URL and subreddit name from the environment variables
webhook_url = os.getenv("WEBHOOK_URL")
subreddit_name = os.getenv("SUBREDDIT_NAME")

# Create a logger object.
logger = logging.getLogger(__name__)

# Set the log level.
logger.setLevel(logging.DEBUG)

# Create a StreamHandler object and pass it to the logger's addHandler() method.
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

# Create a formatter object.
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

# Set the StreamHandler object's formatter attribute.
stream_handler.setFormatter(formatter)

# Create a Reddit instance
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent=os.getenv("USER_AGENT"))

# Get the subreddit
subreddit = reddit.subreddit(subreddit_name)

# Get the last 10 posts from the subreddit
posts = subreddit.new(limit=10)

# Get the phrases you want to search for from the environment variable
phrases = [phrase.strip("[]").replace('"', '')
           for phrase in os.getenv("PHRASES").split(",")]


def check_post_for_phrases(post, phrases):
    """Checks a post for one of the phrases in either post.title or post.selftext.

    Args:
      post: A PRAW submission object.
      phrases: A list of strings to search for.

    Returns:
      True if the post contains one of the phrases, False otherwise.
    """

    for phrase in phrases:
        if phrase in post.title or phrase in post.selftext:
            return True
    return False


def is_office_hours():
    # Checks if it is currently office hours in Pacific Standard Time (PST).

    date_format = '%m_%d_%Y_%H_%M_%S_%Z'
    now = datetime.datetime.now(tz=pytz.timezone('UTC'))
    pst_now = now.astimezone(pytz.timezone('US/Pacific'))
    pst_datetime = pst_now.strftime(date_format)
    hour = int(pst_datetime.split('_')[3])

    return hour >= 9 and hour < 17

logger.info(f"🕑 Triggered during office hours: {is_office_hours()}🕑")

logger.info(f"🕵️‍♀️ Searching last 10 posts to /r/{subreddit}.🕵️‍♀️")
# Check each post for the specified phrases and send a POST request to webhook.site if one is found
for post in posts:
    if check_post_for_phrases(post, phrases):
        # Log a message to the logger
        logger.info(f'✅ Found match.✅')
        logger.info(f'✅ {post.title}✅')
        # Create a POST request to webhook.site
        payload = {
            "post_id": post.id,
            "post_title": post.title,
            "post_url": post.url,
            "post_text": post.selftext,
            "is_office_hours": is_office_hours()
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(webhook_url, json=payload, headers=headers)
        logger.info(f"📤 Sending match to webhook.📤")
        # Check if the POST request was successful
        if response.status_code == 200:
            logger.info(f"👍 POST request to {webhook_url} was successful.👍")
        else:
            logger.error(
                f"👎 POST request to {webhook_url} failed with status code {response.status_code}.👎")
    else:
        logger.debug(f'❌ {post.title}❌')
