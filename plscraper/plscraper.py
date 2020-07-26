import sys
import concurrent.futures
import logging
import re
from lxml.html import fromstring
import requests
import headers
from bs4 import BeautifulSoup
import urllib.parse
import json
import time


def get_website_text(html):
    """ This function returns clean text from the website so it is easier to 
    extract the phone numbers.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.find_all(text=True)
    output = ""
    blacklist = [
        "[document]",
        "noscript",
        "header",
        "html",
        "style",
        "script",
        "meta",
        "head",
        "input",
        "title",
        "script",
    ]
    for t in text:
        if t.parent.name not in blacklist:
            exists = False
            for b in blacklist:
                if "</" + b + ">" in t:
                    exists = True
            if exists == False:
                output += "{} ".format(t)
    return output


def clean_phone_numbers(phone_numbers_from_href, phone_numbers_from_text):
    """ Function which merges the phone numbers 
    gotten from the html code and pure website text.
    Also, light cleaning of the found phone numbers is being performed: 
    all characters that are not digits, a plus sign (+) or parentheses 
    with whitespace are being removed
    Function returns distinct phone numbers
    """
    phone_digits = []
    cleaned_phone_numbers = []

    for phone_number in phone_numbers_from_text:
        phone_digit = re.sub("[^\d]", "", phone_number)
        if phone_digit not in phone_digits and len(phone_digit) > 8:
            phone_digits.append(phone_digit)
            cleaned_phone_numbers.append(
                re.sub("[^\d\(\)\+]", " ", phone_number).strip()
            )

    for phone_number in phone_numbers_from_href:
        phone_digit = re.sub("[^\d]", "", phone_number)
        if phone_digit not in phone_digits and len(phone_digit) > 5:
            phone_digits.append(phone_digit)
            cleaned_phone_numbers.append(
                re.sub("[^\d\(\)\+]", " ", phone_number).strip()
            )

    return cleaned_phone_numbers


def get_phone_numbers(html):
    """ Function which fetches phone numbers from clean website text with 
    regular expressions and from html code
    """

    regexp = (
        "\+?\s{0,5}\(?\s{0,5}\d{1,5}\s{0,5}\(?\)?\-?\s{0,5}\d{1,4}\s{0,5}"
        "\)?\-?\s{0,5}\d{1,4}\s{0,5}\-?\s{0,5}\d{1,4}\s{0,5}\-?\s{0,5}"
        "\d{1,4}\)?"
    )
    phone_numbers_from_text = re.findall(
        r"" + regexp + "", get_website_text(html)
    )
    phone_numbers_from_href = re.findall(r"(?<=\=\"tel\:).*?(?=\")", html)

    return clean_phone_numbers(
        phone_numbers_from_href, phone_numbers_from_text
    )


def prioritize_logos(logos):
    """ Because only one logo is asked this 
    function prioritizes fetched logos
    """
    d = {}
    for logo in logos:
        if "small" in logo.lower():
            d[logo] = 10
        elif "footer" in logo.lower():
            d[logo] = 9
        elif "header" in logo.lower():
            d[logo] = 8
        elif "white" in logo.lower():
            d[logo] = 7
        elif "black" in logo.lower():
            d[logo] = 6
        elif "rgb" in logo.lower():
            d[logo] = 5
        elif "color" in logo.lower():
            d[logo] = 4
        else:
            d[logo] = 3
    sorted(d.items(), key=lambda x: x[1])
    return next(iter(d))


def get_absolute_path(url, logo_link):
    return urllib.parse.urljoin(url, logo_link)


def get_logo_link(html, url):
    """ Function which fetches logo links from html code
    First we try to fetch all img tags with class containing "logo"
    if we didn't find any we try to search for other img tags 
    with link containing "logo".
    If we have found more then one logo we prioritize them and return the first
    """
    tree = fromstring(html)
    images_src_logo = []
    images_class_logo = tree.xpath("//img[contains(@class,'logo')]/@src")
    if not images_class_logo:
        images_src = tree.xpath("//img/@src")
        for i in images_src:
            if "logo" in i.lower():
                images_src_logo.append(i)

    logos = list(set(images_class_logo + images_src_logo))

    if len(logos) > 1:
        logo = prioritize_logos(logos)
    elif len(logos) == 1:
        logo = logos[0]
    else:
        logo = ""

    return get_absolute_path(url, logo)


def download_url(url, num_retries=3):
    """ Download a given URL and return the response.
    If error occurs try again with different user_agent
    """
    try:
        response = requests.get(url, headers=headers.random_header())
    except Exception as e:
        logging.exception("website: " + url + ", download error:" + str(e))
        if num_retries > 0:
            time.sleep(1)
            return download_url(url, num_retries - 1)
    return response


def worker(url):
    """ Main function for fetching and cleaning data from the website """
    html = download_url(url).text
    phone_numbers = get_phone_numbers(html)
    logo = get_logo_link(html, url)

    result = {}
    result["logo"] = logo
    result["phones"] = phone_numbers
    result["website"] = url
    print(json.dumps(result))


if __name__ == "__main__":
    log_format = (
        "%(asctime)s::%(threadName)-10s::%(levelname)s::%(name)s::"
        "%(lineno)d::%(message)s"
    )
    logging.basicConfig(stream=sys.stderr, level="INFO", format=log_format)
    urls = open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(worker, url.strip()))
