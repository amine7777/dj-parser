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


# Test Cases
def test_streaming_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{"foo": "bar"}')
    assert parser.get() == {"foo": "bar"}, f"Got {parser.get()}"
    print("test_streaming_json_parser passed!")

def test_chunked_streaming_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{"foo":')
    parser.consume('"bar"}')
    assert parser.get() == {"foo": "bar"}, f"Got {parser.get()}"
    print("test_chunked_streaming_json_parser passed!")

def test_partial_streaming_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{"foo": "bar')
    assert parser.get() == {"foo": "bar"}, f"Got {parser.get()}"
    print("test_partial_streaming_json_parser passed!")

def test_nested_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{"outer": {"inner": "value"}}')
    assert parser.get() == {"outer": {"inner": "value"}}, f"Got {parser.get()}"
    print("test_nested_json_parser passed!")

def test_incomplete_nested_json():
    parser = StreamingJsonParser()
    parser.consume('{"outer": {"inner": "value')
    assert parser.get() == {"outer": {"inner": "value"}}, f"Got {parser.get()}"
    print("test_incomplete_nested_json passed!")

def test_multiple_chunks():
    parser = StreamingJsonParser()
    parser.consume('{"a": "b", "c":')
    parser.consume(' "d"}')
    assert parser.get() == {"a": "b", "c": "d"}, f"Got {parser.get()}"
    print("test_multiple_chunks passed!")

def test_mixed_chunk_order():
    parser = StreamingJsonParser()
    parser.consume('{"key1": "val1", "key2":')
    parser.consume(' "val2", "key3": "val3"}')
    assert parser.get() == {"key1": "val1", "key2": "val2", "key3": "val3"}, f"Got {parser.get()}"
    print("test_mixed_chunk_order passed!")

def test_empty_input():
    parser = StreamingJsonParser()
    assert parser.get() == {}, f"Got {parser.get()}"
    print("test_empty_input passed!")

def test_partial_key_input():
    parser = StreamingJsonParser()
    parser.consume('{"foo')
    assert parser.get() == {}, f"Got {parser.get()}"
    print("test_partial_key_input passed!")

if __name__ == "__main__":
    try:
        test_streaming_json_parser()
        test_chunked_streaming_json_parser()
        test_partial_streaming_json_parser()
        test_nested_json_parser()
        test_incomplete_nested_json()
        test_multiple_chunks()
        test_mixed_chunk_order()
        test_empty_input()
        test_partial_key_input()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")