use axum::{
    extract::{State, Json},
};
use serde::Deserialize;
use crate::AppState;

#[derive(Deserialize)]
pub struct MovieDownloadRequest {
    id: String,
    slug: String,
}

#[derive(Deserialize)]
pub struct EpisodeDownloadRequest {
    title_id: i32,
    slug: String,
    season: i32,
    episode: i32,
}

pub async fn download_movie(
    State(state): State<AppState>,
    Json(request): Json<MovieDownloadRequest>,
) -> Json<bool> {
    let mut download_manager = state.download_manager.lock().await;
    match download_manager.start_download(
        request.id.clone(),
        request.slug.clone(),
        "movie".to_string(),
        None,
        None,
    ).await {
        Ok(_) => Json(true),
        Err(_) => Json(false),
    }
}

pub async fn download_episode(
    State(state): State<AppState>,
    Json(request): Json<EpisodeDownloadRequest>,
) -> Json<bool> {
    let mut download_manager = state.download_manager.lock().await;
    match download_manager.start_download(
        request.title_id.to_string(),
        request.slug,
        "episode".to_string(),
        Some(request.season),
        Some(request.episode),
    ).await {
        Ok(_) => Json(true),
        Err(_) => Json(false),
    }
}

pub async fn get_download_status(
    State(state): State<AppState>,
) -> Json<Vec<(String, String, f32)>> {
    let download_manager = state.download_manager.lock().await;
    let status = download_manager.get_status();
    
    let formatted_status: Vec<(String, String, f32)> = status
        .iter()
        .map(|(id, info)| (
            id.clone(),
            info.status.clone(),
            info.progress,
        ))
        .collect();
    
    Json(formatted_status)
}
