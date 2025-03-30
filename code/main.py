import gradio as gr
import json

class StreamingJsonParser:
    def __init__(self):
        self.buffer = ""  # Stores incoming JSON chunks
        self.partial_json = {}  # Current state of the parsed JSON
        self.stack = [(self.partial_json, None)]  # Stack of (current_object, current_key)
        self.in_string = False  # Track if inside a string
        self.escape = False  # Handle escape sequences
        self.current_string = ""  # Current string being built
        self.expecting_colon = False  # Track if expecting a colon after a key

    def consume(self, buffer: str):
        """Consumes a chunk of JSON data and updates the parser state."""
        self.buffer += buffer
        self._parse()
        return self  # Allow method chaining

    def get(self):
        """Returns the current state of the parsed JSON object."""
        return self.partial_json

    def _parse(self):
        """Processes the buffer incrementally and updates partial JSON."""
        i = 0
        while i < len(self.buffer):
            char = self.buffer[i]
            
            # Handle string state
            if self.in_string:
                if self.escape:
                    self.current_string += char
                    self.escape = False
                elif char == '\\':
                    self.escape = True
                elif char == '"':
                    # End of string
                    self.in_string = False
                    
                    # If we were reading a key
                    if self.expecting_colon:
                        current_obj, _ = self.stack[-1]
                        self.stack[-1] = (current_obj, self.current_string)
                        self.expecting_colon = False
                    else:
                        # We were reading a value
                        current_obj, current_key = self.stack[-1]
                        if current_key is not None:
                            current_obj[current_key] = self.current_string
                            self.stack[-1] = (current_obj, None)
                    
                    self.current_string = ""
                else:
                    self.current_string += char
                i += 1
                continue
            
            # Not in string state
            if char == '{':
                # Start of a new object
                if len(self.stack) > 0 and self.stack[-1][1] is not None:
                    # This is a nested object, create a new object for the current key
                    current_obj, current_key = self.stack[-1]
                    new_obj = {}
                    current_obj[current_key] = new_obj
                    self.stack[-1] = (current_obj, None)
                    self.stack.append((new_obj, None))
                i += 1
            elif char == '}':
                # End of an object
                if len(self.stack) > 1:  # Don't pop the root object
                    self.stack.pop()
                i += 1
            elif char == '"':
                # Start of a string
                self.in_string = True
                # Determine if it's a key or value
                if self.stack[-1][1] is None and not self.expecting_colon:
                    self.expecting_colon = True
                i += 1
            elif char == ':':
                # Colon separator
                i += 1
            elif char == ',':
                # Comma separator
                i += 1
            elif char.isspace():
                # Skip whitespace
                i += 1
            else:
                # Unexpected character, just skip it
                i += 1
        
        # Handle partial string at the end
        if self.in_string and not self.expecting_colon:
            # We're in a string value, set it as partial value
            current_obj, current_key = self.stack[-1]
            if current_key is not None:
                current_obj[current_key] = self.current_string
        
        # Clear the buffer now that we've processed everything
        self.buffer = ""

# Test functions for Gradio
def test_complete_json(json_input):
    parser = StreamingJsonParser()
    parser.consume(json_input)
    result = parser.get()
    return json.dumps(result, indent=2)

def test_chunked_json(chunk1, chunk2):
    parser = StreamingJsonParser()
    parser.consume(chunk1)
    intermediate = json.dumps(parser.get(), indent=2)
    parser.consume(chunk2)
    final = json.dumps(parser.get(), indent=2)
    return f"After first chunk:\n{intermediate}\n\nAfter second chunk:\n{final}"

def test_partial_json(json_input):
    parser = StreamingJsonParser()
    parser.consume(json_input)
    result = parser.get()
    return json.dumps(result, indent=2)

def test_nested_json(json_input):
    parser = StreamingJsonParser()
    parser.consume(json_input)
    result = parser.get()
    return json.dumps(result, indent=2)

def run_all_tests():
    results = []
    
    # Test 1: Complete JSON
    parser = StreamingJsonParser()
    parser.consume('{"foo": "bar"}')
    expected = {"foo": "bar"}
    actual = parser.get()
    test_result = f"Test 1 - Complete JSON: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 2: Chunked JSON
    parser = StreamingJsonParser()
    parser.consume('{"foo":')
    parser.consume('"bar"}')
    expected = {"foo": "bar"}
    actual = parser.get()
    test_result = f"Test 2 - Chunked JSON: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 3: Partial JSON
    parser = StreamingJsonParser()
    parser.consume('{"foo": "bar')
    expected = {"foo": "bar"}
    actual = parser.get()
    test_result = f"Test 3 - Partial JSON: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 4: Nested JSON
    parser = StreamingJsonParser()
    parser.consume('{"outer": {"inner": "value"}}')
    expected = {"outer": {"inner": "value"}}
    actual = parser.get()
    test_result = f"Test 4 - Nested JSON: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 5: Incomplete Nested JSON
    parser = StreamingJsonParser()
    parser.consume('{"outer": {"inner": "value')
    expected = {"outer": {"inner": "value"}}
    actual = parser.get()
    test_result = f"Test 5 - Incomplete Nested JSON: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 6: Multiple Chunks
    parser = StreamingJsonParser()
    parser.consume('{"a": "b", "c":')
    parser.consume(' "d"}')
    expected = {"a": "b", "c": "d"}
    actual = parser.get()
    test_result = f"Test 6 - Multiple Chunks: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 7: Empty Input
    parser = StreamingJsonParser()
    expected = {}
    actual = parser.get()
    test_result = f"Test 7 - Empty Input: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    # Test 8: Partial Key Input
    parser = StreamingJsonParser()
    parser.consume('{"foo')
    expected = {}
    actual = parser.get()
    test_result = f"Test 8 - Partial Key Input: {'PASSED' if actual == expected else 'FAILED'}\n"
    test_result += f"Expected: {expected}\nActual: {actual}\n"
    results.append(test_result)
    
    return "\n".join(results)

