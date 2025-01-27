use tauri::{Window, Manager};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Notification {
    pub title: String,
    pub body: String,
    pub icon: Option<String>,
}

pub struct NotificationManager {
    window: Window,
}

impl NotificationManager {
    pub fn new(window: Window) -> Self {
        Self { window }
    }

    pub fn send_notification(&self, notification: Notification) {
        #[cfg(target_os = "windows")]
        {
            use windows_sys::Windows::UI::Notifications::*;
            use windows_sys::Windows::Data::Xml::Dom::*;
            
            // Implementazione specifica per Windows
            let toast_xml = format!(
                r#"<toast>
                    <visual>
                        <binding template="ToastGeneric">
                            <text>{}</text>
                            <text>{}</text>
                        </binding>
                    </visual>
                </toast>"#,
                notification.title,
                notification.body
            );

            // Emetti anche un evento all'interfaccia utente
            let _ = self.window.emit("notification", &notification);
        }

        #[cfg(target_os = "macos")]
        {
            // Implementazione specifica per macOS usando NSUserNotification
            let _ = self.window.emit("notification", &notification);
        }

        #[cfg(target_os = "linux")]
        {
            // Implementazione specifica per Linux usando libnotify
            let _ = self.window.emit("notification", &notification);
        }
    }

    pub fn notify_download_complete(&self, title: &str) {
        self.send_notification(Notification {
            title: "Download Completato".to_string(),
            body: format!("{} è stato scaricato con successo!", title),
            icon: None,
        });
    }

    pub fn notify_download_error(&self, title: &str, error: &str) {
        self.send_notification(Notification {
            title: "Errore Download".to_string(),
            body: format!("Errore durante il download di {}: {}", title, error),
            icon: None,
        });
    }

    pub fn notify_new_episode(&self, series_title: &str, season: i32, episode: i32) {
        self.send_notification(Notification {
            title: "Nuovo Episodio Disponibile".to_string(),
            body: format!("S{}E{} di {} è ora disponibile!", season, episode, series_title),
            icon: None,
        });
    }
}
