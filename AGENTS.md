# Outdoor Planner (Flask)

App web per organizzare uscite all'aperto, con iscrizioni, commenti e previsioni meteo. Progetto del laboratorio MMQS: il codice verrà analizzato con SonarQube Cloud e Fortify.

## Da sapere
- Meteo e ricerca luoghi solo con Open-Meteo (forecast e geocoding API): niente chiave. Non usare Nominatim.
- Open-Meteo dà previsioni solo fino a 16 giorni: oltre, l'app mostra "previsioni non ancora disponibili".
- Salvare in cache le risposte meteo (qualche ora) invece di chiamare l'API a ogni pagina.
- Attribuzione obbligatoria nel footer: "Dati meteo: Open-Meteo.com (CC BY 4.0)".
- Ruoli: `organizer` (crea e gestisce le proprie uscite) e `participant` (si iscrive e commenta).
- Dati di prova solo inventati, creati da un comando di seed. Mai dati personali reali.

## Piani
- Piani brevissimi, anche a scapito della grammatica.
- In fondo, l'elenco delle domande ancora aperte.

## Divieti
- Mai committare `.env`, credenziali o il database: nel repository solo `.env.example` senza valori reali.
- Mai scrivere segreti nei comandi: usare variabili d'ambiente.
- Non aggiungere dipendenze senza verificare che il pacchetto esista su PyPI e sia mantenuto.
- Non sopprimere avvisi di linter o analizzatori (NOSONAR, noqa, nosec): correggere la causa.
- Mai `git push --force`, `git reset --hard` o commit diretti su `main`.
