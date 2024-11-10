import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Function to classify each text
def process_text(text):
    response = client.chat.completions.create(
      model="gpt-4o-mini",  # Ensure using an appropriate model
      response_format={ "type": "json_object" },
      messages = [
          {"role": "system", "content": "You are a helpful assistant designed to output JSON with categories 'is_promotional', 'is_healthcare_expert', and 'sentiment_towards_clinical_trials'."},
          {"role": "user", "content": f"Classify the following text: Determine if the message is a promotional message ('yes' or 'no' for is_promotional), identify if the author is a healthcare expert ('yes' or 'no' for is_healthcare_expert), and assess the sentiment towards clinical trials ('positive', 'neutral', 'negative').\n\nText: \"{text}\""}
      ],
      max_tokens=50,
      temperature=0.5,
      n=1
    )
    # Parse the response to extract the classification
    # classification = eval(response.choices[0].message.content)  # Be cautious with eval, ensure safe parsing
    return response.choices[0].message.content

# Function to clean and normalize classification response    
def clean_response(response_text):
    # Convert JSON-like text response to dictionary
    response_dict = eval(response_text)  # Caution with eval, ensure it's from a trusted source

    # Clean up and normalize values
    is_promotional = 1 if response_dict['is_promotional'].strip().lower() == 'yes' else 0
    is_healthcare_expert = 1 if response_dict['is_healthcare_expert'].strip().lower() == 'yes' else 0
    sentiment = response_dict['sentiment_towards_clinical_trials'].strip().lower()
    
    return is_promotional, is_healthcare_expert, sentiment

def generate_personalized_message(text, sentiment):
    # Customize prompt based on sentiment
    if sentiment == 'positive':
        prompt = f"Write an engaging invite (max 100 words) for a user who feels positively about diabetes clinical trials. No subject needed.\n\nText:\n\n{text}"
    elif sentiment == 'neutral':
        prompt = f"Write a brief, informative invite (max 100 words) encouraging a user with a neutral view on  clinical trials to participate. No subject.\n\nText:\n\n{text}"
    elif sentiment == 'negative':
        prompt = f"Write a reassuring invite (max 120 words) addressing concerns about clinical trials. No subject.\n\nText:\n\n{text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Ensure using an appropriate model
        messages=[
            {"role": "system", "content": "You are a helpful assistant generating personalized invite messages for diabetes clinical trial recruitment based on user sentiment."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7,
        n=1
    )

    # Return the generated message
    return response.choices[0].message.content

# Load initial Excel data
data = pd.read_excel('diabetes_clinical_data.xlsx')
results = []

# Process data entries
for index, row in data.iterrows():
    # if index < 346:
    #     continue

    type_of_text = row["Type"]
    title = row["Title"]
    text = row['Text']
    author = row['Author']  

    # Format the input text based on the type
    if type_of_text == "Post":
        final_text = f"Title: {title}\n\nContent:\n{text}"
    elif type_of_text == "Comment":
        final_text = f"Comment in response to the post titled '{title}':\n\n{text}"

    # Get response from GPT
    response_text = process_text(final_text)
    is_promotional, is_healthcare_expert, sentiment = clean_response(response_text)

    # Store the result
    result_dict = {
        'Type': type_of_text,
        'Title': title,
        'Author': author,
        'Text': text,
        'is_promotional': is_promotional,
        'is_healthcare_expert': is_healthcare_expert,
        'sentiment_towards_clinical_trials': sentiment
    }
    results.append(result_dict)

    # # Stop after processing 20 entries
    # if len(results) >= 15:
    #     break

# Convert classification results to DataFrame
classified_df = pd.DataFrame(results)

# Step 2: Filter potential participants (non-promotional, non-expert) and generate personalized messages
potential_participants = classified_df[(classified_df['is_promotional'] == 0) & (classified_df['is_healthcare_expert'] == 0)]

messages = []
for _, row in potential_participants.iterrows():
    sentiment = row['sentiment_towards_clinical_trials']
    text = f"{row['Title']}\n\n{row['Text']}"
    
    # Generate message based on sentiment
    personalized_message = generate_personalized_message(text, sentiment)
    
    # Store the results along with other relevant information
    messages.append({
        'Type': row['Type'],
        'Title': row['Title'],
        'Author': row['Author'],
        'Text': row['Text'],
        'is_promotional': row['is_promotional'],
        'is_healthcare_expert': row['is_healthcare_expert'],
        'sentiment_towards_clinical_trials': row['sentiment_towards_clinical_trials'],
        'Personalized_Message': personalized_message
    })

# Combine classification and personalized message results
final_df = pd.DataFrame(messages)
# Save the final results to an Excel file
final_df.to_excel("personalized_messages_combined.xlsx", index=False)
print("Combined personalized messages saved to 'personalized_messages_combined.xlsx'")
# Save to a new Excel file
# results_df.to_excel("processed_results.xlsx", index=False)
# print("Processed results saved to 'processed_results.xlsx'")

