import time
import hashlib
from typing import List, Tuple, Literal
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_experimental.smart_llm import SmartLLMChain
from app.utils import logger, load_config
from app.re_ranking import ReRanker, configure_reranker

# Load configuration
config = load_config()

config = load_config()
use_reranking = config.get('reranking', {}).get('enabled', False)
reranker = ReRanker(config.get('reranking', {}).get('model_name', "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                    config.get('reranking', {}).get('top_k', 5)) if use_reranking else None

def get_doc_identifier(doc):
    # Create a unique identifier for a document based on its content and metadata
    content = doc.page_content[:100]  # Use first 100 characters of content
    metadata = str(sorted(doc.metadata.items()))  # Convert metadata to a consistent string representation
    return hashlib.md5((content + metadata).encode()).hexdigest()

# Configure re-ranker
try:
    reranker = configure_reranker(config)
except Exception as e:
    logger.error(f"Failed to configure re-ranker: {e}")
    reranker = None

# Get configuration values
n_ideas = config.get('n_ideas', 3)
PROMPT_TEMPLATE = config.get('prompt_template', "")
INITIAL_K = config.get('retrieval', {}).get('initial_k', 10)
MAX_ITERATIONS = config.get('max_iterations', 3)

PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE, input_variables=["chat_history", "context", "question"]
)

context_cache = {}
chat_history: List[Tuple[str, str]] = []

def perform_cgrag(query: str, retriever, llm, chain_type: Literal["smart", "fast"] = "smart") -> Tuple[str, List[Tuple[str, str]]]:
    global chat_history
    iteration = 0
    k = config.get('retrieval', {}).get('initial_k', 10)
    max_iterations = config.get('max_iterations', 3)

    formatted_history = "\n".join([f"Human: {h}\nAI: {a}" for h, a in chat_history])

    while iteration < max_iterations:
        logger.info(f"CGRAG iteration {iteration + 1}/{max_iterations}")

        try:
            if iteration == 0:
                retriever.search_kwargs["k"] = k
                retrieved_docs = retriever.get_relevant_documents(query)
                initial_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

                initial_prompt = PromptTemplate(
                    template="""Given the following user query, identify only any missing concepts, keywords, function or file name needed for a comprehensive answer:\n\nQuery: {query}\n\nInitial Context:\n{context}\n\n Missing Concepts:""",
                    input_variables=["query", "context"],
                )
                initial_chain = LLMChain(llm=llm, prompt=initial_prompt)
                
                missing_concepts_response = initial_chain.run(query=query, context=initial_context)
                missing_concepts = missing_concepts_response.strip()

                refined_query = f"{query} {missing_concepts}"
                logger.info(f"Refined Query: {refined_query}")
                retrieved_docs = retriever.get_relevant_documents(refined_query)
            else:
                cache_key = hashlib.md5(f"{query}_{k}_{formatted_history}".encode()).hexdigest()
                if cache_key in context_cache:
                    retrieved_docs = context_cache[cache_key]
                    logger.info("Using cached retrieved documents")
                else:
                    retriever.search_kwargs["k"] = k
                    retrieved_docs = retriever.get_relevant_documents(query)
                    context_cache[cache_key] = retrieved_docs
                    logger.info(f"Retrieved {len(retrieved_docs)} documents")

            # Apply re-ranking


            if use_reranking and reranker:
                start_time = time.time()
                original_docs = retrieved_docs.copy()
                scored_docs = reranker.rerank(query, retrieved_docs)
                reranked_docs = [doc for doc, _ in scored_docs]
                rerank_time = time.time() - start_time

                # Compare documents
                changes = sum(1 for orig, reranked in zip(original_docs, reranked_docs) if id(orig) != id(reranked))
                change_ratio = changes / len(original_docs)

                logger.info(f"Re-ranking changed {change_ratio:.2%} of all docs. Time taken: {rerank_time:.2f}s")
                
                # Log the top 3 documents before and after re-ranking
                logger.info("Top 3 documents before re-ranking:")
                for i, doc in enumerate(original_docs[:3]):
                    logger.info(f"{i+1}. {doc.metadata.get('file_name', 'Unknown')} - {doc.page_content[:50]}...")
                logger.info("Top 3 documents after re-ranking:")
                for i, doc in enumerate(reranked_docs[:3]):
                    logger.info(f"{i+1}. {doc.metadata.get('file_name', 'Unknown')} - {doc.page_content[:50]}...")
            else:
                reranked_docs = retrieved_docs

            context = "\n\n".join([doc.page_content for doc in reranked_docs])


            logger.info(f"Using chain type: {chain_type}")
            if chain_type == "smart":
                chain = SmartLLMChain(llm=llm, prompt=PROMPT, n_ideas=n_ideas, verbose=True)
            else:
                chain = LLMChain(llm=llm, prompt=PROMPT)

            response = chain.run(chat_history=formatted_history, context=context, question=query)

            answer = response.strip()

            logger.info(f"Generated answer: {answer[:100]}...")

            if any(phrase in answer.lower() for phrase in ["i need more information", "cannot find", "i couldn't find"]):
                k += 5
                iteration += 1
                logger.info(f"Insufficient answer, increasing k to {k}")
            else:
                logger.info("Satisfactory answer obtained")
                break

        except Exception as e:
            logger.error(f"Error during CGRAG iteration: {e}")
            answer = f"An error occurred while processing your query: {str(e)}"
            break

        chat_history.append((query, answer))
        formatted_history = "\n".join([f"Human: {h}\nAI: {a}" for h, a in chat_history])

    chat_history.append((query, answer))

    return answer, chat_history

def start_interactive_session(file_directory: str, retriever, llm, chain_type: Literal["smart", "fast"] = "smart"):
    global chat_history
    logger.info("Starting interactive session")
    logger.info("Welcome to the Code Review Assistant!")
    logger.info("Type 'exit' to end the session.\n")

    while True:
        user_query = input("Enter your question: ")

        if user_query.lower() == 'exit':
            logger.info("User ended the session")
            logger.info("Thank you for using the assistant. Goodbye!")
            break

        try:
            answer, chat_history = perform_cgrag(user_query, retriever, llm, chain_type)
            logger.info(f"\nAnswer:\n{answer}")

            with open('output.md', 'a', encoding='utf-8') as f:
                f.write(f"## Question\n\n{user_query}\n\n")
                f.write(f"## Answer\n\n{answer}\n\n")
        except Exception as e:
            logger.error(f"Error during question answering: {e}")
            print(f"An error occurred: {e}")

    logger.info("Session ended, conversation history saved to output.md")
    logger.info("Your conversation history has been saved to output.md")

if __name__ == "__main__":
    # This block can be used for testing the RAG module independently
    pass
