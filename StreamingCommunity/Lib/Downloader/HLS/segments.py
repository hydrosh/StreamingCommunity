# 18.04.24

import os
import sys
import time
import queue
import signal
import logging
import binascii
import threading

from queue import PriorityQueue
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


# External libraries
import httpx
from tqdm import tqdm


# Internal utilities
from StreamingCommunity.Util.console import console
from StreamingCommunity.Util.headers import get_headers, random_headers
from StreamingCommunity.Util.color import Colors
from StreamingCommunity.Util._jsonConfig import config_manager
from StreamingCommunity.Util.os import os_manager
from StreamingCommunity.Util.call_stack import get_call_stack


# Logic class
from ...M3U8 import (
    M3U8_Decryption,
    M3U8_Ts_Estimator,
    M3U8_Parser,
    M3U8_UrlFix
)
from ...FFmpeg.util import print_duration_table, format_duration
from .proxyes import main_test_proxy

# Config
TQDM_DELAY_WORKER = config_manager.get_float('M3U8_DOWNLOAD', 'tqdm_delay')
TQDM_USE_LARGE_BAR = config_manager.get_int('M3U8_DOWNLOAD', 'tqdm_use_large_bar')

REQUEST_MAX_RETRY = config_manager.get_int('REQUESTS', 'max_retry')
REQUEST_VERIFY = config_manager.get_bool('REQUESTS', 'verify_ssl')

THERE_IS_PROXY_LIST = os_manager.check_file("list_proxy.txt")
PROXY_START_MIN = config_manager.get_float('REQUESTS', 'proxy_start_min')
PROXY_START_MAX = config_manager.get_float('REQUESTS', 'proxy_start_max')

DEFAULT_VIDEO_WORKERS = config_manager.get_int('M3U8_DOWNLOAD', 'default_video_workser')
DEFAULT_AUDIO_WORKERS = config_manager.get_int('M3U8_DOWNLOAD', 'default_audio_workser')



# Variable
headers_index = config_manager.get_dict('REQUESTS', 'user-agent')
max_timeout = config_manager.get_int("REQUESTS", "timeout")