def custom_parser_stream(json_input, chunk_size=0):
    parser = StreamingJsonParser()
    results = []
    
    if chunk_size <= 0:
        # Process all at once
        parser.consume(json_input)
        results.append(f"Processed full input: {json_input}")
        results.append(f"Result: {json.dumps(parser.get(), indent=2)}")
    else:
        # Process in chunks
        for i in range(0, len(json_input), chunk_size):
            chunk = json_input[i:i+chunk_size]
            parser.consume(chunk)
            results.append(f"Processed chunk: {chunk}")
            results.append(f"Intermediate result: {json.dumps(parser.get(), indent=2)}")
    
    return "\n".join(results)

# Interactive parser state for consume button
parser_state = StreamingJsonParser()

def reset_parser():
    global parser_state
    parser_state = StreamingJsonParser()
    return "Parser reset. Current state: {}"

def consume_chunk(chunk):
    global parser_state
    parser_state.consume(chunk)
    return f"Chunk consumed. Current state: {json.dumps(parser_state.get(), indent=2)}"

# Create Gradio interface
with gr.Blocks(title="Streaming JSON Parser") as demo:
    gr.Markdown("# Streaming JSON Parser")
    gr.Markdown("This interface demonstrates a streaming JSON parser that can handle partial and chunked JSON data.")
    
    with gr.Tab("Run All Tests"):
        run_tests_btn = gr.Button("Run All Tests")
        all_tests_output = gr.Textbox(label="Test Results", lines=25)
        run_tests_btn.click(run_all_tests, inputs=[], outputs=all_tests_output)
    
    with gr.Tab("Complete JSON Test"):
        complete_input = gr.Textbox(label="JSON Input", lines=5, value='{"foo": "bar"}')
        complete_test_btn = gr.Button("Test")
        complete_output = gr.Textbox(label="Parser Output", lines=10)
        complete_test_btn.click(test_complete_json, inputs=[complete_input], outputs=complete_output)
    
    with gr.Tab("Chunked JSON Test"):
        with gr.Row():
            chunk1_input = gr.Textbox(label="First Chunk", lines=3, value='{"foo":')
            chunk2_input = gr.Textbox(label="Second Chunk", lines=3, value='"bar"}')
        chunked_test_btn = gr.Button("Test Chunks")
        chunked_output = gr.Textbox(label="Parser Output", lines=15)
        chunked_test_btn.click(test_chunked_json, inputs=[chunk1_input, chunk2_input], outputs=chunked_output)
    
    with gr.Tab("Partial JSON Test"):
        partial_input = gr.Textbox(label="Partial JSON Input", lines=5, value='{"foo": "bar')
        partial_test_btn = gr.Button("Test")
        partial_output = gr.Textbox(label="Parser Output", lines=10)
        partial_test_btn.click(test_partial_json, inputs=[partial_input], outputs=partial_output)
    
    with gr.Tab("Nested JSON Test"):
        nested_input = gr.Textbox(label="Nested JSON Input", lines=5, value='{"outer": {"inner": "value"}}')
        nested_test_btn = gr.Button("Test")
        nested_output = gr.Textbox(label="Parser Output", lines=10)
        nested_test_btn.click(test_nested_json, inputs=[nested_input], outputs=nested_output)
    
    with gr.Tab("Custom Parser"):
        custom_input = gr.Textbox(label="JSON Input", lines=5, placeholder='{"example": "value"}')
        chunk_size = gr.Slider(minimum=0, maximum=20, value=0, step=1, label="Chunk Size (0 for all at once)")
        custom_test_btn = gr.Button("Parse")
        custom_output = gr.Textbox(label="Parser Output", lines=15)
        custom_test_btn.click(custom_parser_stream, inputs=[custom_input, chunk_size], outputs=custom_output)
    
    with gr.Tab("Interactive Parser"):
        gr.Markdown("This tab lets you incrementally consume chunks and see the parser state")
        reset_btn = gr.Button("Reset Parser")
        reset_output = gr.Textbox(label="Reset Result", value="Parser initialized. Current state: {}")
        reset_btn.click(reset_parser, inputs=[], outputs=reset_output)
        
        chunk_input = gr.Textbox(label="Chunk to Consume", lines=3, placeholder='{"foo": "')
        consume_btn = gr.Button("Consume Chunk")
        consume_output = gr.Textbox(label="Current Parser State", lines=10)
        consume_btn.click(consume_chunk, inputs=[chunk_input], outputs=consume_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)