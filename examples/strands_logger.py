"""StreamingLogger for Strands Agents SDK

Utility class to handle streaming events from Strands Agents, including:
- Tool call logging
- Tool result logging
- Chunk text output
"""

import json


class StreamingLogger:
    """Logger to track tool calls and output chunk text from streaming events"""
    
    def __init__(self):
        self.tool_call_counter = 0
        self.displayed_tool_calls = set()  # Track displayed tool calls by toolUseId
        self.processed_event_ids = set()  # Track processed events by event_loop_cycle_id to avoid duplicates
        self.processed_data_events = set()  # Track processed data events to avoid duplicates
    
    def extract_tool_use_from_event(self, event: dict) -> dict | None:
        """Extract toolUse information from event"""
        tool_use = None
        
        # Check top-level toolUse
        if "toolUse" in event:
            tool_use = event["toolUse"]
        # Check message -> content -> toolUse structure
        elif "message" in event:
            message = event["message"]
            if isinstance(message, dict):
                content_list = message.get("content", [])
                if isinstance(content_list, list):
                    for content in content_list:
                        if isinstance(content, dict) and "toolUse" in content:
                            tool_use = content["toolUse"]
                            break
        
        return tool_use if isinstance(tool_use, dict) else None
    
    def extract_tool_result_from_event(self, event: dict) -> dict | None:
        """Extract toolResult information from event. Returns tool_result dict or None"""
        if "message" not in event:
            return None
            
        message = event["message"]
        if not isinstance(message, dict):
            return None
            
        content_list = message.get("content", [])
        if not isinstance(content_list, list):
            return None
            
        for content in content_list:
            if isinstance(content, dict) and "toolResult" in content:
                tool_result = content.get("toolResult", {})
                if isinstance(tool_result, dict):
                    return tool_result
        
        return None
    
    def extract_result_content(self, tool_result: dict) -> str:
        """Extract text content from tool result"""
        if not isinstance(tool_result, dict):
            return str(tool_result)
        
        # Check for content field
        if "content" in tool_result:
            content = tool_result["content"]
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    return first_item["text"]
                return str(first_item)
            elif isinstance(content, str):
                return content
            return str(content)
        
        # Check for text field
        if "text" in tool_result:
            return tool_result["text"]
        
        # Return JSON string for other dict structures
        return json.dumps(tool_result, indent=2, ensure_ascii=False)
    
    def process_tool_events(self, event: dict) -> None:
        """Process tool-related events (tool calls and results)"""
        # Check if we've already processed this event (avoid duplicates)
        event_id = event.get('event_loop_cycle_id')
        if event_id and event_id in self.processed_event_ids:
            return  # Skip duplicate event
        if event_id:
            self.processed_event_ids.add(event_id)
        
        # Check for tool call start
        tool_use = self.extract_tool_use_from_event(event)
        if tool_use:
            tool_use_id = tool_use.get("toolUseId", "")
            tool_name = tool_use.get("name", "unknown")
            tool_input = tool_use.get("input", {}) if isinstance(tool_use.get("input"), dict) else {}
            
            # Log tool call start (avoid duplicates)
            if tool_use_id and tool_use_id not in self.displayed_tool_calls:
                self.displayed_tool_calls.add(tool_use_id)
                self.tool_call_counter += 1
                
                print(f"\n{'='*60}")
                print(f"Tool #{self.tool_call_counter}: {tool_name}")
                print(f"{'='*60}")
                print(json.dumps(tool_input, indent=2, ensure_ascii=False))
                print(f"{'='*60}\n")
        
        # Check for tool result
        tool_result = self.extract_tool_result_from_event(event)
        if tool_result:
            tool_use_id = tool_result.get("toolUseId", "")
            status = tool_result.get("status", "")
            result_content = self.extract_result_content(tool_result)
            
            print(f"{'='*60}")
            header = "Tool Result: \n"
            header += f"[toolUseId] {tool_use_id}\n"
            header += f"[status] {status}\n"
            header += f"[content length] {len(result_content)} characters"
            print(header)
            
            print(f"{'='*60}")
            if result_content:
                # Truncate long results for readability
                if len(result_content) > 1000:
                    preview = result_content[:1000] + "\n...(생략)"
                    print(preview)
                else:
                    print(result_content)
            else:
                print(json.dumps(tool_result, indent=2, ensure_ascii=False))
            print(f"{'='*60}\n")
    
    def process_chunk_text(self, event: dict) -> None:
        """Process chunk text from data events"""
        # Only process 'data' events - message events contain full text and would cause duplicates
        if "data" in event:
            event_id = event.get('event_loop_cycle_id')
            # Avoid processing the same event twice
            if event_id and event_id in self.processed_data_events:
                return
            if event_id:
                self.processed_data_events.add(event_id)
            
            chunk_text = event["data"]
            if chunk_text:
                print(chunk_text, end="", flush=True)
    
    def process_event(self, event) -> None:
        """Process a streaming event: handles both tool calls and chunk text"""
        if not isinstance(event, dict):
            return
        
        # Process tool-related events
        self.process_tool_events(event)
        
        # Process chunk text
        self.process_chunk_text(event)
    
    def reset(self) -> None:
        """Reset logger state for a new query"""
        self.displayed_tool_calls.clear()
        self.processed_event_ids.clear()
        self.processed_data_events.clear()

