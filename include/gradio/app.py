import os
import logging
import gradio as gr
from appInterface import *
from dataChatBot import *


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    persist_dir_default = "/opt/chromadb"
    chatbot = DataChatBot(persist_directory=persist_dir_default)
    gradio_interface = AppInterface(chatbot=chatbot)

    try:
        gradio_interface.launch()
    except Exception as e:
        logger.error(f"Failed to launch Gradio app: {e}")