# yt_dlp_test.py

import yt_dlp
import logging
import traceback
import os

# --- 1. Configure Detailed Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- 2. Define the Video URL to Test ---
VIDEO_URL = "https://youtu.be/Pl_iXB4aPJ8?si=21CK7dWKlBnnI0UM" # Updated URL

def test_video_download_and_list_formats(url: str):
    """
    Attempts to list available formats and then download a single video
    using yt-dlp functionality.
    """
    logging.info(f"--- Starting yt-dlp Test for URL: {url} ---")
    
    # --- 3. First, list available formats ---
    logging.info("--- Listing all available formats for the video ---")
    list_formats_opts = {
        'listformats': True,
        'quiet': False,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(list_formats_opts) as ydl:
            ydl.extract_info(url, download=False) # download=False just lists formats
        logging.info("--- Finished listing formats ---")
    except Exception as e:
        logging.error(f"Failed to list formats: {e}")
        logging.debug(traceback.format_exc())
        logging.warning("Proceeding to attempt download, but listing formats failed.")

    # --- 4. Attempt to download the video ---
    logging.info("--- Attempting to download the video with a robust format ---")
    ydl_opts = {
        # Using a more flexible format selection that works with YouTube's restrictions
        'format': 'best',  # Simplified format selection
        'outtmpl': 'yt_dlp_test_video.%(ext)s', # Saves the video in the current directory
        'quiet': False,        # We want to see all output from yt-dlp
        'socket_timeout': 30,
        'retries': 3,          # Reduced retries for a quicker test
        'fragment_retries': 3,
        'noplaylist': True,
        'noprogress': False,   # Show the download progress bar
        # Add options to bypass YouTube restrictions
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # Try alternative clients
                'skip': ['hls', 'dash'],  # Skip problematic formats
            }
        },
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    
    try:
        logging.info("Initializing yt-dlp for download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info("Attempting to extract info and download...")
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
            
            logging.info("--- ✅ TEST SUCCESSFUL! ---")
            logging.info(f"Video Title: {info_dict.get('title')}")
            logging.info(f"File saved to: {os.path.abspath(video_path)}")

    except Exception as e:
        logging.critical("--- ❌ TEST FAILED! ---")
        logging.error("An exception occurred during the download process.")
        logging.error(f"Exception Type: {type(e).__name__}")
        logging.error(f"Error Details: {e}")
        # The traceback provides the most detailed information for debugging.
        logging.debug(f"\n--- Full Traceback ---\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_video_download_and_list_formats(VIDEO_URL)