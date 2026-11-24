# Idea: OutDoor Planner
 
## Tema
Applicazione web per organizzare uscite all'aperto (escursioni, giri in bici, partite al parco): un organizzatore pubblica l'uscita e gli altri utenti si iscrivono, vedendo le previsioni meteo per il giorno e il luogo dell'evento.
 
## Dati o API
- Open-Meteo Forecast API (https://open-meteo.com/en/docs) per le previsioni meteo del giorno dell'uscita. Gratuita per uso non commerciale, nessuna chiave, dati sotto licenza CC BY 4.0.
- Open-Meteo Geocoding API (https://open-meteo.com/en/docs/geocoding-api) per trasformare il nome del luogo in coordinate.
- Database relazionale proprio (SQLite) per utenti, uscite, iscrizioni e commenti. Solo dati inventati.
## Tre funzionalità minime
1. L'organizzatore crea, modifica e cancella le proprie uscite (titolo, descrizione, luogo, data, posti disponibili, traccia GPX opzionale).
2. Ogni uscita mostra le previsioni meteo per il suo giorno e luogo.
3. I partecipanti si iscrivono (fino ad esaurimento posti), cancellano l'iscrizione e lasciano commenti.
## Stack previsto
Python con Flask, SQLAlchemy, Flask-Login, SQLite.
 
## Perché mi piace
È un'app semplice da spiegare ma con abbastanza parti interessanti per l'analisi statica: login con due ruoli, permessi su chi può modificare cosa, testo libero scritto dagli utenti, upload di file GPX (XML) e chiamate a un'API esterna.
 
