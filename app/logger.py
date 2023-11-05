import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(action)s - %(message)s',
    handlers=[
        logging.FileHandler('app/files/log_file.log')
    ]
)
logger = logging.getLogger('dashboard_logger')

