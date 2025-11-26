# Guida per Sviluppatori - Ovunque

Documenti per chi vuole modificare, estendere o debuggare il modulo Ovunque.

## Setup Locale

### Prerequisiti
- Python 3.10+
- Odoo 19.0
- OpenAI API key

### Installazione Dev Environment

```bash
# 1. Copia il modulo nella directory addons di Odoo
cp -r addons/ovunque /path/to/your/odoo/addons/

# 2. Installa le dipendenze
pip install -r addons/ovunque/requirements.txt

# 3. Riavvia Odoo (in modalità dev)
./odoo-bin -c odoo.conf -d database_name -u ovunque
```

### Reinstallare il modulo in dev

Quando modifichi i file:

```bash
# Upgrade modulo (ricarica il codice)
./odoo-bin -c odoo.conf -d database_name -u ovunque

# O reinstalla completamente
./odoo-bin -c odoo.conf -d database_name --uninstall ovunque -u ovunque

# Per sviluppo interattivo con hot reload:
./odoo-bin -c odoo.conf -d database_name -u ovunque --dev=all
```

## Struttura del Modulo

```
ovunque/
├── __manifest__.py                    # Metadati e dipendenze
├── __init__.py                        # Import models/controllers
├── models/
│   ├── __init__.py
│   └── search_query.py               # Model SearchQuery e SearchResult
├── controllers/
│   ├── __init__.py
│   └── search_controller.py          # REST API endpoints
├── views/
│   ├── search_query_views.xml        # UI model e form
│   └── menu.xml                      # Menu Odoo
├── security/
│   └── ir.model.access.csv           # Permessi accesso
├── requirements.txt                   # Dipendenze Python (openai)
├── utils.py                           # Funzioni utilità helper
├── tests.py                           # Test unitari
├── config_example.py                  # Script di configurazione
├── .env.example                       # Template variabili ambiente
├── README.md                          # Documentazione utenti
├── QUICKSTART.md                      # Guida veloce setup
└── DEVELOPMENT.md                     # Questo file
```

## File Importanti

### `__manifest__.py`
Metadati e configurazione del modulo:

```python
{
    'name': 'Ovunque - Natural Language Search for Odoo',
    'version': '19.0.1.0.0',
    'depends': ['base', 'web'],           # Dipendenze moduli Odoo
    'external_dependencies': {
        'python': ['openai'],              # Librerie Python esterne
    },
    'data': [
        'security/ir.model.access.csv',   # Permessi
        'views/search_query_views.xml',   # Viste
        'views/menu.xml',                 # Menu
    ],
}
```

### `models/search_query.py`

**Classe: SearchQuery**
Gestisce le query di ricerca.

Metodi principali:

#### `action_execute_search(self)`
Esegue la ricerca e popola i risultati.

```python
def action_execute_search(self):
    for record in self:
        # 1. Ripulisci risultati precedenti
        record.result_ids.unlink()
        
        # 2. Genera dominio da GPT-4
        domain = record._parse_natural_language()
        
        # 3. Salva dominio
        record.model_domain = str(domain)
        
        # 4. Esegui query
        Model = self.env[record.model_name]
        results = Model.search(domain)
        
        # 5. Salva risultati
        record.results_count = len(results)
        for res in results:
            record.result_ids.create({...})
```

#### `_parse_natural_language(self)`
Comunica con OpenAI e ritorna il dominio Odoo.

```python
def _parse_natural_language(self):
    # 1. Prendi API key da config
    api_key = self.env['ir.config_parameter'].sudo().get_param('ovunque.openai_api_key')
    
    # 2. Crea client OpenAI
    client = OpenAI(api_key=api_key)
    
    # 3. Costruisci prompt con metadati del modello
    prompt = self._build_prompt(model_fields)
    
    # 4. Chiama GPT-4
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", ...}, {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )
    
    # 5. Estrai e parse dominio
    response_text = response.choices[0].message.content
    domain = self._parse_domain_response(response_text)
    
    return domain
```

#### `_build_prompt(self, model_fields)`
Crea il prompt per GPT-4.

Struttura:
1. **System role**: Istruzioni su cosa fare
2. **Model info**: Nome modello + lista campi disponibili
3. **Query**: La domanda dell'utente
4. **Constraints**: Operatori supportati, formato date, esempi

**Come customizzare**:
```python
def _build_prompt(self, model_fields):
    prompt = f"""
    You are an Odoo domain filter generator...
    
    Model: {self.model_name}
    Fields:
    {self._get_field_info(model_fields)}
    
    Query: {self.name}
    
    IMPORTANT: Respond with ONLY a Python list [...]
    """
    return prompt
```

