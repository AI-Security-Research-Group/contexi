import numpy as np
from typing import List, Tuple
from langchain_community.docstore.document import Document
from sentence_transformers import CrossEncoder
from app.utils import logger

class ReRanker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", top_k: int = 5):
        self.model = CrossEncoder(model_name)
        self.top_k = top_k

    def rerank(self, query: str, documents: List[Document]) -> List[Tuple[Document, float]]:
        if not documents:
            logger.warning("No documents provided for re-ranking.")
            return []

        logger.info(f"Re-ranking {len(documents)} documents")
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)

        # Log score statistics
        logger.info(f"Re-ranking scores - Mean: {np.mean(scores):.4f}, Std: {np.std(scores):.4f}")
        logger.info(f"Score range: [{np.min(scores):.4f}, {np.max(scores):.4f}]")

        # Sort documents by score in descending order
        scored_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        
        # Log position changes
        original_positions = {id(doc): i for i, doc in enumerate(documents)}
        position_changes = sum(1 for i, (doc, _) in enumerate(scored_docs) if original_positions[id(doc)] != i)
        logger.info(f"Number of documents that changed position: {position_changes} out of {len(documents)}")

        return scored_docs[:self.top_k]

    
    def get_diversity_reranked(self, query: str, documents: List[Document]) -> List[Document]:
        logger.info(f"Starting diversity-focused re-ranking for {len(documents)} documents")
        """Re-rank documents with a focus on diversity."""
        if not documents:    
            return []

        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)

        # Initialize selected indices and diversity penalty
        selected_indices = []
        diversity_penalty = np.zeros(len(documents))

        for _ in range(min(self.top_k, len(documents))):
            # Apply diversity penalty and select the best remaining document
            penalized_scores = scores - diversity_penalty
            best_idx = np.argmax(penalized_scores)
            selected_indices.append(best_idx)
            logger.info(f"Selected document {best_idx} for diversity. Score: {penalized_scores[best_idx]:.4f}")

            # Update diversity penalty
            for i in range(len(documents)):
                if i not in selected_indices:
                    similarity = self.compute_similarity(documents[best_idx].page_content, documents[i].page_content)
                    diversity_penalty[i] += similarity

        # Return the selected documents in their original order
        return [documents[i] for i in sorted(selected_indices)]
        logger.info(f"Diversity re-ranking complete. Returning {len(selected_indices)} documents")

    @staticmethod
    def compute_similarity(doc1: str, doc2: str) -> float:
        """Compute similarity between two documents. This is a placeholder implementation."""
        # In a real implementation, you might use cosine similarity of document embeddings
        return len(set(doc1.split()) & set(doc2.split())) / len(set(doc1.split()) | set(doc2.split()))

def configure_reranker(config):
    model_name = config.get('reranking', {}).get('model_name', "cross-encoder/ms-marco-MiniLM-L-6-v2")
    top_k = config.get('reranking', {}).get('top_k', 5)
    logger.info(f"Configuring ReRanker with model: {model_name} and top_k: {top_k}")
    return ReRanker(model_name, top_k)