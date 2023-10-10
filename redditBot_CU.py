import praw
import datetime
import pytz
import requests
import dotenv
import os

# Load the environment variables
dotenv.load_dotenv()
# Get the webhook URL from the environment variables
webhook_url = os.getenv("WEBHOOK_URL")
phrases = os.getenv("PHRASES").split(",")
# Create a Reddit instance
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent=os.getenv("USER_AGENT"))


def isOfficeHours():
    date_format = '%m_%d_%Y_%H_%M_%S_%Z'
    # Get the current time in PST.
    date = datetime.datetime.now(tz=pytz.timezone('UTC'))
    date = date.astimezone(pytz.timezone('US/Pacific'))
    # Get the PST date and time in the specified format.
    pst_datetime = date.strftime(date_format)
    # Parse the hour value from the formatted string.
    hour = int(pst_datetime.split('_')[3])
    # Format the PST date and time into the desired format.
    formatted_datetime = date.strftime('%m/%d/%Y %H:%M PST')
    print(formatted_datetime)

    # Check if the time is between 9am and 5pm in PST.
    if hour >= 9 and hour < 17:
        return True
    else:
        return False


if isOfficeHours():
    print('Inside office hours in PST.')
else:
    print('Outside office hours in PST.')

# Get the subreddit
subreddit = reddit.subreddit(os.getenv("SUBREDDIT_NAME"))
# Get the last 10 posts from the subreddit
posts = subreddit.new(limit=10)

# Create a list of the phrases you want to search for
phrases = ["outage", "down", "can't login", "infinite loading", "Outage"]
# Create an array to store the post IDs
post_ids = []


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


for i, post in enumerate(posts):
    if check_post_for_phrases(post, phrases):
        post_ids.append(post.id)
        # Create a POST request to webhook.site
        payload = {
            "post_id": post.id,
            "post_title": post.title,
            "post_url": post.url,
            "post_text": post.selftext
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(webhook_url, json=payload, headers=headers)
        # Check if the POST request was successful
        if response.status_code == 200:
            print("POST request to webhook.site was successful.")
        else:
            print(
                f"POST request to webhook.site failed with status code {response.status_code}.")
