"""Streamlit stream renderer for markdown output"""

import json
from typing import Any

from ..events import (
    TextEvent,
    CurrentToolUseEvent,
    ToolResultEvent,
    ToolStreamEvent,
    ReasoningEvent,
    LifecycleEvent,
    MultiAgentNodeStartEvent,
    MultiAgentNodeStreamEvent,
    MultiAgentNodeStopEvent,
    MultiAgentHandoffEvent,
    MultiAgentResultEvent,
)
from .base import BaseStreamRenderer


class StreamlitStreamRenderer(BaseStreamRenderer):
    """Stream renderer for Streamlit output (returns markdown strings)"""
    
    # Sentinel value to force header on next text event
    _TEXT_SOURCE_RESET = object()
    
    def __init__(self, parser=None):
        super().__init__(parser)
        self.displayed_tool_calls = set()
        self.current_text_source: str | None | object = None  # Track current text source to show prefix only on change
        self.current_reasoning_active: bool = False  # Track if reasoning is currently active to show prefix only on start
    
    def format_tool_display(self, tool_name: str, tool_input: dict | None) -> str:
        """Format tool name and arguments for display"""
        if not tool_input:
            return f"{tool_name}()"
        
        formatted_args = []
        for k, v in tool_input.items():
            if isinstance(v, str) and len(v) > 50:
                formatted_args.append(f"{k}='{v[:50]}...'")
            else:
                formatted_args.append(f"{k}={v!r}")
        
        return f"{tool_name}({', '.join(formatted_args)})"
    
    def on_text(self, event: TextEvent) -> str:
        """Return text chunk as-is"""
        # Reset reasoning state when text event occurs
        self.current_reasoning_active = False
        # Add source prefix only when source changes (not on every token)
        if event.source != self.current_text_source:
            self.current_text_source = event.source
            if event.source:
                return f"\n\n:blue[**[Sub-Agent ⚡ {event.source}]**] {event.data}"
            else:
                # Switching back to main agent
                return f"\n\n{event.data}"
        return event.data
    
    def on_tool_use(self, event: CurrentToolUseEvent) -> str:
        """Return tool call as markdown - shows accumulated input as it streams"""
        # Reset text source so next text event will show header again
        self.current_text_source = self._TEXT_SOURCE_RESET
        # Reset reasoning state when tool use occurs
        self.current_reasoning_active = False
        
        # Use tool_id for deduplication if available, otherwise use tool_name
        dedup_key = event.tool_id or event.tool_name
        is_new_tool_call = dedup_key and dedup_key not in self.displayed_tool_calls
        
        if is_new_tool_call:
            self.displayed_tool_calls.add(dedup_key)
        
        prefix = f":blue[**[Sub-Agent ⚡ {event.source}]** ]" if event.source else ""
        
        if is_new_tool_call:
            # First time - show full tool call
            result = f"\n\n{prefix}**⚙️ Tool 호출:**"
            # Show tool_id if available
            if event.tool_id:
                result += f" **`{event.tool_name}`** (`{event.tool_id}`)\n\n"
            return result
        else:
            # Update - show input update (for streaming accumulation)
            if event.tool_input:
                result = f"\n```json\n{json.dumps(event.tool_input, indent=2, ensure_ascii=False)}\n```\n\n"
                return result
        return ""
    
    def on_tool_result(self, event: ToolResultEvent) -> str:
        """Return tool result as markdown"""
        # Reset text source so next text event will show header again
        self.current_text_source = self._TEXT_SOURCE_RESET
        # Reset reasoning state when tool result occurs
        self.current_reasoning_active = False
        
        if not event.data:
            return ""
        
        preview_len = min(500, len(event.data))
        preview = event.data[:preview_len]
        if len(event.data) > preview_len:
            preview += "\n...(생략)"
        
        prefix = f":blue[**[Sub-Agent ⚡ {event.source}]** ]" if event.source else ""
        result = f"\n\n{prefix}**✅ Tool 결과:** {len(event.data):,} chars\n\n"
        result += f"```\n{preview}\n```\n\n"
        result += "\n\n---\n\n"
        return result
    
    def on_tool_stream(self, event: ToolStreamEvent) -> str:
        """Return tool stream event as markdown"""
        # Reset text source so next text event will show header again
        self.current_text_source = self._TEXT_SOURCE_RESET
        # Reset reasoning state when tool stream occurs
        self.current_reasoning_active = False
        
        tool_use_dict = event.tool_use if isinstance(event.tool_use, dict) else {}
        tool_name = tool_use_dict.get("name", "unknown")
        tool_id = tool_use_dict.get("toolUseId")
        tool_input = tool_use_dict.get("input", {})
        
        result = f"\n\n**📡 Tool Stream: `{tool_name}`**"
        if tool_id:
            result += f" (`{tool_id}`)"
        result += "\n\n"
        
        # Show tool_input if available
        if tool_input:
            result += f"```json\n{json.dumps(tool_input, indent=2, ensure_ascii=False)}\n```\n\n"
        
        # Show stream data
        if event.data:
            if isinstance(event.data, str):
                preview_len = min(500, len(event.data))
                preview = event.data[:preview_len]
                if len(event.data) > preview_len:
                    preview += "\n...(생략)"
                result += f"```\n{preview}\n```\n\n"
            else:
                result += f"```json\n{json.dumps(event.data, indent=2, ensure_ascii=False)}\n```\n\n"
        return result
    
    def on_reasoning(self, event: ReasoningEvent) -> str:
        """Return reasoning text with > prefix (blockquote style)"""
        # Replace newlines with newline + > to maintain blockquote across multiple lines
        text = event.data.replace("\n", "\n> ")
        
        # Add > prefix and 💭 emoji only when reasoning starts (not on every token)
        if not self.current_reasoning_active:
            self.current_reasoning_active = True
            return f"> 💭 {text}"
        return text
    
    def on_lifecycle(self, event: LifecycleEvent) -> str:
        """Return lifecycle event as markdown"""
        if event.lifecycle_type == "init":
            return "\n\n> :orange[🔄 **Event loop initialized**]\n\n"
        elif event.lifecycle_type == "start":
            return "\n\n> :orange[▶️ **Event loop cycle starting**]\n\n"
        elif event.lifecycle_type == "complete":
            return "\n\n> :green[✅ **Cycle completed**]\n\n"
        elif event.lifecycle_type == "force_stop":
            reason = event.force_stop_reason or "unknown reason"
            return f"\n\n> :red[🛑 **Event loop force-stopped**: {reason}]\n\n"
        return ""
    
    def on_multiagent_node_start(self, event: MultiAgentNodeStartEvent) -> str:
        """Return multi-agent node start as markdown"""
        return f"\n\n:blue[🔄 **Node [{event.node_id}]** ({event.node_type}) starting]\n\n"
    
    def on_multiagent_node_stream(self, event: MultiAgentNodeStreamEvent) -> list[Any]:
        """Process multi-agent node stream (recursively process inner event)"""
        # Recursively process inner event
        return self.process(event.inner_event)
    
    def on_multiagent_node_stop(self, event: MultiAgentNodeStopEvent) -> str:
        """Return multi-agent node stop as markdown"""
        node_result = event.node_result
        if hasattr(node_result, 'execution_time'):
            exec_time = node_result.execution_time
            return f"\n\n:green[✅ **Node [{event.node_id}]** completed in {exec_time} ms]\n\n"
        else:
            return f"\n\n:green[✅ **Node [{event.node_id}]** completed]\n\n"
    
    def on_multiagent_handoff(self, event: MultiAgentHandoffEvent) -> str:
        """Return multi-agent handoff as markdown"""
        from_nodes = ", ".join(event.from_node_ids)
        to_nodes = ", ".join(event.to_node_ids)
        result = f"\n\n:purple[🔀 **Handoff**: {from_nodes} → {to_nodes}]\n\n"
        if event.message:
            result += f":purple[   Message: {event.message}]\n\n"
        return result
    
    def on_multiagent_result(self, event: MultiAgentResultEvent) -> str:
        """Return multi-agent final result as markdown"""
        result = event.result
        if hasattr(result, 'status'):
            return f"\n\n:green[📊 **Multi-agent completed**: {result.status}]\n\n"
        else:
            return "\n\n:green[📊 **Multi-agent completed**]\n\n"
    
    def reset(self):
        """Reset renderer state"""
        super().reset()
        self.displayed_tool_calls.clear()
        self.current_text_source = None
        self.current_reasoning_active = False


# Backward compatibility alias
StreamlitAdapter = StreamlitStreamRenderer

