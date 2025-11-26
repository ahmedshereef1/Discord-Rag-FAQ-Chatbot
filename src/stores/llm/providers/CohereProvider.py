from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereEnums, DocumentTypeEnums
import cohere  # pyright: ignore[reportMissingImports]
import logging
from typing import Optional, List, Union


class CohereProvider(LLMInterface):

    def __init__(self, api_key: str,
                 default_input_max_characters: int = 1000,
                 default_generation_max_output_token: int = 1000,
                 default_generation_temperature: float = 0.1):

        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_token = default_generation_max_output_token
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id: Optional[str] = None
        self.embedding_model_id: Optional[str] = None
        self.embedding_size: Optional[int] = None

        # ensure attribute exists even if client creation fails
        self.client = None
        try:
            self.client = cohere.ClientV2(api_key=self.api_key)
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to initialize Cohere client: %s", e)

        self.logger = logging.getLogger(__name__)
        self.enums = CohereEnums

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        if not isinstance(text, str):
            text = str(text)
        return text[: self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: Optional[list] = None,
                      max_output_tokens: int = None, temperature: float = None):
        if not self.client:
            self.logger.error("Cohere client was not initialized")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for Cohere was not set")
            return None

        if chat_history is None:
            chat_history = []

        # make sure messages are a list of dicts
        messages = []
        messages.extend(chat_history)
        messages.append({"role": "user", "content": self.process_text(prompt)})

        try:
            response = self.client.chat(
                model=self.generation_model_id,
                messages=messages,
                temperature=temperature or self.default_generation_temperature,
                max_tokens=max_output_tokens or self.default_generation_max_output_token
            )
        except Exception as e:
            self.logger.error("Cohere chat call failed: %s", e)
            return None

        # tolerant extraction
        try:
            if hasattr(response, "message") and getattr(response.message, "content", None):
                content = response.message.content
                if isinstance(content, list) and len(content) > 0 and getattr(content[0], "text", None):
                    return content[0].text
            if hasattr(response, "output") and isinstance(response.output, list) and len(response.output) > 0:
                o0 = response.output[0]
                text = getattr(o0, "content", None) or getattr(o0, "text", None)
                if isinstance(text, list) and len(text) > 0:
                    candidate = text[0]
                    return getattr(candidate, "text", candidate)
                elif isinstance(text, str):
                    return text
        except Exception as e:
            self.logger.debug("Failed to extract generated text: %s", e)

        self.logger.error("Unexpected response shape from Cohere chat: %r", response)
        return None

    def embed_text(self, text: Union[str, List[str]], document_type: str = None) -> Optional[List[float]]:
        if not self.client:
            self.logger.error("Cohere client was not initialized")
            return None

        if isinstance(text, str):
            text = [text]

        if not self.embedding_model_id:
            self.logger.error("Embedding model for Cohere was not set")
            return None

        input_type = CohereEnums.DOCUMENT
        if document_type == DocumentTypeEnums.QUERY:
            input_type = CohereEnums.QUERY

        # FIX 1: process each text individually
        processed = [self.process_text(t) for t in text]
        processed = [p for p in processed if p]  

        if not processed:
            self.logger.error("Empty text after processing")
            return None

        try:
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=processed,  
                input_type=input_type,
                embedding_types=["float"],
            )
            self.logger.debug("Cohere embed response: %r", response)
        except Exception as e:
            self.logger.error("Cohere embed call failed: %s", e)
            return None

        # tolerant extraction of embedding vector
        try:
            if hasattr(response, "embeddings"):
                emb = response.embeddings

                # FIX 3: extract all embeddings from list
                if isinstance(emb, list) and len(emb) > 0:
                    result = []
                    for item in emb:
                        if hasattr(item, "float"):
                            result.append(item.float)
                        elif hasattr(item, "embedding"):
                            result.append(item.embedding)
                    if result:
                        return result

                # FIX 4: return all embeddings, not just first
                if getattr(emb, "float", None):
                    fl = emb.float
                    if isinstance(fl, list) and len(fl) > 0:
                        return fl  # Return all, not fl[0]
        except Exception as e:
            self.logger.debug("Failed to extract embedding: %s", e)

        self.logger.error("Unexpected response shape from Cohere embed: %r", response)
        return None
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt
        }
