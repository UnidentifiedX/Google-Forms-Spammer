import json
import re
import time
from bs4 import BeautifulSoup, ResultSet
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class ConsoleColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

while True:
    question_dictionary = {}

    print(ConsoleColor.HEADER + "Enter google form URL" + ConsoleColor.ENDC)
    url = input()
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Check if link is valid
    response = None
    try:
        response = driver.get(url)  

        # Scrape google form
        src = driver.page_source
        soup = BeautifulSoup(src, 'html.parser')
        driver.quit()
    except:
        print(ConsoleColor.FAIL + "The URL you have entered is invalid. Have you entered the correct URL?" + ConsoleColor.ENDC)
        driver.quit()
        url = None
        continue

    output_html = input(ConsoleColor.HEADER + "Do you want to output the scraped data to a HTML file? (y/n): " + ConsoleColor.ENDC)
    if output_html.lower() == "y":
        # Write HTML to file
        f = open("page.html", "w", encoding="utf-8")
        f.write(soup.prettify())
        f.close()

    # Split items into its separate beautifulsoup list 
    questions = soup.find_all(lambda div: div.name == "div" and len(div.attrs) == 2, {"role": "listitem"})
    open_ended_ids = soup.find_all("input", {"type": "hidden", "value": ""})   
    open_ended_ids_count = 0

    for question in questions:
        _soup = BeautifulSoup(str(question), 'html.parser')
        _question = _soup.find("span", {}).contents[0]
        _required = False
        _options = []
        _id = None
        _type = None

        try:
            # Try if question is an MCQ question
            _id = _soup.find("input").attrs["name"].replace("_sentinel", "")
            all_spans = _soup.find_all("span")
            required_question = _soup.find("span", {"aria-label": "Required question"})
            if all_spans[-1].contents[0] != "Clear selection" and _soup.find_all("div")[-2].contents[0] == "Required":
                raise Exception("Should not be an MCQ")

            # Check if the question is required
            if required_question != None:
                _required = True

                spans = all_spans[1:]
                for i in range(len(spans) - 2): 
                    # +1 because we skip the first span, which is the title
                    # -2 because we also want to skip the last span, which is 'clear selection'
                    _options.append(spans[i + 2].contents[0])
            else:
                spans = all_spans[1:-1]
                for i in range(len(spans) - 2): 
                    # +1 because we skip the first span, which is the title
                    # -2 because we also want to skip the last span, which is 'clear selection'
                    _options.append(spans[i + 1].contents[0])
                
            if len(_options) == 0: 
                raise Exception("Should not be an MCQ")
            _type = "Multiple Choice"
        except:
            try:
                # Try if question is a Short/Long Answer question
                _id = open_ended_ids[open_ended_ids_count].attrs['name']
                if "_sentinel" in _id:
                    raise Exception("Should not be an OE question")

                if _soup.find("span", {"aria-label": "Required question"}) != None:
                    _required = True

                open_ended_ids_count += 1
                _type = "Open Ended"
            except:
                # Checkbox question
                _id = _soup.find("input", {"type": "hidden"}).attrs['name'].replace("_sentinel", "")
                required_question = _soup.find("span", {"aria-label": "Required question"})
                all_spans = _soup.find_all("span")

                # Check if the question is required
                if required_question != None:
                    _required = True

                    spans = all_spans[1:]
                    for i in range(len(spans) - 1): 
                        _options.append(spans[i + 1].contents[0])
                else:
                    spans = all_spans[1:]
                    for i in range(len(spans)): 
                        _options.append(spans[i].contents[0])
                
                _type = "Checkbox"

        question_dictionary[_id] = {
            "Question": _question,
            "Type": _type,
            "Options": _options,
            "Required": _required
        }

    print(ConsoleColor.HEADER + "Here is the data below" + ConsoleColor.ENDC)
    print(json.dumps(question_dictionary, indent=4))
    
    # TODO: Add graph phrmat to show data collected


# new_link = re.sub(r'(?is)viewForm.+', "formResponse", link).replace("/d/e", "/u/0/d/e")
# data = {
#     "entry.2076157167_sentinel": "",
#     "entry.363405991_sentinel": "",
#     "fvv": 1,
#     "partialResponse": "[null,null,'-7475484278777559539']",
#     "pageHistory": 0,
#     "fbzx": -7475484278777559539
# }
# response = requests.post(new_link, data=data)

