use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use reqwest::Client;

#[derive(Debug, Serialize, Deserialize)]
pub struct SubtitleCue {
    pub start_time: f64,
    pub end_time: f64,
    pub text: String,
}

pub struct SubtitleManager {
    client: Client,
    cache_path: PathBuf,
}

impl SubtitleManager {
    pub fn new(cache_path: PathBuf) -> Self {
        Self {
            client: Client::new(),
            cache_path,
        }
    }

    pub async fn download_subtitles(&self, url: &str, language: &str) -> Result<PathBuf> {
        let response = self.client.get(url).send().await?;
        let content = response.text().await?;

        let filename = format!("subtitles_{}_{}.srt", 
            self.generate_subtitle_id(url), 
            language
        );
        let path = self.cache_path.join(filename);

        std::fs::write(&path, content)?;
        Ok(path)
    }

    pub fn parse_srt(&self, content: &str) -> Result<Vec<SubtitleCue>> {
        let mut cues = Vec::new();
        let mut lines = content.lines().peekable();

        while lines.peek().is_some() {
            // Skip cue number
            let _ = lines.next();

            // Parse timestamp line
            if let Some(timestamp_line) = lines.next() {
                let (start_time, end_time) = self.parse_timestamp_line(timestamp_line)?;

                // Parse text lines
                let mut text = String::new();
                while let Some(line) = lines.next() {
                    if line.is_empty() {
                        break;
                    }
                    if !text.is_empty() {
                        text.push('\n');
                    }
                    text.push_str(line);
                }

                cues.push(SubtitleCue {
                    start_time,
                    end_time,
                    text,
                });
            }
        }

        Ok(cues)
    }

    fn parse_timestamp_line(&self, line: &str) -> Result<(f64, f64)> {
        let parts: Vec<&str> = line.split(" --> ").collect();
        if parts.len() != 2 {
            anyhow::bail!("Invalid timestamp line format");
        }

        let start_time = self.parse_timestamp(parts[0])?;
        let end_time = self.parse_timestamp(parts[1])?;

        Ok((start_time, end_time))
    }

    fn parse_timestamp(&self, timestamp: &str) -> Result<f64> {
        let parts: Vec<&str> = timestamp.trim().split(':').collect();
        if parts.len() != 3 {
            anyhow::bail!("Invalid timestamp format");
        }

        let hours: f64 = parts[0].parse()?;
        let minutes: f64 = parts[1].parse()?;
        let seconds: f64 = parts[2].replace(',', ".").parse()?;

        Ok(hours * 3600.0 + minutes * 60.0 + seconds)
    }

    fn generate_subtitle_id(&self, url: &str) -> String {
        use std::hash::{Hash, Hasher};
        use std::collections::hash_map::DefaultHasher;

        let mut hasher = DefaultHasher::new();
        url.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }
}
