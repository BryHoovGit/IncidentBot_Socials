import praw
import requests
import datetime
import pytz
import os

webhook_url = os.environ.get("WEBHOOK_URL")
subreddit_name = os.environ.get("SUBREDDIT_NAME")
phrases = os.environ.get("PHRASES")

# Create a Reddit instance
reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                     client_secret=os.environ.get("CLIENT_SECRET"),
                     user_agent=os.environ.get("USER_AGENT"))

# Get the subreddit
subreddit = reddit.subreddit(subreddit_name)

# Get the last 10 posts from the subreddit
posts = subreddit.new(limit=10)

# Get the phrases you want to search for from the environment variable
phrases = [phrase.strip("[]").replace('"', '')
           for phrase in phrases.split(",")]


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
    """Checks if it is currently office hours in Pacific Standard Time (PST).

    Returns:
        True if it is currently office hours, False otherwise.
    """

    # Get the current time in UTC
    now = datetime.datetime.now(tz=pytz.timezone('UTC'))

    # Convert the current time to PST
    pst_now = now.astimezone(pytz.timezone('US/Pacific'))

    # Get the hour of the day in PST
    hour = pst_now.hour

    # Return True if it is currently between 9am and 5pm in PST
    return hour >= 9 and hour < 17


def lambda_handler(event, context):
    print(f"🕑 Triggered during office hours: {is_office_hours()}🕑")
    print(f"🕵️‍♀️ Searching last 10 posts to /r/{subreddit}.🕵️‍♀️")
    """AWS Lambda function handler."""

    # Check each post for the specified phrases and send a POST request to webhook.site if one is found
    for post in posts:
        if check_post_for_phrases(post, phrases):
            # Log a message to the console
            print(f'✅ Found match.✅')
            print(f'✅ {post.title}✅')
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
            response = requests.post(
                webhook_url, json=payload, headers=headers)
            print(f"📤 Sending match to webhook.📤")
            # Check if the POST request was successful
            if response.status_code == 200:
                print(f"👍 POST request to {webhook_url} was successful.👍")
            else:
                print(
                    f"👎 POST request to {webhook_url} failed with status code {response.status_code}.👎")
        else:
            print(f'❌ {post.title}❌')
