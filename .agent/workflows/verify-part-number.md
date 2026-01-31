---
description: Verify a generated part number on distributor sites (Octopart, Mouser, DigiKey, Amphenol)
---

# Part Number Verification Workflow

Use this workflow to verify that a generated D38999 part number exists and is available from actual distributors.

## Steps

1. **Copy the Generated Part Number**
   - In the Part Builder (Step 4), click on the part number to copy it
   - Example: `D38999/24FE19-35SN`

2. **Search on Octopart (Primary)**
   // turbo
   Open browser to: `https://octopart.com/search?q=<PART_NUMBER>`
   - Verify the part appears in search results
   - Check if multiple distributors stock it
   - Note pricing and lead times

3. **Search on Mouser (US Distributor)**
   // turbo
   Open browser to: `https://www.mouser.com/c/?q=<PART_NUMBER>`
   - Check if part is in stock or available to order
   - Note: Mouser shows "Available to Ship" status

4. **Search on DigiKey (US Distributor)**
   // turbo
   Open browser to: `https://www.digikey.com/en/products/result?keywords=<PART_NUMBER>`
   - Check "In Stock" status
   - Note pricing tiers

5. **Search on Amphenol Library (Manufacturer)**
   // turbo
   Open browser to: `https://www.amphenol-industrial.com/search?q=<PART_NUMBER>`
   - Verify this is a valid Amphenol configuration
   - Check for datasheet downloads

6. **Document Results**
   - Record which sites had the part
   - Note if it's standard stock vs special order
   - Update availability data if needed

## Expected Results

| Site | What to Look For |
|------|------------------|
| Octopart | Part appears, shows multiple sources |
| Mouser | "In Stock" or "Available to Order" |
| DigiKey | "In Stock" badge, pricing shown |
| Amphenol | Valid product page, datasheet link |

## If Part Not Found

1. Check for typos in part number format
2. Try searching without the class letter (E)
3. May indicate a special/custom configuration
4. Update Part Builder availability data
