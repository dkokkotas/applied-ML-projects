import requests
from bs4 import BeautifulSoup
import re
from nltk.corpus import stopwords 

stop_words = set(stopwords.words('english'))
word_data = []


def scrape_rogets_thesaurus(url):
    response = requests.get(url)
    if response.status_code == 200: 
        soup = BeautifulSoup(response.content, 'html.parser')
        classes = soup.find_all('div', class_='chapter')  # find all classes
        print("Found Classes:", len(classes))
        
        for class_div in classes:
            print('Next Class')
            class_data = extract_class(class_div)
            print(class_data)
            divisions = class_div.find_all('h2', recursive=False)[1:]
            print("Found Divisions:", len(divisions))  # Any divisions?
            
            if divisions:
                for division in divisions:
                    division_data = extract_division(division)
                    print(division_data)
                    current_division = division  # Keep track of the current division
                    next_element = current_division.find_next_sibling()
                    sections = []
                    while next_element and next_element.name != 'h2':
                        if next_element.name == 'h3':
                            sections.append(next_element)
                        next_element = next_element.find_next_sibling()
                    print("Found sections:", len(sections))  # Any sections?
                    process_sections(sections, class_data, division_data)
            else:
                sections = class_div.find_all('h3', recursive=False)
                print("Found sections:", len(sections))  # Any sections?
                process_sections(sections, class_data)
    return word_data
                



def extract_class(class_div):
    class_name = class_div.find('h2').text.strip()
    class_name = class_name.replace('\r\n', ' ')  # replace newlines with spaces
    class_name = re.sub(r'\s+', ' ', class_name).strip()  # remove extra spaces

    return {"name": class_name}




def extract_division(division):
    division_name = division.text.strip()  # Get division name
    return {"name": division_name}




def process_sections(sections, class_data, division_data=None):
    for section in sections:
        section_name = section.text.strip()
        print(section_name)
        words, word_count = extract_words(section)
        print("Words in this Section:", words)
        # print("Number of paragraphs in Section:", word_count)
        for word in words.split(','):
            word_data.append({
                'class': class_data["name"],
                'division': division_data["name"] if division_data else None,
                'section': section_name,
                'word': word
            })




def extract_words(element):
    words = []
    words_count = 0  # Initialize the count
    current_element = element.find_next('p', class_='p2')

    while current_element:  
        if current_element.name == 'h3' or current_element.name == 'h2':  
            break  

        if current_element.name == 'p' and current_element.get('class') == ['p2']:
            raw_text = current_element.text.strip()
            #phrases = re.findall(r'\b(?!a\b)\w+[\w\'-]+(?: (?:and )?\w+[\w\'-]+)*(?: [\w\'-]+\w+)(?=(?:\s|[\']*[a-z])|\b(?!a\b))', raw_text)
            pattern = r'\b(\w+(?:\s+\w+)+)\b(?=[^\w\s]+)'
            phrases = re.findall(pattern, raw_text)
            #phrases = [re.sub(r'\d+', '', phrase).strip() for phrase in phrases]
            phrases = [phrase.lower() for phrase in phrases]
                
            raw_text_without_phrases = remove_phrases(raw_text, phrases)  # remove phrases
            cleaned_words = clean_words(raw_text_without_phrases)
            words.extend(cleaned_words.split())  # add the cleaned words to the list
            words_count += len(cleaned_words.split())

        current_element = current_element.find_next_sibling() 

    return ','.join(words), words_count

        


def clean_words(text):
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text) # remove content within brackets
    
    text = " ".join([word for word in text.split() if word not in stop_words]) # stop word removal
    
    unique_words = list(set(text.split())) # duplicate removal
    no_numbers = " ".join([word for word in unique_words if not word.isdigit()]) # filter out numbers

    # remove single character words (excluding 'a' and 'I')
    text = " ".join([word for word in no_numbers.split() if len(word) > 1 or word in ('a', 'I')])

    # remove words containing mixed letters and numbers
    text = re.sub(r'\b\w*[0-9]+\w*\b', '', text) 

    # remove short abbreviations and names
    def is_valid_word(word): 
        return bool(re.match(r'\b[a-zA-Z]{2,}\b', word))

    text = re.sub(r'\b\w{2,4}\b', '', text)  
    text = ' '.join([word for word in text.split() if is_valid_word(word)])  

    return text




def remove_phrases(text, phrases):
    # use regular expressions for flexible removal
    phrase_pattern = r'\b(?:' + '|'.join(re.escape(phrase) for phrase in phrases) + r')\b'
    return re.sub(phrase_pattern, '', text)