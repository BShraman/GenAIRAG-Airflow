import re, requests, os
from langchain.schema import Document
from langchain_community.document_loaders import BSHTMLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
from langchain.vectorstores import Chroma

class DocumentProcessor:
    """
    A class to clean and process documents.
    """

    @staticmethod
    def clean_text(text):
        # non-ASCII characters, unwanted special characters, and normalizing whitespace
        text = text.encode('ascii', 'ignore').decode('ascii')

        # Normalize whitespace (replace multiple spaces and newlines with a single space)
        text = re.sub(r'\s+', ' ', text)

        # Remove unwanted special characters like 'Â'
        text = text.replace('Â', '')

        # Remove unnecessary trailing spaces or newlines
        text = text.strip()

        return text
    
    def document_cleansing(self, page):
        """
        Process the document content after loading it using BSHTMLLoader.
        Cleans up the text, removes unwanted characters, and normalizes the content.
        
        Args:
            page (Document): A Document object from BSHTMLLoader.
            
        Returns:
            Document: A new Document object with cleaned content.
        """
        # Clean the page content
        cleaned_content = self.clean_text(page.page_content)
        
        # Return a Document object with cleaned content
        return Document(page_content=cleaned_content, metadata=page.metadata)
    
    def document_loader(self, url):
        """Fetch HTML content from the URL."""
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        html_content = response.text

        """Convert HTML content into documents using BSHTMLLoader."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".html") as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name

        print("======== Load the Document !!!==============")
        loader = BSHTMLLoader(file_path=temp_file_path)
        documents = loader.load()

        return documents[0]
    
    def process_document(self , document):
        """
        Cleans and processes a single Document object.

        Args:
            document (Document): Document to process.

        Returns:
            Document: Cleaned Document.
        """
        cleaned_content = self.clean_text(document.page_content)
        return Document(page_content=cleaned_content, metadata=document.metadata)

    def split_document(self, document="", chunk_size="", chunk_overlap=""):
        """
        Splits a cleaned document into smaller chunks using RecursiveCharacterTextSplitter.

        Args:
            document (Document): Document to split.
            chunk_size (int): Maximum size of each chunk.
            chunk_overlap (int): Overlap between chunks.

        Returns:
            list[Document]: List of split documents.
        """
        self.document = document
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print("========= Spliting Documents =================")
        splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        return splitter.split_documents([self.document])
    

    def document_embedding_vectorstore(self, splits="", collection_name="" ,persist_directory="" ):
        
        print("========= Embeddings and Vector Store =============")
        self.splits = splits
        self.persist_directory = os.getenv("PERSIST_DIRECTORY")
        self.collection_name = collection_name
        
        embeddings = OpenAIEmbeddings()
        #generate_embeddings=embeddings.embed_documents([doc.page_content for doc in documents])
        vectordb = Chroma.from_documents(
            collection_name=self.collection_name,
            documents=self.splits,
            embedding=embeddings,
            persist_directory=self.persist_directory)
        
        #Save this so we can use it later!
        vectordb.persist()
    
