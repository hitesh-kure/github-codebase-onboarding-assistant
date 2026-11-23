
from langchain_ollama import OllamaEmbeddings


embeddings_model = OllamaEmbeddings(
    model="nomic-embed-text"
)


def generate_embedding(text: str):

    vector = embeddings_model.embed_query(text)

    return vector


def generate_embeddings(texts: list[str]):

    vectors = embeddings_model.embed_documents(texts)

    return vectors
