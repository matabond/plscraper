import sys
import concurrent.futures
import logging
import re
from lxml.html import fromstring
import requests
import headers
from bs4 import BeautifulSoup

def get_website_text(html):
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
    regexp = (
        "\+?\s{0,5}\(?\s{0,5}\d{1,5}\s{0,5}\(?\)?\-?\s{0,5}\d{1,4}\s{0,5}"
        "\)?\-?\s{0,5}\d{1,4}\s{0,5}\-?\s{0,5}\d{1,4}\s{0,5}\-?\s{0,5}\d{1,4}\)?"
    )
    phone_numbers_from_href = re.findall(r"(?<=\=\"tel\:).*?(?=\")", html)
    phone_numbers_from_text = re.findall(
        r"" + regexp + "", get_website_text(html)
    )
    return clean_phone_numbers(
        phone_numbers_from_href, phone_numbers_from_text
    )

def get_logo_links (html):
    tree=fromstring(html)
    logos=tree.xpath("//img[contains(@class,'logo')]/@src")
    return logos

def download_url(url, num_retries=3):
    """ Download a given URL and return the page content"""
    logging.info("Downloading:" + url)
    try:
        response = requests.get(url, headers=headers.random_header())
    except Exception as e:
        logging.exception("website: " + url + ", download error:" + str(e))
        if num_retries > 0:
            return download_url(url, num_retries - 1)
    logging.info("Downloaded:" + url)
    return response

def worker(url):
    response = download_url(url)
    html = response.text
    logging.info("Getting phone numbers:" + url)
    phone_numbers = get_phone_numbers(html)
    logging.info(url)
    logging.info(phone_numbers)


if __name__ == "__main__":
    log_format = (
        "%(asctime)s::%(threadName)-10s::%(levelname)s::%(name)s::"
        "%(lineno)d::%(message)s"
    )
    logging.basicConfig(filename="log.txt", level="INFO", format=log_format)
    urls = open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(worker, url.strip()))
        for future in concurrent.futures.as_completed(futures):
            pass
