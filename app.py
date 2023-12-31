import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import json
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request
import people
import random
import os
import time

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


blacklist = [
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
    'sub', 'sup', 'wbr', 'svg', "subsection", "wikimedia", "lt", "gt", "archived",
    "huffpost", "reuters", "forbes", "contents", "references", "newsweek" 'English',
    'español',
    'français',
    'deutsch',
    'italiano',
    'português',
    'pусский',
    '中文',
    '日本語',
    'العربية',
    'हिन्दी',
    '한국어',
    'polski',
    'nederlands',
    'türkçe',
    'עברית',  # Hebrew
    'Ελληνικά',  # Greek
    'svenska',  # Swedish
    'norsk bokmål',  # Norwegian Bokmål
    'dansk',  # Danish
    'suomi',  # Finnish
    'magyar',  # Hungarian
    'čeština',  # Czech
    'ไทย',  # Thai
    'bahasa Indonesia',  # Indonesian
    'tiếng Việt',  # Vietnamese
    'தமிழ்',  # Tamil
    'فارسی',  # Persian,
    "newsweek"
]

def guess(person, guess, generate=False, outname=""):
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
            if any(w_frag.lower() in red.lower() for red in redirs) or len(w_frag)<5 or any(w in ["'", '"'] for w in w_frag) or w_frag.lower() in blacklist:
                good=False
                break
        if good and len(word)>5 and word.isalnum():
            out+=[word]
    if generate:
        unique_string = " ".join(((out)))
        wordcloud = WordCloud(width=1000, height=500).generate(unique_string)

        wordcloud.to_file(outname)


    return guess.lower() in redirs

app = Flask("wikicloud")

app.config['UPLOAD_FOLDER'] = "static"

@app.route("/info/<celeb>")
def info(celeb):
    return json.dumps(people.people[celeb])

@app.route("/")
def home():
    key, val = random.choice(list(people.people.items()))
    if not os.path.exists(f"static/{key}.png"):
        if key=="Doge":
            guess("dogecoin", "nope", True, f"static/{key}.png")
        else:
            guess(key, "nope", True, f"static/{key}.png")
    src=f"static/{key}.png"
    return render_template("app.html", src=src, name=key)

@app.route("/load")
def load_images():
    start=time.time()
    for person, _ in people.people.items():
        exists=os.path.exists(f"static/{person}.png")
        if not exists:
            if person=="Doge":
                guess("dogecoin", "nope", True, f"static/{person}.png")
            else:
                guess(person, "nope", True, f"static/{person}.png")
        keys = list(people.people.keys())
        print(f'{"Skipped" if exists else "Generated"} {person} ({keys.index(person)+1}/{len(keys)})')
    end=time.time()
    return json.dumps({
        "code": 200,
        "message": "successfully cached all images",
        "timetaken": end-start
    })

@app.route("/submit/<g>")
def guess_json(g):
    return json.dumps(guess(g, request.args["guess"]))
