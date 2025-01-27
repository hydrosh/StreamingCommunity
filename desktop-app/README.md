# StreamingCommunity Desktop App

Versione desktop dell'applicazione StreamingCommunity, sviluppata con Rust e Tauri.

## Caratteristiche

- Streaming di film e serie TV
- Download dei contenuti
- Gestione watchlist
- Ricerca avanzata
- Interfaccia nativa e performante
- Notifiche di sistema
- Gestione download con pause/resume
- Player video personalizzato con supporto sottotitoli

## Prerequisiti

1. **Rust e Cargo**
   ```bash
   # Windows
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   # Riavviare il terminale dopo l'installazione
   ```

2. **Node.js e npm**
   - Scaricare e installare da [nodejs.org](https://nodejs.org/)

3. **Dipendenze di sistema per Tauri**
   - Microsoft Visual Studio C++ Build Tools
   - WebView2

4. **MongoDB**
   - Installare MongoDB Community Edition
   - Assicurarsi che il servizio sia in esecuzione

## Struttura del Progetto

```
desktop-app/
├── src/               # Frontend (React)
├── src-tauri/        # Backend (Rust)
├── public/           # Asset statici
└── target/           # Build output
```

## Sviluppo

1. **Installare le dipendenze**
   ```bash
   # Frontend
   cd src
   npm install

   # Backend
   cd ../src-tauri
   cargo build
   ```

2. **Avviare in modalità sviluppo**
   ```bash
   cargo tauri dev
   ```

3. **Build per la produzione**
   ```bash
   cargo tauri build
   ```

## Configurazione

1. **MongoDB**
   - Modificare la stringa di connessione in `config.json`
   - Database di default: `streamingcommunity`

2. **Download**
   - I file scaricati vengono salvati in `~/Downloads/StreamingCommunity`
   - Configurabile in `config.json`

## Troubleshooting

### Errori comuni

1. **Errore WebView2**
   - Assicurarsi che Microsoft Edge WebView2 Runtime sia installato
   - Scaricare da: https://developer.microsoft.com/microsoft-edge/webview2/

2. **Errore Build Tools**
   - Installare Visual Studio Build Tools 2022
   - Selezionare "C++ build tools" durante l'installazione

3. **Errore MongoDB**
   - Verificare che il servizio MongoDB sia in esecuzione
   - Controllare la stringa di connessione in `config.json`

## Contribuire

1. Fork del repository
2. Creare un branch per la feature (`git checkout -b feature/nome-feature`)
3. Commit dei cambiamenti (`git commit -am 'Aggiunta nuova feature'`)
4. Push del branch (`git push origin feature/nome-feature`)
5. Aprire una Pull Request

## Licenza

MIT License - vedere il file LICENSE per i dettagli
