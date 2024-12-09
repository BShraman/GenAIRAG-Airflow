from airflow.operators.empty import EmptyOperator
from airflow.decorators import dag, task
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.datasets import Dataset
import os
import json
import sys

# Adding 'utils' folder to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from docProcessingEmbedding import DocumentProcessor
from chromaDBCheacker import ChromaDBChecker

# Constants
dataset_folder = os.getenv("INLINE_DATA_VOLUME")
CREATE_CLASS_TASK_ID = "create_class"
CLASS_ALREADY_EXISTS_TASK_ID = "class_already_exists"

@dag(
    schedule=None,
    start_date=days_ago(1),
    catchup=False,
    default_args={'owner': 'airflow', 'retries': 0, 'retry_delay': timedelta(minutes=5)},
    description="Fetch, process, and store document metadata and embeddings",
    tags=["document-processing", "embedding"]
)
def doc_processing_embedding_dag():
    """
    Airflow DAG to process documents, check class existence, and handle embeddings in ChromaDB.
    """

    @task()
    def start_task():
        """Reads the dataset folder and extracts URL and Collection Name from JSON file."""
        folder_path = str(dataset_folder)
        try:
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
            if not json_files:
                print("No JSON file found in the dataset folder")
                return None
            
            file_path = os.path.join(folder_path, json_files[0])
            with open(file_path, 'r') as file:
                data = json.load(file)

            return {"url": data.get('url'), "collection_name": data.get('collection_name')}
        except Exception as e:
            print(f"Error reading JSON file: {str(e)}")
            return None

    @task.branch()
    def check_collection_task(data):
        """
        Checks if the ChromaDB collection exists and branches accordingly.
        """
        chromadb_utils = ChromaDBChecker(collection_name=data['collection_name'])
        return chromadb_utils.check_collection_exists(CREATE_CLASS_TASK_ID, CLASS_ALREADY_EXISTS_TASK_ID)

    @task()
    def create_class():
        """Creates a new class in ChromaDB."""
        print("Creating a new class in ChromaDB...")
        return True  # Indicate that the class was created

    @task()
    def class_already_exists():
        """Handles the case when the class already exists in ChromaDB."""
        print("Class already exists in ChromaDB.")
        return False  # Indicate that no class was created

    @task()
    def process_embed_store_task(data, create_task_result):
        """
        Processes the document, generates embeddings, and stores them in ChromaDB.
        """
        if not create_task_result:
            print("Skipping embedding process as no new class was created.")
            return

        processor = DocumentProcessor()
        url = data['url']
        collection_name = data['collection_name']

        document = processor.document_loader(url)
        pre_processed = processor.document_cleansing(document)
        splits = processor.split_document(pre_processed, chunk_size=1500, chunk_overlap=150)

        persist_directory = os.getenv("persist_directory")
        processor.document_embedding_vectorstore(splits, collection_name, persist_directory)
        print("Document processing and embedding storage completed.")

    # Tasks
    data = start_task()
    branch_task = check_collection_task(data)
    create_task = create_class()
    exists_task = class_already_exists()
    process_task_instance = process_embed_store_task(data, create_task)
    end_task = EmptyOperator(task_id="end_task")

    # Task flow
    data >> branch_task
    branch_task >> create_task >> process_task_instance
    branch_task >> exists_task
    process_task_instance >> end_task

# Define DAG
dag = doc_processing_embedding_dag()
