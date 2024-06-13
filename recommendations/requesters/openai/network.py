from openai import AsyncOpenAI


class OpenAIClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def create_chat_completion(
        self, messages: list[dict[str, str]], model: str
    ) -> str:
        chat = await self.client.chat.completions.create(messages=messages, model=model)
        return chat.choices[0].message.content
