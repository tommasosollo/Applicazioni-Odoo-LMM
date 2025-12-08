# Usage Guide - E-Commerce SEO Translator Pro

## Quick Start

### 1. Set Up API Key (First Time Only)

```
Settings → E-Commerce → SEO Translator Pro
↓
Paste your OpenAI API key
↓
Save
```

### 2. Generate Description

```
Products → Open Product
↓
AI SEO Tools tab
↓
Optionally fill: Tone, Keywords, Technical Specs
↓
Click "Generate SEO Description"
↓
Confirm changes and save
```

### 3. Generate Meta-Tags

```
Products → Open Product
↓
AI SEO Tools tab
↓
Click "Generate Meta-Tags"
↓
Auto-populated: Meta Title, Description, Keywords
```

---

## API Examples

### Example 1: Generate Description for Product

**Request:**
```bash
curl -X POST http://localhost:8069/seo-ai/batch-generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": [123],
    "action": "description"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Batch generation completed for 1 products",
  "count": 1
}
```

### Example 2: Get SERP Preview

**Request:**
```bash
curl -X POST http://localhost:8069/seo-ai/meta-preview \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 123
  }'
```

**Response:**
```json
{
  "success": true,
  "title": "Premium Wireless Headphones | Best Sound Quality",
  "url": "/shop/p/123",
  "description": "Experience exceptional audio with our premium wireless headphones. Advanced noise cancellation, 30-hour battery life, and premium build quality...",
  "keywords": "headphones, wireless, audio, premium",
  "last_generated": "2025-01-15T10:30:00"
}
```

### Example 3: Get Generation History

**Request:**
```bash
curl -X GET "http://localhost:8069/seo-ai/history?product_id=123&limit=5"
```

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "id": 1,
      "action": "description_generation",
      "status": "success",
      "create_date": "2025-01-15T10:30:00",
      "user": "Admin",
      "duration_ms": 3200
    },
    {
      "id": 2,
      "action": "meta_tags_generation",
      "status": "success",
      "create_date": "2025-01-15T10:25:00",
      "user": "Admin",
      "duration_ms": 2800
    }
  ],
  "count": 2
}
```

---

## Prompt Variations

### Variation 1: Professional Tone

**Input:**
```
Product: Premium Coffee Maker
Tone: Professional
Keywords: espresso, coffee, Italian, premium
Technical Specs: Dual boiler system, 15 bar pressure, stainless steel
```

**Output (Description):**
```html
<p>
  Discover the pinnacle of coffee craftsmanship with our premium Italian espresso machine. 
  Engineered with precision and built to exacting standards, this professional-grade coffee maker 
  delivers barista-quality espresso with every extraction.
</p>
<ul>
  <li>Dual boiler system for simultaneous brewing and steaming</li>
  <li>15 bar pressure for optimal extraction</li>
  <li>Premium stainless steel construction</li>
  <li>Professional-grade components throughout</li>
</ul>
<p>
  Whether you're a coffee enthusiast or a seasoned barista, this espresso machine 
  sets the standard for premium home coffee brewing.
</p>
```

**Output (Meta-Tags):**
```
Meta Title: Premium Italian Espresso Machine | Professional Coffee Maker
Meta Description: Professional-grade espresso machine with dual boiler system and 15 bar pressure. Barista-quality coffee at home.
Meta Keywords: espresso machine, coffee maker, Italian, premium, professional
```

---

### Variation 2: Casual Tone

**Input:**
```
Product: Casual Sneakers
Tone: Casual
Keywords: sneakers, comfort, style, everyday
Technical Specs: Memory foam insoles, lightweight mesh, durable outsole
```

**Output (Description):**
```html
<p>
  Meet your new favorite sneaker! We've packed serious comfort and style into every pair, 
  so you can look great and feel amazing from morning to night.
</p>
<ul>
  <li>Ultra-comfy memory foam insoles</li>
  <li>Lightweight breathable mesh</li>
  <li>Built to last with durable outsole</li>
  <li>Perfect for any casual occasion</li>
</ul>
<p>
  Grab a pair and experience the difference quality footwear makes. Your feet will thank you!
</p>
```

**Output (Meta-Tags):**
```
Meta Title: Comfy & Stylish Sneakers | Perfect for Everyday
Meta Description: The ultimate sneaker for comfort and style. Memory foam insoles, lightweight design. Perfect for everyday wear!
Meta Keywords: sneakers, comfortable shoes, casual style, everyday footwear
```

---

### Variation 3: Technical Tone

**Input:**
```
Product: Industrial LED Panel
Tone: Technical
Keywords: LED, industrial, efficiency, specification
Technical Specs: 4000K color temp, 95+ CRI, 200lm/W efficiency, IP65 rated
```

**Output (Description):**
```html
<p>
  High-performance LED panel engineered for demanding industrial applications. 
  Specifications designed to exceed professional lighting standards.
</p>
<ul>
  <li>4000K color temperature for daylight simulation</li>
  <li>95+ CRI ensures accurate color rendering</li>
  <li>200lm/W luminous efficacy (industry leading)</li>
  <li>IP65 environmental protection rating</li>
</ul>
<p>
  Ideal for manufacturing facilities, workshops, and commercial spaces requiring 
  precise lighting specifications and operational efficiency.
