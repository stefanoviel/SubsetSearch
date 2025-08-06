import argparse
import json
import time
import random # Import the random module for delays
from urllib.parse import urlparse
import requests
from tqdm import tqdm  # Import tqdm for progress bar
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_fully_scrolled_page_source(url: str) -> str:
    """
    Uses Selenium to open a URL, scroll to the very bottom to load all dynamic
    content, and then returns the final page source HTML.
    """
    print("Launching browser to scroll through the page...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        print(f"Scrolled down, new page height is {new_height} pixels.")
    print("Finished scrolling. Extracting page source.")
    page_source = driver.page_source
    driver.quit()
    return page_source

def request_extract_links(url: str, page_source: str = None, session: requests.Session = None) -> tuple[list[str], str]:
    """
    Modified to accept a requests.Session object for making requests.
    """
    if page_source is None:
        # Use the provided session object if it exists, otherwise use plain requests
        requester = session or requests
        response = requester.get(url)
        response.raise_for_status()
        page_source = response.text

    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a')
    extracted_links = []
    for link in links:
        href = link.get('href')
        if href and (href.startswith('http://') or href.startswith('https://')):
            extracted_links.append(href)
    return extracted_links, page_source

def extract_links_and_filter(url: str, page_source: str) -> tuple[list[str], str]:
    """
    Extracts all links to individual blog posts, IGNORING comment pages.
    """
    links, page_source = request_extract_links(url, page_source=page_source)
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    blog_posts = []
    if links:
        for link in links:
            if link.startswith(base_url) and '/p/' in link and not link.endswith('/comments') and link not in blog_posts:
                blog_posts.append(link)
    return blog_posts, page_source

def extract_links_from_post(url: str, session: requests.Session) -> tuple[list[str], str]:

    try:
        # Use the session to make the request
        links, page_source = request_extract_links(url, session=session)
        extracted_links = []
        if links:
            for link in links:
                if "substack" not in link and link not in extracted_links:
                    extracted_links.append(link)
        return extracted_links, page_source
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch {url} after multiple retries: {e}")
        return [], ""

def crawl_posts_from_archive(url: str) -> tuple[list[str], dict[str, str]]:
    all_links = []
    all_page_sources = {}
    
    archive_page_source = get_fully_scrolled_page_source(url)
    post_links, page_source = extract_links_and_filter(url, page_source=archive_page_source)
    print(f"\nFound {len(post_links)} unique post links (excluding comments) in the archive page: {url}")
    all_links.extend(post_links)
    all_page_sources[url] = page_source

    # --- ***NEW***: Setup requests session with retry logic ---
    session = requests.Session()
    # Add a user-agent header to look more like a real browser
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    
    # Define our retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry on
        backoff_factor=1  # Wait 1s, 2s, 4s between retries
    )
    # Mount the strategy to the session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # --- End of session setup ---

    for link in tqdm(post_links, desc="Extracting post from archive"):
        blog_links, page_source = extract_links_from_post(link, session)
        all_links.extend(blog_links)
        all_page_sources[link] = page_source
        time.sleep(random.uniform(0.5, 1.5)) # Sleep for 0.5 to 1.5 seconds

    found_blog_posts = filter_comment_urls(all_links)

    for link in tqdm(found_blog_posts, desc="Downloading post additional links"):
        if  link not in all_page_sources.keys() and "wiki" not in link and "substack.com" not in link:
            _, content = request_extract_links(link, session=session)
            all_page_sources[link] = content
        
    print(f"\nTotal links found (before deduplication): {len(all_links)}")
    unique_results = list(set(all_links))
    print(f"Total unique links found: {len(unique_results)}")
    return unique_results, all_page_sources

def filter_comment_urls(url_list):

  # Use a list comprehension to create a new list.
  # It includes a URL only if the substring "comment/" is not found in it.
  filtered_list = [url for url in url_list if "comment/" not in url]
  filtered_list = [url for url in url_list if "/comment" not in url]
  return filtered_list


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract blog post links from a webpage with infinite scroll.")
    parser.add_argument("--url", help="The URL of the blog page to scrape.", required=True)
    args = parser.parse_args()

    found_blog_posts, page_sources = crawl_posts_from_archive(args.url)

    output_filename = "extracted_links.txt"
    with open(output_filename, "w", encoding='utf-8') as f:
        for link in found_blog_posts:
            f.write(link + "\n")

    with open("page_sources.json", "w", encoding="utf-8") as f:
        json.dump(page_sources, f, ensure_ascii=False, indent=2)
    
    print(f"\nSuccessfully saved {len(found_blog_posts)} links to {output_filename}")