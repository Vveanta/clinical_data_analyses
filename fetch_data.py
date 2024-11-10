import praw
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timezone
import time
from censoring import censor_text, create_matcher
import spacy

# Initialize Reddit instance
# Load environment variables from .env file
load_dotenv()

# Initialize Reddit instance with environment variables
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT")
)

# Initialize NLP and matcher
nlp = spacy.load("en_core_web_md")
censor_flags = {
    'names': True,
    'dates': True,
    'phones': True,
    'address': True
}
matcher = create_matcher(nlp, censor_flags)

## Define lists to store data
data = []
# Define subreddits, search terms, and keywords for filtering relevant posts
subreddits_approach_1 = ['clinicaltrials', 'clinicalresearch']
search_terms_approach_1 = ["diabetes", "diabetes study", "diabetes treatment"]

subreddits_approach_2 = ['diabetes', 'Type1Diabetes', 'diabetes_t1', 'diabetes_t2']
search_terms_approach_2 = ["clinical trial", "research study", "treatment trial"]

# Keywords for identifying relevant content
keywords = ['study', 'trial', 'research', 'treatment', 'participants', 'enroll', 'testing', 'medical trial']

# Function to filter relevant posts based on keywords in content and title
def is_relevant(text):
    return any(keyword.lower() in text.lower() for keyword in keywords)

# Define a function to scrape posts and comments from a subreddit with given search terms
def scrape_subreddit(subreddit_name, search_terms):
    subreddit = reddit.subreddit(subreddit_name)
    print(f"Scraping subreddit: {subreddit.display_name}")
    count = 0
    for term in search_terms:
        for post in subreddit.search(term, limit=10):  # Adjust limit as needed
            # Check if the post is relevant
            if is_relevant(post.title) or is_relevant(post.selftext):
                title_text = post.title[:5000]
                body_text = post.selftext[:5000]
                censored_title, _ = censor_text(title_text, nlp, matcher, censor_flags)
                censored_text, _ = censor_text(body_text, nlp, matcher, censor_flags)
                data.append({
                    'Type': 'Post',
                    'Post_id': post.id,
                    'Title': censored_title,
                    'Author': post.author.name if post.author else 'Unknown',
                    'Timestamp': datetime.fromtimestamp(post.created_utc, tz=timezone.utc).replace(tzinfo=None),
                    'Text': censored_text,
                    'Total_comments': post.num_comments,
                    'Post_URL': post.url
                })
                count += 1
                # Scrape comments for each post if there are any
                if post.num_comments > 0:
                    post.comments.replace_more(limit=5)
                    for comment in post.comments.list():
                        comment_text = comment.body[:5000]
                        censored_comment_text, _ = censor_text(comment_text, nlp, matcher, censor_flags)
                        # if is_relevant(comment.body): # Check if the comment is relevant
                        data.append({
                            'Type': 'Comment',
                            'Post_id': post.id,
                            'Title': censored_title,
                            'Author': comment.author.name if comment.author else 'Unknown',
                            'Timestamp': pd.to_datetime(comment.created_utc, unit='s'),
                            'Text': censored_comment_text,
                            'Total_comments': 0,  # Comments don’t have this attribute
                            'Post_URL': None  # Comments don’t have this attribute
                        })
                        count += 1
            # time.sleep(1)
    print(f"Total relevant entries for '{subreddit.display_name}': {count}")

# Scraping using Approach 1
for subreddit in subreddits_approach_1:
    scrape_subreddit(subreddit, search_terms_approach_1)

# Scraping using Approach 2
for subreddit in subreddits_approach_2:
    scrape_subreddit(subreddit, search_terms_approach_2)

# Create pandas DataFrame for posts and comments
diclic_data = pd.DataFrame(data)
# diclic_data.head()
print("no of data points collected:",len(diclic_data))
diclic_data.to_excel('diabetes_clinical_data.xlsx')