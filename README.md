# OutDoor Planner — EGGSolutions-MMQS
 
Progetto di laboratorio per il corso di **Modelli e Metodi per la Qualità del Software (MMQS)**, A.A. 2026/2027.
 
## Descrizione
 
OutDoor Planner è un'applicazione web per organizzare uscite all'aperto (escursioni, giri in bici, partite al parco). Un organizzatore pubblica l'uscita, gli altri utenti si iscrivono e tutti vedono le previsioni meteo per il giorno e il luogo dell'evento.
 
L'applicazione viene sviluppata con l'aiuto di un coding agent, poi analizzata con strumenti di analisi statica (SonarQube Cloud e Fortify), corretta e analizzata di nuovo per misurarne il miglioramento.
 
## Membri del gruppo
 
| Nome e cognome | Matricola | Username GitHub |
|---|---|---|
| Gabriele Contestabile | 827758 | [@GabryWasTaken](https://github.com/GabryWasTaken) |
 
## Proposta progettuale
 
La proposta è disponibile in [`idee/gabriele.md`](idee/gabriele.md).
 
## Stack
 
- Python, Flask
- SQLAlchemy + SQLite
- Flask-Login
## Dati e API esterne
 
- [Open-Meteo Forecast API](https://open-meteo.com/en/docs): previsioni meteo.
- [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api): ricerca dei luoghi.
Dati meteo forniti da [Open-Meteo.com](https://open-meteo.com/), sotto licenza [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
 
Tutti gli utenti e i contenuti presenti nell'applicazione sono **inventati**: nessun dato personale reale.
 
## Regole del repository
 
- Nessuna credenziale nel repository: password, token e chiavi vanno nel file `.env`, escluso dal `.gitignore`.
- Ogni modifica passa da un branch e una pull request verso `main`.
## Stato del lavoro
 
- [x] Organizzazione GitHub creata
- [x] Repository creato
- [x] Proposta progettuale pubblicata (PR #1)
- [ ] MVP dell'applicazione
- [ ] Prima scansione (SonarQube Cloud, Fortify)
- [ ] Correzioni
- [ ] Seconda scansione e confronto
- [ ] Presentazione finale
 
