import json
import re
import threading
import time
from bs4 import BeautifulSoup
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

successful_requests = 0
def do_request(times: int, url, data):
    global successful_requests
    for i in range(times):
        response = requests.post(url, data=data)
        if response.status_code == 200:
            successful_requests += 1
        print(response)

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

    output_html = True if input(ConsoleColor.HEADER + "Do you want to output the scraped data to a HTML file? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
    if output_html:
        # Write HTML to file
        f = open("page.html", "w", encoding="utf-8")
        f.write(soup.prettify())
        f.close()

    # Split items into its separate beautifulsoup list 
    questions = soup.find_all(lambda div: div.name == "div" and len(div.attrs) == 2, {"role": "listitem"})
    open_ended_ids = soup.find_all("input", {"type": "hidden", "value": ""})   
    open_ended_ids_count = 0

    for id in questions:
        _soup = BeautifulSoup(str(id), 'html.parser')
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
                    _options.append(spans[i + 2].contents[0])
            else:
                spans = all_spans[1:-1]
                for i in range(len(spans) - 2): 
                    # +1 because we skip the first span, which is the title
                    _options.append(spans[i + 1].contents[0])

            _type = "Multiple Choice"
        except:
            try:
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
                
            except:
                # Try if question is a Short/Long Answer question
                _id = "entry." + _soup.find(lambda div: div.name == "div" and "data-params" in div.attrs, {}).attrs['data-params'].split('[')[3].replace(",", "")

                if _soup.find("span", {"aria-label": "Required question"}) != None:
                    _required = True

                open_ended_ids_count += 1
                _type = "Open Ended"

        question_dictionary[_id] = {
            "Question": _question,
            "Type": _type,
            "Options": _options,
            "Required": _required
        }

    print(ConsoleColor.HEADER + "Now, we will go through each of the questions for an answer" + ConsoleColor.ENDC)
    question_count = 1
    answers = {}
    for id in question_dictionary:
        _type = question_dictionary[id]['Type']
        _required = question_dictionary[id]['Required']
        _options = question_dictionary[id]['Options']

        print(ConsoleColor.OKGREEN + f"Question {question_count}" + ConsoleColor.ENDC)
        print(f"Question: {question_dictionary[id]['Question']}")
        print(f"Type: {_type}")
        print(f"Required: {_required}")

        if _type != "Open Ended":
            print(f"Options: {', '.join(option for option in _options)}")

            if _type == "Multiple Choice":
                if _required == True:
                    while True:
                        print(ConsoleColor.HEADER + "Type in the option that you want to select" + ConsoleColor.ENDC)
                        answer = input()
                        if answer not in _options:
                            print(ConsoleColor.FAIL + "The option you have entered does not exist in the list of options. Please try again.")
                            continue
                        else:
                            correct = True if input(ConsoleColor.HEADER + f"Is the option '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                            if correct:
                                answers[id] = answer
                                break
                            else:
                                continue
                else:
                    while True:
                        print(ConsoleColor.HEADER + "Type in the option that you want to select. Leave blank for empty." + ConsoleColor.ENDC)
                        answer = input()
                        if answer == "":
                            answers[id] = ""
                            break
                        else:
                            if answer not in _options:
                                print(ConsoleColor.FAIL + "The option you have entered does not exist in the list of options. Please try again.")
                                continue
                            else:
                                correct = True if input(ConsoleColor.HEADER + f"Is the option '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                                if correct:
                                    answers[id] = answer
                                    break
                                else:
                                    continue
            else:
                if _required == True:
                    while True:
                        print(ConsoleColor.HEADER + "Type in the option(s) that you want to select, separated by a comma" + ConsoleColor.ENDC)
                        answer = input().split(",")
                        if set(answer).issubset(_options):
                            correct = True if input(ConsoleColor.HEADER + f"Is the option '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                            if correct:
                                answers[id] = answer
                                break
                            else:
                                continue
                        else:
                            print(ConsoleColor.FAIL + "The option you have entered does not exist in the list of options. Please try again.")
                            continue                            
                else:
                    while True:
                        print(ConsoleColor.HEADER + "Type in the option that you want to select. Leave blank for empty." + ConsoleColor.ENDC)
                        answer = input()
                        if answer == "":
                            answers[id] = ""
                            break
                        else:
                            answer = input().split(",")
                            if set(answer).issubset(_options):
                                correct = True if input(ConsoleColor.HEADER + f"Is the option '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                                if correct:
                                    answers[id] = answer
                                    break
                                else:
                                    continue
                            else:
                                print(ConsoleColor.FAIL + "The option(s) you have entered does not exist in the list of options. Please try again.")
                                continue
        else:
            if _required == True:
                while True:
                    captcha_required = True if input(ConsoleColor.HEADER + "Do you need to answer a captcha (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                    if captcha_required:
                        captcha_range = input(ConsoleColor.HEADER + "Enter the start and end position of the captcha, separated by a comma: " + ConsoleColor.ENDC).split(",")
                        captcha = None
                        try:
                            captcha = _question[int(captcha_range[0]) - 1:int(captcha_range[1])]
                        except:
                            print(ConsoleColor.FAIL + "An error has occured. Try ensuring that you have entered the correct range of values, and that they are valid int32." + ConsoleColor.ENDC)
                            continue
                        
                        correct = True if input(ConsoleColor.HEADER + f"Is the captcha '{captcha}' correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                        if correct:
                            answers[id] = captcha
                            break
                        else:
                            continue
                    else:
                        print(ConsoleColor.HEADER + "Type in your answer." + ConsoleColor.ENDC)
                        answer = input()
                        if "".join(answer.split()) == "":
                            print("".join(answer.split()))
                            print(ConsoleColor.FAIL + "This question is required and cannot be left blank (including whitespace)" + ConsoleColor.ENDC)
                            continue
                        else:
                            correct = True if input(ConsoleColor.HEADER + f"Is the answer '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                            if correct:
                                answers[id] = answer
                                break
                            else:
                                continue
            else:
                while True:
                    print(ConsoleColor.HEADER + "Type in your answer. Leave blank for empty." + ConsoleColor.ENDC)
                    answer = input()
                    if "".join(answer.split()) == "":
                        answers[id] = ""
                        break
                    else:
                        correct = True if input(ConsoleColor.HEADER + f"Is the answer '{answer}' you've entered correct? (y/n): " + ConsoleColor.ENDC).lower() == "y" else False
                        if correct:
                            answers[id] = answer
                            break
                        else:
                            continue

        question_count += 1

    print(ConsoleColor.OKCYAN + "Success! Here is the infomation collected:" + ConsoleColor.ENDC)
    print(json.dumps(answers, indent=4))

    times = None
    while True:
        try:
            times = int(input(ConsoleColor.HEADER + "Now, we will proceed with the spamming. How many times do you want to answer the form?: " + ConsoleColor.ENDC))
            break
        except:
            print(ConsoleColor.FAIL + "An error has occured. Please ensure that you have entered a valid Int32" + ConsoleColor.ENDC)
            continue
    
    new_url = url.split("/viewform")[0].replace("/d/e", "/u/0/d/e") + "/formResponse"
    start = time.time()
    thread_count = int(times/10)
    threads = []
    for i in range(thread_count - 1):
        t = threading.Thread(target=do_request, args=(10, new_url, answers,))
        t.daemon = True
        threads.append(t)
    
    t = threading.Thread(target=do_request, args=(times % 10, new_url, answers,))
    t.daemon = True
    threads.append(t)

    for i in range(len(threads)):
        threads[i].start()
            
    for i in range(len(threads)):
        threads[i].join()

    end = time.time()
    print(ConsoleColor.OKGREEN + f"Complete! Sent {times} requests, ({successful_requests} successful, {times - successful_requests} unsuccessful) in {end - start} seconds.")
    successful_requests = 0