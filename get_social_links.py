#!/usr/bin/env python3
"""
Script to extract social media links from omar.house.gov using Playwright.

This script demonstrates how to:
1. Use Playwright Python library to navigate to a website
2. Close popups automatically
3. Extract social media links from the page
4. Process the links into a clean dictionary format
"""

import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def extract_domain_name(url):
    """
    Extract the social media platform name from a URL.

    Examples:
        https://instagram.com/repilhan -> instagram
        https://www.facebook.com/RepIlhan/ -> facebook
        https://x.com/Ilhan -> x

    Args:
        url: The social media URL

    Returns:
        The platform name (domain without www or TLD variations)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove 'www.' prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]

    # Extract the main platform name (before the first dot)
    platform = domain.split('.')[0]

    return platform


def process_social_links(links):
    """
    Convert a list of social media URLs into a dictionary.

    Args:
        links: List of social media URLs

    Returns:
        Dictionary with platform names as keys and URLs as values
        Example: {"instagram": "https://instagram.com/repilhan", ...}
    """
    social_dict = {}

    for url in links:
        platform = extract_domain_name(url)
        social_dict[platform] = url

    return social_dict


def close_popups(page):
    """
    Close any popups on the page (like newsletter signups, cookie notices, etc.).

    This function attempts to close common popup patterns:
    - Buttons with "Close dialog" text
    - Close buttons with X symbols
    - Cookie consent dialogs

    Args:
        page: The Playwright page object

    Returns:
        None
    """
    print("Closing any popups...")

    # List of common close button patterns to try
    close_patterns = [
        'button:has-text("Close dialog")',
        'button:has-text("Close")',
        'button[aria-label*="close" i]',
        'button:has-text("✕")',
        'button:has-text("×")',
        '.close-button',
        '.modal-close'
    ]

    # Try each pattern to find and close popups
    for pattern in close_patterns:
        try:
            close_button = page.locator(pattern).first
            if close_button.is_visible(timeout=1000):
                close_button.click()
                print(f"Popup closed successfully using pattern: {pattern}")
                # Wait a moment for the popup to close
                page.wait_for_timeout(500)
                return
        except Exception:
            # This pattern didn't work, try the next one
            continue

    print("No popups found to close")


def get_social_links(url):
    """
    Use Playwright to navigate to a URL and extract social media links.

    Args:
        url: The website URL to scrape for social media links

    Returns:
        Dictionary of social media links with platform names as keys
    """
    # Start Playwright
    with sync_playwright() as p:
        # Launch the browser with your system Chromium
        # headless=False means you can see the browser window
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=False
        )

        # Create a new page/tab
        page = browser.new_page()

        print(f"Navigating to {url}...")
        # Navigate to the website
        page.goto(url, wait_until="domcontentloaded")

        # Wait a moment for dynamic content to load
        page.wait_for_timeout(2000)

        # Close any popups using the dedicated function
        close_popups(page)

        print("Extracting social media links...")
        # Find the social links container
        # The container has class 'evo-social-icons-here'
        social_container = page.locator('.evo-social-icons-here')

        # Extract all links within the container
        social_links_elements = social_container.locator('a')

        # Get the href attributes from all social links
        links = []
        count = social_links_elements.count()

        for i in range(count):
            link = social_links_elements.nth(i)
            href = link.get_attribute('href')
            if href:
                links.append(href)

        print(f"Found {len(links)} social media links")

        # Close the browser
        browser.close()

        # Process the links into dictionary format
        social_dict = process_social_links(links)

        return social_dict


def main():
    """
    Main function to run the social links extraction.
    """
    # The URL to scrape for social media links
    target_url = "https://omar.house.gov/"

    print("=" * 60)
    print(f"Social Media Links Extractor")
    print(f"Target: {target_url}")
    print("=" * 60)

    # Get the social links
    social_links = get_social_links(target_url)

    # Print the result as formatted JSON
    print("\n" + "=" * 60)
    print("Social Media Links:")
    print("=" * 60)
    print(json.dumps(social_links, indent=2))

    # Also save to a file
    output_file = "social_links.json"
    with open(output_file, 'w') as f:
        json.dump(social_links, f, indent=2)

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
