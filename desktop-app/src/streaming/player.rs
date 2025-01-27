use anyhow::Result;
use tauri::Window;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct PlayerState {
    pub is_playing: bool,
    pub current_time: f64,
    pub duration: f64,
    pub volume: f64,
    pub is_muted: bool,
    pub subtitle_track: Option<String>,
}

pub struct VideoPlayer {
    window: Window,
    state: PlayerState,
}

impl VideoPlayer {
    pub fn new(window: Window) -> Self {
        Self {
            window,
            state: PlayerState {
                is_playing: false,
                current_time: 0.0,
                duration: 0.0,
                volume: 1.0,
                is_muted: false,
                subtitle_track: None,
            },
        }
    }

    pub fn play(&mut self) -> Result<()> {
        self.state.is_playing = true;
        self.emit_state()?;
        Ok(())
    }

    pub fn pause(&mut self) -> Result<()> {
        self.state.is_playing = false;
        self.emit_state()?;
        Ok(())
    }

    pub fn seek(&mut self, time: f64) -> Result<()> {
        self.state.current_time = time;
        self.emit_state()?;
        Ok(())
    }

    pub fn set_volume(&mut self, volume: f64) -> Result<()> {
        self.state.volume = volume;
        self.emit_state()?;
        Ok(())
    }

    pub fn toggle_mute(&mut self) -> Result<()> {
        self.state.is_muted = !self.state.is_muted;
        self.emit_state()?;
        Ok(())
    }

    pub fn set_subtitle_track(&mut self, language: Option<String>) -> Result<()> {
        self.state.subtitle_track = language;
        self.emit_state()?;
        Ok(())
    }

    fn emit_state(&self) -> Result<()> {
        self.window.emit("player-state", &self.state)?;
        Ok(())
    }
}