#### `_parse_domain_response(self, response_text)`
Estrae il dominio Odoo dalla risposta di GPT-4.

**Gestisce**:
- Markdown (````python ... ````)
- Testo spurio prima/dopo la lista
- Whitespace e newline
- Domini vuoti `[]`

**Fallback**:
- Prova `ast.literal_eval()` (safe)
- Fallback a `eval()` (meno sicuro ma più permissivo)

**Classe: SearchResult**
Memorizza i singoli record trovati.

Campi:
- `query_id`: Link a SearchQuery
- `record_id`: ID del record
- `record_name`: display_name del record
- `model`: Nome del modello

### `controllers/search_controller.py`

**Endpoint 1: POST /ovunque/search**
```python
@http.route('/ovunque/search', type='jsonrpc', auth='user', methods=['POST'])
def natural_language_search(self, **kwargs):
    # 1. Estrai parametri
    query_text = kwargs.get('query')
    model_name = kwargs.get('model')
    
    # 2. Crea SearchQuery record
    search_record = request.env['search.query'].create({
        'name': query_text,
        'model_name': model_name,
    })
    
    # 3. Esegui
    search_record.action_execute_search()
    
    # 4. Ritorna risultati
    if search_record.status == 'success':
        return {
            'success': True,
            'results': [...],
            'count': search_record.results_count,
        }
    else:
        return {
            'success': False,
            'error': search_record.error_message
        }
```

**Endpoint 2: GET /ovunque/models**
```python
@http.route('/ovunque/models', type='jsonrpc', auth='user')
def get_available_models(self, **kwargs):
    # Ritorna lista di modelli disponibili
    SearchQuery = request.env['search.query']
    models = []
    for code, label in SearchQuery.AVAILABLE_MODELS:
        models.append({'name': code, 'label': label})
    return {'success': True, 'models': models}
```

### `views/search_query_views.xml`

Viste Odoo (ORM → UI mapping).

**search_query_view_list**: Lista di tutte le query eseguite
```xml
<record id="search_query_view_list" model="ir.ui.view">
    <field name="name">search.query.list</field>
    <field name="model">search.query</field>
    <field name="arch" type="xml">
        <list>
            <field name="name"/>          <!-- Query text -->
            <field name="model_name"/>    <!-- Target model -->
            <field name="status"/>        <!-- Badge success/error -->
            <field name="results_count"/> <!-- # risultati -->
        </list>
    </field>
</record>
```

**search_query_view_form**: Dettaglio singola query
```xml
<record id="search_query_view_form" model="ir.ui.view">
    <field name="name">search.query.form</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_execute_search" string="Execute Search" class="btn-primary"/>
            </header>
            <sheet>
                <group>
                    <field name="name"/>        <!-- Query input -->
                    <field name="model_name"/>  <!-- Dropdown modelli -->
                </group>
                <notebook>
                    <page string="Results">
                        <field name="result_ids"/>  <!-- Tabella risultati -->
                    </page>
                    <page string="Debug Info">
                        <field name="model_domain"/>    <!-- Dominio generato -->
                        <field name="raw_response"/>    <!-- Risposta GPT-4 -->
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

### `views/menu.xml`

Struttura menu Odoo:

```xml
<menuitem id="menu_ovunque" name="Ovunque" sequence="10"/>
  <!-- Search Queries submenu -->
  <menuitem parent="menu_ovunque" name="Search Queries" 
            action="action_search_query_view" sequence="10"/>
  <!-- Results submenu -->
  <menuitem parent="menu_ovunque" name="Results" 
            action="action_search_result_view" sequence="15"/>
  <!-- Configuration submenu -->
  <menuitem id="menu_ovunque_config" parent="menu_ovunque" 
            name="Configuration" sequence="20"/>
```

### `security/ir.model.access.csv`

Permessi di accesso ai model (CSV):

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_search_query_user,search_query access for users,model_search_query,base.group_user,1,1,1,0
access_search_query_manager,search_query access for managers,model_search_query,base.group_system,1,1,1,1
access_search_result_user,search_result access for users,model_search_result,base.group_user,1,0,0,0
access_search_result_manager,search_result access for managers,model_search_result,base.group_system,1,1,1,1
```

Colonne:
- `id`: ID univoco (XML)
- `name`: Label descrittivo
- `model_id:id`: Riferimento al model
- `group_id:id`: Gruppo (users, managers)
- `perm_read/write/create/unlink`: 1=permesso, 0=negato

### `requirements.txt`

Dipendenze Python del modulo:

```
openai>=1.0.0
```

Installa con:
```bash
pip install -r addons/ovunque/requirements.txt
```

Oppure nel virtual environment di Odoo:
```bash
source /path/to/odoo/venv/bin/activate
pip install -r addons/ovunque/requirements.txt
```

