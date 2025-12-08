# E-Commerce SEO Translator Pro

**AI-powered SEO description generation, translation, and meta-tag creation for Odoo products.**

## Features

✅ **AI Description Generation** - Generate SEO-optimized product descriptions (150-250 words) using GPT-4  
✅ **Contextual Translation** - Translate descriptions while respecting brand glossary  
✅ **Meta-Tag Generation** - Automatically generate SEO meta-tags (title, description, keywords)  
✅ **SERP Preview** - Preview search engine result snippets  
✅ **Rate Limiting & Resilience** - Automatic retry, backoff, and circuit breaker protection  
✅ **Audit Trail** - Complete history of all generations with GDPR compliance  
✅ **Batch Operations** - Generate for multiple products at once  
✅ **Glossary Management** - Maintain technical terms for accurate translations  

## Installation

### Prerequisites

- **Odoo**: 19.0 or later
- **Python**: 3.10+
- **OpenAI API Key**: Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Setup

```bash
# 1. Copy module to addons
cp -r ecommerce_seo_translator_pro /path/to/odoo/addons/

# 2. Install dependencies
pip install -r ecommerce_seo_translator_pro/requirements.txt

# 3. Restart Odoo
./odoo-bin -u all

# 4. Install module via Odoo UI
# Go to Apps → Search "E-Commerce SEO Translator Pro" → Install
```

## Configuration

### Step 1: Set OpenAI API Key

**IMPORTANT:** The API key must be configured manually in Odoo using the Python shell.

**Via Odoo Python Console:**
```bash
./odoo-bin shell -d your_database_name
```

Then run:
```python
env['ir.config_parameter'].sudo().set_param(
    'ecommerce_seo_translator_pro.openai_api_key',
    'sk-your-api-key-here'
)
print("✓ API Key configured successfully")
```

**Via Database Query (Direct SQL - Advanced Users Only):**
```sql
INSERT INTO ir_config_parameter (key, value) 
VALUES ('ecommerce_seo_translator_pro.openai_api_key', 'sk-your-api-key-here')
ON DUPLICATE KEY UPDATE value = 'sk-your-api-key-here';
```

**Where to get your API Key:**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (format: `sk-...`)
4. Store it securely - never commit to version control

### Step 2: Verify Configuration

Test if the API key is correctly configured:
```python
./odoo-bin shell -d your_database_name
```

```python
api_key = env['ir.config_parameter'].sudo().get_param('ecommerce_seo_translator_pro.openai_api_key', '')
if api_key:
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
else:
    print("✗ API Key NOT configured")
```

## Usage

### Generate Description

1. Go to **Products** (Inventory or Website)
2. Open a product
3. Go to **AI SEO Tools** tab
4. Fill in optional fields:
   - **Technical Specifications**: Additional specs for AI to consider
   - **Keywords**: Comma-separated keywords to incorporate
   - **Tone**: Professional, Casual, or Technical
5. Click **Generate SEO Description**
6. AI generates description and meta-tags
7. Review in preview
8. Click **Save** to confirm

### Translate Descriptions

1. Open a product (must be in primary language)
2. Go to **AI SEO Tools** tab
3. Click **Translate All**
4. AI translates to all active languages using glossary
5. Translations are saved automatically

### Generate Meta-Tags

1. Open a product
2. Go to **AI SEO Tools** tab
3. Click **Generate Meta-Tags**
4. AI generates:
   - Meta Title (max 60 chars)
   - Meta Description (max 160 chars)
   - Meta Keywords (comma-separated)

### Batch Generation

**Via Odoo UI:**
1. Go to **Products** list
2. Select multiple products (checkboxes)
3. Actions dropdown → Generate Descriptions / Generate Meta-Tags / Translate

**Via API:**
```json
POST /seo-ai/batch-generate
{
  "product_ids": [1, 2, 3],
  "action": "description"
}
```

## API Reference

### Generate Description

```json
POST /seo-ai/batch-generate
{
  "product_ids": [123],
  "action": "description"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Batch generation completed for 1 products",
  "count": 1
}
```

### Get Meta Preview (SERP Snippet)

```json
POST /seo-ai/meta-preview
{
  "product_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "title": "Premium Product | Best Quality",
  "url": "/shop/p/123",
  "description": "Discover exceptional quality with our premium product...",
  "keywords": "product, quality, premium",
  "last_generated": "2025-01-15T10:30:00"
}
```

### Get Generation History

```json
GET /seo-ai/history?product_id=123&limit=10
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
    }
  ],
  "count": 1
}
```

## Glossary Management

### Add Terms

1. Go to **Inventory → Products → Glossary Terms** (or via Menu)
2. Click **Create**
3. Fill in:
   - **English Term**: Original term (e.g., "warranty")
   - **Translation**: Translated term (e.g., "garanzia" for Italian)
   - **Language Code**: Target language (e.g., "it", "es", "fr")
   - **Category**: Product, Technical, Marketing, or Brand
4. Click **Save**

### View Glossary

- **By Language**: Filter by language code
- **By Category**: Filter by term category
- **Search**: Search by term or translation

**Note:** The glossary is used to maintain consistent terminology when translating product descriptions across languages.

## Troubleshooting

### No Results Generated

**Check:**
1. OpenAI API key is set and valid
2. API key has credits (check platform.openai.com/account/billing)
3. Internet connection is working
4. Check product has name and description

**Debug:**
- Go to product → AI SEO Tools tab
- Check **Debug Information** field for error messages

### Translation Not Working

**Check:**
1. Product has translations enabled in Odoo
2. Active languages are configured
3. Glossary has entries for target language (optional)

### Rate Limit Exceeded

**Solution:**
- Wait 1 minute before trying again
- Rate limit is 5 requests per minute per user

### API Key Error

**Solution:**
1. Get new key from platform.openai.com/api-keys
2. Ensure no spaces in key
3. Test key in Python:
   ```python
   from openai import OpenAI
   client = OpenAI(api_key='sk-...')
   models = client.models.list()
   ```

## Security

✅ **No Raw SQL** - Uses Odoo ORM only  
✅ **Field Validation** - Only allowed fields accepted  
✅ **Audit Logging** - All operations logged  
✅ **GDPR Compliant** - Content masking option  
✅ **Access Control** - Group-based permissions  
✅ **API Key Safety** - Keys stored securely  

## Permissions

- **SEO AI User**: Can generate descriptions, translations, meta-tags
- **SEO AI Manager**: Full access including glossary management and audit logs

## Performance

| Operation | Speed | Cost |
|-----------|-------|------|
| Description Generation | ~3-5 seconds | ~$0.03 |
| Translation | ~2-3 seconds | ~$0.02 |
| Meta-Tags | ~2-3 seconds | ~$0.02 |
| Batch (10 products) | ~30-40 seconds | ~$0.30 |

## Limitations

⚠️ **Note:**
- Max 50 characters for meta title (auto-truncated to 60)
- Max 160 characters for meta description
- Max 200 characters for meta keywords
- Works best with 150-250 word descriptions
- Requires paid OpenAI API (GPT-4)

## Support

For issues, questions, or feature requests, refer to the main project documentation at `../README.md`.

## Version History

- **v19.0.1.0.0** - Initial release with description, translation, and meta-tag generation

## License

LGPL-3 - See LICENSE file
