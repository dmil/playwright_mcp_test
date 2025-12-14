#!/usr/bin/env python3
"""
Script to extract social media links from a website using Claude with Playwright MCP.

This script demonstrates how to:
1. Connect to the Playwright MCP server
2. Use Claude with MCP tools to navigate and close popups intelligently
3. Extract social media links using MCP
4. Process the links into a clean dictionary format with Python
"""

import asyncio
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
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


async def get_social_links_with_mcp(url):
    """
    Use Claude with Playwright MCP to navigate to a URL and extract social links.

    This function:
    1. Connects to the Playwright MCP server
    2. Runs an agentic loop where Claude uses MCP tools to:
       - Navigate to the URL
       - Close popups intelligently
       - Extract social media links
    3. Returns the extracted links as a list

    Args:
        url: The website URL to scrape for social media links

    Returns:
        List of social media link URLs
    """
    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\nError: Please set your ANTHROPIC_API_KEY in the .env file")
        print("Get your API key from: https://console.anthropic.com/settings/keys")
        print("Then add it to the .env file in this directory\n")
        return []

    # Create the MCP client
    client = PlaywrightMCPClient(api_key)

    try:
        # Connect to the Playwright MCP server
        await client.connect()

        # Create the prompt for Claude
        user_message = f"""
Please use the Playwright MCP tools to complete the following task:

1. Navigate to {url}
2. Wait for the page to load
3. Use the MCP to close any popups that appear (like newsletter signups, cookie notices, etc.)
4. Find the social media links on the page (look for links to Facebook, Twitter/X, Instagram, YouTube, etc.)
5. Extract all the social media link URLs
6. Use the "report_social_links" tool to return the list of URLs

Make sure to extract all social media links you can find on the page.
"""

        # Define a structured output tool for Claude to use
        final_answer_tool = {
            "name": "report_social_links",
            "description": "Report the extracted social media links as a structured list",
            "input_schema": {
                "type": "object",
                "properties": {
                    "links": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A social media URL"
                        },
                        "description": "List of social media link URLs"
                    }
                },
                "required": ["links"]
            }
        }

        # Run the agentic loop with structured output
        response = await client.run_agent_loop(
            user_message,
            max_iterations=15,
            final_answer_tool=final_answer_tool
        )

        # Extract the links from the structured response
        if isinstance(response, dict) and "links" in response:
            social_links = response["links"]
        else:
            print(f"Unexpected response format: {response}")
            social_links = []

        return social_links

    finally:
        # Always disconnect from the MCP server
        await client.disconnect()


async def main():
    """
    Main function to run the social links extraction.
    """
    # The URL to scrape for social media links
    target_url = "https://crawford.house.gov/"

    print("=" * 70)
    print("  Social Media Links Extractor")
    print("  (Using Claude + Playwright MCP)")
    print("=" * 70)
    print(f"Target URL: {target_url}\n")

    # Get the social links using Claude with Playwright MCP
    social_links_list = await get_social_links_with_mcp(target_url)

    if not social_links_list:
        print("\n✗ No social links found or error occurred")
        return

    print(f"\n✓ Extracted {len(social_links_list)} social media links")

    # Process the links into dictionary format using Python
    print("\nProcessing links into dictionary format...")
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
