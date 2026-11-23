"""
Function calling without hand-written JSON schemas.

    box = ToolBox()

    @box.tool
    def get_fare(city: str, cabin: Literal["economy", "business"] = "economy") -> dict:
        '''Return the fare to a destination.

        Args:
            city: Destination city name.
            cabin: Cabin class.
        '''

    reply = box.run(messages, provider="ollama")
    for chunk in box.stream(messages): ...

Schemas are derived from type hints and the Google-style docstring. The run/stream loops
execute every requested call, feed results back, and repeat until the model answers in text.
"""

from __future__ import annotations

import inspect
import json
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from toolkit.llm import completion

_JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", dict: "object"}


def _schema(annotation: Any) -> dict:
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is Literal:
        return {"type": _JSON_TYPES.get(type(args[0]), "string"), "enum": list(args)}
    if origin in (list, tuple, set):
        return {"type": "array", "items": _schema(args[0]) if args else {}}
    if origin is Union or str(origin) == "<class 'types.UnionType'>":  # Optional[X] / X | None
        non_null = [a for a in args if a is not type(None)]
        return _schema(non_null[0]) if non_null else {}
    return {"type": _JSON_TYPES.get(annotation, "string")}


def _parse_docstring(doc: str) -> tuple[str, dict[str, str]]:
    """Split a Google-style docstring into (summary, {param: description})."""
    if not doc:
        return "", {}
    summary, _, rest = inspect.cleandoc(doc).partition("Args:")
    params = dict(re.findall(r"^\s*(\w+)(?:\s*\(.*?\))?:\s*(.+)$", rest, re.MULTILINE))
    return " ".join(summary.split()), params


@dataclass
class Tool:
    fn: Callable
    name: str
    description: str
    parameters: dict

    @classmethod
    def from_function(cls, fn: Callable) -> Tool:
        summary, param_docs = _parse_docstring(fn.__doc__ or "")
        hints = get_type_hints(fn)
        properties, required = {}, []
        for pname, param in inspect.signature(fn).parameters.items():
            prop = _schema(hints.get(pname, str))
            if pname in param_docs:
                prop["description"] = param_docs[pname]
            properties[pname] = prop
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        parameters = {"type": "object", "properties": properties, "required": required}
        return cls(fn=fn, name=fn.__name__, description=summary, parameters=parameters)

    @property
    def spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCall:
    """A completed call, kept for logging / UI display."""

    name: str
    arguments: dict
    result: Any


@dataclass
class ToolBox:
    tools: dict[str, Tool] = field(default_factory=dict)
    max_rounds: int = 5
    on_call: Callable[[ToolCall], None] | None = None

    def tool(self, fn: Callable) -> Callable:
        """Decorator: register a function as a tool."""
        self.tools[fn.__name__] = Tool.from_function(fn)
        return fn

    def add(self, *fns: Callable) -> ToolBox:
        for fn in fns:
            self.tool(fn)
        return self

    @property
    def specs(self) -> list[dict]:
        return [t.spec for t in self.tools.values()]

    # -- execution ---------------------------------------------------------

    def execute(self, call_id: str, name: str, raw_args: str) -> dict:
        """Run one tool and return the `tool` message for the model.
        Errors are returned to the model as text so it can recover or explain."""
        args: dict = {}
        try:
            args = json.loads(raw_args or "{}")
            if name not in self.tools:
                raise KeyError(f"unknown tool {name!r}")
            result = self.tools[name].fn(**args)
        except Exception as exc:
            result = {"error": f"{type(exc).__name__}: {exc}"}
        if self.on_call:
            self.on_call(ToolCall(name, args, result))
        content = result if isinstance(result, str) else json.dumps(result, default=str)
        return {"role": "tool", "tool_call_id": call_id, "content": content}

    def run(self, messages: list, provider: str | None = None, model: str | None = None) -> str:
        """Blocking loop. Appends assistant/tool turns to `messages` and returns the final text."""
        for _ in range(self.max_rounds):
            message = completion(messages, provider, model, tools=self.specs).choices[0].message
            if not message.tool_calls:
                messages.append({"role": "assistant", "content": message.content or ""})
                return message.content or ""
            messages.append(message.model_dump(exclude_none=True))
            for tc in message.tool_calls:
                messages.append(self.execute(tc.id, tc.function.name, tc.function.arguments))
        raise RuntimeError(f"No final answer after {self.max_rounds} tool rounds")

    def stream(
        self, messages: list, provider: str | None = None, model: str | None = None
    ) -> Iterator[str]:
        """
        Streaming loop. Text deltas are yielded as they arrive; tool-call deltas arrive in
        fragments (name first, then the JSON arguments in pieces) and are stitched together
        by index before execution.
        """
        for _ in range(self.max_rounds):
            text, calls = "", {}
            for chunk in completion(messages, provider, model, tools=self.specs, stream=True):
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    text += delta.content
                    yield delta.content
                for tc in delta.tool_calls or []:
                    slot = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                    slot["id"] = tc.id or slot["id"]
                    if tc.function:
                        slot["name"] += tc.function.name or ""
                        slot["arguments"] += tc.function.arguments or ""

            if not calls:
                messages.append({"role": "assistant", "content": text})
                return
            ordered = [calls[i] for i in sorted(calls)]
            messages.append(
                {
                    "role": "assistant",
                    "content": text or None,
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": c["arguments"]},
                        }
                        for c in ordered
                    ],
                }
            )
            for c in ordered:
                messages.append(self.execute(c["id"], c["name"], c["arguments"]))
        raise RuntimeError(f"No final answer after {self.max_rounds} tool rounds")
