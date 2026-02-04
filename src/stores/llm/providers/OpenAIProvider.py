from ..LLMInterface import LLMInterface 
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging
from typing import List, Union

class OpenAIProvider(LLMInterface):
    def __init__(self,api_key : str , api_url: str = None,
                 default_input_max_characters: int = 1000,
                 default_generation_max_output_token: int=1000,
                 default_generation_temperature: float=0.1):
        
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_token = default_generation_max_output_token
        self.default_generation_temperature = default_generation_temperature
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url if self.api_url and len(self.api_url) else None
        )
        self.logger = logging.getLogger(__name__)
        self.enums = OpenAIEnums
    
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
    
    def process_text(self, text: str):
        if not isinstance(text, str):
            text = str(text)
        return text[: self.default_input_max_characters].strip()
    
    def _uses_max_completion_tokens(self) -> bool:
        """
        Check if the current model uses max_completion_tokens instead of max_tokens.
        Newer models like gpt-4o, o1-preview, o1-mini require max_completion_tokens.
        """
        newer_model_prefixes = ['gpt-4o', 'o1-preview', 'o1-mini', 'o1']
        if not self.generation_model_id:
            return False
        return any(self.generation_model_id.startswith(prefix) for prefix in newer_model_prefixes)
    
    def generate_text(self, prompt: str, chat_history: list = None, max_output_tokens: int = None, temperature: float = None):
        if not self.client:
            self.logger.error("OpenAI was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI was not set")
            return None 
        
        if chat_history is None:
            chat_history = []
        
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_token
        temperature = temperature if temperature is not None else self.default_generation_temperature
        
        chat_history.append(
            self.construct_prompt(prompt=prompt, role=OpenAIEnums.USER.value)
        )
        
        # Build parameters based on model type
        params = {
            "model": self.generation_model_id,
            "messages": chat_history,
            "temperature": temperature
        }
        
        # Prefer the newer parameter to avoid unsupported-parameter errors
        params["max_completion_tokens"] = max_output_tokens

        self.logger.debug("OpenAI request params prepared: model=%s max_completion_tokens=%s temperature=%s",
                          self.generation_model_id, max_output_tokens, temperature)
        
        # call model with retries for common unsupported-parameter errors
        def _call_model_with_params(model_id: str, call_params: dict):
            call_params = dict(call_params)
            call_params["model"] = model_id
            return self.client.chat.completions.create(**call_params)

        response = None
        try:
            try:
                response = _call_model_with_params(self.generation_model_id, params)
            except Exception as e:
                err_str = str(e)
                # handle models that reject custom temperature values
                if "temperature" in err_str and ("does not support" in err_str or "Unsupported value" in err_str):
                    self.logger.warning("Generation model does not support custom temperature; retrying without temperature")
                    params.pop("temperature", None)
                    try:
                        response = _call_model_with_params(self.generation_model_id, params)
                    except Exception as e2:
                        self.logger.error("OpenAI chat call failed on retry without temperature: %s", e2)
                else:
                    self.logger.error("OpenAI chat call failed: %s", e)

        except Exception:
            self.logger.exception("Unexpected error when calling OpenAI model")

        # fallback to a known-working model if initial model failed
        if not response:
            fallback_model = "gpt-5-nano"
            if self.generation_model_id != fallback_model:
                self.logger.info("Attempting fallback to model %s", fallback_model)
                try:
                    response = _call_model_with_params(fallback_model, params)
                except Exception as e3:
                    err_str = str(e3)
                    if "temperature" in err_str and ("does not support" in err_str or "Unsupported value" in err_str):
                        self.logger.warning("Fallback model does not support custom temperature; retrying without temperature")
                        try:
                            params.pop("temperature", None)
                            response = _call_model_with_params(fallback_model, params)
                        except Exception as e4:
                            self.logger.error("Fallback OpenAI chat call also failed: %s", e4)
                    else:
                        self.logger.error("Fallback OpenAI chat call failed: %s", e3)
        
        if not response or not response.choices or len(response.choices) == 0:
            self.logger.error("Invalid response from OpenAI")
            return None
        
        return response.choices[0].message.content
    
    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI was not set")
            return None
        
        if isinstance(text, str):
            text = [text]
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI was not set")
            return None
        
        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text
        )
        
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Embedding response is empty or invalid")
            return None
        
        return [rec.embedding for rec in response.data]
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt
        }