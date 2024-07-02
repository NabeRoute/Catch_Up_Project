import atexit
import os
import glob
import logging

def clear_temp_files():
    temp_files = glob.glob('./tmp/*')
    for file in temp_files:
        os.remove(file)
    logging.info("Temporary files cleared")