import os
import gradio as gr
import json
import requests
import json
import chromadb


class AppInterface:
    """Gradio Interface class to create and launch the Gradio app."""

    def __init__(self, chatbot):
        """
        Initialize GradioInterface with the DataChatBot instance.

        Args:
            chatbot (DataChatBot): An instance of the DataChatBot class to interact with.
        """
        self.chatbot = chatbot
        self.persist_directory = os.getenv("PERSIST_DIRECTORY")
        self.collection_list = self.get_collection_list()
        self.collection_name_default = self.collection_list[0] if self.collection_list else None
        self.base_url = os.getenv("AIRFLOW_WEBSERVER_URL")
        self.dag_id = os.getenv("AIRFLOW_DAG_ID_FOR_RESTAPI")
        self.username = os.getenv("AIRFLOW_USERNAME")
        self.password = os.getenv("AIRFLOW_PASSWORD")
        self.endpoint = f"{self.base_url}/api/v1/dags/{self.dag_id}/dagRuns"
        self.headers = {"Content-Type": "application/json"}
        self.file_path=os.getenv("INLINE_DATA_VOLUME")

    def trigger_airflow_dag(self,conf=None):
        """
        Trigger an Airflow DAG using Basic Authentication.

        Args:
            conf (dict, optional): Configuration parameters for the DAG run.

        Returns:
            str: Status message indicating success or failure.

        Raises:
            Exception: If the request fails or returns an error status code.
        """

        payload = {"conf": conf} if conf else {}

        try:
            response = requests.post(
                self.endpoint, auth=(self.username, 
                                     self.password), 
                                     headers=self.headers,
                                     json=payload)

            if response.status_code == 200:
                return "DAG triggered successfully."
                
            else:
                raise Exception(
                    f"Failed to trigger DAG. Status code: {response.status_code}, Response: {response.text}")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error triggering DAG: {str(e)}")

    def save_url_to_file(self, url: str, file_path: str = "/opt/data/data.json") -> dict:
        """
        Save a given URL to a local file.

        Args:
            url (str): The URL to save.
            file_path (str): Path to the file where the URL will be saved.

        Returns:
            str: Confirmation message.
        """
        file_path =f"{self.file_path}/data.json"
        try:
            # Delete the file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)

            # Create a dictionary with the URL details
            collection_name = url.split("//")[1].split("/")[0]
            
            #Trigger Airflow Dag
            status = self.trigger_airflow_dag()

            result = {
                "status": status,
                "url": url,
                "collection_name": collection_name,
            }

            # Write the URL to the file
            with open(file_path, "w") as file:
                file.write(json.dumps(result, indent=4))       

            return result
        
        except Exception as e:
            return f"Error saving URL: {str(e)}"

    def chatbot_interface(self, question: str, collection_name: str) -> str:
        """
        Gradio interface function to handle user input and return chatbot responses.

        Args:
            question (str): User's question.
            collection_name (str): Name of the collection to query.

        Returns:
            str: Chatbot's response.
        """
        question_template = """You are an intelligent assistant with access to context-rich documents.
        Given the question: "{question}", and the following context:
        {context}
        Provide a detailed, helpful answer."""

        # Load collection
        collection = self.chatbot.load_collection(collection_name)

        # Create the chat agent
        agent = self.chatbot.create_chat_agent(collection, template=question_template)

        # Get the chatbot's response
        return self.chatbot.ask_question(agent, question)
    
    def get_collection_list(self):
        """
        Retrieve available collection names from a ChromaDB persistent directory.
        
        Args:
            persist_directory (str): Path to the directory where ChromaDB data is stored.

        Returns:
            list: A list of collection names.
        """
        
        try:
            # Ensure the persistence directory exists
            if not os.path.exists(self.persist_directory):
                raise FileNotFoundError(f"Persistence directory '{self.persist_directory}' does not exist.")

            # Initialize ChromaDB client with the new method
            client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Fetch collections
            collections = client.list_collections()
            
            if not collections:
                print(f"No collections found in directory: {self.persist_directory}")
                return []
            
            # Extract and return collection names
            return [collection.name for collection in collections]
        
        except FileNotFoundError as e:
            print(f"File error: {str(e)}")
            return []
        except Exception as e:
            print(f"Error retrieving collections: {str(e)}")
            return []

    def launch(self):
        """Launch the Gradio interface."""
        # Step 1: Interface to save URL
        url_interface = gr.Interface(
            fn=self.save_url_to_file,
            inputs=gr.Textbox(label="Enter URL:", placeholder="Type the URL here..."),
            outputs=gr.Textbox(label="Status Message"),
            title="Save URL",
            description="Enter a URL to save it to a local file.",
        )

        # Step 2: Chatbot interface
        chatbot_interface = gr.Interface(
            fn=self.chatbot_interface,
            inputs=[
                gr.Textbox(label="Enter your question:", placeholder="Type your question here..."),
                gr.Dropdown(
                    label="Collection Name:", 
                    choices=self.collection_list, 
                    value=self.collection_name_default, 
                    interactive=True),
            ],
            outputs=gr.Textbox(label="Chatbot Response:"),
            title="ChromaDB Chatbot",
            description="Ask questions about a specific dataset stored in ChromaDB.",
        )

        # Combine interfaces into a single app
        gr.TabbedInterface([url_interface, chatbot_interface], ["Save URL", "Chatbot"]).launch(
            server_name="0.0.0.0", server_port=7860
        )
