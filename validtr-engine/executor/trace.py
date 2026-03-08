"""Execution tracing — captures all events during a run."""

import time

from models.result import ExecutionTrace, LLMCall, ToolCall


class TraceCollector:
    """Collects execution events into an ExecutionTrace."""

    def __init__(self):
        self.trace = ExecutionTrace()
        self._start_time = time.time()

    def record_llm_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
    ) -> None:
        self.trace.llm_calls.append(
            LLMCall(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )
        )
        self.trace.total_tokens += input_tokens + output_tokens

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        result: str,
        duration_ms: int,
    ) -> None:
        self.trace.tool_calls.append(
            ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=result[:500],  # Truncate large results
                duration_ms=duration_ms,
            )
        )

    def finalize(self) -> ExecutionTrace:
        self.trace.total_duration_ms = int((time.time() - self._start_time) * 1000)
        return self.trace
