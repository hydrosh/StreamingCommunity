use std::sync::Arc;
use axum::{
    routing::{get, post},
    Router,
    Json,
    extract::Query,
};
use mongodb::{Client, Database};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tokio::sync::Mutex;

mod api;
mod models;
mod db;
mod download;

use models::{WatchlistItem, UpdateWatchlistItem, SearchResponse, TitleInfo};
use download::DownloadManager;

#[derive(Clone)]
pub struct AppState {
    db: Database,
    download_manager: Arc<Mutex<DownloadManager>>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Inizializza il logger
    env_logger::init();

    // Connessione MongoDB
    let client = Client::with_uri_str("mongodb://localhost:27017").await?;
    let db = client.database("streamingcommunity");

    // Inizializza il download manager
    let download_manager = Arc::new(Mutex::new(DownloadManager::new()));

    // Stato condiviso dell'applicazione
    let state = AppState {
        db,
        download_manager,
    };

    // Crea il router con CORS abilitato
    let app = Router::new()
        .route("/api/search", get(api::search::search_titles))
        .route("/api/title", get(api::titles::get_title_info))
        .route("/api/season", get(api::titles::get_season_info))
        .route("/api/watchlist", get(api::watchlist::get_watchlist)
            .post(api::watchlist::add_to_watchlist)
            .delete(api::watchlist::remove_from_watchlist))
        .route("/api/watchlist/update", post(api::watchlist::update_watchlist))
        .route("/api/download/movie", post(api::download::download_movie))
        .route("/api/download/episode", post(api::download::download_episode))
        .route("/api/download/status", get(api::download::get_download_status))
        .layer(CorsLayer::permissive())
        .with_state(state);

    // Avvia il server
    println!("Server in ascolto su http://localhost:3000");
    axum::Server::bind(&"127.0.0.1:3000".parse()?)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}
