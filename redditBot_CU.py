import logging
import praw
import json
import os
import datetime
import requests

webhook = os.environ.get("WEBHOOK_URL")
subreddit_name = os.environ.get("SUBREDDIT_NAME")
phrases = json.loads(os.environ.get("PHRASES"))

# Configure the logger
logger = logging.getLogger()
logger.setLevel('INFO')

# Create a Reddit instance
reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                     client_secret=os.environ.get("CLIENT_SECRET"),
                     user_agent=os.environ.get("USER_AGENT"))

# Get the subreddit
subreddit = reddit.subreddit(subreddit_name)

# Get the last 10 posts from the subreddit
posts = subreddit.new(limit=10)


def check_post_for_phrases(post, phrases):
    """Returns True if the post contains one of the phrases, False otherwise."""

    return any(phrase in post.title or phrase in post.selftext for phrase in phrases)


def send_post_request(post):
    """Sends a POST request to `webhook` with the post data."""

    logger.info(
        "Sending POST request to webhook with post {}...".format(post.id))

    payload = {
        "post_id": post.id,
        "post_title": post.title,
        "post_url": post.url,
        "post_text": post.selftext,
        "is_office_hours": datetime.datetime.now().hour >= 16 and datetime.datetime.now().hour <= 23
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(webhook, headers=headers, json=payload)

    # Check if the POST request was successful
    if response.status_code == 200:
        logger.info("👍 POST request to {} was successful.".format(webhook))
    else:
        logger.error("👎 POST request to {} failed with status code {}.".format(
            webhook, response.status_code))


def lambda_handler(event, context):
    """Triggered during office hours."""
    logger.info("🕑 Triggered during office hours: {}".format(
        datetime.datetime.now().hour >= 16 and datetime.datetime.now().hour <= 23))
    logger.info("🔎 Searching last 10 posts to /r/{}.".format(subreddit_name))

    # Create a list of all the post titles, with a ✅ or ❌ prefix depending on whether the post contains a phrase
    post_titles = []
    for post in subreddit.new(limit=10):
        prefix = "✅ " if check_post_for_phrases(post, phrases) else "❌ "
        post_titles.append(prefix + post.title)

    # Send a logger event with the list of post titles
    logger.info("Post titles: {}".format(post_titles))

    for post in subreddit.new(limit=10):
        if check_post_for_phrases(post, phrases):
            send_post_request(post)

    return {
        'statusCode': 200,
        'body': json.dumps('{"message": "Lambda function executed successfully."}')
    }
