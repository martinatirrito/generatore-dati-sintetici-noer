#LEGGERE LE REGOLE DI NoER, INVENTARE I DATI E METTERLI IN TRE FILE JSON COERENTI  

import json
import os
import re
import ollama
from faker import Faker

fake = Faker('it_IT')

# Dizionari per la consistenza (Foreign Keys simulate)
ID_CLIENTI_REALI = []       # Memorizza dinamicamente gli UUID generati per i clienti
PRODOTTI_REALI = []         # Memorizza le coppie (ID, Nome) dei prodotti inseriti a catalogo
PANIERE_PRODOTTI_AI = []    # Memorizza l'array di stringhe restituito dal modello LLM

#DIALOGO CON AI 
def chiedi_prodotti_all_ai():
    """
    Interroga il modello locale Llama 3.2 tramite Ollama per ottenere
    un elenco di prodotti reali e coerenti con un contesto di e-commerce.
    """
    print("\n[AI] Sto interrogando Llama 3.2 in locale per generare prodotti realistici...")
    try:
        prompt = (
            "Genera una lista di 25 nomi di prodotti commerciali reali e variegati per un e-commerce generalista "
            "(es. 'Smartphone 5G', 'T-shirt in cotone', 'Caffettiera espresso', 'Zaino impermeabile'). "
            "Rispondi ESCLUSIVAMENTE con un array JSON di stringhe, senza alcuna introduzione, commento o formattazione markdown. "
            "Esempio di output richiesto: [\"Prodotto 1\", \"Prodotto 2\"]"
        )
        
        risposta = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        testo_risposta = risposta['message']['content'].strip()
        
        # ALGORITMO DI TRIMMING: Isola l'array JSON escludendo eventuale testo spurio dell'LLM
        #I metodi .find('[') e .rfind(']') tagliano via tutto il testo inutile, isolando solo la struttura racchiusa tra 
        #le parentesi quadre per evitare che il successivo json.loads vada in crash.
        inizio_array = testo_risposta.find('[')
        fine_array = testo_risposta.rfind(']') + 1

        if inizio_array != -1 and fine_array != -1:
            lista_prodotti = json.loads(testo_risposta[inizio_array:fine_array])
            print(f"[AI] Successo! Ricevuti {len(lista_prodotti)} prodotti reali dal modello linguistico.")
            return lista_prodotti
    except Exception as e:
        print(f"[Avviso] Errore di connessione a Ollama ({e}). Uso un paniere di backup standard.")

    # STRATEGIA DI FALLBACK: Garantisce la fault tolerance se il demone Ollama è offline
    return ["Laptop Pro 15", "Auricolari Bluetooth", "Orologio Smart", "Scrivania Regolabile", "Sedia Ergonomica"]

def pulisci_e_separa_schemi(nome_file):
    with open(nome_file, 'r', encoding='utf-8') as f:
        contenuto = f.read()
    
    #ESPRESSIONE REGOLARE: Intercetta i marcatori JSDoc '/** Collection NOME */' generati da NoER
    #La libreria re (Regular Expressions) cerca nel testo i pattern strutturati del tipo / Collection CUSTOMER */. 
    #Lo script usa questi commenti formali di NoER come dei "coltelli" per separare i vari schemi JSON e 
    #mapparli dentro un dizionario Python indicizzato per nome collezione
    blocchi = re.split(r'/\*\*\s*\*?\s*Collection\s+(\w+)\s*\*/', contenuto)
    schemi_collezioni = {}

    #ciclo per associare chiave-valore
    for i in range(1, len(blocchi), 2):
        nome_collezione = blocchi[i]
        testo_json = blocchi[i+1].strip()
        inizio_graffa = testo_json.find('{')
        if inizio_graffa != -1:
            schemi_collezioni[nome_collezione] = json.loads(testo_json[inizio_graffa:])
    return schemi_collezioni

