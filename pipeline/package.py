"""Package public files only, keeping the local editor out of deployment."""
from pathlib import Path
import shutil
from store import ROOT, locked, build

def package():
    with locked(): build()
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    for name in ['index.html', 'style.css', 'pop-type.css', 'app.js', 'feed.js', 'favicon.svg']:
        shutil.copyfile(ROOT / 'site' / name, destination / name)
    for name in ['assets', 'fonts']:
        shutil.copytree(ROOT / 'site' / name, destination / name, dirs_exist_ok=True)
    (destination / '.nojekyll').touch()
    print('Public site: dist/')

if __name__ == '__main__': package()
