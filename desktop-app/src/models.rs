use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize)]
pub struct WatchlistItem {
    pub id: i32,
    pub title: String,
    pub slug: String,
    pub media_type: String,
    pub current_episode: Option<i32>,
    pub current_season: Option<i32>,
    pub last_watched: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateWatchlistItem {
    pub id: i32,
    pub current_episode: Option<i32>,
    pub current_season: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchResponse {
    pub id: i32,
    pub title: String,
    pub slug: String,
    pub media_type: String,
    pub year: Option<i32>,
    pub poster_path: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TitleInfo {
    pub id: i32,
    pub title: String,
    pub slug: String,
    pub media_type: String,
    pub year: Option<i32>,
    pub poster_path: Option<String>,
    pub overview: Option<String>,
    pub seasons: Option<Vec<Season>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Season {
    pub season_number: i32,
    pub episode_count: i32,
    pub episodes: Vec<Episode>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Episode {
    pub episode_number: i32,
    pub title: String,
    pub overview: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DownloadStatus {
    pub id: String,
    pub title: String,
    pub media_type: String,
    pub status: String,
    pub progress: f32,
    pub season: Option<i32>,
    pub episode: Option<i32>,
}
