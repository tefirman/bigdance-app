#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   app.py
@Time    :   2024/02/20
@Author  :   Taylor Firman
@Version :   1.0
@Contact :   tefirman@gmail.com
@Desc    :   Main entry point for March Madness bracket app
'''

from shiny import App
import logging
from datetime import datetime
from pathlib import Path
import os

# Import our modular components
from ui import app_ui
from server import server
from data import initialize_tournament_data

# Set up logging configuration
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)

# Create analysis_data directory if it doesn't exist
analysis_dir = Path('analysis_data/men_100entries')
# analysis_dir = Path('analysis_data/women_100entries')
if not analysis_dir.exists():
    analysis_dir.mkdir(parents=True, exist_ok=True)
    # Copy README to analysis_data directory if it exists
    readme_path = Path('analysis_data_README.md')
    if readme_path.exists():
        with open(readme_path, 'r') as source:
            with open(analysis_dir / 'README.md', 'w') as dest:
                dest.write(source.read())

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the app object that shinyapps.io is looking for
app = App(app_ui, server)

def main():
    """Main entry point for the application"""
    try:
        # Initialize data
        logger.info("Initializing tournament data...")
        initialize_tournament_data()
        
        # Run the app
        logger.info("Starting application...")
        port = int(os.environ.get("PORT", 8000))
        app.run(host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Error running application: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
