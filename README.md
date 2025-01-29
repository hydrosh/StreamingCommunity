Per testare

0. Installare nodejs "https://nodejs.org/en/download/package-manager"
1. Installare requirements "pip install -r "requirements.txt"
2. Inserire url per mongodb "https://www.mongodb.com/it-it"
3. Eseguire server.py con "python server.py"
4. Spostarsi su client\dashboard
5. Eseguire npm install, npm run build, npm install -g serve

## Dark Mode
La dark mode è stata implementata utilizzando il contesto del tema in React. Gli utenti possono passare tra la modalità chiara e quella scura tramite un interruttore nel menu delle impostazioni. Le classi CSS vengono applicate dinamicamente in base al tema selezionato.

## Bug Noti
- Watchlist reindirizza a 404.
- I download di serie TV (o episodi) non funzionano più; mancano controlli aggiuntivi e download dell'intera stagione.
- Messaggio con richiesta se scaricare le nuove stagioni quando si fa il check in watchlist.
- Coda di download con bottone "Aggiungi alla coda".
- Pulsante "Elimina" in Downloads non funziona.

## Non ci sono altre problematiche attualmente note.

Cosa da fare
- Migliorare controlli.
- Aggiungere bottone per scaricare una stagione intera.
- Migliore player in case watch con bottone.
...