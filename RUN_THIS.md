# Quick Start - Copy & Paste This After Restarting

## First, Verify MCP is Connected

```
/mcp
```

You should see:
```
playwright: ✓ Connected
```

---

## Then, Run Your Task

Copy and paste this prompt:

```
Use Playwright MCP to:

1. Navigate to https://omar.house.gov/
2. Find the HTML container that holds the social media links (Facebook, X/Twitter, Instagram, YouTube)
3. Return the CSS selector for that container
4. Display all the social media links found within it as a list

Please show me both the selector and the actual links.
```

---

## Expected Output

I'll use the Playwright MCP tools to:
- Navigate to the site
- Inspect the page structure
- Locate the social links container
- Extract and display:
  - The CSS selector (e.g., `nav.social-links`, `.footer-social`, etc.)
  - All social media links as a formatted list

---

## Done!

That's it! The Playwright MCP handles all the browser automation behind the scenes.
