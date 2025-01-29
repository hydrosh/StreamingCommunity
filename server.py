# 13.12.24

import os
import logging
#logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
import datetime
from urllib.parse import urlparse, unquote
from typing import Optional
import threading
import time

# External
import uvicorn
from rich.console import Console
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Util
from StreamingCommunity.Util.os import os_summary

console = Console()

# Initialize MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['streamingcommunity']
    downloads_collection = db['downloads']
    watchlist_collection = db['watchlist']
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    raise

# Initialize FastAPI
app = FastAPI()

# Util
from StreamingCommunity.Util.logger import Logger
Logger()  # Initialize logging configuration
from StreamingCommunity.Util._jsonConfig import config_manager
from server_type import WatchlistItem, UpdateWatchlistItem
from server_util import updateUrl

# Internal
from StreamingCommunity.Api.Template.Class.SearchType import MediaItem
from StreamingCommunity.Api.Site.streamingcommunity.api import get_version_and_domain, search_titles, get_infoSelectTitle, get_infoSelectSeason
from StreamingCommunity.Api.Site.streamingcommunity.film import download_film
from StreamingCommunity.Api.Site.streamingcommunity.series import download_video
from StreamingCommunity.Api.Site.streamingcommunity.util.ScrapeSerie import ScrapeSerie

# Player
from StreamingCommunity.Api.Player.vixcloud import VideoSource

# Variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Download configuration
MAX_CONCURRENT_DOWNLOADS = 1  # Default to 1 concurrent download
active_downloads = set()  # Set to track active downloads
download_queue_lock = threading.Lock()
current_download_progress = {"id": None, "progress": 0}  # Track current download progress

# Site variable
version, domain = get_version_and_domain()
season_name = None
scrape_serie = ScrapeSerie("streamingcommunity")
video_source = VideoSource("streamingcommunity", True)

DOWNLOAD_DIRECTORY = os.getcwd()

# Mongo variable
# client = MongoClient(config_manager.get("EXTRA", "mongodb"))
# db = client[config_manager.get("EXTRA", "database")]
# watchlist_collection = db['watchlist']
# downloads_collection = db['downloads']

def update_download_progress(download_id, progress, status=None):
    """Update the progress of a download in the database"""
    try:
        downloads_collection.update_one(
            {"_id": download_id},
            {"$set": {"progress": progress}}
        )
        if status:
            downloads_collection.update_one(
                {"_id": download_id},
                {"$set": {"status": status}}
            )
            if status == 'completed':
                downloads_collection.update_one(
                    {"_id": download_id},
                    {"$set": {
                        "status": 'completed',
                        "progress": 100,
                        "completed_at": datetime.datetime.now(datetime.timezone.utc)
                    }}
                )
                logging.info(f"Updated download status to completed for ID: {download_id}")
        logging.info(f"Updated progress for download {download_id}: {progress}%")
    except Exception as e:
        logging.error(f"Error updating progress for download {download_id}: {str(e)}")

