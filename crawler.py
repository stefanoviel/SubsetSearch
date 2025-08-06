from extract_links import extract_links_with_js
from urllib.parse import urlparse


def extract_posts(url): 
    """
    This function takes a URL of a blog page, extracts all the links to individual blog posts,
    and returns them as a list.
    """
    # Extract all links from the page
    links = extract_links_with_js(url)

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    blog_posts = []
    if links is not None:
        for link in links:
            if link.startswith(base_url) and link not in blog_posts:
                blog_posts.append(link)
    
    return blog_posts

def extract_links_from_blog(url: str) -> list[str]:
    """
    This function is a wrapper to extract blog post links from a given URL.
    It uses the extract_blog_posts function defined above.
    """

    links = extract_links_with_js(url)

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
    for _ in range(5): 
        current_url = to_visit.pop(0)
        print(f"Crawling: {current_url}")
        visited.add(current_url)

        post_links = extract_posts(current_url)

        for link in post_links:
            blog_links = extract_links_from_blog(link)
            results.extend(blog_links)
            print(f"Found {len(blog_links)} blog links in {link}")

            for blog_link in blog_links:
                parsed_url = urlparse(blog_link)
                if link not in results and parsed_url.netloc not in visited and parsed_url.netloc not in to_visit:
                    to_visit.append(parsed_url.netloc)
                    print(f"Added {parsed_url.netloc} to visit list.")

        print(f"Total links found so far: {len(results)}")
    
    return results
            


if __name__ == "__main__":
    import argparse

    # --- Set up command-line argument parsing ---
    parser = argparse.ArgumentParser(description="Extract blog post links from a webpage.")
    parser.add_argument("url", help="The URL of the blog page to scrape.")
    args = parser.parse_args()

    # --- Run the extraction ---
    found_blog_posts = crawl_all_websites(args.url)

    # --- Print the results ---
    if found_blog_posts:
        print(f"Found {len(found_blog_posts)} blog posts on {args.url}:")
        for i, post in enumerate(found_blog_posts, 1):
            print(f"{i}. {post}")
    else:
        print(f"No blog posts found on {args.url}")