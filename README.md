# 🔔 Controllo Concorsi — Monitoraggio Automatico Bandi e Comunicazioni

**Controllo Concorsi** è un sistema di monitoraggio automatico in Python che controlla periodicamente gli **URL specificati nel file dedicato (`monitor.py`)** — come le pagine web dei concorsi pubblici (es. portale **InPA**, Camere di Commercio, ASL, Comuni, Ministeri) — e **invia una notifica via email** non appena vengono pubblicati nuovi allegati, PDF, graduatorie o comunicazioni.

Grazie all'integrazione con **GitHub Actions**, lo script gira gratuitamente in cloud (ogni 5 minuti) **senza bisogno di tenere il proprio computer acceso**.

---

## ⚙️ Come funziona

1. **Lista degli URL da monitorare (`monitor.py`)**: Il sistema monitora tutti e soli gli URL che vengono inseriti dall'utente nella sezione `SITES_TO_MONITOR` all'interno del file dedicato [`monitor.py`](./monitor.py). Per ogni URL inserito, lo script scarica il contenuto principale (`<main>`) della pagina ed estrae tutti i link a documenti, allegati e comunicazioni.
2. **Memoria di stato (`known_links.json`)**:
   * **Al primo avvio** per un nuovo sito, lo script salva tutti i link già presenti sulla pagina dentro `known_links.json` senza inviare email (così da non intasare la casella con vecchi allegati).
   * **Ai controlli successivi**, confronta i link attuali della pagina con quelli salvati in `known_links.json`.
3. **Notifica Email + Salvataggio automatico**:
   * Se rileva uno o più link nuovi, invia un'email HTML formattata con i link diretti ai nuovi documenti a tutti i destinatari configurati.
   * Solo dopo che l'email è stata inviata con successo, aggiorna `known_links.json` ed esegue automaticamente un `git commit` e `git push` sul repository.

---

## 🚀 Guida passo-passo per avviarlo in autonomia (Cloud con GitHub Actions)

Non serve installare nulla sul tuo PC: puoi far girare tutto gratuitamente sui server di GitHub in 5 minuti.

### 1. Fai un Fork (o copia) di questo repository
Clicca sul pulsante **Fork** in alto a destra su questa pagina GitHub per creare una copia del progetto sul tuo account personale.
*(Consiglio: se vuoi mantenere privati gli indirizzi email dei destinatari o i concorsi che segui, puoi duplicare il codice in un tuo repository Privato).*

---

### 2. Genera una "Password per le app" su Gmail
Per permettere allo script di inviare le email tramite il tuo account Gmail senza esporre la tua password principale, Google richiede una **Password per le app** (di 16 lettere):

1. Vai nelle impostazioni del tuo Account Google alla sezione **[Sicurezza](https://myaccount.google.com/security)**.
2. Assicurati di aver attivato la **Verifica in due passaggi** (è obbligatoria per poter creare password per le app).
3. Vai direttamente alla pagina **[Password per le app](https://myaccount.google.com/apppasswords)** (oppure cercala nella barra di ricerca delle impostazioni Google).
4. Inserisci un nome identificativo (es. `Controllo Concorsi`) e clicca su **Crea**.
5. Google ti mostrerà un codice di **16 caratteri** (es. `abcd efgh ijkl mnop`). **Copialo**, ti servirà al punto successivo.

---

### 3. Configura i GitHub Secrets (Email e Password del mittente)
Non inserire **mai** la tua password dentro il file `monitor.py`! Usa la cassaforte crittografata di GitHub:

1. Nel **tuo** repository su GitHub, clicca sulla scheda **Settings** (in alto).
2. Nel menu a sinistra, espandi **Secrets and variables** e clicca su **Actions**.
3. Clicca sul pulsante verde **New repository secret** e aggiungi questi due segreti:
   * **Primo Secret:**
     * **Name:** `SENDER_EMAIL`
     * **Secret:** il tuo indirizzo Gmail completo (es. `mario.rossi@gmail.com`)
   * **Secondo Secret:**
     * **Name:** `SENDER_PASSWORD`
     * **Secret:** la Password per le app di 16 caratteri generata al Passo 2 (es. `abcdefghijklmnop`)

---

### 4. Personalizza i concorsi da seguire e i destinatari (`monitor.py`)
Apri il file [`monitor.py`](./monitor.py) e modifica:

1. **Lista dei siti (`SITES_TO_MONITOR`)**:
   Inserisci il nome e l'URL dei concorsi che vuoi tenere d'occhio:
   ```python
   SITES_TO_MONITOR = [
       {
           "name": "InPA-Diverse Amministrazioni-Assistenti",
           "url": "https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=2479a6e7761b48f2be7fa54b3699cb98"
       },
       {
           "name": "InPA-Diverse Amministrazioni-Funzionari",
           "url": "https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=054e2ea57835433bad131fcae791b810"
       }
   ]
   ```
   > **💡 Nota per i bandi InPA:** Quando copi il link di un bando da InPA, usa sempre l'URL del portale pubblico nel formato:
   > `https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=ID_DEL_CONCORSO`
   > (Evita i link `https://portale.inpa.gov.it/ui/public-area/concoursedetail/...` perché vengono renderizzati via JavaScript).

2. **Destinatari delle notifiche (`RECIPIENT_EMAILS`)**:
   Sostituisci gli indirizzi di esempio con una o più email reali che dovranno ricevere gli avvisi:
   ```python
   RECIPIENT_EMAILS = ["tua.email@gmail.com", "collega@gmail.com"]
   ```

---

### 5. Attiva il controllo automatico ogni 5 minuti
Per evitare esecuzioni a vuoto prima della configurazione, il timer automatico è commentato di default. Per attivarlo:

1. Apri il file [`.github/workflows/monitor.yml`](./.github/workflows/monitor.yml).
2. Rimuovi il simbolo `#` davanti a `schedule:` e `- cron: '*/5 * * * *'`:
   ```yaml
   on:
     schedule:
       - cron: '*/5 * * * *'
     workflow_dispatch:
   ```
3. Salva (**Commit changes**).
4. Vai nella scheda **Actions** del tuo repository:
   * Se hai fatto un Fork, clicca sul pulsante verde **"I understand my workflows, go ahead and enable them"**.
   * Clicca su **Web Link Monitor** a sinistra e poi su **Run workflow** a destra per lanciare subito il primo controllo manuale!

---

## 🧪 Come testare se l'invio dell'email funziona

1. Al **primo avvio**, lo script popolerà il file `known_links.json` con tutti i link attuali dei bandi configurati (senza inviare email).
2. Per verificare che l'email ti arrivi correttamente:
   * Apri il file `known_links.json` su GitHub e clicca sulla matita (**Edit**).
   * Cancella **un solo link** dalla lista di uno dei concorsi e salva (**Commit changes**).
   * Torna nella scheda **Actions** → **Web Link Monitor** → **Run workflow**.
3. Lo script rileverà quel link come "nuovo", ti invierà subito l'email di notifica e aggiornerà nuovamente `known_links.json`!

---

## 💻 Esecuzione in locale (Opzionale)

Se preferisci testare o eseguire lo script sul tuo PC:

```bash
# 1. Installa le dipendenze (Python 3.9+)
pip install -r requirements.txt

# 2. Imposta le variabili d'ambiente (esempio su Windows PowerShell)
$env:SENDER_EMAIL="tua.email@gmail.com"
$env:SENDER_PASSWORD="tua_password_per_le_app"

# 3. Avvia lo script
python monitor.py
```
