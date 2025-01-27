use axum::{
    extract::{State, Json},
};
use crate::{
    models::{WatchlistItem, UpdateWatchlistItem},
    AppState,
    db::DbClient,
};

pub async fn get_watchlist(
    State(state): State<AppState>,
) -> Json<Vec<WatchlistItem>> {
    let db_client = DbClient::new(state.db);
    match db_client.get_watchlist().await {
        Ok(items) => Json(items),
        Err(_) => Json(Vec::new()),
    }
}

pub async fn add_to_watchlist(
    State(state): State<AppState>,
    Json(item): Json<WatchlistItem>,
) -> Json<bool> {
    let db_client = DbClient::new(state.db);
    match db_client.add_to_watchlist(item).await {
        Ok(_) => Json(true),
        Err(_) => Json(false),
    }
}

pub async fn update_watchlist(
    State(state): State<AppState>,
    Json(update): Json<UpdateWatchlistItem>,
) -> Json<bool> {
    let db_client = DbClient::new(state.db);
    match db_client.update_watchlist(update).await {
        Ok(_) => Json(true),
        Err(_) => Json(false),
    }
}

pub async fn remove_from_watchlist(
    State(state): State<AppState>,
    Json(item): Json<WatchlistItem>,
) -> Json<bool> {
    let db_client = DbClient::new(state.db);
    match db_client.remove_from_watchlist(item.id).await {
        Ok(_) => Json(true),
        Err(_) => Json(false),
    }
}
