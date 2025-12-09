# AI-Odoo Data Assistant - Development Guide

Development notes, architecture decisions, and debugging tips for both modules:
- **Ovunque** - Natural Language Search
- **E-Commerce SEO Translator Pro** - AI-powered SEO Optimization

---

## Quick Module Navigation

| Module | Purpose | Location | Key File |
|--------|---------|----------|----------|
| **Ovunque** | Natural language search queries | `addons/ovunque/` | `models/search_query.py` |
| **SEO Translator Pro** | AI product descriptions & translations | `addons/ecommerce_seo_translator_pro/` | `models/ai_service.py` |

---

## Ovunque Module

### Architecture Overview

**Ovunque** has two distinct query execution paths:

#### 1. Simple (Single-Model) Queries
- Uses OpenAI GPT-4 to convert natural language to Odoo domain syntax
- Example: "Unpaid invoices" → `[('state', '!=', 'posted')]`
- ~1-2 seconds per query (API latency)

#### 2. Multi-Model Queries (Pattern-Based)
- Uses **pure regex pattern matching** to detect cross-model queries
- NO LLM involved - instant execution
- Example: "Clients with 10+ invoices" → Automatic pattern detection + Python aggregation
- ~100-500ms per query (zero API cost)

### Execution Flow

```
User Input: "Fatture non pagate"
                    ↓
[1] Check if multi-model pattern
    No match → Go to Simple Query path
                    ↓
[2] Build prompt for GPT-4
    • Model info
    • Field list
    • Query examples
                    ↓
[3] Call OpenAI API
    Response: [('state', '!=', 'posted')]
                    ↓
[4] Validate domain fields
    Check all fields exist in model
                    ↓
[5] Execute domain search
    Model.search([...])
                    ↓
[6] Store results & display


User Input: "Clienti con più di 10 fatture"
                    ↓
[1] Check if multi-model pattern
    MATCH found: partners_with_count_invoices
                    ↓
[2] Execute pattern logic
    (NO API CALL)
    • Search all account.move
    • Group by partner_id
    • Count per partner
    • Filter: count >= 10
                    ↓
[3] Return matching partners
    Results: [Partner1, Partner3]
                    ↓
[4] Store results & display
```

---

### Key Code Locations (Ovunque)

#### models/search_query.py - SearchQuery Model

**Entry Point:**
- `action_execute_search()` - Main method called from UI

**Multi-Model Path:**
- `_detect_multi_model_query()` - Regex pattern matching
- `_execute_multi_model_search()` - Routes to operation type
- `_execute_count_aggregate()` - Count aggregation logic
- `_execute_exclusion()` - Exclusion logic

**Simple Query Path:**
- `_execute_single_model_search()` - Domain-based execution
- `_parse_natural_language()` - Calls OpenAI API
- `_build_prompt()` - Constructs LLM prompt
- `_parse_domain_response()` - Extracts domain from response
- `_validate_domain_fields()` - Field validation
- `_fix_price_fields()` - Auto-fix common field mistakes

#### Multi-Model Patterns (MULTI_MODEL_PATTERNS dict)

Location: `models/search_query.py:line ~50`

Each pattern has:
```python
'pattern_name': {
    'pattern': r'regex_to_match',           # Matches user query
    'primary_model': 'res.partner',         # Model to return
    'secondary_model': 'account.move',      # Model to aggregate/filter from
    'operation': 'count_aggregate',         # 'count_aggregate' or 'exclusion'
    'aggregate_field': 'partner_id',        # Field grouping
    'link_field': 'partner_id',             # Link field
}
```

---

### Multi-Model Query Operations

#### Count Aggregation

**Use case**: "Clients with 10+ invoices"

**Logic**:
1. Search all secondary model records (account.move)
2. Group by aggregate_field (partner_id)
3. Count records per group
4. Filter where count >= threshold
5. Return matching primary model records (res.partner)

