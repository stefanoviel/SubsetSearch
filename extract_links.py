# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import argparse
import time

# --- IMPORTANT SETUP ---
# This script uses Selenium to control a web browser, which allows JavaScript to run.
# To use it, you need to install the required libraries:
# pip install selenium beautifulsoup4 webdriver-manager

def extract_links_with_js(url: str) -> list[str]:
    """
    This function takes a URL as input, uses a web driver to load the page
    (executing JavaScript), and then extracts all the links.

    :param url: The URL of the webpage to scrape.
    :return: A list of links found on the page.
    """
    # --- 1. Set up and launch the browser ---
    driver = None  # Initialize driver to None
    try:
        # Use webdriver-manager to automatically download and manage the chromedriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode (no browser window)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # --- 2. Fetch the page content ---
        driver.get(url)

        # --- 3. Wait for JavaScript to load ---
        # This is a simple way to wait. For complex pages, you might need
        # to implement more advanced "explicit waits" for specific elements.
        time.sleep(2)  # Wait for 5 seconds

        # --- 4. Parse the final HTML ---
        # Get the page source after JavaScript has been executed
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # --- 5. Close the browser ---
        # This is crucial to free up resources
        if driver:
            driver.quit()

    # --- 6. Extract all links ---
    # Find all the anchor tags <a> which are used for hyperlinks
    links = soup.find_all('a')

    # --- 7. Store and clean the links ---
    extracted_links = []
    for link in links:
        # Get the value of the 'href' attribute
        href = link.get('href')
        if href:
            # Filter for absolute URLs
            if href.startswith('http://') or href.startswith('https://'):
                 extracted_links.append(href)

    return extracted_links

if __name__ == "__main__":
    # --- Set up command-line argument parsing ---
    parser = argparse.ArgumentParser(description="Extract all links from a webpage after executing JavaScript.")
    parser.add_argument("url", help="The URL of the webpage to scrape.")
    args = parser.parse_args()

    # --- Run the extraction ---
    found_links = extract_links_with_js(args.url)

    # --- Print the results ---
    if found_links:
        print(f"Found {len(found_links)} links on {args.url}:")
        for i, link in enumerate(found_links, 1):
            print(f"{i}. {link}")
    elif found_links is None:
        print("Could not retrieve links from the page.")
    else:
        print(f"No links found on {args.url}")
