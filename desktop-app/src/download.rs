use std::collections::HashMap;
use std::path::PathBuf;
use tokio::sync::{mpsc, Mutex};
use serde::{Deserialize, Serialize};
use anyhow::Result;
use reqwest::Client;
use futures::StreamExt;
use std::sync::Arc;
use crate::notifications::NotificationManager;

#[derive(Debug, Clone, Serialize)]
pub struct DownloadInfo {
    pub status: String,
    pub progress: f32,
    pub title: String,
    pub media_type: String,
    pub season: Option<i32>,
    pub episode: Option<i32>,
    pub path: Option<PathBuf>,
    pub error: Option<String>,
}

pub struct DownloadManager {
    downloads: HashMap<String, DownloadInfo>,
    max_concurrent: usize,
    client: Client,
    download_path: PathBuf,
    notification_manager: Arc<NotificationManager>,
}

impl DownloadManager {
    pub fn new(download_path: PathBuf, notification_manager: Arc<NotificationManager>) -> Self {
        Self {
            downloads: HashMap::new(),
            max_concurrent: 1,
            client: Client::new(),
            download_path,
            notification_manager,
        }
    }

    pub async fn start_download(
        &mut self,
        id: String,
        title: String,
        media_type: String,
        season: Option<i32>,
        episode: Option<i32>,
        url: String,
    ) -> Result<()> {
        let download = DownloadInfo {
            status: "queued".to_string(),
            progress: 0.0,
            title: title.clone(),
            media_type,
            season,
            episode,
            path: None,
            error: None,
        };

        self.downloads.insert(id.clone(), download);
        self.process_queue().await?;
        Ok(())
    }

    async fn process_queue(&mut self) -> Result<()> {
        let active_downloads = self.downloads
            .iter()
            .filter(|(_, info)| info.status == "downloading")
            .count();

        if active_downloads >= self.max_concurrent {
            return Ok(());
        }

        // Trova il prossimo download in coda
        if let Some((id, _)) = self.downloads
            .iter()
            .find(|(_, info)| info.status == "queued")
            .map(|(id, _)| (id.clone(), ())) {
            
            if let Some(download) = self.downloads.get_mut(&id) {
                download.status = "downloading".to_string();
                
                // Crea il percorso del file
                let filename = match (download.season, download.episode) {
                    (Some(s), Some(e)) => format!("{}_S{:02}E{:02}.mp4", download.title, s, e),
                    _ => format!("{}.mp4", download.title),
                };
                let file_path = self.download_path.join(&filename);
                download.path = Some(file_path.clone());

                // Clona i dati necessari per il task di download
                let client = self.client.clone();
                let id_clone = id.clone();
                let title_clone = download.title.clone();
                let notification_manager = self.notification_manager.clone();
                let url_clone = url.clone();
                
                // Avvia il download in background
                tokio::spawn(async move {
                    match Self::download_file(&client, &url_clone, &file_path).await {
                        Ok(_) => {
                            notification_manager.notify_download_complete(&title_clone);
                            if let Some(download) = self.downloads.get_mut(&id_clone) {
                                download.status = "completed".to_string();
                                download.progress = 100.0;
                            }
                        }
                        Err(e) => {
                            notification_manager.notify_download_error(&title_clone, &e.to_string());
                            if let Some(download) = self.downloads.get_mut(&id_clone) {
                                download.status = "error".to_string();
                                download.error = Some(e.to_string());
                            }
                        }
                    }
                });
            }
        }

        Ok(())
    }

    async fn download_file(client: &Client, url: &str, path: &PathBuf) -> Result<()> {
        let response = client.get(url).send().await?;
        let total_size = response.content_length().unwrap_or(0);
        
        let mut file = tokio::fs::File::create(path).await?;
        let mut downloaded: u64 = 0;
        let mut stream = response.bytes_stream();

        while let Some(item) = stream.next().await {
            let chunk = item?;
            tokio::io::AsyncWriteExt::write_all(&mut file, &chunk).await?;
            downloaded += chunk.len() as u64;

            if total_size > 0 {
                let progress = (downloaded as f32 / total_size as f32) * 100.0;
                // Aggiorna il progresso
                // TODO: implementare un sistema di callback per aggiornare l'UI
            }
        }

        Ok(())
    }

    pub fn get_status(&self) -> Vec<(String, &DownloadInfo)> {
        self.downloads
            .iter()
            .map(|(id, info)| (id.clone(), info))
            .collect()
    }

    pub fn set_max_concurrent(&mut self, max: usize) {
        self.max_concurrent = max;
    }

    pub fn cancel_download(&mut self, id: &str) -> Result<()> {
        if let Some(download) = self.downloads.get_mut(id) {
            download.status = "cancelled".to_string();
            // TODO: implementare la cancellazione effettiva del download
        }
        Ok(())
    }

    pub fn retry_download(&mut self, id: &str) -> Result<()> {
        if let Some(download) = self.downloads.get_mut(id) {
            download.status = "queued".to_string();
            download.progress = 0.0;
            download.error = None;
        }
        Ok(())
    }
}
