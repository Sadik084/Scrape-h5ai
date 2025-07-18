from bs4 import BeautifulSoup
from urllib import request, parse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import threading
import time
import html
from urllib.parse import unquote, urlparse
import collections

HOST = "put_your_host_link"

all_links = []
lock = threading.Lock()
visited = set()
progress_bar = None

def fetch_links(url):
    try:
        resp = request.urlopen(url)
        soup = BeautifulSoup(resp, "html.parser")
        return soup.select("#fallback > table > tr > td.fb-n > a")
    except:
        return []

def scrape(path=""):
    global progress_bar
    url = parse.urljoin(HOST, path)

    with lock:
        if url in visited:
            return
        visited.add(url)

    links = fetch_links(url)
    folders = []

    for link in links:
        name = link.text.strip()
        href = link.get("href", "")
        if "Parent Directory" in name:
            continue

        full_path = parse.urljoin(path, href)
        full_url = parse.urljoin(HOST, full_path)

        if href.endswith("/"):
            folders.append(full_path)
        else:
            with lock:
                all_links.append((name, full_url))
                progress_bar.update(1)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(scrape, folders)

def generate_html(file_links, filename="index.html"):
    folders = collections.defaultdict(list)
    for name, url in file_links:
        parts = url.split('/')
        if len(parts) > 6:
            folder = '/'.join(parts[5:-1])
        else:
            folder = "root"
        folders[folder].append((name, url))

    folders = dict(sorted(folders.items()))
    for k in folders:
        folders[k].sort()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>File Index</title>
<style>
body {{ font-family: Arial, sans-serif; background:#f9f9f9; padding:20px; }}
.container {{ max-width: 900px; margin: auto; background:#fff; padding:20px; box-shadow:0 0 15px rgba(0,0,0,0.1); border-radius: 8px; }}
h1 {{ color: #333; }}
input[type="search"] {{
  width: 100%; padding: 10px; margin-bottom: 20px;
  border: 1px solid #ccc; border-radius: 5px;
  font-size: 16px;
}}
.folder {{
  margin-bottom: 15px;
  border: 1px solid #ddd; border-radius: 5px;
  padding: 10px;
  background: #fafafa;
}}
.folder summary {{
  font-weight: bold; font-size: 18px; cursor: pointer;
  outline: none;
}}
.folder ul {{
  list-style:none; padding-left: 20px; margin-top: 10px;
}}
.folder li {{
  margin: 5px 0;
}}
a {{
  color: #0077cc; text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}
.no-results {{
  color: #999; font-style: italic; padding: 10px; display: none;
}}
</style>
</head>
<body>
<div class="container">
<h1>File Index ({len(file_links)} files)</h1>
<input type="search" id="searchInput" placeholder="Search files and folders..." onkeyup="filterList()">
<div id="fileList">
"""

    for folder, items in folders.items():
        safe_folder = html.escape(unquote(folder))
        html_content += f'<details class="folder" open>\n<summary>{safe_folder}</summary>\n<ul>\n'
        for name, url in items:
            safe_name = html.escape(name)
            safe_url = html.escape(url)
            html_content += f'<li><a href="{safe_url}" target="_blank">{safe_name}</a></li>\n'
        html_content += '</ul>\n</details>\n'

    html_content += """
<p class="no-results" id="noResults">No results found.</p>
</div>
</div>

<script>
function filterList() {
  let input = document.getElementById('searchInput').value.toLowerCase();
  let folders = document.querySelectorAll('#fileList details.folder');
  let noResults = document.getElementById('noResults');
  let totalVisible = 0;

  folders.forEach(folder => {
    let folderText = folder.querySelector('summary').textContent.toLowerCase();
    let items = folder.querySelectorAll('li');
    let visibleItems = 0;

    items.forEach(item => {
      let text = item.textContent.toLowerCase();
      if(text.includes(input) || folderText.includes(input)) {
        item.style.display = '';
        visibleItems++;
      } else {
        item.style.display = 'none';
      }
    });

    if(visibleItems > 0) {
      folder.style.display = '';
      totalVisible += visibleItems;
      folder.open = true;
    } else {
      folder.style.display = 'none';
      folder.open = false;
    }
  });

  noResults.style.display = totalVisible === 0 ? 'block' : 'none';
}
</script>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

def save_links_grouped(file_links, filename="links.txt"):
    folders = collections.defaultdict(list)
    for name, url in file_links:
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) > 1:
            folder = unquote(parts[-2])  # decode folder name here
        else:
            folder = "root"
        folders[folder].append(url)

    with open(filename, "w", encoding="utf-8") as f:
        for folder, urls in folders.items():
            f.write(f"{folder}:\n")
            for url in urls:
                f.write(f"  {url}\n")  # two spaces before each link
            f.write("\n")

if __name__ == "__main__":
    start = time.time()
    progress_bar = tqdm(desc="Scraping files", unit="file", dynamic_ncols=True)
    scrape()
    progress_bar.close()

    save_links_grouped(all_links)

    generate_html(all_links)

    end = time.time()
    print(f"\n✅ Done! Scraped {len(all_links)} files in {round(end - start, 2)}s")
    print("📁 Saved to links.txt and index.html")
