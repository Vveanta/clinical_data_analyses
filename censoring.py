import re
import spacy
from spacy.matcher import Matcher
from google.cloud import language_v1
import os

# Function to create a matcher with specified flags
def create_matcher(nlp, censor_flags):
    matcher = Matcher(nlp.vocab)
    
    if censor_flags['phones']:
        phone_patterns = [
            [{"SHAPE": "ddd"}, {"ORTH": "-", "OP": "?"}, {"SHAPE": "ddd"}, {"ORTH": "-", "OP": "?"}, {"SHAPE": "dddd"}],
            [{"SHAPE": "(ddd)"}, {"ORTH": "-", "OP": "?"}, {"SHAPE": "ddd"}, {"ORTH": "-", "OP": "?"}, {"SHAPE": "dddd"}],
            [{"SHAPE": "ddd"}, {"ORTH": ".", "OP": "?"}, {"SHAPE": "ddd"}, {"ORTH": ".", "OP": "?"}, {"SHAPE": "dddd"}],
            [{"SHAPE": "+"}, {"SHAPE": "dd"}, {"ORTH": " ", "OP": "?"}, {"SHAPE": "dddddddddd", "OP": "?"}],
            [{"SHAPE": "dddddddddd"}]
        ]
        for pattern in phone_patterns:
            matcher.add("PHONE_NUMBER", [pattern])
    
    if censor_flags['names']:
        name_pattern = [[{"ENT_TYPE": "PERSON"}]]
        matcher.add("NAMES", name_pattern)
    
    if censor_flags['dates']:
        date_pattern = [[{"ENT_TYPE": "DATE"}]]
        matcher.add("DATES", date_pattern)
    
    if censor_flags['address']:
        email_pattern = [{"TEXT": {"REGEX": "[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]+"}}]
        matcher.add("EMAIL", [email_pattern])
    
    return matcher

# Helper function to preprocess phone numbers
def preprocess_text_for_phones(text, stats):
    phone_regex = r'\+?\d[\d\s\-\(\)]{10,14}\d'
    matches = re.finditer(phone_regex, text)
    phone_count = 0
    for match in matches:
        start, end = match.span()
        text = text[:start] + "█" * (end - start) + text[end:]
        phone_count += 1
    stats['PHONES'] += phone_count
    return text, stats

def preprocess_text_for_dates(text, stats):
    date_regex = r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b'
    matches = re.finditer(date_regex, text)
    date_count = 0
    for match in matches:
        start, end = match.span()
        text = text[:start] + "█" * (end - start) + text[end:]
        date_count += 1
    stats['DATES'] += date_count
    return text, stats

def byte_offset_to_char_position(text, byte_offset):
    # Encode the text up to the byte offset into bytes using UTF-8
    # Then count the length of the encoded bytes, which gives the character position
    encoded_text = text.encode('utf-8')
    char_position = 0
    byte_count = 0

    for char in text:
        char_length = len(char.encode('utf-8'))
        if byte_count + char_length > byte_offset:
            break
        byte_count += char_length
        char_position += 1

    return char_position

def censor_text_with_google_nlp(text, censor_flags, stats):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "files/dataengineering-project1-ddca4f2d3131.json"
    # Use Google NLP to identify and censor additional sensitive information
    if len(text) > 5000:
        text = text[:5000]
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document, encoding_type='UTF8')

    censored_text = list(text)
    # Special handling for addresses
    for entity in response.entities:
        entity_type = language_v1.Entity.Type(entity.type_).name

        if (entity_type == "ADDRESS" and censor_flags['address']):
            for mention in entity.mentions:
                # Ignore common type mentions
                if mention.type == language_v1.EntityMention.Type.COMMON:
                    continue
                # Censor the mention
                start_char_pos = byte_offset_to_char_position(text, mention.text.begin_offset)
                end_char_pos = byte_offset_to_char_position(text, mention.text.begin_offset + len(mention.text.content))

                for i in range(start_char_pos, end_char_pos):
                    if i < len(censored_text):  # Ensure index is within bounds
                        censored_text[i] = "█"
                # Update stats
                stats['ADDRESS'] += 1
    #doing this in two pases so that first addresses are censored and then entities with location tag so that there are no overlaps and lesser false negatives
    partially_censored_text = "".join(censored_text)
    document = language_v1.Document(content=partially_censored_text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document, encoding_type='UTF8')

    for entity in response.entities:
        entity_type = language_v1.Entity.Type(entity.type_).name
        if (entity_type == "PERSON" and censor_flags['names']) or \
           (entity_type == "LOCATION" and censor_flags['address']):
            for mention in entity.mentions:
                if mention.type == language_v1.EntityMention.Type.COMMON:
                    continue
                start_char_pos = byte_offset_to_char_position(partially_censored_text, mention.text.begin_offset)
                end_char_pos = byte_offset_to_char_position(partially_censored_text, mention.text.begin_offset + len(mention.text.content))

                for i in range(start_char_pos, end_char_pos):
                    if i < len(censored_text):  # Ensure index is within bounds
                        censored_text[i] = "█"
                # Update stats
                if entity_type == "PERSON":
                    stats['NAMES'] += 1
                elif entity_type == "LOCATION":
                    stats['ADDRESS'] += 1

    return "".join(censored_text), stats

# Helper function to apply censorship to matched spans
def apply_censoring(span, censored_text):
    for i in range(span.start_char, span.end_char):
        censored_text[i] = "█"

# Main censoring function
def censor_text(text, nlp, matcher, censor_flags):
    stats = {'NAMES': 0, 'DATES': 0, 'PHONES': 0, 'ADDRESS': 0, 'EMAIL': 0}
    
    if censor_flags['phones']:
        text, stats = preprocess_text_for_phones(text, stats)
    
    if censor_flags['dates']:
        text, stats = preprocess_text_for_dates(text, stats)
    
    if censor_flags['names'] or censor_flags['address']:
        text, stats = censor_text_with_google_nlp(text, censor_flags, stats)
    
    doc = nlp(text)
    censored_text = list(text)
    
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        apply_censoring(span, censored_text)
        if nlp.vocab.strings[match_id] in stats:
            stats[nlp.vocab.strings[match_id]] += 1
    
    return "".join(censored_text), stats