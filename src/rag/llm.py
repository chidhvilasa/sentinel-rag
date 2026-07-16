"""
LLM Interface Module

Handles communication with the local LLM via Ollama.
This is the main generation component that receives sanitized context.
"""
from typing import List, Optional, Generator
from dataclasses import dataclass
import ollama


@dataclass
class GenerationResult:
    """Result of LLM generation"""
    query: str
    context: str
    response: str
    model: str
    tokens_used: int


class OllamaLLM:
    """
    Interface to local LLMs via Ollama.
    
    Supports:
    - llama3:8b (recommended)
    - mistral:7b
    - phi3:mini
    - And other Ollama-compatible models
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant. Answer questions based on the provided context. 
If the context doesn't contain relevant information, say so clearly.
Do not make up information that isn't in the context.
Be concise and accurate."""
    
    def __init__(
        self,
        model: str = "llama3:8b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the LLM interface.
        
        Args:
            model: Ollama model name
            base_url: Ollama server URL
            temperature: Generation temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
            system_prompt: Custom system prompt
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        # Configure Ollama client
        self.client = ollama.Client(host=base_url)
        
        # Verify model is available
        self._verify_model()
    
    def _verify_model(self):
        """Check if the model is available locally"""
        try:
            models = self.client.list()
            available = [m['name'] for m in models.get('models', [])]
            
            # Check if model (or a variant) is available
            model_base = self.model.split(':')[0]
            found = any(model_base in m for m in available)
            
            if not found:
                print(f"Warning: Model '{self.model}' not found locally.")
                print(f"Available models: {available}")
                print(f"Run: ollama pull {self.model}")
        except Exception as e:
            print(f"Warning: Could not verify model availability: {e}")
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the full prompt with context"""
        return f"""Context information:
---
{context}
---

Based on the above context, please answer the following question:
{query}"""
    
    def generate(
        self,
        query: str,
        context: str,
        stream: bool = False
    ) -> GenerationResult:
        """
        Generate a response using the LLM.
        
        Args:
            query: User's question
            context: Retrieved and sanitized context
            stream: Whether to stream the response
            
        Returns:
            GenerationResult with the response
        """
        prompt = self._build_prompt(query, context)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        )
        
        return GenerationResult(
            query=query,
            context=context,
            response=response['message']['content'],
            model=self.model,
            tokens_used=response.get('eval_count', 0)
        )
    
    def generate_stream(
        self,
        query: str,
        context: str
    ) -> Generator[str, None, None]:
        """
        Stream a response token by token.
        
        Yields:
            Response tokens as they're generated
        """
        prompt = self._build_prompt(query, context)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        stream = self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        )
        
        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
    
    def simple_query(self, prompt: str) -> str:
        """
        Simple query without RAG context.
        
        Useful for testing the LLM directly.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        )
        
        return response['message']['content']
    
    def health_check(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            self.client.list()
            return True
        except Exception:
            return False
