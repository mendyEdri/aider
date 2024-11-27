import importlib
import json
import httpx
from typing import Optional, Dict, Any, List

class LazyLiteWixLLM:
    _lazy_module = None
    _client = None
    _api_key = None
    _api_base = "https://bo.wix.com/_serverless/mobile-apps-editor-middleware/generate/text"

    def __init__(self):
        self.model_cost = {}  # Mirror litellm's model_cost dict
        self.suppress_debug_info = True
        self.set_verbose = False
        self.drop_params = True

    def __getattr__(self, name):
        if name == "_lazy_module":
            return super()
        # Only initialize when actually needed
        self._init_client()
        return getattr(self._lazy_module, name)

    def _init_client(self):
        if self._lazy_module is not None:
            return

        # Create a module-like object that mirrors litellm's interface
        class WixLLMModule:
            def __init__(self, parent):
                self.parent = parent
                self.suppress_debug_info = True
                self.set_verbose = False
                self.drop_params = True

            def completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Any:
                """Mirror litellm's completion interface but use Wix's API"""
                return self.parent.completion(model, messages, **kwargs)

        self._lazy_module = WixLLMModule(self)

    def set_api_key(self, api_key: str):
        """Set the API key for Wix's API"""
        self._api_key = api_key

    def _format_messages_for_wix(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Format messages into Wix API format"""
        # Extract the last user message as the main message
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        if not user_messages:
            raise ValueError("No user messages found")
        
        last_user_message = user_messages[-1]['content']
        
        # Collect all previous messages as code references
        code_refs = []
        for msg in messages[:-1]:  # Exclude the last message
            if msg['role'] in ['user', 'assistant'] and msg['content']:
                code_refs.append(msg['content'])
        
        return {
            "message": last_user_message,
            "code_ref": "\n".join(code_refs) if code_refs else None
        }

    def completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        Implementation of the completion method that will call Wix's API
        Mirrors litellm's completion interface
        """
        if not self._api_key:
            raise ValueError("API key must be set before making requests")

        # Format messages for Wix API
        wix_payload = self._format_messages_for_wix(messages)

        # Make request to Wix API
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = httpx.post(
                self._api_base,
                headers=headers,
                json=wix_payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Convert Wix API response to litellm format
            wix_response = response.json()
            
            # Create a response object that mirrors litellm's response format
            class CompletionResponse:
                def __init__(self, response_data):
                    self.choices = [
                        type('Choice', (), {
                            'message': type('Message', (), {
                                'content': response_data.get('generated_text', ''),
                                'function_call': None,
                                'tool_calls': None
                            }),
                            'finish_reason': 'stop'
                        })()
                    ]
                    # Estimate token usage since Wix API doesn't provide it
                    content_length = len(response_data.get('generated_text', ''))
                    self.usage = type('Usage', (), {
                        'prompt_tokens': len(str(wix_payload)) // 4,  # Rough estimate
                        'completion_tokens': content_length // 4,    # Rough estimate
                        'total_tokens': (len(str(wix_payload)) + content_length) // 4
                    })()

            return CompletionResponse(wix_response)

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error during API call: {str(e)}")
        except Exception as e:
            raise Exception(f"Error during API call: {str(e)}")

    def __getstate__(self):
        """Support for pickling"""
        return {
            '_api_key': self._api_key,
            'model_cost': self.model_cost
        }

    def __setstate__(self, state):
        """Support for unpickling"""
        self._api_key = state.get('_api_key')
        self.model_cost = state.get('model_cost', {})
        self._lazy_module = None
        self._client = None 