**Code**: `_execute_count_aggregate()`

#### Exclusion

**Use case**: "Products never ordered"

**Logic**:
1. Search all secondary model records (sale.order)
2. Extract link_field values (product_ids)
3. Find primary records NOT in that set
4. Return results

**Code**: `_execute_exclusion()`

---

### Debugging (Ovunque)

#### Log Prefixes

When reviewing logs, look for these prefixes:

```
[LLM]          → OpenAI API communication
[PARSE]        → Domain parsing from LLM response
[REPAIR]       → Syntax error fixing attempts
[VALIDATE]     → Field validation
[FIX]          → Auto-fixing field names
[MULTI-MODEL]  → Pattern detection and execution
[ERROR]        → Errors during execution
```

**View logs**:
```bash
tail -f /var/log/odoo/odoo.log | grep "[MULTI-MODEL]\|[LLM]"
```

#### Debugging a Query

1. **Check the form**:
   - Go to Ovunque → Query Search
   - Click the problematic query
   - See `model_domain` field (domain used)
   - See `raw_response` field (raw LLM output)

2. **Check logs**:
   ```bash
   tail -f /var/log/odoo/odoo.log | grep "[LLM]\|[PARSE]"
   ```

3. **Inspect available fields**:
   ```bash
   # In Odoo shell
   ./odoo-bin shell -d dbname
   exec(open('/path/to/addons/ovunque/debug_fields.py').read())
   ```

   Or visit: `http://localhost:8069/ovunque/debug-fields?model=res.partner`

#### Common Issues (Ovunque)

**Empty Results `[]`**

**Cause**: LLM didn't generate a valid domain

**Fix**:
1. Check `raw_response` field in query form
2. Look for syntax errors in generated domain
3. Try rephrasing query more specifically
4. Check available fields with debug endpoint

**"Field X is computed and cannot be used in queries"**

**Cause**: LLM used a computed field (not stored in DB)

**Fix**:
1. Use `/ovunque/debug-fields?model=X` to see stored fields only
2. Rephrase query with specific field names
3. For products: use `list_price` not `lst_price` or `price`

**OpenAI API Errors**

**Cause**: API key invalid, rate limit, or no credits

**Fix**:
1. Check API key at https://platform.openai.com/api-keys
2. Verify account has credits
3. Wait a few minutes for rate limits to reset
4. Test key in Python:
   ```python
   from openai import OpenAI
   client = OpenAI(api_key='sk-...')
   models = client.models.list()
   ```

---

### Adding New Multi-Model Patterns

#### Step 1: Define the Pattern

Edit `models/search_query.py`, find `MULTI_MODEL_PATTERNS` dict:

```python
MULTI_MODEL_PATTERNS = {
    'my_new_pattern': {
        'pattern': r'(your|keywords).*?regex.*?pattern',
        'primary_model': 'res.partner',
        'secondary_model': 'account.move',
        'operation': 'count_aggregate',  # or 'exclusion'
        'aggregate_field': 'partner_id',
        'link_field': 'partner_id',
    }
}
```

#### Step 2: Test Regex

```bash
# In Python
import re
pattern = r'(your|keywords).*?regex'
test_queries = [
    "Your test query 1",
    "Your test query 2",
]
for query in test_queries:
    match = re.search(pattern, query, re.IGNORECASE)
    print(f"{query} → {match}")
```

#### Step 3: Test in Odoo

1. Reload module: Apps → Ovunque → Reload
2. Go to Ovunque → Query Search
3. Test your pattern query
4. Check logs for `[MULTI-MODEL]` entries

---

### Performance Considerations

#### Single-Model Queries (Ovunque)
- **Speed**: Limited by OpenAI API (~1-2 seconds)
- **Cost**: ~0.03¢ per query
- **Bottleneck**: API latency