#mappa i tipi BSON forniti da NoER
#Quando lo script sta analizzando lo schema dell'ordine (ORDER) e incontra il campo cid o pid, 
#ignora la generazione di stringhe casuali; va invece a pescare un valore all'interno dei vettori globali popolati 
#durante i cicli precedent. Se incontra un campo chiamato name, vi inietta i nomi commerciali sensati 
#estratti da Llama 3.2 (evitando che un prodotto e-commerce si chiami con parole casuali o latine prodotte da Faker).
def genera_valore_campo(nome_campo, info_campo, nome_collezione=""):
    tipo_bson = info_campo.get('bsonType')
    nome_min = nome_campo.lower()
    
    # Rilevamento e formattazione nativa dei campi temporali
    if tipo_bson == 'date' or 'date' in nome_min or 'data' in nome_min:
        return fake.date_this_year().isoformat()
        
    if tipo_bson == 'string':
        # INIEZIONE CHIAVI: Se siamo nell'ordine, recuperiamo un ID cliente realmente generato in precedenza
        if nome_collezione == "ORDER" and nome_min == "cid":
            return fake.random_element(ID_CLIENTI_REALI) if ID_CLIENTI_REALI else fake.uuid4()
        
        # INIEZIONE PRODOTTI: Associa l'ordine a un ID di un prodotto realmente esistente a catalogo
        if nome_collezione == "ORDER" and nome_min == "pid":
            return fake.random_element(PRODOTTI_REALI)["pid"] if PRODOTTI_REALI else fake.uuid4()
        
        # RISOLUZIONE BUG SEMANTICO: Sostituisce le stringhe casuali di Faker con i prodotti dell'AI
        if nome_min == "name":
            return fake.random_element(PANIERE_PRODOTTI_AI) if PANIERE_PRODOTTI_AI else fake.word()
            
        # Contesto standard migliorato
        # mappatura semantica standard (email, address, phone) tramite dizionario condizionale 
        if 'status' in nome_min:
            return fake.random_element(["In elaborazione", "Spedito", "Consegnato"])
        elif 'method' in nome_min:
            return fake.random_element(["Carta di Credito", "PayPal", "Bonifico"])
        elif 'firstname' in nome_min:
            return fake.first_name()
        elif 'lastname' in nome_min or 'surname' in nome_min:
            return fake.last_name()
        elif 'email' in nome_min:
            return fake.email()
        elif 'street' in nome_min or 'address' in nome_min:
            return fake.street_name()
        elif 'city' in nome_min:
            return fake.city()
        elif 'zipcode' in nome_min:
            return fake.postcode()
        elif 'phone' in nome_min:
            return fake.phone_number()
        else:
            return fake.word()
            
    elif tipo_bson == 'integer':
        if 'price' in nome_min:
            return fake.random_int(15, 800)
        elif 'quantity' in nome_min:
            return fake.random_int(1, 3)
        return fake.random_int(1, 50)
        
    elif tipo_bson == 'array':
        info_items = info_campo.get('items', {})
        if info_items.get('bsonType') == 'object':
            proprieta_oggetto = info_items.get('properties', {})
            return [generare_documento(proprieta_oggetto, nome_collezione) for _ in range(fake.random_int(1, 2))]
        else:
            return [fake.word() for _ in range(2)]
            
    elif tipo_bson == 'object':
        proprieta_oggetto = info_campo.get('properties', {})
        return generare_documento(proprieta_oggetto, nome_collezione)
        
    return None

def generare_documento(proprieta_schema, nome_collezione):
    documento = {}
    for nome_campo, info_campo in proprieta_schema.items():
        if nome_campo == '_id':
            nuovo_id = fake.uuid4()
            documento['_id'] = nuovo_id
            if nome_collezione == "CUSTOMER":
                ID_CLIENTI_REALI.append(nuovo_id)
        else:
            documento[nome_campo] = genera_valore_campo(nome_campo, info_campo, nome_collezione)
            
    if nome_collezione == "PRODUCT" and '_id' in documento and 'name' in documento:
        PRODOTTI_REALI.append({
            "pid": documento['_id'],
            "name": documento['name']
        })
        
    return documento


def avvia_generatore_ai():
    global PANIERE_PRODOTTI_AI
    nome_file_schema = 'e-commerce_platform_t_json_corretto.json'
    
    if not os.path.exists(nome_file_schema):
        print(f"Errore: File {nome_file_schema} non trovato.")
        return
        
    print("=== GENERATORE IBRIDO NoSQL (Python + LLM Locale) ===")
    scelta_utente = input("Quanti documenti vuoi generare per ogni collezione? (premi Invio per 100): ")
    quantita = int(scelta_utente) if scelta_utente.strip().isdigit() else 100
    
    PANIERE_PRODOTTI_AI = chiedi_prodotti_all_ai()
    
    schemi = pulisci_e_separa_schemi(nome_file_schema)
    #L'ordine dell'array non è casuale. Non possiamo generare un ORDER (ordine) se prima non abbiamo creato i clienti (CUSTOMER) e 
    #i prodotti (PRODUCT), perché altrimenti non avremmo ID reali a cui agganciarci per preservare l'integrità del database sintetico
    ordine_generazione = ["CUSTOMER", "PRODUCT", "ORDER"]
    database_popolato = {}
    
    for collezione in ordine_generazione:
        if collezione in schemi:
            print(f"\nGenerazione di {quantita} record per {collezione}...")
            proprieta = schemi[collezione].get('$jsonSchema', {}).get('properties', {})
            
            lista_documenti = [generare_documento(proprieta, collezione) for _ in range(quantita)]
            database_popolato[collezione] = lista_documenti
            
            nome_output = f"{collezione.lower()}_generati_ai.json"
            with open(nome_output, 'w', encoding='utf-8') as f:
                json.dump(lista_documenti, f, indent=4, ensure_ascii=False)
            print(f" -> Completato! Creato il file '{nome_output}'")
            
    if "ORDER" in database_popolato and database_popolato["ORDER"]:
        print("\n--- VERIFICA FINALE OUTPUT IBRIDO (Esempio di un ordine) ---")
        print(json.dumps(database_popolato["ORDER"][0], indent=4, ensure_ascii=False))

if __name__ == "__main__":
    avvia_generatore_ai()