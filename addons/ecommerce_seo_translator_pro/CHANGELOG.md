# Changelog

All notable changes to this project will be documented in this file.

## [19.0.1.0.0] - 2025-01-15

### Added
- **AI Description Generation**: Generate SEO-optimized product descriptions using GPT-4
- **Contextual Translation**: Translate descriptions with custom glossary support
- **Meta-Tag Generation**: Automatic generation of SEO meta-tags (title, description, keywords)
- **SERP Preview**: Display search engine result page snippet preview
- **Glossary Management**: Maintain technical and brand-specific terms for translations
- **Rate Limiting**: Limit API calls to 5 requests per minute per user
- **Circuit Breaker**: Automatic failure recovery with exponential backoff
- **Audit Trail**: Complete history of all generations with user tracking
- **GDPR Compliance**: Content masking and SHA256 hashing for privacy
- **Batch Operations**: Generate for multiple products in one action
- **REST API**: JSON endpoints for integration
- **Access Control**: Role-based permissions (User, Manager)
- **Async Support**: Compatible with queue_job for background processing
- **Demo Data**: Sample glossary entries for Italian language
- **Cron Jobs**: Automatic cleanup of old history records (90+ days)

### Technical
- Compatible with Odoo 19.0 and OWL 2
- Python 3.10+ with type hints
- Full test coverage with mock provider
- OpenAI GPT-4 integration
- Retry logic with tenacity library
- Complete logging with structured prefixes

### Documentation
- Comprehensive README with installation and usage
- USAGE.md with API examples and prompts
- Security and GDPR notes
- Troubleshooting guide

## [Unreleased]

### Planned
- Support for multiple AI providers (Anthropic Claude, Groq, Ollama)
- Advanced aggregations (SUM, AVG, COUNT in glossary)
- Temporal patterns (e.g., "not contacted in 6 months")
- Pattern learning from user feedback
- UI wizard for creating custom patterns
- SQL optimization for large datasets with caching
- Support for custom models
- Multi-table correlations (3+ tables)
