import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataChatBot:
    """DataChatBot class to handle the initialization, data processing, and querying with ChromaDB."""

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    def __init__(self, persist_directory: str):
        """
        Initialize the DataChatBot with ChromaDB persistence directory and OpenAI API key.

        Args:
            persist_directory (str): Path to ChromaDB persistence directory.
        """
        if not self.OPENAI_API_KEY:
            logger.error("OpenAI API Key is not set.")
            raise ValueError("OpenAI API Key is required.")

        self.persist_directory = persist_directory
        self.embedding_function = OpenAIEmbeddings(model=self.EMBEDDING_MODEL)
        self.response_model = os.getenv("RESPONSE_MODEL")

    def load_collection(self, collection_name: str) -> Chroma:
        """
        Load a collection from ChromaDB.

        Args:
            collection_name (str): The name of the collection to load.

        Returns:
            Chroma: A Chroma vector store instance.
        """
        logger.info(f"Loading collection: {collection_name} from {self.persist_directory}")
        try:
            vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function
            )
            return vector_store
        except Exception as e:
            logger.error(f"Error loading collection {collection_name}: {e}")
            raise

    def create_chat_agent(self, collection: Chroma, template: str) -> RetrievalQA:
        """
        Create a retrieval-based QA agent using OpenAI and a custom prompt template.

        Args:
            collection (Chroma): A vector store instance.
            template (str): The template for the question-answer flow.

        Returns:
            RetrievalQA: A RetrievalQA chain object.
        """
        logger.info("Creating chat agent with the provided template.")
        prompt = PromptTemplate(input_variables=["question", "context"], template=template)
        llm = ChatOpenAI(model=self.response_model, 
                         temperature=0)
        
        return RetrievalQA.from_chain_type(
            llm=llm,
            retriever=collection.as_retriever(),
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt}
        )

    def ask_question(self, agent: RetrievalQA, question: str) -> str:
        """
        Ask a question using the chat agent and get the response.

        Args:
            agent (RetrievalQA): The retrieval-based QA agent.
            question (str): The question to ask.

        Returns:
            str: The agent's response.
        """
        logger.info(f"User is asking: {question}")
        try:
            response = agent.run(question)
            logger.info(f"Chatbot response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return f"Error: {str(e)}"