#### Multi-Model Queries (Ovunque)
- **Speed**: Python execution (~100-500ms)
- **Cost**: Free (no API calls)
- **Bottleneck**: Database queries for large datasets

#### Scaling

**For better performance**:
- Index frequently searched fields
- Use multi-model patterns for repetitive complex queries (saves API costs)
- Cache results if needed
- For >100k records per table, consider custom SQL with caching

---

### Ovunque Project Files

#### Core Implementation
- `models/search_query.py` - Main SearchQuery model (1000+ lines)
- `controllers/search_controller.py` - REST API endpoints
- `views/search_query_views.xml` - UI forms and lists

#### Utilities
- `utils.py` - Helper functions (API key, field extraction)
- `debug_fields.py` - Shell script to inspect model fields
- `sql_generator.py` - Optional SQL fallback (for future use)

#### Config
- `__manifest__.py` - Module metadata
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `config_example.py` - Configuration template

#### Documentation
- `README.md` - User documentation
- `DEVELOPMENT.md` - Developer guide
- `MULTI_MODEL_PATTERNS.md` - Pattern reference
- `RELEASE_NOTES_v2.0.0.md` - Version history

---

## E-Commerce SEO Translator Pro Module

### Architecture Overview

**E-Commerce SEO Translator Pro** uses OpenAI GPT-4 for AI-powered content generation with built-in resilience:

#### 1. Description Generation Path
- Sends product details to GPT-4
- Generates 150-250 word SEO-optimized descriptions
- Applies tone preferences (Professional, Casual, Technical)
- ~3-5 seconds per generation (API latency)

#### 2. Translation Path
- Translates generated descriptions to multiple languages
- Applies custom glossary for brand consistency
- Automatic retry with backoff on rate limits
- Cost-efficient batching for multiple languages

#### 3. Meta-Tags Path
- Generates SEO meta-title (60 chars max)
- Creates meta-description (160 chars max)
- Extracts keywords automatically
- Provides SERP preview

### Key Code Locations (SEO Translator Pro)

#### models/ai_service.py - AI Generation Service

**Main Methods:**
- `generate_description()` - Generate SEO description with tone
- `translate_description()` - Multi-language translation
- `generate_meta_tags()` - Meta-title, description, keywords
- `_call_openai_with_retry()` - API calls with backoff/retry
- `_create_prompt()` - Prompt engineering

#### models/product_template.py - Product Extensions

**Fields Added:**
- `seo_description` - AI-generated SEO description
- `seo_meta_title` - Meta title for search engines
- `seo_meta_description` - Meta description (160 chars)
- `seo_keywords` - Extracted keywords
- `generation_history` - Audit trail of all generations

#### models/history.py - Generation Audit

**Tracks:**
- Prompt text (what was sent to AI)
- Generated content
- User who triggered generation
- Timestamp and duration
- API costs and tokens used
- Error logs if generation failed

### SEO Translator Pro Features

#### Rate Limiting & Resilience
- Circuit breaker pattern (stops on continuous failures)
- Exponential backoff (1s → 2s → 4s → 8s)
- Max 3 retries per request
- Graceful degradation on API failures

#### Glossary Management
- Store brand terms, product names, technical specs
- Auto-applied during translation
- Language-specific overrides supported
- Prevent mistranslation of key terms

#### SERP Preview
- Shows how search results will appear
- Title preview with character count
- Description preview with character count
- Click-through rate estimation

### Debugging (SEO Translator Pro)

#### Log Prefixes
```
[AI_SERVICE]   → AI generation lifecycle
[TRANSLATION]  → Multi-language translation
[API_CALL]     → OpenAI API communication
[RETRY]        → Retry attempts with backoff
[GLOSSARY]     → Glossary application
[ERROR]        → Generation errors
```

**View logs**:
```bash
tail -f /var/log/odoo/odoo.log | grep "[AI_SERVICE]\|[TRANSLATION]\|[API_CALL]"
```

