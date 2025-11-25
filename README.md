# Ovunque - Natural Language Search for Odoo 19

Una ricerca Google per i tuoi dati Odoo. Scrivi come parli e lascia che l'AI faccia il resto.

## Problema Risolto

Il piccolo imprenditore non sa usare i "Filtri Personalizzati" di Odoo. Se vuole sapere:
- "Chi mi deve pagare?"
- "Quali prodotti stanno finendo?"

Deve cliccare 5 volte o chiedere alla segretaria. Con **Ovunque**, scrive semplicemente: "Fammi vedere tutte le fatture non pagate di Rossi di quest'anno".

## Come Funziona

1. **Input**: L'utente scrive una query in linguaggio naturale
2. **LLM Processing**: OpenAI GPT-4 traduce il testo in un dominio Odoo
3. **Query Execution**: Il dominio viene eseguito sul database
4. **Results**: I risultati vengono visualizzati nella barra di ricerca

## Installazione

### 1. Requisiti

- Odoo 19
- Python 3.10+
- OpenAI API key

### 2. Installare dipendenze Python

```bash
pip install openai
docker exec odoo-ai-19 pip install --break-system-packages openai
```

### 3. Clonare il modulo

```bash
cd addons
git clone <repository> ovunque
```

oppure copiare la cartella `ovunque` in `addons/`.

### 4. Installare il modulo in Odoo

1. Andare a **App** > **Apps** > **Update Apps List**
2. Cercare **Ovunque**
3. Cliccare **Install**

## Configurazione

### 1. Impostare OpenAI API Key

Dopo l'installazione:

1. Andare a **Ovunque** > **Configuration** > **API Settings**
2. Aggiungere il parametro:
   - **Key**: `ovunque.openai_api_key`
   - **Value**: `sk-...` (la tua OpenAI API key)

Oppure in Python:

```python
env['ir.config_parameter'].sudo().set_param('ovunque.openai_api_key', 'sk-your-key')
```

### 2. (Opzionale) Usare Ollama per LLM locale

Se vuoi usare un modello locale con Ollama, modifica `models/search_query.py`:

```python
# Sostituisci openai.ChatCompletion.create con:
import subprocess
response_text = subprocess.check_output([
    'curl', 'http://localhost:11434/api/generate',
    '-d', json.dumps({
        'model': 'mistral',
        'prompt': prompt,
        'stream': False
    })
]).decode().split('\n')[-2]
```

## Utilizzo

### Search Queries Panel

Per fare una ricerca, vai a **Ovunque → Search Queries** dalla barra laterale.

1. Clicca **Create**
2. Scrivi la tua domanda nel campo **Query Text**
3. Seleziona il **Target Model** (Partner, Invoice, Product, etc.)
4. Clicca **Execute Search**

I risultati appariranno nella tab **Results**.

### Esempi di Query

**Fatture (account.move):**
- "Fatture non pagate di questo mese"
- "Tutte le fatture di Rossi del 2024"
- "Fatture con importo > 1000 euro"

**Prodotti (product.product):**
- "Prodotti in magazzino sotto i 5 pezzi"
- "Tutti i prodotti della categoria 'Elettronica'"
- "Prodotti con prezzo tra 10 e 100 euro"

**Ordini di Vendita (sale.order):**
- "Ordini spediti della scorsa settimana"
- "Ordini in sospeso di cliente Milano"

**Contatti (res.partner):**
- "Fornitori della regione Toscana"
- "Clienti che non hanno ordinato nel 2024"

### Visualizzare la Cronologia

Vai a **Ovunque → Search Queries** per visualizzare:
- Cronologia di tutte le query eseguite
- Dominio generato dall'IA
- Numero di risultati
- Errori (se presenti)

## Architettura

```
ovunque/
├── __manifest__.py          # Metadati modulo
├── models/
│   └── search_query.py      # Model per gestire le query
├── controllers/
│   └── search_controller.py # API endpoints
├── views/
│   ├── search_query_views.xml  # Viste per il model
│   └── menu.xml             # Menu e azioni
└── static/src/
    ├── js/search_bar.js     # Widget di ricerca
    └── xml/search_template.xml # Template HTML
```

## File Importanti

### `models/search_query.py`

Il cuore del sistema. Conteniene:
- `_parse_natural_language()`: Comunica con OpenAI e traduce il testo
- `_build_prompt()`: Crea il prompt con i metadati del modello
- `action_execute_search()`: Esegue il dominio e recupera risultati

### `controllers/search_controller.py`

REST API:
- `POST /ovunque/search`: Ricerca principale
- `GET /ovunque/models`: Lista modelli disponibili

### `static/src/js/search_bar.js`

Widget frontend che:
- Aggiunge barra di ricerca a ogni lista view
- Gestisce input/output utente
- Comunica con le API backend

## Troubleshooting

### "OpenAI API key not configured"

```
Soluzione: Impostare la chiave API in Ovunque > Configuration > API Settings
```

### "Could not parse the query"

```
Motivi comuni:
1. LLM ha generato un dominio invalido
2. Nome del campo sbagliato
3. Tipo di dato non riconosciuto

Soluzione: Controllare "Raw LLM Response" in Ovunque > Search Queries
```

### Risultati sbagliati

```
Il prompt potrebbe aver bisogno di regolazione.
Modifica _build_prompt() in models/search_query.py per aggiungere più context.
```

## Limitazioni Attuali

- Massimo 50 risultati per query
- Supporta solo modelli standard di Odoo
- Richiede OpenAI API (costo per token)
- Non supporta query complesse multi-modello (JOIN)
- Search Queries accessible solo dal menu dedicato (non integrata nelle list views)

## Prossime Features

- [ ] **Barra di ricerca integrata** nelle list views
- [ ] Caching dei risultati
- [ ] Supporto per Llama 2, Mixtral (modelli open-source)
- [ ] Query complesse con JOIN tra modelli
- [ ] Esportazione risultati (CSV, Excel)
- [ ] Salvataggio query personalizzate come filtri
- [ ] Dashboard con query frequenti
- [ ] Integrazione con chatbot Odoo
- [ ] Autocomplete per nomi di campi
- [ ] Storico delle query eseguite per singolo utente

## License

AGPL-3.0

## Support

Per bug o suggerimenti, aprire un issue nel repository.
