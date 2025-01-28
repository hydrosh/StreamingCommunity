# 3.12.23

import os
import time
import logging


# Internal utilities
from StreamingCommunity.Util.console import console, msg
from StreamingCommunity.Util.os import os_manager
from StreamingCommunity.Util.message import start_message
from StreamingCommunity.Util.call_stack import get_call_stack
from StreamingCommunity.Lib.Downloader import HLS_Downloader


# Logic class
from StreamingCommunity.Api.Template.Util import execute_search
from StreamingCommunity.Api.Template.Class.SearchType import MediaItem


# Player
from StreamingCommunity.Api.Player.vixcloud import VideoSource


# Variable
from .costant import ROOT_PATH, SITE_NAME, MOVIE_FOLDER
        

def download_film(id: str, slug: str, progress_callback=None):
    """
    Download a film from StreamingCommunity.

    Args:
        id (str): The ID of the film.
        slug (str): The slug of the film.
        progress_callback (callable, optional): Callback function to track download progress.
    """
    try:
        # Sanitize the slug for filesystem use
        safe_slug = os_manager.get_sanitize_file(slug)
        
        # Create output directory
        output_dir = os.path.join(ROOT_PATH, SITE_NAME, MOVIE_FOLDER, safe_slug)
        os.makedirs(output_dir, exist_ok=True)
        
        # Full path for the output file
        output_path = os.path.join(output_dir, f"{safe_slug}.mp4")
        
        # Start message and display film information
        start_message()
        console.print(f"[yellow]Download:  [red]{slug} \n")

        # Get video source information
        video_source = VideoSource(SITE_NAME, False)
        video_source.setup(id)
        video_source.get_iframe(id)
        video_source.get_content()
        
        # Get the M3U8 playlist URL and verify it
        m3u8_playlist = video_source.get_playlist()
        if not m3u8_playlist:
            raise Exception("Failed to get M3U8 playlist URL")
            
        logging.info(f"Got M3U8 playlist URL: {m3u8_playlist}")
        
        # Create downloader instance with progress callback
        def wrapped_callback(progress, status=None):
            if progress_callback:
                progress_callback(progress, status)
                
        downloader = HLS_Downloader(
            output_filename=output_path,
            m3u8_playlist=m3u8_playlist,
            is_playlist_url=True,
            progress_callback=wrapped_callback
        )
        
        # Start download and check result
        try:
            result = downloader.start()
            if result == 404:
                raise Exception("Failed to download video - 404 error")
        except Exception as e:
            if progress_callback:
                progress_callback(0, "error")
            raise Exception(f"Download failed: {str(e)}")
            
        if not os.path.exists(output_path):
            raise Exception("Download completed but output file not found")
            
        return output_path
        
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        if progress_callback:
            progress_callback(0, "error")
        raise
