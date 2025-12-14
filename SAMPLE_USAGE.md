# Playwright MCP Sample Usage Guide

## Setup Complete ✓

The Playwright MCP server has been successfully configured and is connected!

**Location**: `~/.claude.json` (local configuration)
**Server**: playwright
**Status**: ✓ Connected

---

## How to Use Playwright MCP

The Playwright MCP works through Claude Code - you ask me (Claude) to perform browser automation tasks, and I'll use the Playwright MCP tools automatically.

### Step 1: Restart Claude Code Session

**IMPORTANT**: You need to start a new Claude Code session for the Playwright tools to become available.

Exit this session and start a new one:
```bash
# Exit current session (Ctrl+D or type 'exit')
# Then restart
claude code
```

---

## Step 2: Ask Claude to Use Playwright

Once in a new session, you can ask me to perform browser automation tasks. Here's how to accomplish your goal:

### Sample Prompt for Your Task

```
Use Playwright to:
1. Navigate to https://omar.house.gov/
2. Find the container element that has social media links (Facebook, X/Twitter, Instagram, YouTube)
3. Return the CSS selector for that container
4. List all the social media links found within it
```

---

## What Happens Behind the Scenes

When you ask me to use Playwright, I'll:

1. **Launch Browser**: Start a Playwright browser instance
2. **Navigate**: Go to the specified URL
3. **Find Elements**: Locate the social links container using CSS selectors or other methods
4. **Extract Data**: Get the selector and extract all links
5. **Return Results**: Show you the selector and list of social media links

---

## Available Playwright MCP Capabilities

The Playwright MCP provides these tools (available after restart):

- **playwright_navigate**: Navigate to a URL
- **playwright_screenshot**: Take screenshots
- **playwright_click**: Click elements
- **playwright_fill**: Fill form inputs
- **playwright_evaluate**: Run JavaScript in the page context
- **playwright_find_element**: Find elements using selectors
- And more!

---

## Example Interaction (After Restart)

```
You: Use Playwright to find social links on https://omar.house.gov/

Claude: I'll use Playwright to navigate to that site and find the social media links.

[Claude uses playwright_navigate tool]
[Claude uses playwright_find_element or similar tools]

Claude: Found it! The social media links are in a container with selector:
`nav.social-links` (example)

Social media links:
- Facebook: https://facebook.com/...
- Twitter/X: https://twitter.com/...
- Instagram: https://instagram.com/...
- YouTube: https://youtube.com/...
```

---

## Quick Start Commands

After restarting, try these:

```bash
# Check MCP status
/mcp

# Then ask me:
"Navigate to https://omar.house.gov/ and find the social media links container"
```

---

## Troubleshooting

**Q**: I don't see Playwright tools available
**A**: Make sure you've restarted the Claude Code session after adding the MCP server

**Q**: How do I know if Playwright MCP is working?
**A**: Type `/mcp` in the new session - you should see "playwright: ✓ Connected"

**Q**: Can I remove the MCP server?
**A**: Yes, run: `claude mcp remove playwright`

---

## Next Steps

1. **Exit this session** (Ctrl+D)
2. **Restart Claude Code**: `claude code`
3. **Verify**: Type `/mcp` to confirm Playwright is connected
4. **Go**: Ask me to navigate to the website and find the social links!

---

*This MCP setup is stored in `~/.claude.json` and will be available in all your Claude Code sessions.*
