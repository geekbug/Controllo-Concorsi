import requests
from bs4 import BeautifulSoup
import json
import os
import time
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from urllib.parse import urljoin

# ==========================================
# CONFIGURAZIONE SITI DA MONITORARE
# ==========================================

SITES_TO_MONITOR = [
    {
        "name": "InPA-Diverse Amministrazioni-Assistenti",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=2479a6e7761b48f2be7fa54b3699cb98"
    },
    {
        "name": "InPA-Diverse Amministrazioni-Funzionari",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=054e2ea57835433bad131fcae791b810"
    }
    # Aggiungi qui altri concorsi o pagine web da monitorare:
    # ,
    # {
    #     "name": "Nome del Concorso o Ente",
    #     "url": "https://www.esempio.it/bandi-di-concorso"
    # }
]

STATE_FILE = "known_links.json"

# Configurazione Email
# Le credenziali del mittente vengono lette dalle variabili d'ambiente (GitHub Secrets)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Inserisci qui uno o più indirizzi email a cui inviare le notifiche
RECIPIENT_EMAILS = ["tuo.indirizzo@esempio.com", "altro.destinatario@esempio.com"]

# ==========================================

def get_links_from_page(url):
    """Scarica la pagina e ne estrae i link nella sezione del contenuto principale."""
    try:
        # Un User-Agent standard per evitare di essere bloccati da alcuni siti istituzionali
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[{datetime.now()}] Errore durante il caricamento di {url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Cerchiamo il tag <main> per evitare i link del menu di navigazione
    main_content = soup.find("main")
    if not main_content:
        # Fallback all'intera pagina se non c'è un tag <main>
        main_content = soup

    links = set()
    for a_tag in main_content.find_all("a", href=True):
        href = a_tag['href'].strip()
        
        # Risolviamo i link relativi in modo automatico (es. /pagina.html diventa https://sito.it/pagina.html)
        href = urljoin(url, href)
        
        # Ignoriamo i link vuoti, ancore interne (#) o script/mailto
        if href and not href.startswith(('javascript:', 'mailto:', 'tel:')) and '#' not in href:
            links.add(href)
            
    return links

def load_known_links():
    """Carica i link salvati precedentemente (strutturati a dizionario)."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {}
            return {site: set(links) for site, links in data.items()}
    except Exception as e:
        print(f"[{datetime.now()}] Errore durante la lettura del file di stato: {e}")
        return {}

def save_known_links(state_dict):
    """Salva il dizionario dei link nel file JSON."""
    try:
        serializable_data = {site: list(links) for site, links in state_dict.items()}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=4)
    except Exception as e:
        print(f"[{datetime.now()}] Errore durante il salvataggio del file di stato: {e}")

def send_email(new_links, site_name, site_url):
    """Invia un'email ai destinatari con la lista dei nuovi link trovati per un sito specifico."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"[{datetime.now()}] ATTENZIONE: Credenziali email non configurate. Salto l'invio dell'email.")
        return False

    subject = f"Aggiornamento {site_name}: Nuovi link trovati!"
    
    body_text = f"Sono stati trovati dei nuovi link sulla pagina di {site_name}: {site_url}\n\nNuovi link:\n"
    for link in new_links:
        body_text += f"- {link}\n"
        
    body_html = f"""\
    <html>
      <body>
        <h2>Aggiornamento: {site_name}</h2>
        <p>Sono stati aggiunti nuovi link sulla pagina: <a href="{site_url}">{site_url}</a></p>
        <p><strong>Nuovi link trovati:</strong></p>
        <ul>
    """
    for link in new_links:
        body_html += f'<li><a href="{link}">{link}</a></li>'
        
    body_html += """\
        </ul>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENT_EMAILS)

    part1 = MIMEText(body_text, "plain")
    part2 = MIMEText(body_html, "html")

    msg.attach(part1)
    msg.attach(part2)

    sender_clean = SENDER_EMAIL.strip()
    password_clean = SENDER_PASSWORD.strip()

    # Tentativo 1: Porta 587 con STARTTLS (più stabile sui runner cloud GitHub Actions)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_clean, password_clean)
            server.sendmail(sender_clean, RECIPIENT_EMAILS, msg.as_string())
        print(f"[{datetime.now()}] Email inviata con successo (porta 587 STARTTLS) per {site_name}!")
        return True
    except Exception as e_587:
        print(f"[{datetime.now()}] Invio su porta 587 fallito ({type(e_587).__name__}: {e_587}). Riprovo su porta 465 SSL...")
        traceback.print_exc()

    # Tentativo 2: Fallback su porta 465 con SMTP_SSL
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.ehlo()
            server.login(sender_clean, password_clean)
            server.sendmail(sender_clean, RECIPIENT_EMAILS, msg.as_string())
        print(f"[{datetime.now()}] Email inviata con successo (porta 465 SSL) per {site_name}!")
        return True
    except Exception as e_465:
        print(f"[{datetime.now()}] Errore durante l'invio dell'email ({type(e_465).__name__}): {e_465}")
        traceback.print_exc()
        return False

def main():
    print(f"[{datetime.now()}] Avvio del monitoraggio multiplo ({len(SITES_TO_MONITOR)} siti)...")
    
    known_state = load_known_links()
    state_changed = False
    email_failed = False
    
    try:
        for site in SITES_TO_MONITOR:
            site_name = site["name"]
            site_url = site["url"]
            print(f"[{datetime.now()}] ---> Controllo sito: {site_name}")
            
            current_links = get_links_from_page(site_url)
            if not current_links:
                print(f"[{datetime.now()}] Nessun link estratto da '{site_name}' (pagina vuota o irraggiungibile). Salto.")
                continue
            
            # Se il sito non è mai stato controllato (o aveva 0 link salvati per errore), inizializzalo
            if site_name not in known_state or len(known_state[site_name]) == 0:
                print(f"[{datetime.now()}] Primo avvio per '{site_name}'. Inizializzazione di {len(current_links)} link correnti...")
                known_state[site_name] = current_links
                state_changed = True
                continue
                
            known_links = known_state[site_name]
            
            # Trova i link nuovi
            new_links = current_links - known_links
            
            if new_links:
                print(f"[{datetime.now()}] Trovati {len(new_links)} NUOVI link in '{site_name}'!")
                for link in new_links:
                    print(f"  - {link}")
                
                # Invia email e aggiorna lo stato SOLO se l'email parte con successo
                if send_email(new_links, site_name, site_url):
                    known_state[site_name] = known_links.union(current_links)
                    state_changed = True
                else:
                    print(f"[{datetime.now()}] Non aggiorno i link noti per '{site_name}' così riproverò a inviare l'email al prossimo ciclo.")
                    email_failed = True
            else:
                print(f"[{datetime.now()}] Nessun nuovo link in '{site_name}'.")

        # Salva su file solo se c'è stata almeno una modifica in uno dei siti
        if state_changed:
            save_known_links(known_state)
            print(f"[{datetime.now()}] File JSON aggiornato con successo.")

        if email_failed:
            print(f"[{datetime.now()}] ATTENZIONE: Almeno un invio email è fallito.")
            exit(1)
            
    except Exception as e:
        print(f"[{datetime.now()}] Errore imprevisto nel main: {e}")
        exit(1)

if __name__ == "__main__":
    main()