def process_download_queue():
    while True:
        with download_queue_lock:
            # Check if we can start new downloads
            if len(active_downloads) < MAX_CONCURRENT_DOWNLOADS:
                # Get next queued item
                next_download = downloads_collection.find_one(
                    {"status": "queued"}, 
                    sort=[("timestamp", 1)]
                )
                
                if next_download:
                    download_id = str(next_download["_id"])
                    if download_id not in active_downloads:
                        active_downloads.add(download_id)
                        logging.info(f"Starting download of {next_download['type']}: {next_download['slug']}")
                        downloads_collection.update_one(
                            {"_id": next_download["_id"]},
                            {"$set": {"status": "downloading", "progress": 0}}
                        )
                        
                        try:
                            def progress_callback(progress, status=None):
                                update_download_progress(next_download["_id"], progress, status)
                            
                            if next_download["type"] == "movie":
                                logging.info(f"Downloading movie: {next_download['slug']}")
                                # Get the relative path where the file will be saved
                                rel_movie_path = "/".join([
                                    "streamingcommunity",
                                    config_manager.get("DEFAULT", "movie_folder_name"),
                                    next_download['slug'],
                                    f"{next_download['slug']}.mp4"
                                ])
                                # Get the full path for actual file operations
                                full_movie_path = os.path.join(
                                    DOWNLOAD_DIRECTORY,
                                    config_manager.get("DEFAULT", "root_path"),
                                    *rel_movie_path.split("/")
                                )
                                os.makedirs(os.path.dirname(full_movie_path), exist_ok=True)
                                
                                download_film(
                                    id=next_download["id"],
                                    slug=next_download["slug"],
                                    progress_callback=progress_callback
                                )
                                
                                # Update relative path in database when download is complete
                                downloads_collection.update_one(
                                    {"_id": next_download["_id"]},
                                    {"$set": {
                                        "status": "completed",
                                        "progress": 100,
                                        "path": rel_movie_path
                                    }}
                                )
                                
                            elif next_download["type"] == "episode":
                                logging.info(f"Downloading episode S{next_download['season']}E{next_download['episode']} of {next_download['slug']}")
                                # Get the relative path where the file will be saved
                                rel_episode_path = "/".join([
                                    "streamingcommunity",
                                    config_manager.get("DEFAULT", "serie_folder_name"),
                                    next_download['slug'],
                                    f"S{next_download['season']}E{next_download['episode']}.mp4"
                                ])
                                # Get the full path for actual file operations
                                full_episode_path = os.path.join(
                                    DOWNLOAD_DIRECTORY,
                                    config_manager.get("DEFAULT", "root_path"),
                                    *rel_episode_path.split("/")
                                )
                                os.makedirs(os.path.dirname(full_episode_path), exist_ok=True)
                                
                                download_video(
                                    next_download["season"],
                                    next_download["episode"],
                                    next_download["id"],
                                    next_download["slug"],
                                    progress_callback=progress_callback
                                )
                                
                                # Update relative path in database when download is complete
                                downloads_collection.update_one(
                                    {"_id": next_download["_id"]},
                                    {"$set": {
                                        "status": "completed",
                                        "progress": 100,
                                        "path": rel_episode_path
                                    }}
                                )
                                
                        except Exception as e:
                            logging.error(f"Download failed: {str(e)}")
                            downloads_collection.update_one(
                                {"_id": next_download["_id"]},
                                {"$set": {
                                    "status": "failed",
                                    "error": str(e),
                                    "progress": 0
                                }}
                            )
                        finally:
                            active_downloads.remove(download_id)
                            
        time.sleep(1)  # Avoid busy waiting

# Start download queue processor in background
download_queue_thread = threading.Thread(target=process_download_queue, daemon=False)
download_queue_thread.start()
logging.info(f"Download queue processor started (max concurrent downloads: {MAX_CONCURRENT_DOWNLOADS})")

# ---------- SITE API ------------
@app.get("/", summary="Health Check")
async def index():
    logging.info("Health check endpoint accessed")
    return "Server is operational"

@app.get("/api/search")
async def get_list_search(q: Optional[str] = Query(None)):
    if not q:
        logging.warning("Search request without query parameter")
        raise HTTPException(status_code=400, detail="Missing query parameter")
    try:
        result = search_titles(q, domain)
        logging.info(f"Search performed for query: {q}")
        return result
    except Exception as e:
        logging.error(f"Error in search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/getInfo")
