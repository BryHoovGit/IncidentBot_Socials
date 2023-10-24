import logging
import praw
import json
import boto3

webhook = os.environ.get("WEBHOOK_URL")
subreddit_name = os.environ.get("SUBREDDIT_NAME")
phrases = json.loads(os.environ.get("PHRASES"))

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
    return any(phrase in post.title or phrase in post.selftext for phrase in phrases)


def lambda_handler(event, context):
    # Log a message to the console
    logging.info("Triggered during office hours: {}".format(
        datetime.now().hour))
    logging.info("Searching last 10 posts to /r/{}.".format(subreddit_name))

    # Check each post for the specified phrases and send a POST request to webhook.site if one is found
    for post in subreddit.new(limit=10):
        if check_post_for_phrases(post, phrases):
            # Create a POST request to webhook.site
            payload = {
                "post_id": post.id,
                "post_title": post.title,
                "post_url": post.url,
                "post_text": post.selftext,
                "is_office_hours": datetime.now().hour >= 9 and datetime.now().hour < 17
            }
            headers = {
                "Content-Type": "application/json"
            }

            # Send the POST request
            client = boto3.client('apigatewaymanagementapi')
            response = client.post_to_connection(
                ConnectionId=webhook,
                Data=json.dumps(payload, indent=4),
                Headers=headers
            )

            # Check if the POST request was successful
            if response['StatusCode'] == 200:
                logging.info(
                    "POST request to {} was successful.".format(webhook))
            else:
                logging.error("POST request to {} failed with status code {}.".format(
                    webhook, response['StatusCode']))

    return {
        'statusCode': 200,
        'body': json.dumps('{"message": "Lambda function executed successfully."}')
    }
