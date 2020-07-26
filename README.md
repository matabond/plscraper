# Phone and logo scraper (plscraper)

Command-line application that, given a list of website URLs as input, visits them and finds, extracts and outputs the websites' logo image URLs and all phone numbers (e.g. mobile phones, land lines, fax numbers) present on the websites.

## Installation

```bash
pip install -r requirements.txt
or with docker
docker build --tag plscraper .
```

## Usage

```python
cd plscraper
cat ../data/data.txt | python3 -m plscraper
or with docker
cat data/data.txt | docker run -i plscraper

```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
[MIT](https://choosealicense.com/licenses/mit/)