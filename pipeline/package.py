"""Package public files only, keeping the local editor out of deployment."""
from pathlib import Path
import shutil
from store import ROOT, locked, build

def package():
    with locked(): build()
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    for name in ['index.html', 'style.css', 'app.js', 'feed.js', 'favicon.svg']:
        shutil.copyfile(ROOT / 'site' / name, destination / name)
    (destination / '.nojekyll').touch()
    print('Public site: dist/')

if __name__ == '__main__': package()