### `.env.example`

Template per variabili d'ambiente:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Come usare:
```bash
# 1. Copia il file
cp addons/ovunque/.env.example .env

# 2. Modifica con i tuoi valori
# OPENAI_API_KEY=sk-your-actual-key

# 3. Carica le variabili
source .env
# Oppure esporta singolarmente
export OPENAI_API_KEY=sk-your-key
```

Nel `config_example.py` le variabili vengono lette da `.env` automaticamente.

### `utils.py`

Funzioni utilità helper per il modulo:

#### `setup_api_key(env, api_key)`
Configura la chiave API di OpenAI in Odoo:
```python
from ovunque.utils import setup_api_key
setup_api_key(self.env, 'sk-...')
```

#### `get_model_fields_for_llm(env, model_name, limit=30)`
Recupera i campi di un modello formattati per LLM:
```python
from ovunque.utils import get_model_fields_for_llm
fields_info = get_model_fields_for_llm(self.env, 'res.partner', limit=30)
# Ritorna stringa formattata:
# - name (char): Name
# - email (email): Email Address
# ...
```

#### `validate_domain(domain)`
Valida che un dominio sia corretto:
```python
from ovunque.utils import validate_domain
assert validate_domain([('name', 'ilike', 'test')])  # True
assert not validate_domain([('name', 'test')])       # False
```

#### `parse_search_results(records, max_results=50)`
Converte resultset a lista di dict:
```python
results = get_model_fields_for_llm(records, max_results=50)
# Ritorna: [{'id': 1, 'display_name': 'John Doe'}, ...]
```

#### `common_search_patterns()`
Ritorna esempi di query per ogni modello:
```python
patterns = common_search_patterns()
# patterns['account.move'] = ["Unpaid invoices from this month", ...]
```

### `config_example.py`

Script per configurare il modulo automaticamente:

Uso:
```bash
# Via Python script
python addons/ovunque/config_example.py

# Oppure leggi la env var OPENAI_API_KEY da .env
```

Il file configura automaticamente:
1. Legge `OPENAI_API_KEY` da variabile d'ambiente
2. Configura il parametro `ovunque.openai_api_key` in Odoo
3. Stampa conferma di successo

### `tests.py`

Test unitari per il modulo. Include test per:

**TestOvunqueSearchQuery**:
- `test_create_search_query()`: Crea query di ricerca
- `test_search_query_required_fields()`: Valida campi required
- `test_search_query_defaults()`: Testa valori di default
- `test_domain_parsing()`: Testa parsing di domini
- `test_invalid_model_name()`: Testa gestione modelli non validi

**TestOvunqueControllers**:
- `test_models_endpoint()`: Testa endpoint /ovunque/models

**TestOvunqueUtils**:
- `test_validate_domain()`: Valida dominio checker
- `test_common_search_patterns()`: Testa libreria pattern

Esegui i test:
```bash
# Via Odoo test runner
./odoo-bin -c odoo.conf -d database_name -u ovunque --test-enable

# Oppure via pytest
python -m pytest addons/ovunque/tests.py -v

# Con coverage
python -m pytest addons/ovunque/tests.py --cov=ovunque --cov-report=html
```

## Debugging

### Visualizzare i log di Odoo

```bash
# Se Odoo è in esecuzione in foreground
tail -f /var/log/odoo/odoo.log

# Oppure con systemctl
journalctl -u odoo -f --tail 50
```

### Log message nel codice

```python
import logging
_logger = logging.getLogger(__name__)

# Nel tuo codice:
_logger.info(f"Query: {self.name}")
_logger.error(f"Error: {e}")
_logger.warning("Attenzione!")
```

### Testare via Python shell

```bash
# Da un terminale separato, con Odoo in esecuzione
./odoo-bin -c odoo.conf -d database_name --shell

# Dentro la shell Python (sostituisci con i tuoi valori):
>>> from odoo.api import Environment

>>> SearchQuery = env['search.query']
>>> query = SearchQuery.create({
...     'name': 'test query',
...     'model_name': 'res.partner',
... })
>>> query.action_execute_search()
>>> print(query.model_domain)
>>> print(query.results_count)
```

### Abilitare il debugger

```bash
# Avvia Odoo in modalità debug
./odoo-bin -c odoo.conf -d database_name --dev=pdb

# Nel codice, aggiungi un breakpoint:
import pdb; pdb.set_trace()

# Oppure usa breakpoint() (Python 3.7+)
breakpoint()
```

## Estensioni Comuni

### 1. Aggiungere un nuovo modello

Modifica `models/search_query.py`:

```python
AVAILABLE_MODELS = [
    ('res.partner', 'Partner / Contact'),
    ('stock.picking', 'Stock Picking'),  # NUOVO
]
```

