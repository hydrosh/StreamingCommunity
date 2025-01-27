use anyhow::Result;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

mod player;
mod subtitles;

#[derive(Debug, Serialize, Deserialize)]
pub struct VideoSource {
    pub url: String,
    pub quality: String,
    pub subtitles: Option<Vec<SubtitleTrack>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SubtitleTrack {
    pub language: String,
    pub url: String,
}

pub struct StreamManager {
    client: Client,
    download_path: PathBuf,
}

impl StreamManager {
    pub fn new(download_path: PathBuf) -> Self {
        Self {
            client: Client::new(),
            download_path,
        }
    }

    pub async fn get_video_sources(&self, id: &str, media_type: &str) -> Result<Vec<VideoSource>> {
        // Implementa la logica per ottenere le fonti video dal server originale
        let sources = match media_type {
            "movie" => self.get_movie_sources(id).await?,
            "episode" => self.get_episode_sources(id).await?,
            _ => vec![],
        };
        Ok(sources)
    }

    async fn get_movie_sources(&self, id: &str) -> Result<Vec<VideoSource>> {
        // TODO: Implementa la logica per ottenere le fonti video per i film
        Ok(vec![])
    }

    async fn get_episode_sources(&self, id: &str) -> Result<Vec<VideoSource>> {
        // TODO: Implementa la logica per ottenere le fonti video per gli episodi
        Ok(vec![])
    }

    pub async fn get_subtitles(&self, video_id: &str) -> Result<Vec<SubtitleTrack>> {
        // TODO: Implementa la logica per ottenere i sottotitoli
        Ok(vec![])
    }
}
