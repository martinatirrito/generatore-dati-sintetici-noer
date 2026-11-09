L'aspetto innovativo del sistema risiede nel suo **approccio ibrido**:
1. **Dati Strutturati Standard (Libreria Faker):** Campi senza dipendenze logiche complesse (UUID, nomi, date, telefoni) vengono sintetizzati istantaneamente per ottimizzare i tempi di calcolo.
2. **Contesto Semantico (LLM locale Llama 3.2 via Ollama):** Campi legati a vincoli semantici e di dominio (es. nomi e descrizioni di prodotti coerenti) vengono sintetizzati sfruttando l'Intelligenza Artificiale Generativa offline per salvaguardare la riservatezza delle informazioni.

---

## Struttura del Progetto
Il modulo software si compone di due script principali in linguaggio Python:

* `generatore.py`: Contiene l'intero motore algoritmico per la generazione ibrida e il mantenimento dell'integrità referenziale.
* `carica_su_mongodb.py`: Gestisce la pipeline di persistenza dei dati, la connessione sicura con il DBMS e il caricamento di massa (Bulk Import) dei record.

---

## 1. Il Motore di Generazione: `generatore.py`
Questo script si occupa di generare in-memory i record per le tre collezioni principali (`customer`, `product`, `order`), assicurando una consistenza incrociata al 100%.

### Logica delle Funzioni Principali
Lo script implementa le seguenti funzioni e procedure logiche:

#### A. Generazione Clienti (`customer`)
* **Funzione/Logica:** Utilizza un ciclo iterativo per istanziare i record dei clienti.
* **Approccio:** Essendo dati anagrafici standard, la sintesi è affidata interamente alla libreria `Faker`.
* **Campi Generati:** `_id` (UUID), `firstname`, `lastname`, `email`, `address`.

#### B. Generazione Prodotti (`product`)
* **Funzione/Logica:** Interroga localmente l'LLM per ottenere coppie coerenti di nome prodotto e descrizione.
* **Approccio:** Prompt strutturato per forzare l'output in formato JSON. Include un blocco di gestione errori (`try-except`) per gestire eventuali risposte non conformi dell'LLM senza bloccare il processo.

#### C. Integrità Referenziale negli Ordini (`order`)
* **Funzione/Logica:** Associa i prodotti generati ai clienti esistenti.
* **Approccio:** Estrae gli ID dal registro dei clienti generati e crea l'ordine incorporando i dettagli del prodotto e calcolando dinamicamente il prezzo totale.

---

## 2. Pipeline di Persistenza: `carica_su_mongodb.py`
Questo script gestisce il caricamento dei dati generati all'interno di MongoDB:

* **Pulizia Iniziale:** Esegue un `drop()` delle collezioni esistenti per garantire l'idempotenza del processo (evitando duplicati a ogni esecuzione).
* **Bulk Ingestion:** Utilizza `insert_many()` per caricare i vettori di documenti in un'unica operazione di rete, ottimizzando i tempi di scrittura.

---

## 3. Validazione tramite Query di Aggregazione (Lookup)
Per verificare la corretta consistenza referenziale tra le collezioni, è possibile eseguire la seguente query di test in MongoDB (tramite playground o shell):

```javascript
use('ecommerce_tesi_db');

db.order.aggregate([
  { $limit: 1 },    {$lookup: {
      from: "customer",
      localField: "CUSTOMER.cid", // Dot notation per raggiungere l'ID del cliente nell'ordine
      foreignField: "_id",
      as: "cliente_associato"
    }
  }
]);