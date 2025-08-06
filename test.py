from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

def request_extract_links(url: str) -> list[str]:
    page_source = requests.get(url)
    soup = BeautifulSoup(page_source.text, 'html.parser')

    links = soup.find_all('a')

    extracted_links = []
    for link in links:
        href = link.get('href')
        if href:
            # Filter for absolute URLs
            if href.startswith('http://') or href.startswith('https://'):
                    extracted_links.append(href)

    return extracted_links

def extract_posts(url): 
    """
    This function takes a URL of a blog page, extracts all the links to individual blog posts,
    and returns them as a list.
    """
    # Extract all links from the page
    links = request_extract_links(url)

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    blog_posts = []
    if links is not None:
        for link in links:
            if link.startswith(base_url) and link not in blog_posts:
                blog_posts.append(link)
    
    return blog_posts

def extract_links_from_post(url: str) -> list[str]:
    """
    This function is a wrapper to extract blog post links from a given URL.
    It uses the extract_blog_posts function defined above.
    """

    links = request_extract_links(url)

    extracted_links = []
    if links is not None:
        for link in links:
            if "substack" not in link and link not in extracted_links:
                extracted_links.append(link)
    
    return extracted_links


def crawl_all_websites(url) -> list[str]:
    results = []
    visited = set()  # To keep track of visited URLs
    to_visit = [url]

    # while to_visit:
    for _ in range(10):
        if not to_visit:
            break 
        current_url = to_visit.pop(0)
        # print(f"Crawling: {current_url}")
        visited.add(current_url)

        post_links = extract_posts(current_url)
        results.extend(post_links)

        for link in post_links:
            blog_links = extract_links_from_post(link)
            results.extend(blog_links)
            print(f"Found {len(blog_links)} blog links in {link}")

            for blog_link in blog_links:
                parsed_url = urlparse(blog_link)
                print("parsed_url: ", parsed_url)
                if parsed_url.netloc not in visited and parsed_url.netloc not in to_visit:
                    to_visit.append(f"{parsed_url.scheme}://{parsed_url.netloc}")
                    print(f"Added {parsed_url.scheme}://{parsed_url.netloc} to visit list.")

        print(f"Total links found so far: {len(results)}")
    
    return results


def filter_comment_urls(url_list):

  # Use a list comprehension to create a new list.
  # It includes a URL only if the substring "comment/" is not found in it.
  filtered_list = [url for url in url_list if "comment/" not in url]
  return filtered_list

if __name__ == "__main__":
    import argparse

    # --- Set up command-line argument parsing ---
    parser = argparse.ArgumentParser(description="Extract blog post links from a webpage.")
    parser.add_argument("--url", help="The URL of the blog page to scrape.")
    args = parser.parse_args()

    # --- Run the extraction ---
    found_blog_posts = crawl_all_websites(args.url)

    # --- Filter out comment URLs ---
    found_blog_posts = filter_comment_urls(found_blog_posts)

    with open("extracted_links.txt", "w") as f:
        for link in found_blog_posts:
            f.write(link + "\n")