class M3U8_Segments:
    def __init__(self, url: str, tmp_folder: str, is_index_url: bool = True, progress_callback=None):
        """
        Initializes the M3U8_Segments object.

        Parameters:
            - url (str): The URL of the M3U8 playlist.
            - tmp_folder (str): The temporary folder to store downloaded segments.
            - is_index_url (bool): Flag indicating if `m3u8_index` is a URL (default True).
            - progress_callback (callable): Optional callback function to receive progress updates.
        """
        self.url = url
        self.tmp_folder = tmp_folder
        self.is_index_url = is_index_url
        self.progress_callback = progress_callback
        self.expected_real_time = None
        self.max_timeout = max_timeout
        
        self.tmp_file_path = os.path.join(self.tmp_folder, "0.ts")
        os.makedirs(self.tmp_folder, exist_ok=True)

        # Util class
        self.decryption: M3U8_Decryption = None 
        self.class_ts_estimator = M3U8_Ts_Estimator(0) 
        self.class_url_fixer = M3U8_UrlFix(url)

        # Sync
        self.queue = PriorityQueue()
        self.stop_event = threading.Event()
        self.downloaded_segments = set()
        self.base_timeout = 1.0
        self.current_timeout = 5.0

        # Stopping
        self.interrupt_flag = threading.Event()
        self.download_interrupted = False

        # OTHER INFO
        self.info_maxRetry = 0
        self.info_nRetry = 0
        self.info_nFailed = 0

    def __get_key__(self, m3u8_parser: M3U8_Parser) -> bytes:
        """
        Retrieves the encryption key from the M3U8 playlist.

        Parameters:
            - m3u8_parser (M3U8_Parser): The parser object containing M3U8 playlist information.

        Returns:
            bytes: The encryption key in bytes.
        """
        headers_index = {'user-agent': get_headers()}

        # Construct the full URL of the key
        key_uri = urljoin(self.url, m3u8_parser.keys.get('uri'))
        parsed_url = urlparse(key_uri)
        self.key_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        logging.info(f"Uri key: {key_uri}")

        # Make request to get porxy
        try:
            response = httpx.get(
                url=key_uri, 
                headers=headers_index,
                timeout=max_timeout
            )
            response.raise_for_status()

        except Exception as e:
            raise Exception(f"Failed to fetch key from {key_uri}: {e}")

        # Convert the content of the response to hexadecimal and then to bytes
        hex_content = binascii.hexlify(response.content).decode('utf-8')
        byte_content = bytes.fromhex(hex_content)
        
        #console.print(f"[cyan]Find key: [red]{hex_content}")
        return byte_content
    
    def parse_data(self, m3u8_content: str) -> None:
        """
        Parses the M3U8 content to extract segment information.

        Parameters:
            - m3u8_content (str): The content of the M3U8 file.
        """
        m3u8_parser = M3U8_Parser()
        m3u8_parser.parse_data(uri=self.url, raw_content=m3u8_content)

        self.expected_real_time = m3u8_parser.get_duration(return_string=False)
        self.expected_real_time_s = m3u8_parser.duration

        # Check if there is an encryption key in the playlis
        if m3u8_parser.keys is not None:
            try:

                # Extract byte from the key
                key = self.__get_key__(m3u8_parser)
                
            except Exception as e:
                raise Exception(f"Failed to retrieve encryption key {e}.")

            iv = m3u8_parser.keys.get('iv')
            method = m3u8_parser.keys.get('method')

            # Create a decryption object with the key and set the method
            self.decryption = M3U8_Decryption(key, iv, method)

        # Store the segment information parsed from the playlist
        self.segments = m3u8_parser.segments

        # Fix URL if it is incomplete (missing 'http')
        for i in range(len(self.segments)):
            segment_url = self.segments[i]

            if "http" not in segment_url:
                self.segments[i] = self.class_url_fixer.generate_full_url(segment_url)
                logging.info(f"Generated new URL: {self.segments[i]}, from: {segment_url}")

        # Update segments for estimator
        self.class_ts_estimator.total_segments = len(self.segments)
        logging.info(f"Segmnets to download: [{len(self.segments)}]")

        # Proxy
        if THERE_IS_PROXY_LIST:
            console.log("[red]Start validation proxy.")
            self.valid_proxy = main_test_proxy(self.segments[0])
            console.log(f"[cyan]N. Valid ip: [red]{len(self.valid_proxy)}")

            if len(self.valid_proxy) == 0:
                sys.exit(0)

    def get_info(self) -> None:
        """
        Makes a request to the index M3U8 file to get information about segments.
        """
        headers_index = {'user-agent': get_headers()}

        if self.is_index_url:

            # Send a GET request to retrieve the index M3U8 file
            response = httpx.get(
                self.url, 
                headers=headers_index, 
                timeout=max_timeout
            )
            response.raise_for_status()

            # Save the M3U8 file to the temporary folder
            path_m3u8_file = os.path.join(self.tmp_folder, "playlist.m3u8")
            open(path_m3u8_file, "w+").write(response.text) 

            # Parse the text from the M3U8 index file
            self.parse_data(response.text)  

        else:

            # Parser data of content of index pass in input to class
            self.parse_data(self.url)
    
    def setup_interrupt_handler(self):
        """
        Set up a signal handler for graceful interruption.
        """
        def interrupt_handler(signum, frame):
            if not self.interrupt_flag.is_set():
                console.log("\n[red] Stopping download gracefully...")
                self.interrupt_flag.set()
                self.download_interrupted = True
                self.stop_event.set()

    def make_requests_stream(self, ts_url: str, index: int, progress_bar: tqdm, backoff_factor: float = 1.5) -> bool:
        """
        Downloads a TS segment and adds it to the segment queue with retry logic.

        Parameters:
            - ts_url (str): The URL of the TS segment.
            - index (int): The index of the segment.
            - progress_bar (tqdm): Progress counter for tracking download progress.
            - backoff_factor (float): The backoff factor for exponential backoff (default is 1.5 seconds).
            
        Returns:
            bool: True if download was successful, False otherwise
        """       
        for attempt in range(REQUEST_MAX_RETRY):
            if self.interrupt_flag.is_set():
                return False
            
            try:
                start_time = time.time()
                
                # Make request to get content
                if THERE_IS_PROXY_LIST:
                    # Get proxy from list
                    proxy = self.valid_proxy[index % len(self.valid_proxy)]
                    logging.info(f"Use proxy: {proxy}")

                    with httpx.Client(proxies=proxy, verify=REQUEST_VERIFY) as client:  
                        response = client.get(
                            url=ts_url, 
                            headers=random_headers(self.key_base_url) if 'key_base_url' in self.__dict__ else {'user-agent': get_headers()}, 
                            timeout=max_timeout, 
                            follow_redirects=True
                        )
                else:
                    with httpx.Client(verify=REQUEST_VERIFY) as client_2:
                        response = client_2.get(
                            url=ts_url, 
                            headers=random_headers(self.key_base_url) if 'key_base_url' in self.__dict__ else {'user-agent': get_headers()}, 
                            timeout=max_timeout, 
                            follow_redirects=True
                        )

                # Validate response and content
                response.raise_for_status()
                segment_content = response.content
                
                # Decrypt if needed
                if self.decryption is not None:
                    try:
                        segment_content = self.decryption.decrypt(segment_content)
                    except Exception as e:
                        logging.error(f"Error decrypting segment {index}: {str(e)}")
                        continue

                # Add to queue and update progress
                self.queue.put((index, segment_content))
                progress_bar.update(1)
                return True

            except Exception as e:
                logging.error(f"Error downloading segment {index} (attempt {attempt + 1}): {str(e)}")
                if attempt < REQUEST_MAX_RETRY - 1:
                    time.sleep(backoff_factor * (2 ** attempt))
                continue

        return False

    def write_segments_to_file(self):
        """
        Writes segments to file with additional verification and improved error handling.
        """
        buffer = {}
        expected_index = 0
        segments_written = set()
        total_segments = len(self.segments)
        
        with open(self.tmp_file_path, 'wb') as f:
            while not self.stop_event.is_set() or not self.queue.empty():
                if self.interrupt_flag.is_set():
                    break
                
                try:
                    index, segment_content = self.queue.get(timeout=self.current_timeout)

                    # Successful queue retrieval: reduce timeout gradually
                    self.current_timeout = max(self.base_timeout, self.current_timeout * 0.8)

                    # Handle failed segments
                    if segment_content is None:
                        self.info_nFailed += 1
                        logging.error(f"Segment {index} failed to download")
                        if index == expected_index:
                            expected_index += 1
                        continue

                    # Write segment if it's the next expected one
                    if index == expected_index:
                        try:
                            f.write(segment_content)
                            segments_written.add(index)
                            f.flush()
                            os.fsync(f.fileno())  # Ensure data is written to disk
                            expected_index += 1

                            # Calculate and report progress
                            progress = int((len(segments_written) / total_segments) * 100)
                            if self.progress_callback:
                                self.progress_callback(progress)

                            # Write any buffered segments that are now in order
                            while expected_index in buffer:
                                next_segment = buffer.pop(expected_index)
                                if next_segment is not None:
                                    f.write(next_segment)
                                    segments_written.add(expected_index)
                                    f.flush()
                                    os.fsync(f.fileno())
                                expected_index += 1

                        except IOError as e:
                            logging.error(f"Failed to write segment {index}: {e}")
                            self.info_nFailed += 1
                    else:
                        buffer[index] = segment_content

                except queue.Empty:
                    # Increase timeout more gradually
                    self.current_timeout = min(self.max_timeout, self.current_timeout * 1.2)
                    if self.stop_event.is_set():
                        break

                except Exception as e:
                    logging.error(f"Error processing segment {index}: {str(e)}")
                    self.info_nFailed += 1

        return len(segments_written)

    def download_streams(self, description: str, type: str):
        """
        Downloads all TS segments in parallel and writes them to a file.

        Parameters:
            - description: Description to insert on tqdm bar
            - type (str): Type of download: 'video' or 'audio'
        """
        self.setup_interrupt_handler()

        # Initialize progress bar
        total_segments = len(self.segments)
        downloaded_count = 0
        failed_segments = set()
        retry_count = 0
        max_retries = 3  # Maximum number of retry attempts for failed segments
        
        with tqdm(
            total=total_segments,
            desc=description,
            unit='segment',
            delay=TQDM_DELAY_WORKER,
            dynamic_ncols=True,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        ) as progress_bar:

            while retry_count < max_retries and (downloaded_count < total_segments):
                # Create thread pool
                with ThreadPoolExecutor(max_workers=DEFAULT_VIDEO_WORKERS if type == 'video' else DEFAULT_AUDIO_WORKERS) as executor:
                    futures = []

                    # Submit download tasks for remaining segments
                    segments_to_download = range(total_segments) if retry_count == 0 else failed_segments
                    for index in segments_to_download:
                        if self.interrupt_flag.is_set():
                            break

                        futures.append(
                            executor.submit(
                                self.make_requests_stream,
                                self.segments[index],
                                index,
                                progress_bar
                            )
                        )

                    # Wait for all downloads to complete
                    failed_segments.clear()
                    for future in as_completed(futures):
                        if future.result():  # If download was successful
                            downloaded_count += 1
                            progress = int((downloaded_count / total_segments) * 100)
                            if self.progress_callback:
                                self.progress_callback(progress)
                        else:
                            failed_segments.add(index)
                            self.info_nRetry += 1
                    
                    if self.interrupt_flag.is_set():
                        break

                # Update retry count and check if we need another retry
                if failed_segments:
                    retry_count += 1
                    if retry_count < max_retries:
                        logging.info(f"Retrying {len(failed_segments)} failed segments (attempt {retry_count + 1}/{max_retries})")
                        time.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    break

        if self.interrupt_flag.is_set():
            return None

        # Write segments to file and get count of successfully written segments
        segments_written = self.write_segments_to_file()
        
        # Clean up
        self.stop_event.set()
        progress_bar.close()

        # Final verification with improved error reporting
        final_completion = (segments_written / total_segments) * 100
        if final_completion < 99.9:  # Less than 99.9% complete
            missing = set(range(total_segments)) - set(range(segments_written))
            error_msg = f"Download incomplete ({final_completion:.1f}%). Missing {len(missing)} segments."
            if len(missing) <= 10:  # Only show missing segments if there are 10 or fewer
                error_msg += f" Missing segments: {sorted(missing)}"
            raise Exception(error_msg)

        # Verify output file
        if not os.path.exists(self.tmp_file_path):
            raise Exception("Output file missing")
        
        file_size = os.path.getsize(self.tmp_file_path)
        if file_size == 0:
            raise Exception("Output file is empty")
        
        # Get expected time and print summary
        ex_hours, ex_minutes, ex_seconds = format_duration(self.expected_real_time_s)
        ex_formatted_duration = f"[yellow]{int(ex_hours)}[red]h [yellow]{int(ex_minutes)}[red]m [yellow]{int(ex_seconds)}[red]s"
        
        console.print(f"[cyan]Download Summary:")
        console.print(f"[cyan]Max retry per URL[white]: [green]{self.info_maxRetry}")
        console.print(f"[cyan]Total retries[white]: [green]{self.info_nRetry}")
        console.print(f"[cyan]Failed segments[white]: [red]{self.info_nFailed}")
        console.print(f"[cyan]Actual duration[white]: {print_duration_table(self.tmp_file_path, None, True)}")
        console.print(f"[cyan]Expected duration[white]: {ex_formatted_duration}\n")

        if self.info_nRetry >= len(self.segments) * (1/3.33):
            console.print(
                "[yellow]⚠ Performance Warning[/yellow]\n\n"
                "High number of retries detected. Consider:\n"
                "1. Reducing the number of [cyan]workers[/cyan] in [magenta]config.json[/magenta]\n"
                "2. Checking your network connection\n"
                "3. Verifying the stream source is stable"
            )

        return {
            'type': type,
            'nFailed': self.info_nFailed,
            'completion': final_completion,
            'retries': self.info_nRetry
        }