#LEGGE I FILE JSON APPENA CREATI E LI METTE SU MONGO DB PULENDO I RESIDUI DELLE VECCHIE COMPUTAZIONI
import json
import os
from pymongo import MongoClient

def importa_dati_mongodb():
    # 1. Connessione a MongoDB locale (porta standard 27017)
    try:
        # INIZIALIZZAZIONE DRIVER: Apertura del canale verso il MongoDB locale
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        # HEALTH CHECK STRATEGICO: Forza un ping sincrono verso il server per verificarne lo stato operativo 
        client.server_info() #È una chiamata che interroga il server chiedendogli dettagli sul sistema. Se il server risponde, sappiamo che è acceso; se non risponde entro 2 secondi (serverSelectionTimeoutMS=2000), scatta l'errore controllato.
        print("Connessione a MongoDB riuscita con successo!")
    except Exception as e:
        print("Errore: Assicurati che MongoDB sia avviato sul tuo Mac!")
        print(f"Dettaglio errore: {e}")
        return

    # SELEZIONE DELLO SPAZIO DI MEMORIZZAZIONE (Viene allocato dinamicamente se non esiste)
    # 2. Creazione o selezione del Database della tesi
    db = client["ecommerce_tesi_db"]
    
    # Mappatura tra i file generati e le collezioni di MongoDB
    file_da_caricare = {
        "customer": "customer_generati_ai.json",
        "product": "product_generati_ai.json",
        "order": "order_generati_ai.json"
    }
    
    print("\nInizio importazione dei dati sintetici...")
    print("-" * 40)

    for nome_collezione, nome_file in file_da_caricare.items():
        if not os.path.exists(nome_file):
            print(f"Avviso: File {nome_file} non trovato. Salto questa collezione.")
            continue
            
        # Leggiamo il file JSON
        with open(nome_file, 'r', encoding='utf-8') as f:
            documenti = json.load(f)
        
        collezione = db[nome_collezione]

        # IDEMPOTENZA DEL TEST: Svuota la collezione prima del popolamento per prevenire collisioni di chiavi        
        collezione.delete_many({}) #{} indicano che non c'è nessun filtro, quindi l'istruzione dice a MongoDB: "cancella tutto quello che trovi dentro questa specifica collezione". È fondamentale per fare in modo che ogni test sia "puro" e contenga sempre e solo 100 record freschi
        
        # BULK INGESTION: Scrittura massiva dell'intero array in un'unica transazione di rete
        # Inseriamo i 100 documenti
        if documenti:
            risultato = collezione.insert_many(documenti) #Invia l'intera lista di 100 record in un colpo solo.
            print(f" -> Collezione '{nome_collezione}': inseriti correttamente {len(risultato.inserted_ids)} documenti.")
            
    print("-" * 40)
    print("Processo completato! Il tuo database MongoDB è popolato e pronto.")
    print("Database creato: 'ecommerce_tesi_db'")
    print("Collezioni create: 'customer', 'product', 'order'")

if __name__ == "__main__":
    importa_dati_mongodb()
    