### 2. Cambiare il modello LLM

Da GPT-4 a GPT-3.5 (più economico):

```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Invece di "gpt-4"
    ...
)
```

Oppure usare un modello locale con Ollama:

```python
from ollama import OllamaLLM

def _parse_natural_language(self):
    llm = OllamaLLM(model="mistral")
    response = llm.invoke(prompt)
    return self._parse_domain_response(response)
```

### 3. Aggiungere cache ai risultati

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _parse_natural_language_cached(query_text, model_name):
    # Cache la risposta di GPT-4
    ...
```

### 4. Aggiungere validazione dominio

```python
def _validate_domain(self, domain):
    """Verifica che il dominio sia valido per il modello"""
    Model = self.env[self.model_name]
    try:
        # Test: cerca con il dominio
        results = Model.search(domain, limit=1)
        return True
    except Exception as e:
        _logger.error(f"Invalid domain: {e}")
        return False
```

### 5. Exportare risultati a CSV

```python
def action_export_csv(self):
    """Esporta i risultati a CSV"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    for result in self.result_ids:
        writer.writerow([result.record_id, result.record_name])
    
    return {
        'type': 'ir.actions.act_url',
        'url': f'/download/results_{self.id}.csv',
        'target': 'new',
    }
```

## Testing

Il modulo include test unitari completi in `tests.py`. Per aggiungere un nuovo test:

### Struttura di un Test

```python
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestMyFeature(TransactionCase):
    def setUp(self):
        super().setUp()
        self.SearchQuery = self.env['search.query']
    
    def test_my_feature(self):
        """Test description"""
        query = self.SearchQuery.create({
            'name': 'Test query',
            'model_name': 'res.partner',
        })
        self.assertEqual(query.status, 'draft')
```

### Eseguire i Test

```bash
# Tutti i test del modulo
./odoo-bin -c odoo.conf -d database_name -u ovunque --test-enable

# Oppure via pytest (se disponibile)
python -m pytest addons/ovunque/tests.py -v

# Test specifico
python -m pytest addons/ovunque/tests.py::TestOvunqueSearchQuery::test_create_search_query -v

# Con coverage
python -m pytest addons/ovunque/tests.py --cov=ovunque --cov-report=html
```

### Test Coverage

I test attuali coprono:
- ✅ Creazione di search query
- ✅ Validazione campi required
- ✅ Valori di default
- ✅ Parsing dominio
- ✅ Gestione modelli non validi
- ✅ Endpoints API
- ✅ Funzioni utilità

## Performance Tips

1. **Limita i risultati**: Modifica `max_results` in `action_execute_search()`
2. **Caching**: Cache i domini generati per query simili
3. **Async**: Usa Odoo jobs per query lunghe
4. **Index DB**: Aggiungi indici sui campi più cercati

## Common Issues

### "ImportError: No module named openai"

```bash
# Installa la libreria
pip install openai>=1.0.0

# Oppure nel virtual environment di Odoo
source /path/to/odoo/venv/bin/activate
pip install -r addons/ovunque/requirements.txt

# Riavvia Odoo
./odoo-bin -c odoo.conf -d database_name -u ovunque
```

### "Module not found" o "Model is not installed"

Reinstalla il modulo:
```bash
# Via CLI
./odoo-bin -c odoo.conf -d database_name --uninstall ovunque -u ovunque

# Oppure via Web UI
Ovunque → App Library → Ovunque → Install/Upgrade
```

### GPT-4 ritorna dominio vuoto `[]`

Aumenta il `max_tokens` o aggiungi più context al prompt in `models/search_query.py`:
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    max_tokens=800,  # Aumentato da 500
)
```

### Timeout su query lunghe

Aumenta il timeout di Odoo in `odoo.conf`:
```ini
[options]
http_request_timeout = 120  # secondi
```

### Errore: "API key not configured"

Verifica che la chiave sia stata salvata:
```bash
# Via shell Odoo
./odoo-bin -c odoo.conf -d database_name --shell

# Dentro la shell:
>>> env['ir.config_parameter'].sudo().get_param('ovunque.openai_api_key')
```

Se vuoto, configura:
```python
env['ir.config_parameter'].sudo().set_param('ovunque.openai_api_key', 'sk-your-key')
```

## Checklist per PR

- [ ] Test locali passano
- [ ] Nessun errore nei log
- [ ] Documentazione aggiornata
- [ ] Database migrations (se necessario)
- [ ] Permessi aggiornati in `ir.model.access.csv`
- [ ] Codice formattato (black, flake8)
- [ ] Commit message descrittivo

## License

AGPL-3.0 - Vedi LICENSE file
