"""Attach source-provided Open Graph preview images; keep files at the source."""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit
from store import locked, read, save, build

class Preview(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('property', attrs.get('name')) == 'og:image' and not self.image:
            self.image = attrs.get('content')

def enrich(document):
    for post in document['posts']:
        if post['type'] != 'news' or post.get('image_url'):
            continue
        try:
            request = Request(post['source_url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=15) as response:
                parser = Preview()
                parser.feed(response.read(3_000_000).decode('utf-8', errors='replace'))
            if parser.image:
                image = urljoin(post['source_url'], parser.image)
                url = urlsplit(image)
                if url.scheme == 'https' and url.hostname and not url.username and not url.password:
                    post['image_url'] = image
                    print('Image:', post['id'])
        except Exception as error:
            print('Image unavailable:', post['id'], type(error).__name__)
    return document

if __name__ == '__main__':
    with locked():
        save(enrich(read()))
        build()