async def get_info_title(
    url: Optional[str] = Query(None),
    id: Optional[str] = Query(None),
    type: Optional[str] = Query(None)
):
    try:
        # Se abbiamo l'URL, assicuriamoci che sia completo
        if url:
            if not url.startswith('http'):
                url = f"https://streamingcommunity.{domain}/titles/{url}"
            result = get_infoSelectTitle(url, domain, version)
        # Altrimenti, se abbiamo ID e type, costruiamo l'URL
        elif id and type:
            # Prima cerca il titolo per ottenere lo slug
            search_results = search_titles(f"id:{id}", domain)
            title = next((t for t in search_results if str(t['id']) == str(id)), None)
            
            if not title:
                logging.warning(f"Title with ID {id} not found in search results")
                raise HTTPException(status_code=404, detail="Title not found")
            
            # Costruisci l'URL con lo slug
            url = f"https://streamingcommunity.{domain}/titles/{id}-{title['slug']}"
            logging.info(f"Constructed URL: {url}")
            result = get_infoSelectTitle(url, domain, version)
        else:
            logging.warning("GetInfo request with invalid parameters")
            raise HTTPException(status_code=400, detail="Missing required parameters")

        if not result:
            raise HTTPException(status_code=404, detail="Title not found")

        if result.get('type') == "tv":
            global season_name, scrape_serie, video_source

            season_name = result.get('slug')

            scrape_serie.setup(
                version=version, 
                media_id=int(result.get('id')), 
                series_name=result.get('slug')
            )

            video_source.setup(result.get('id'))

            logging.info(f"TV series info retrieved: {season_name}")

        return result
    
    except Exception as e:
        logging.error(f"Error retrieving title info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/getInfoSeason")
async def get_info_season(url: Optional[str] = Query(None), n: Optional[str] = Query(None)):
    if not url or not n:
        logging.warning("GetInfoSeason request with missing parameters")
        raise HTTPException(status_code=400, detail="Missing URL or season number")
    
    try:
        result = get_infoSelectSeason(url, n, domain, version)
        logging.info(f"Season info retrieved for season {n}")
        return result
    
    except Exception as e:
        logging.error(f"Error retrieving season info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve season information")

@app.get("/api/getdomain")
async def get_domain():
    try:
        global version, domain
        version, domain = get_version_and_domain()
        logging.info(f"Domain retrieved: {domain}, Version: {version}")

        return {"domain": domain, "version": version}
    
    except Exception as e:
        logging.error(f"Error retrieving domain: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve domain information")

# ---------- DOWNLOAD API ------------
@app.get("/api/download/film")
async def call_download_film(id: Optional[str] = Query(None), slug: Optional[str] = Query(None)):
    if not id or not slug:
        logging.warning("Download film request with missing parameters")
        raise HTTPException(status_code=400, detail="Missing film ID or slug")
    
    try:
        # Check if already in downloads
        existing_download = downloads_collection.find_one({
            "type": "movie",
            "id": id,
            "status": {"$in": ["queued", "downloading", "completed"]}
        })
        
        if existing_download:
            status = existing_download["status"]
            if status == "completed":
                path = existing_download.get("path")
                if path:
                    return {"status": "completed", "path": path}
                else:
                    return {"status": "error", "detail": "Path not found for completed download"}
            return {"status": status}

        # Add to queue
        download_data = {
            'type': 'movie',
            'id': id,
            'slug': slug,
            'status': 'queued',
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        }
        downloads_collection.insert_one(download_data)
        
        logging.info(f"Film queued for download: {slug}")
        return {"status": "queued"}
    
    except Exception as e:
        logging.error(f"Error queueing film: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue film")

