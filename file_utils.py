import os
import time
import logging
from datetime import datetime, timedelta

def cleanup_old_files(directory, hours=1):
    now = time.time()
    cutoff = now - (hours * 3600)

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and os.path.getctime(filepath) < cutoff:
            try:
                os.remove(filepath)
                logging.info(f"Deleted old file: {filename}")
            except Exception as e:
                logging.error(f"Error deleting file {filename}: {str(e)}")
