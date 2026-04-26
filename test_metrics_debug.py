#!/usr/bin/env python3
"""Debug metrics behavior"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import json
from domain.services.streaming_response import StreamingResponse

response = StreamingResponse()

chunks = [
    {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}},
    {"contentBlockDelta": {"delta": {"text": " world"}, "contentBlockIndex": 1}},
]

event_stream = []
for chunk_data in chunks:
    chunk_bytes = json.dumps(chunk_data).encode("utf-8")
    event_stream.append({"chunk": {"bytes": chunk_bytes}})

tokens = list(response.stream_tokens(event_stream))

print(f"Token 0: '{tokens[0][0]}', count={tokens[0][1].token_count}, id={id(tokens[0][1])}")
print(f"Token 1: '{tokens[1][0]}', count={tokens[1][1].token_count}, id={id(tokens[1][1])}")
print(f"Same object? {tokens[0][1] is tokens[1][1]}")