#### Common Issues (SEO Translator Pro)

**"API key not configured"**

**Fix**:
```bash
./odoo-bin shell -d your_database
env['ir.config_parameter'].sudo().set_param(
    'ecommerce_seo_translator_pro.openai_api_key',
    'sk-your-key'
)
```

**Rate limit errors (429)**

**Fix**:
1. Check OpenAI account at https://platform.openai.com
2. Verify billing/credits available
3. Module auto-retries with exponential backoff
4. Monitor logs for `[RETRY]` entries

**Poor translation quality**

**Fix**:
1. Add product-specific terms to glossary
2. Check glossary is assigned to language
3. Review generation_history for glossary application
4. Consider technical specifications for context

### SEO Translator Pro Project Files

#### Core Implementation
- `models/ai_service.py` - AI generation service with retry logic
- `models/product_template.py` - Product model extensions
- `models/history.py` - Generation history and audit trail
- `models/glossary.py` - Brand glossary management

#### Controllers
- `controllers/website_controller.py` - SERP preview endpoints

#### Config
- `__manifest__.py` - Module metadata
- `requirements.txt` - Dependencies (openai, tenacity)

#### Documentation
- `README.md` - User guide
- `USAGE.md` - Detailed usage examples
- `CHANGELOG.md` - Version history

---

## General Development Setup

### Setup Local Environment (Both Modules)

```bash
# Clone and setup
git clone <repo>
cd ai-odoo-data-assistant

# Install dependencies for BOTH modules
pip install -r addons/ovunque/requirements.txt
pip install -r addons/ecommerce_seo_translator_pro/requirements.txt

# Run Odoo in dev mode
./odoo-bin -c odoo.conf -d mydb -u all --dev=all
```

### Making Changes

1. Edit files in `addons/{module_name}/models/` or `controllers/`
2. Reload module: Apps → Module Name → Reload (or restart Odoo)
3. Test in UI or via API
4. Check logs with appropriate grep filters

### Code Style (Both Modules)

- Follow Odoo conventions (PEP 8 for Python)
- Add logging with proper prefixes: `_logger.info(f"[PREFIX] message")`
- Document complex methods with docstrings
- Use type hints where helpful
- Never hardcode API keys or secrets

### Testing

```bash
# Test specific module
./odoo-bin -u ovunque -d mydb
./odoo-bin -u ecommerce_seo_translator_pro -d mydb

# Run module tests
./odoo-bin -u ovunque,ecommerce_seo_translator_pro -d mydb --test-tags=ovunque
```

---

## Useful Commands (Both Modules)

### Inspect Model Fields
```bash
./odoo-bin shell -d mydb
Model = env['product.template']
for field_name, field_obj in Model._fields.items():
    print(f"{field_name}: {field_obj.type}")
```

### Check OpenAI Connection
```python
from openai import OpenAI
client = OpenAI(api_key='sk-...')
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

### Reload Both Modules
```bash
./odoo-bin -u ovunque,ecommerce_seo_translator_pro -d mydb
```

---

## Security Notes (Both Modules)

✅ All queries use Odoo ORM (no raw SQL)
✅ Odoo RLS (Row-Level Security) always applied
✅ Field validation prevents invalid field names
✅ All queries/operations audited and logged
✅ API keys stored securely in database parameters (NOT in code)
✅ Sensitive fields masked in logs/export
✅ Rate limiting prevents abuse

---

## References

- **Odoo Documentation**: https://www.odoo.com/documentation/
- **OpenAI API**: https://platform.openai.com/docs/api-reference
- **Odoo Domain Syntax**: https://www.odoo.com/documentation/latest/developer/reference/orm.html#odoo.models.Model.search
- **Ovunque DEVELOPMENT.md**: `addons/ovunque/DEVELOPMENT.md`
- **SEO Translator Pro USAGE.md**: `addons/ecommerce_seo_translator_pro/USAGE.md`
