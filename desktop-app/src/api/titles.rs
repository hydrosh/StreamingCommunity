use axum::{
    extract::{Query, State},
    Json,
};
use serde::Deserialize;
use crate::{models::{TitleInfo, Season}, AppState};

#[derive(Deserialize)]
pub struct TitleQuery {
    id: Option<String>,
    url: Option<String>,
    #[serde(rename = "type")]
    media_type: Option<String>,
}

#[derive(Deserialize)]
pub struct SeasonQuery {
    url: Option<String>,
    n: Option<String>,
}

pub async fn get_title_info(
    State(state): State<AppState>,
    Query(query): Query<TitleQuery>,
) -> Json<TitleInfo> {
    // Implementa la logica per ottenere le informazioni sul titolo
    // Per ora restituisce un oggetto vuoto
    Json(TitleInfo {
        id: 0,
        title: String::new(),
        slug: String::new(),
        media_type: String::new(),
        year: None,
        poster_path: None,
        overview: None,
        seasons: None,
    })
}

pub async fn get_season_info(
    State(state): State<AppState>,
    Query(query): Query<SeasonQuery>,
) -> Json<Season> {
    // Implementa la logica per ottenere le informazioni sulla stagione
    // Per ora restituisce un oggetto vuoto
    Json(Season {
        season_number: 0,
        episode_count: 0,
        episodes: Vec::new(),
    })
}
