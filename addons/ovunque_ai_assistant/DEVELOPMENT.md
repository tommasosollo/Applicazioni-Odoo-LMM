# Development Guide - Ovunque

Questa guida spiega come estendere e personalizzare il modulo Ovunque.

## Architettura del Modulo

```
Model (search.query)
        ↓
Controller API (/ovunque/search)
        ↓
LLM Processing (OpenAI)
        ↓
Domain Generator
        ↓
Database Query
        ↓
Frontend (search_bar.js)
```

## Componenti Principali

### 1. Model: `search_query.py`

Il core del sistema.

#### Metodo: `_parse_natural_language()`

Traduce il testo in dominio Odoo.

```python
def _parse_natural_language(self):
    # 1. Carica API key
    # 2. Recupera info del modello
    # 3. Chiama OpenAI
    # 4. Parsea il risultato
    # 5. Valida il dominio
    return domain
```

**Per personalizzare l'LLM:**

```python
# Sostituisci openai.ChatCompletion.create con il tuo provider
def _parse_natural_language(self):
    # Usa Ollama invece
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'mistral',
        'prompt': prompt_text,
        'stream': False
    })
    return self._parse_domain_response(response.json()['response'])
```

#### Metodo: `_build_prompt()`

Crea il prompt per l'LLM.

**Personalizzazione:** Aggiungi context specifico al dominio

```python
def _build_prompt(self, model_fields):
    fields_info = self._get_field_info(model_fields)
    
    # Aggiungi istruzioni custom
    prompt = f"""
    ...
    IMPORTANT: For dates, always use YYYY-MM-DD format
    For money, use amounts in EUR
    For names, use ilike operator for case-insensitive search
    ...
    """
    return prompt
```

### 2. Controller: `search_controller.py`

API endpoints per il frontend.

#### Route: `POST /ovunque/search`

```python
@http.route('/ovunque/search', type='json', auth='user', methods=['POST'])
def natural_language_search(self, **kwargs):
    query_text = kwargs.get('query')
    model_name = kwargs.get('model')
    # ... esegui ricerca
    return {
        'success': True,
        'results': [...],
        'count': ...,
        'domain': ...
    }
```

**Per aggiungere filtraggio personalizzato:**

```python
@http.route('/ovunque/search', type='json', auth='user', methods=['POST'])
def natural_language_search(self, **kwargs):
    # Aggiungi filtri extra prima di restituire
    domain = eval(search_record.model_domain)
    
    # Aggiungi sempre il company_id corrente
    domain += [('company_id', '=', request.env.company.id)]
    
    results = Model.search(domain)
    return {...}
```

### 3. Frontend: `search_bar.js`

Widget di ricerca per il browser.

#### Classe: `SearchBar`

```javascript
SearchBar.executeSearch = function() {
    // 1. Legge input
    // 2. Chiama API
    // 3. Mostra risultati
}
```

**Per personalizzare la barra:**

```javascript
// Aggiungi filtri aggiuntivi
executeSearch: function() {
    const company = this.getCompanyFilter();
    const warehouse = this.getWarehouseFilter();
    
    // Passa al backend
    rpc.query({
        route: '/ovunque/search',
        params: {
            query: query,
            model: model,
            company_id: company,
            warehouse_id: warehouse
        }
    });
}
```

## Estensioni Comuni

### 1. Aggiungere un nuovo modello

```python
# In controllers/search_controller.py
searchable_models = [
    'account.move',
    'product.product',
    'custom.model',  # Aggiungi il tuo modello
]
```

### 2. Aggiungere filtri personalizzati

```python
# In models/search_query.py
def action_execute_search(self):
    domain = self._parse_natural_language()
    
    # Aggiungi filtri automatici
    domain += [
        ('company_id', '=', self.env.company.id),  # Azienda corrente
        ('active', '=', True),  # Solo record attivi
    ]
    
    Model = self.env[self.model_name]
    results = Model.search(domain)
    # ...
```

### 3. Integrare LLM locale (Ollama)

```python
# In models/search_query.py
import requests

def _parse_natural_language(self):
    # Usa Ollama invece di OpenAI
    prompt = self._build_prompt(model_fields)
    
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'mistral',
            'prompt': prompt,
            'stream': False,
            'temperature': 0.2,
        }
    )
    
    response_text = response.json()['response']
    domain = self._parse_domain_response(response_text)
    return domain
```

### 4. Aggiungere caching dei risultati

```python
# In models/search_query.py
from odoo.tools import cache

@cache('search.query._parse_natural_language', 300)  # Cache 5 minuti
def _parse_natural_language(self):
    # Cached method
    return self._execute_llm_call()
```

### 5. Aggiungere logging dettagliato

```python
import logging

_logger = logging.getLogger(__name__)

def _parse_natural_language(self):
    _logger.info(f"Processing query: {self.name}")
    
    try:
        domain = self._execute_llm_call()
        _logger.info(f"Generated domain: {domain}")
        return domain
    except Exception as e:
        _logger.error(f"LLM error: {e}", exc_info=True)
        raise
```

## Testing

### Eseguire i test

```bash
./odoo-bin -c config.conf -u all --test-enable --stop-after-init
```

### Scrivere test custom

```python
# In tests.py
from odoo.tests import TransactionCase

class TestCustomSearch(TransactionCase):
    
    def test_my_custom_query(self):
        query = self.env['search.query'].create({
            'name': 'My test query',
            'model_name': 'res.partner',
        })
        
        query.action_execute_search()
        
        self.assertEqual(query.status, 'success')
        self.assertGreater(query.results_count, 0)
```

## Performance Tips

1. **Caching**: Implementa caching per query frequenti
2. **Batch operations**: Processa più query in parallelo
3. **Index**: Aggiungi indici ai campi comuni (`name`, `date`, `state`)
4. **Limit**: Limita i risultati a 50-100 record

```python
def action_execute_search(self):
    domain = self._parse_natural_language()
    
    Model = self.env[self.model_name]
    results = Model.search(domain, limit=100)  # Aggiungi limit
    
    self.results_count = Model.search_count(domain)
```

## Debugging

### Visualizzare i logs

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info("Info message")
_logger.warning("Warning")
_logger.error("Error")
_logger.debug("Debug info")
```

Vedi i logs in:
- **Settings** > **Technical** > **Logs**
- O nella console Odoo

### Debuggare il LLM Response

La query errata viene salvata in `raw_response` per ogni search query.

```python
query = self.env['search.query'].search([('status', '=', 'error')], limit=1)
print(query.raw_response)  # Vedi esattamente cosa ha generato l'LLM
```

## Best Practices

1. **Sempre validare il dominio** prima di eseguire
2. **Loggare errori dettagliati** per debugging
3. **Testare con diversi LLM** per robustezza
4. **Aggiungere timeout** alle chiamate API
5. **Implementare retry logic** per errori temporanei
6. **Documentare le estensioni** con docstrings

## Risorse

- [Odoo ORM API](https://www.odoo.com/documentation/19.0/developer/reference/orm.html)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- [Odoo Domain Syntax](https://www.odoo.com/documentation/19.0/developer/reference/orm.html#search)
- [Ollama Documentation](https://ollama.ai)

## Supporto

Per domande o problemi, consulta:
- [README.md](README.md) - Guida principale
- [QUICKSTART.md](QUICKSTART.md) - Setup rapido
- Issues nel repository
