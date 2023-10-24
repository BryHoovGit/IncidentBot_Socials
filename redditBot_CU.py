import praw
import dateparser
import json
import os
import boto3
import dotenv

# Load the environment variables
dotenv.load_dotenv()

webhook = os.environ.get("WEBHOOK_URL")
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


def check_post_for_phrases(post, phrases):
    # True if the post contains one of the phrases, False otherwise.
    for phrase in phrases:
        if phrase in post.title or phrase in post.selftext:
            return True
    return False


def is_office_hours(now=dateparser.parse('now', settings={'TIMEZONE': 'US/Pacific'})):
    # True if it is currently office hours, False otherwise.
    hour = now.hour
    print(hour)
    return hour >= 9 and hour < 17


def lambda_handler(event, context):
    print(f"🕑 Triggered during office hours: {is_office_hours()}🕑")
    print(f"🕵️‍♀️ Searching last 10 posts to /r/{subreddit_name}.🕵️‍♀️")
    # Check each post for the specified phrases and send a POST request to webhook.site if one is found
    for post in subreddit.new(limit=10):
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
                "is_office_hours": is_office_hours(),
            }
            headers = {
                "Content-Type": "application/json",
            }
            # send the POST request
            client = boto3.client('apigatewaymanagementapi')
            response = client.post_to_connection(
                ConnectionId=webhook,
                Data=json.dumps(payload, indent=4),
                Headers=headers,
            )
            print(f"📤 Sending match to webhook.📤")
            # Check if the POST request was successful
            if response['StatusCode'] == 200:
                print(f"👍 POST request to {webhook} was successful.👍")
            else:
                print(
                    f"👎 POST request to {webhook} failed with status code {response['StatusCode']}.👎")
        else:
            print(f'❌ {post.title}❌')
