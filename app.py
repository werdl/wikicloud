import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import json
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request

headers = {
    'User-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582' # little hack
}

def get_redirects(target):
    title = target.split('/')[-1]
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': title,
        'bllimit': 'max',  # Retrieve all backlinks
        'format': 'json',
    }

    response = requests.get('https://en.wikipedia.org/w/api.php', params=params)
    data = response.json()

    if 'error' in data:
        print(f"Error: {data['error']['info']}")
        return []

    redirects = [page['title'].lower().strip() for page in data['query']['backlinks']]
    return redirects

def get_search_url(query: str):
    json_stuff = json.loads(requests.get(f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={query}").text)
    return f"http://en.wikipedia.org/wiki/{json_stuff['query']['search'][0]['title']}"


remove = [
    'section', 'article', 'aside', 'figcaption', 'figure',
    'footer', 'header', 'hgroup', 'nav', 'details', 'summary',
    'blockquote', 'cite', 'pre', 'code', 'mark', 'output',
    'progress', 'time', 'details', 'summary', 'fieldset',
    'legend', 'abbr', 'address', 'bdi', 'bdo', 'button',
    'data', 'dfn', 'var', 'samp', 'kbd', 'sub', 'sup',
    'small', 'strong', 'cite', 'q', 'ins', 'del', 's',
    'u', 'ruby', 'rt', 'rp', 'canvas', 'script', 'noscript',
    'object', 'embed', 'audio', 'video', 'track', 'map',
    'area', 'table', 'thead', 'tbody', 'tfoot', 'colgroup',
    'col', 'tr', 'th', 'td', 'form', 'input', 'button',
    'select', 'option', 'textarea', 'label', 'fieldset',
    'legend', 'datalist', 'optgroup', 'keygen', 'output',
    'canvas', 'math', 'mark', 'progress', 'time', 'ruby',
    'sub', 'sup', 'wbr', 'svg', "subsection", "wikimedia", "lt", "gt", "archived"
]

def guess(person, guess, generate=False):
    url = get_search_url(person)

    redirs = get_redirects(url)
    redirs.append(url.split("/")[-1].lower())
    redirs+=["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

    html = BeautifulSoup(requests.get(url, headers=headers).text, features="html.parser")
    words = [item.lower() for item in html.get_text(separator="\n").split("\n")]

    out=[]


    for word in words:
        good=True
        for w_frag in word.split(" "):
            if any(w_frag.lower() in red.lower() for red in redirs) or len(w_frag)<5 or any(w in ["'", '"'] for w in w_frag) or w_frag.lower() in remove:
                good=False
                break
        if good:
            out+=[word]
    if generate:
        unique_string = " ".join(list(set(out)))
        wordcloud = WordCloud(width=1000, height=500).generate(unique_string)

        wordcloud.to_file("out.png")


    return guess.lower() in redirs

app = Flask("wikicloud")

@app.route("/gen")
def generate():
    return json.load(True)

guess("steve wozniak", "nn", True)
for x in range(3):
    inp=input("Enter your guess")
    print(guess("steve wozniak", inp))
