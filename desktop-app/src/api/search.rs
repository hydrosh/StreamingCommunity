use axum::{
    extract::{Query, State},
    Json,
};
use serde::Deserialize;
use crate::{models::SearchResponse, AppState};

#[derive(Deserialize)]
pub struct SearchQuery {
    q: String,
}

pub async fn search_titles(
    State(state): State<AppState>,
    Query(query): Query<SearchQuery>,
) -> Json<Vec<SearchResponse>> {
    // Implementa la logica di ricerca qui
    // Per ora restituisce un vettore vuoto
    Json(Vec::new())
}
