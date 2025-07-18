# h5ai index Scraper

This Python script scrapes file links from h5ai http server.

## Features
- Recursively scrapes folders and files from a given host URL.
- Shows a progress bar during scraping.
- Generates a neat HTML page with collapsible folders and a live search filter.
- Saves all scraped file URLs to `links.txt`.

## Requirements

- Python 3.x
- `beautifulsoup4` for parsing HTML
- `tqdm` for progress bar

## Installation

Run the following command to install required libraries:

```bash
pip install beautifulsoup4 tqdm