@app.get("/api/download/episode")
async def call_download_episode(
    n_s: Optional[int] = Query(None),
    n_ep: Optional[int] = Query(None),
    titleID: Optional[int] = Query(None),
    slug: Optional[str] = Query(None)
):
    if not all([n_s, n_ep, titleID, slug]):
        logging.warning("Download episode request with missing parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    try:
        # Check if already in downloads
        existing_download = downloads_collection.find_one({
            "type": "tv",
            "id": titleID,
            "season": n_s,
            "episode": n_ep,
            "status": {"$in": ["queued", "downloading", "completed"]}
        })
        
        if existing_download:
            status = existing_download["status"]
            if status == "completed":
                return {"status": "completed", "path": existing_download["path"]}
            return {"status": status}

        # Add to queue
        download_data = {
            'type': 'tv',
            'id': titleID,
            'slug': slug,
            'season': n_s,
            'episode': n_ep,
            'status': 'queued',
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        }
        downloads_collection.insert_one(download_data)
        
        logging.info(f"Episode queued for download: {slug} S{n_s}E{n_ep}")
        return {"status": "queued"}

    except Exception as e:
        logging.error(f"Error queueing episode: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue episode")

@app.get("/api/download/season")
async def download_season(
    season: Optional[str] = Query(None),
    titleID: Optional[str] = Query(None),
    slug: Optional[str] = Query(None)
):
    if not all([season, titleID, slug]):
        logging.warning("Download season request with missing parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    try:
        # Get season info to get episode count
        season_info = get_infoSelectSeason(slug, season)
        if not season_info:
            raise HTTPException(status_code=404, detail="Season not found")

        # Get total episodes in season
        total_episodes = len(season_info.get('episodes', []))
        if total_episodes == 0:
            raise HTTPException(status_code=404, detail="No episodes found in season")

        queued_episodes = []
        # Queue each episode for download
        for episode_num in range(1, total_episodes + 1):
            download_data = {
                "type": "tv",
                "id": titleID,
                "slug": slug,
                "season": int(season),
                "episode": episode_num,
                "status": "queued",
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            }
            
            # Check if this episode is already in the queue or completed
            existing = downloads_collection.find_one({
                "type": "tv",
                "id": titleID,
                "slug": slug,
                "season": int(season),
                "episode": episode_num,
                "status": {"$in": ["queued", "downloading", "completed"]}
            })
            
            if not existing:
                downloads_collection.insert_one(download_data)
                queued_episodes.append({
                    "episode": episode_num,
                    "status": "queued"
                })
            else:
                queued_episodes.append({
                    "episode": episode_num,
                    "status": existing["status"]
                })
        
        logging.info(f"Season queued for download: {slug} S{season}")
        return {"status": "queued", "episodes": queued_episodes}

    except Exception as e:
        logging.error(f"Error queueing season: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue season")

@app.get("/api/downloads/status")
async def get_download_status():
    """Get the current download status and queue"""
    current_download = None
    if current_download_progress["id"]:
        current_download = downloads_collection.find_one({"_id": current_download_progress["id"]})
        if current_download:
            current_download["progress"] = current_download_progress["progress"]
            
    queue = list(downloads_collection.find(
        {"status": "queued"},
        sort=[("timestamp", 1)]
    ))
    
    return {
        "current_download": current_download,
        "queue": queue,
        "active_downloads": len(active_downloads)
    }

@app.put("/api/downloads/config")
async def update_download_config(max_concurrent: int):
    """Update download configuration"""
    global MAX_CONCURRENT_DOWNLOADS
    if max_concurrent < 1:
        raise HTTPException(status_code=400, detail="Max concurrent downloads must be at least 1")
    
    MAX_CONCURRENT_DOWNLOADS = max_concurrent
    logging.info(f"Updated max concurrent downloads to: {MAX_CONCURRENT_DOWNLOADS}")
    return {"max_concurrent": MAX_CONCURRENT_DOWNLOADS}

@app.get("/server/downloaded/{filename:path}")
async def serve_downloaded_file(filename: str):
    try:
        # Decodifica il nome file
        filename = unquote(filename)
        logging.info(f"Requested file: {filename}")
        
        # Costruisci il path completo
        file_path = os.path.join(
            DOWNLOAD_DIRECTORY,
            config_manager.get("DEFAULT", "root_path"),
            filename  # il filename ora contiene il path relativo completo
        )
        logging.info(f"Full path: {file_path}")
        
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            
        logging.info(f"Serving file: {file_path}")
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=os.path.basename(file_path)
        )
        
    except Exception as e:
        logging.error(f"Error serving file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- WATCHLIST UTIL MONGO ------------
@app.post("/server/watchlist/add")
async def add_to_watchlist(item: WatchlistItem):
    existing_item = watchlist_collection.find_one({
        'name': item.name, 
        'url': item.url, 
        'season': item.season
    })

    if existing_item:
        logging.warning(f"Item already in watchlist: {item.name}")
        raise HTTPException(status_code=400, detail="Il titolo è già nella watchlist")

    watchlist_collection.insert_one({
        'name': item.name,
        'title_url': item.url,
        'season': item.season,
        'added_on': datetime.datetime.utcnow()
    })

    logging.info(f"Added to watchlist: {item.name}")
    return {"message": "Titolo aggiunto alla watchlist"}

@app.post("/server/watchlist/update")
async def update_title_watchlist(update: UpdateWatchlistItem):
    result = watchlist_collection.update_one(
        {'title_url': update.url},
        {'$set': {'season': update.season}}
    )

    if result.matched_count == 0:
        logging.warning(f"Item not found for update: {update.url}")
        raise HTTPException(status_code=404, detail="Titolo non trovato nella watchlist")
    
    if result.modified_count == 0:
        logging.info(f"Season unchanged for: {update.url}")
        return {"message": "La stagione non è cambiata"}

    logging.info(f"Updated season for: {update.url}")
    return {"message": "Stagione aggiornata con successo"}

@app.post("/server/watchlist/remove")
async def remove_from_watchlist(item: WatchlistItem):
    # You can handle just the 'name' field here
    result = watchlist_collection.delete_one({'name': item.name})

    if result.deleted_count == 0:
        logging.warning(f"Item not found for removal: {item.name}")
        raise HTTPException(status_code=404, detail="Titolo non trovato nella watchlist")
    
    logging.info(f"Successfully removed from watchlist: {item.name}")
    return {"message": "Titolo rimosso dalla watchlist"}

@app.get("/server/watchlist/get")
async def get_watchlist():
    watchlist_items = list(watchlist_collection.find({}, {'_id': 0}))

    if not watchlist_items:
        logging.info("Watchlist is empty")
        return {"message": "La watchlist è vuota"}

    logging.info("Watchlist retrieved")
    return watchlist_items
    
@app.get("/server/watchlist/check")
async def get_new_season():
    title_new_seasons = []
    watchlist_items = list(watchlist_collection.find({}, {'_id': 0}))
    logging.error("GET: ", watchlist_items)

    if not watchlist_items:
        logging.info("Watchlist is empty")
        return {"message": "La watchlist è vuota"}

    for item in watchlist_items:
        try:
            new_url = updateUrl(item['title_url'], domain)

            result = get_infoSelectTitle(new_url, domain, version)
            if not result or 'season_count' not in result:
                continue

            number_season = result.get("season_count")
            if number_season > item.get("season"):
                title_new_seasons.append({
                    'title_url': item['title_url'],
                    'name': item['name'],
                    'season': number_season,
                    'nNewSeason': number_season - item['season']
                })

        except Exception as e:
            logging.error(f"Error checking new season for {item['title_url']}: {e}")

    if title_new_seasons:
        logging.info(f"New seasons found: {len(title_new_seasons)}")
        return title_new_seasons

    return {"message": "Nessuna nuova stagione disponibile"}

# ---------- DOWNLOAD UTIL MONGO ------------
def ensure_collections_exist(db):
    required_collections = ['watchlist', 'downloads']
    existing_collections = db.list_collection_names()

    for collection_name in required_collections:
        if collection_name not in existing_collections:
            # Creazione della collezione
            db.create_collection(collection_name)
            logging.info(f"Created missing collection: {collection_name}")
        else:
            logging.info(f"Collection already exists: {collection_name}")

@app.get("/server/path/get")
async def fetch_all_downloads():
    try:
        downloads = list(downloads_collection.find({}, {'_id': 0}))
        logging.info("Downloads retrieved")
        return downloads
    
    except Exception as e:
        logging.error(f"Error fetching downloads: {e}")
        raise HTTPException(status_code=500, detail="Errore nel recupero dei download")

@app.get("/server/path/movie")
async def get_movie_path(id: str):
    try:
        # Find movie in downloads collection
        movie = downloads_collection.find_one(
            {"type": "movie", "id": id, "status": "completed"}
        )

        if movie and 'path' in movie:
            full_path = os.path.join(DOWNLOAD_DIRECTORY, config_manager.get("DEFAULT", "root_path"), movie['path'])
            logging.info(f"Full path: {full_path}")
            logging.info(f"Relative path: {movie['path']}")
            
            if os.path.exists(full_path):
                logging.info(f"Movie path retrieved: {movie['path']}")
                return {"path": movie['path']}
            else:
                logging.error(f"Movie file not found at: {full_path}")
                raise HTTPException(status_code=404, detail="File not found")
        else:
            logging.warning(f"Movie not found in downloads or path missing: {id}")
            raise HTTPException(status_code=404, detail="Movie not found in downloads")

    except Exception as e:
        logging.error(f"Error getting movie path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/server/path/episode")
async def fetch_episode_path(id: Optional[int] = Query(None), season: Optional[int] = Query(None), episode: Optional[int] = Query(None)):
    if not id or not season or not episode:
        logging.warning("Episode path request with missing parameters")
        raise HTTPException(status_code=400, detail="Missing parameters (id, season, episode)")

    try:
        episode_data = downloads_collection.find_one(
            {'type': 'tv', 'id': id, 'n_s': season, 'n_ep': episode},
            {'_id': 0, 'path': 1}
        )

        if episode_data and 'path' in episode_data:
            logging.info(f"Episode path retrieved: {episode_data['path']}")
            return {"path": episode_data['path']}
        
        else:
            logging.warning(f"Episode not found: ID {id}, Season {season}, Episode {episode}")
            raise HTTPException(status_code=404, detail="Episode not found")
        
    except Exception as e:
        logging.error(f"Error fetching episode path: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch episode path")

@app.delete("/server/delete/episode")
async def remove_episode(series_id: int = Query(...), season_number: int = Query(...), episode_number: int = Query(...)):
    episode = downloads_collection.find_one({
        'type': 'tv',
        'id': series_id,
        'n_s': season_number,
        'n_ep': episode_number
    }, {'_id': 0, 'path': 1})

    if not episode:
        logging.warning(f"Episode not found: S{season_number}E{episode_number}")
        raise HTTPException(status_code=404, detail="Episodio non trovato")

    file_path = os.path.join(DOWNLOAD_DIRECTORY, config_manager.get("DEFAULT", "root_path"), episode.get('path'))
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Episode file deleted: {file_path}")

    downloads_collection.delete_one({
        'type': 'tv',
        'id': series_id,
        'n_s': season_number,
        'n_ep': episode_number
    })

    return {"success": True}

@app.delete("/server/delete/movie")
async def remove_movie(movie_id: str = Query(...)):
    movie = downloads_collection.find_one({'type': 'movie', 'id': movie_id}, {'_id': 0, 'path': 1})

    if not movie:
        logging.warning(f"Movie not found: ID {movie_id}")
        raise HTTPException(status_code=404, detail="Film non trovato")

    file_path = os.path.join(DOWNLOAD_DIRECTORY, config_manager.get("DEFAULT", "root_path"), movie.get('path'))
    parent_folder = os.path.dirname(file_path)

    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Movie file deleted: {file_path}")

    if os.path.exists(parent_folder) and not os.listdir(parent_folder):
        os.rmdir(parent_folder)
        logging.info(f"Parent folder deleted: {parent_folder}")

    downloads_collection.delete_one({'type': 'movie', 'id': movie_id})
    return {"success": True}

if __name__ == "__main__":
    ensure_collections_exist(db)
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8080,
        reload=False
    )