</p>
```

**Output (Meta-Tags):**
```
Meta Title: Industrial LED Panel 200lm/W | 4000K Technical Specs
Meta Description: High-performance LED panel with 95+ CRI, IP65 rating. 200lm/W efficiency for industrial applications.
Meta Keywords: LED panel, industrial lighting, 4000K, IP65, high efficiency
```

---

## Glossary Examples

### Italian Glossary Setup

| English Term | Italian | Category | Notes |
|------------|-----------|-----------|--------|
| warranty | garanzia | product | Standard product warranty |
| premium | premium | brand | Brand positioning term |
| eco-friendly | ecologico | marketing | Environmental marketing |
| specifications | specifiche | technical | Technical documentation |
| durability | durabilità | product | Product feature |
| energy-efficient | efficienza energetica | technical | Technical specification |

### Usage Example

**Original (English):**
```
This premium product features eco-friendly materials and excellent durability with a 2-year warranty.
```

**After Translation to Italian (using glossary):**
```
Questo prodotto premium utilizza materiali ecologici e offre eccellente durabilità con garanzia di 2 anni.
```

---

## Translation Workflow

### Step 1: Set Primary Language

- Go to Settings → Languages
- Mark one as primary (usually "en_US")
- Add other active languages (e.g., Italian, Spanish, French)

### Step 2: Create Glossary (Optional)

- Settings → E-Commerce → Glossary Management
- Add key terms for each language
- Ensures consistency across translations

### Step 3: Generate Translations

```
Product (in English) → Open
↓
AI SEO Tools tab
↓
Click "Translate All"
↓
Wait for auto-translation to all languages
↓
Review translations
```

### Step 4: Verify Translations

- Each language version is automatically saved
- Glossary terms are respected
- Manual edits can still be done per language

---

## Batch Generation Best Practices

### Best Practice 1: Generate All at Once

```bash
# Select 50 products in list view
# Actions → Generate Descriptions
# All 50 get generated in ~10-15 minutes
```

### Best Practice 2: Stagger for Rate Limits

```bash
# If rate limit hit, wait 1 minute
# Then continue with next batch
# Safe limit: 5 products every minute (5 req/min limit)
```

### Best Practice 3: Review Quality

```bash
# Generate descriptions in batches of 5-10
# Review quality before proceeding
# Make manual adjustments if needed
# Helps maintain brand consistency
```

---

## Troubleshooting

### Issue: "OpenAI API key not configured"

**Solution:**
1. Go to Settings → E-Commerce → SEO Translator Pro
2. Paste your API key from platform.openai.com/api-keys
3. Click Save
4. Reload module if needed: Apps → SEO Translator Pro → Reload

### Issue: "Rate limit exceeded. Maximum 5 requests per minute"

**Solution:**
- Wait 60 seconds before trying again
- Stagger batch operations
- Increase time between generations

### Issue: Empty or Poor Quality Generated Content

**Solution:**
1. Provide more detail in Technical Specifications
2. Add relevant Keywords
3. Ensure product Description is filled in
4. Check Odoo logs for API errors
5. Verify API key is valid

### Issue: Translation Not Working

**Solution:**
1. Ensure product has translations enabled
2. Add target languages in Settings → Languages
3. Create glossary entries (optional but recommended)
4. Check internet connection
5. Verify API key has credits

---

## Advanced Configuration

### Enable Async Generation (Requires queue_job)

```bash
# Settings → E-Commerce → SEO Translator Pro
# Enable "Enable Async Generation"
# Save

# Then in terminal, start queue job worker:
./odoo-bin -u all
# Queue jobs will process in background
```

### Enable GDPR Content Masking

```bash
# Settings → E-Commerce → SEO Translator Pro
# Enable "GDPR: Mask Content in Logs"
# Save

# All sensitive content will be hashed (SHA256)
# while still maintaining audit trail
```

### Customize Rate Limits

Edit `models/ai_service.py`:
```python
# Line ~65
if len(requests) >= 5:  # Change 5 to desired limit
    return True
```

Then reload module.

---

## Cost Optimization

### Tip 1: Use Batch Operations

| Method | Cost per Product |
|--------|-----------------|
| Individual generation | ~$0.03 |
| Batch of 10 | ~$0.03 total / $0.003 each |
| Batch of 50 | ~$0.15 total / $0.003 each |

### Tip 2: Reuse Translations

- Glossary terms prevent re-translation
- Share between similar products
- Reduces API calls and costs

### Tip 3: Schedule During Off-Hours

- Process batches at night
- Avoid peak API rate limits
- Potential for lower costs during low-demand periods

---

## Monitoring & Analytics

### View Generation Stats

```python
# In Odoo shell
stats = env['seo.ai.history'].get_stats_by_product(product_id)
print(f"Total generations: {stats['total_actions']}")
print(f"Successful: {stats['successful']}")
print(f"Errors: {stats['errors']}")
```

### Export History

```python
# In Odoo shell
records = env['seo.ai.history'].search([
    ('create_date', '>=', '2025-01-01'),
])
for r in records:
    print(f"{r.product_id.name}: {r.action} ({r.status})")
```

### Cleanup Old Records

```python
# In Odoo shell (keep last 90 days)
deleted_count = env['seo.ai.history'].cleanup_old_records(days=90)
print(f"Deleted {deleted_count} old records")
```

This happens automatically via cron weekly.

---

## Next Steps

- Read the main [README.md](README.md) for installation and configuration
- Explore the [API Reference](README.md#api-reference) for integration
- Check [Glossary Management](README.md#glossary-management) for translation setup
- Review [Security](README.md#security) for GDPR and data protection
