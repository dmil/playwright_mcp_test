#!/usr/bin/env python3
"""
Script to extract social media links from a website using a hybrid approach.

This script demonstrates how to:
1. Navigate to a webpage using regular Playwright
2. Use Claude with Playwright MCP to find the CSS selector for the social links container
3. Extract the actual links using regular Playwright (deterministic code)
4. Process the links into a clean dictionary format with Python

This approach minimizes reliance on MCP and uses it only where AI-powered element
detection is most valuable (finding the right container selector).
"""

import asyncio
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from mcp_client import PlaywrightMCPClient

# Load environment variables from .env file
load_dotenv()


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


async def get_container_selector_with_mcp(url):
    """
    Use Claude with Playwright MCP to find the CSS selector for the social links container.

    This function uses MCP ONLY to identify the container selector, not to extract the links.
    It will navigate to the page via MCP and ask Claude to find the appropriate selector.

    Args:
        url: The website URL to analyze

    Returns:
        CSS selector string for the container with social media links
    """
    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\nError: Please set your ANTHROPIC_API_KEY in the .env file")
        print("Get your API key from: https://console.anthropic.com/settings/keys")
        print("Then add it to the .env file in this directory\n")
        return None

    # Create the MCP client
    client = PlaywrightMCPClient(api_key)

    try:
        # Connect to the Playwright MCP server
        await client.connect()

        # Create the prompt for Claude - asking ONLY for the container selector
        user_message = f"""
Please use the Playwright MCP tools to complete the following task:

1. Navigate to {url}
2. Wait for the page to load
3. Close any popups if they appear
4. Find the container element that holds the social media links (Facebook, Twitter/X, Instagram, YouTube, etc.)
5. Return the CSS selector for that container using the "report_selector" tool

IMPORTANT: Return the CSS selector for the CONTAINER element, not the individual links.
The selector should be something that can be passed to page.locator() in Playwright.
For example: "nav.social-links", ".footer-social", "[aria-label='Social Media']", etc.
"""

        # Define a structured output tool for Claude to report the selector
        final_answer_tool = {
            "name": "report_selector",
            "description": "Report the CSS selector for the social links container",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "The CSS selector for the container element holding the social media links"
                    }
                },
                "required": ["selector"]
            }
        }

        # Run the agentic loop with structured output
        response = await client.run_agent_loop(
            user_message,
            max_iterations=15,
            final_answer_tool=final_answer_tool
        )

        # Extract the selector from the structured response
        if isinstance(response, dict) and "selector" in response:
            selector = response["selector"]
            return selector
        else:
            print(f"Unexpected response format: {response}")
            return None

    finally:
        # Always disconnect from the MCP server
        await client.disconnect()


async def extract_social_links_with_playwright(url, container_selector):
    """
    Use regular Playwright to navigate to a page and extract all links from a container.

    This is deterministic code that doesn't require AI - it simply:
    1. Navigates to the URL
    2. Finds the container using the provided selector
    3. Extracts all links from within that container

    Args:
        url: The website URL to scrape
        container_selector: CSS selector for the container element

    Returns:
        List of all link URLs found in the container
    """
    async with async_playwright() as p:
        # Launch browser (headless mode)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Navigate to the URL (wait for DOM to load, not network idle)
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until='domcontentloaded')

            # Find the container element
            container = page.locator(container_selector)

            # Wait for the container to be visible on the page
            try:
                await container.first.wait_for(state='attached', timeout=10000)
                print(f"Found container with selector: {container_selector}")
            except Exception as e:
                print(f"Warning: Container '{container_selector}' not found or not visible: {e}")
                return []

            # Get all links within the container
            links = container.locator('a')
            link_count = await links.count()
            print(f"Found {link_count} links in the container")

            # Extract href attributes from all links
            all_links = []
            for i in range(link_count):
                link = links.nth(i)
                href = await link.get_attribute('href')

                # Add any valid href to the list
                if href:
                    all_links.append(href)

            return all_links

        finally:
            # Close the browser
            await browser.close()


async def main():
    """
    Main function to run the social links extraction using a hybrid approach.

    Workflow:
    1. Use MCP to get the CSS selector for the social links container
    2. Use regular Playwright to navigate and extract the actual links
    3. Process the results into a clean dictionary format
    """
    # The URL to scrape for social media links
    target_url = "https://omar.house.gov/"

    print("=" * 70)
    print("  Social Media Links Extractor")
    print("  (Hybrid: MCP for selector + Playwright for extraction)")
    print("=" * 70)
    print(f"Target URL: {target_url}\n")

    # Step 1: Use MCP to get the container selector
    print("Step 1: Using Playwright MCP to find container selector...")
    container_selector = await get_container_selector_with_mcp(target_url)

    if not container_selector:
        print("\n✗ Failed to get container selector from MCP")
        return

    print(f"✓ Got container selector: {container_selector}\n")

    # Step 2: Use regular Playwright to extract the links
    print("Step 2: Using regular Playwright to extract links...")
    social_links_list = await extract_social_links_with_playwright(target_url, container_selector)

    if not social_links_list:
        print("\n✗ No social links found")
        return

    print(f"\n✓ Extracted {len(social_links_list)} social media links")

    # Step 3: Process the links into dictionary format using Python
    print("\nStep 3: Processing links into dictionary format...")
    social_links_dict = process_social_links(social_links_list)

    # Print the result as formatted JSON
    print("\n" + "=" * 70)
    print("Social Media Links:")
    print("=" * 70)
    print(json.dumps(social_links_dict, indent=2))

    # Also save to a file
    output_file = "social_links.json"
    with open(output_file, 'w') as f:
        json.dump(social_links_dict, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
