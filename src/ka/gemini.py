"""Gemini: embeddings and tool-calling chat. One small wrapper so the agent and tests never touch the SDK directly."""

from dataclasses import dataclass, field

from google import genai
from google.genai import types


@dataclass
class Turn:
    text: str = ""
    function_calls: list[dict] = field(default_factory=list)  # {"name", "args"}
    input_tokens: int = 0
    output_tokens: int = 0
    raw: object = None


class Gemini:
    def __init__(self, api_key: str, model: str, embed_model: str, dims: int):
        self.client = genai.Client(api_key=api_key)
        self.model, self.embed_model, self.dims = model, embed_model, dims

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 50):  # batch limit is generous; 50 keeps requests small
            r = self.client.models.embed_content(
                model=self.embed_model,
                contents=texts[i : i + 50],
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dims),
            )
            out.extend([e.values for e in r.embeddings])
        return out

    def chat(self, system: str, contents: list, tools: list[dict] | None) -> Turn:
        decls = [types.FunctionDeclaration(**t) for t in tools or []]
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
            tools=[types.Tool(function_declarations=decls)] if decls else None,
        )
        r = self.client.models.generate_content(model=self.model, contents=contents, config=cfg)
        t = Turn(raw=r)
        u = r.usage_metadata
        if u:
            t.input_tokens = u.prompt_token_count or 0
            t.output_tokens = u.candidates_token_count or 0
        for fc in r.function_calls or []:
            t.function_calls.append({"name": fc.name, "args": dict(fc.args or {})})
        if not t.function_calls:  # reading .text on a function-call reply logs an SDK warning
            try:
                t.text = r.text or ""
            except Exception:  # noqa: BLE001
                t.text = ""
        return t

    # ---- helpers to build the conversation (kept here so the agent stays SDK-agnostic) ----
    @staticmethod
    def user(text: str):
        return types.Content(role="user", parts=[types.Part.from_text(text=text)])

    @staticmethod
    def model_turn(turn: Turn):
        return turn.raw.candidates[0].content

    @staticmethod
    def tool_results(results: list[tuple[str, dict]]):
        return types.Content(
            role="user", parts=[types.Part.from_function_response(name=n, response=r) for n, r in results]
        )
