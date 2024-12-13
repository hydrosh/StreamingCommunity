# 01.03.24

import logging


# External libraries
import httpx


# Internal utilities
from StreamingCommunity.Util.headers import get_headers
from StreamingCommunity.Util._jsonConfig import config_manager
from StreamingCommunity.Api.Player.Helper.Vixcloud.util import Season, EpisodeManager


# Variable
max_timeout = config_manager.get_int("REQUESTS", "timeout")


class ScrapeSerie:
    def __init__(self, site_name: str):
        """
        Initialize the ScrapeSerie class for scraping TV series information.
        
        Args:
            site_name (str): Name of the streaming site to scrape from
        """
        self.is_series = False
        self.headers = {'user-agent': get_headers()}
        self.base_name = site_name
        self.domain = config_manager.get_dict('SITE', self.base_name)['domain']

    def setup(self, version: str = None, media_id: int = None, series_name: str = None):
        """
        Set up the scraper with specific media details.
        
        Args:
            version (str, optional): Site version for request headers
            media_id (int, optional): Unique identifier for the media
            series_name (str, optional): Name of the TV series
        """
        self.version = version
        self.media_id = media_id

        # If series name is provided, initialize series-specific managers
        if series_name is not None:
            self.is_series = True
            self.series_name = series_name
            self.season_manager = None
            self.episode_manager: EpisodeManager = EpisodeManager()

    def collect_info_title(self) -> None:
        """
        Retrieve season information for a TV series from the streaming site.
        
        Raises:
            Exception: If there's an error fetching season information
        """
        self.headers = {
            'user-agent': get_headers(),
            'x-inertia': 'true', 
            'x-inertia-version': self.version,
        }

        try:

            response = httpx.get(
                url=f"https://{self.base_name}.{self.domain}/titles/{self.media_id}-{self.series_name}", 
                headers=self.headers, 
                timeout=max_timeout
            )
            response.raise_for_status()

            # Extract seasons from JSON response
            json_response = response.json().get('props')

            # Collect info about season
            self.season_manager = Season(json_response.get('title'))
            self.season_manager.collect_images(self.base_name, self.domain)

            # Collect first episode info
            for i, ep in enumerate(json_response.get('loadedSeason').get('episodes')):
                self.season_manager.episodes.add(ep)
                self.season_manager.episodes.get(i).collect_image(self.base_name, self.domain)
            
        except Exception as e:
            logging.error(f"Error collecting season info: {e}")
            raise

    def collect_info_season(self, number_season: int) -> None:
        """
        Retrieve episode information for a specific season.
        
        Args:
            number_season (int): Season number to fetch episodes for
        
        Raises:
            Exception: If there's an error fetching episode information
        """
        self.headers = {
            'user-agent': get_headers(),
            'x-inertia': 'true', 
            'x-inertia-version': self.version,
        }

        try:
            response = httpx.get(
                url=f'https://{self.base_name}.{self.domain}/titles/{self.media_id}-{self.series_name}/stagione-{number_season}', 
                headers=self.headers, 
                timeout=max_timeout
            )
            response.raise_for_status()

            # Extract episodes from JSON response
            json_response = response.json().get('props').get('loadedSeason').get('episodes')
                
            # Add each episode to the episode manager
            for dict_episode in json_response:
                self.episode_manager.add(dict_episode)

        except Exception as e:
            logging.error(f"Error collecting title season info: {e}")
            raise
