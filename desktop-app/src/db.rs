use mongodb::{
    bson::{doc, Document},
    Collection, Database,
};
use crate::models::{WatchlistItem, UpdateWatchlistItem};
use anyhow::Result;

pub struct DbClient {
    db: Database,
}

impl DbClient {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn add_to_watchlist(&self, item: WatchlistItem) -> Result<()> {
        let collection = self.db.collection::<WatchlistItem>("watchlist");
        
        // Verifica se l'elemento esiste già
        let filter = doc! { "id": item.id };
        if collection.find_one(filter.clone(), None).await?.is_none() {
            collection.insert_one(item, None).await?;
        }
        
        Ok(())
    }

    pub async fn update_watchlist(&self, update: UpdateWatchlistItem) -> Result<()> {
        let collection = self.db.collection::<WatchlistItem>("watchlist");
        
        let filter = doc! { "id": update.id };
        let update_doc = doc! {
            "$set": {
                "current_episode": update.current_episode,
                "current_season": update.current_season,
                "last_watched": chrono::Utc::now(),
            }
        };
        
        collection.update_one(filter, update_doc, None).await?;
        Ok(())
    }

    pub async fn remove_from_watchlist(&self, id: i32) -> Result<()> {
        let collection = self.db.collection::<WatchlistItem>("watchlist");
        collection.delete_one(doc! { "id": id }, None).await?;
        Ok(())
    }

    pub async fn get_watchlist(&self) -> Result<Vec<WatchlistItem>> {
        let collection = self.db.collection::<WatchlistItem>("watchlist");
        let mut cursor = collection.find(None, None).await?;
        
        let mut items = Vec::new();
        while cursor.advance().await? {
            items.push(cursor.deserialize_current()?);
        }
        
        Ok(items)
    }

    pub async fn get_downloads(&self) -> Result<Vec<Document>> {
        let collection = self.db.collection::<Document>("downloads");
        let mut cursor = collection.find(None, None).await?;
        
        let mut items = Vec::new();
        while cursor.advance().await? {
            items.push(cursor.deserialize_current()?);
        }
        
        Ok(items)
    }
}
