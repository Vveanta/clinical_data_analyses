# Clinical Trial Recruitment - Sentiment Analysis & Personalized Messaging

This project aims to ethically scrape and analyze web data from Reddit, utilize sentiment analysis to understand users' attitudes towards clinical trials, and leverage AI to generate personalized recruitment messages. It identifies potential participants for diabetes-related clinical trials by evaluating posts and comments from specific subreddits, categorizing them based on sentiment and user background, and generating targeted messages to encourage clinical trial participation.

**Note**: Since the specific type of clinical trials was not provided, this project assumes recruitment for diabetes-related trials, and all implementation is tailored accordingly.

## Table of Contents
- [Setup Instructions](#setup-instructions)
- [Methodology](#methodology)
- [Data Collected](#data-collected)
- [Ethical Considerations](#ethical-considerations)

---

## Setup Instructions

### Prerequisites
This project requires Python 3.11. Ensure that you have all the necessary libraries installed. They are specified in `requirements.txt`.

### Installation Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Vveanta/clinical_data_analyses.git
   cd clinical_data_analyses
   ```

2. **Create a virtual environment**:
   ```bash
   python3.11 -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the SpaCy English model**:
   ```bash
   python -m spacy download en_core_web_md
   ```

### Environment Variables
Create a `.env` file in the root directory to securely store API keys and credentials:

#### Reddit API (PRAW)
```plaintext
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
USER_AGENT=your_user_agent
```

#### OpenAI API
```plaintext
OPENAI_API_KEY=your_openai_api_key
```

#### Google Cloud Language API
Ensure the Google Cloud Language API service account key file is stored at the path `files/dataengineering-project1-ddca4f2d3131.json`.

### Files and Directory Structure
- **censoring.py**: Handles sensitive information censorship using custom patterns and Google Cloud's NLP API.
- **fetch_data.py**: Scrapes Reddit for relevant posts/comments, applies censorship, and saves the raw data.
- **process_text.py**: Classifies the scraped data by sentiment and expertise level, generating personalized messages based on sentiment.
- **diabetes_clinical_data.xlsx**: Contains censored data from Reddit scraping.
- **personalized_messages_combined.xlsx**: Stores classified data with generated personalized messages.
- **run_all.sh**: A script to execute `fetch_data.py` and `process_text.py` sequentially.

### Running the Full Pipeline
To execute both `fetch_data.py` and `process_text.py` in sequence, run the following shell script:

```bash
./run_all.sh
```

This script will first scrape and censor data from Reddit, then classify and personalize messages in sequence.

---

## Methodology

### 1. Data Collection
   - **Reddit Scraping**: We utilized PRAW to scrape posts and comments from diabetes-related subreddits (`clinicaltrials`, `clinicalresearch`, `diabetes`, etc.) using search terms like "diabetes," "clinical trial," and "treatment study."
   - **Filtering Relevant Content**: Posts and comments containing keywords like "trial," "study," "research," and "treatment" were retained to focus on discussions relevant to clinical trials.
   - **API Constraints**: Due to limitations in the frequency of API requests, the code is currently set to fetch up to 10 posts per search term (limit=10). However, this can be easily adjusted to fetch more posts (e.g., 100 or 1000) to meet higher data requirements in production environments.
### 2. Data Censoring
   - **Sensitive Information Removal**: Implemented censorship to protect user privacy by identifying and masking sensitive information such as names, dates, phone numbers, addresses, and email addresses.
   - **Assumptions**: Reddit usernames were not censored, under the assumption that they may be needed to send messages to potential participants.
   - **Methodology**: Used custom regular expressions, SpaCy for entity recognition, and Google Cloud’s NLP API for enhanced detection and masking of names, locations, and other identifiable information.
   - **Output**: Censored data was saved to `diabetes_clinical_data.xlsx` for analysis without compromising privacy.

### 3. Sentiment Analysis & Classification
   - **OpenAI API Classification**: For each entry, we used the OpenAI API to categorize data into three fields:
      - `is_promotional`: Identifies if a message is promotional (yes/no).
      - `is_healthcare_expert`: Detects if the author is a healthcare expert (yes/no).
      - `sentiment_towards_clinical_trials`: Assesses sentiment toward clinical trials (positive, neutral, negative).
   - **Filtered Data**: Entries identified as both `is_promotional = no` and `is_healthcare_expert = no` were isolated as potential clinical trial participants.

### 4. Personalized Message Generation
   - **Tailored Invitations**: Based on the user’s sentiment toward clinical trials, we generated customized messages using OpenAI’s language model to appeal to users positively, neutrally, or negatively inclined towards clinical trials. Messages were crafted to encourage participation in an ethically sensitive way.
   - **Output**: Results were saved in `personalized_messages_combined.xlsx`, containing message details along with the sentiment classification.

---

## Data Collected

### 1. `diabetes_clinical_data.xlsx`
   - **Contents**: Censored posts and comments collected from Reddit.
   - **Fields**: `Type`, `Post_id`, `Title`, `Author`, `Timestamp`, `Text`, `Total_comments`, `Post_URL`.

### 2. `personalized_messages_combined.xlsx`
   - **Contents**: Classified data with generated personalized messages.
   - **Fields**:
     - `Type`, `Title`, `Author`, `Text`: Original censored post/comment details.
     - `is_promotional`: (1 for yes, 0 for no).
     - `is_healthcare_expert`: (1 for yes, 0 for no).
     - `sentiment_towards_clinical_trials`: Sentiment label (`positive`, `neutral`, `negative`).
     - `Personalized_Message`: AI-generated message tailored to user sentiment.

---

## Ethical Considerations

1. **Data Privacy**: All collected Reddit posts and comments were censored to protect user privacy. Sensitive information such as names, dates, phone numbers, addresses, and email addresses were masked using SpaCy’s NLP model, regex patterns, and Google Cloud’s NLP API.
2. **Data Ethics**: The OpenAI API was utilized with caution to ensure the generated messages were respectful, informative, and did not coerce or mislead users regarding clinical trial participation.
3. **Compliance**: The project adheres to Reddit’s API Terms of Service and OpenAI's ethical guidelines for data usage. All data handling respects user privacy and focuses on responsible messaging.

