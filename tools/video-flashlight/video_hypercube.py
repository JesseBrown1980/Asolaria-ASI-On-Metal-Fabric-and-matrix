#!/usr/bin/env python3
"""Exact four-floor video-feature hypercube: 64→256→1024→4096."""
from __future__ import annotations

import hashlib
import struct
import time
from typing import Any

import zstandard as zstd
from tokenizers import Tokenizer
from tokenizers import models as token_models
from tokenizers import pre_tokenizers
from tokenizers import trainers

TOKEN_CHARACTER_BASE = 0xE000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bytes_to_6bit(data: bytes) -> tuple[list[int], int]:
    tokens: list[int] = []
    accumulator = 0
    bits = 0
    for byte in data:
        accumulator = (accumulator << 8) | byte
        bits += 8
        while bits >= 6:
            bits -= 6
            tokens.append((accumulator >> bits) & 0x3F)
            accumulator &= (1 << bits) - 1 if bits else 0
    padding = 0
    if bits:
        padding = 6 - bits
        tokens.append((accumulator << padding) & 0x3F)
    return tokens, padding


def tokens6_to_bytes(tokens: list[int], padding: int, original_length: int) -> bytes:
    accumulator = 0
    bits = 0
    output = bytearray()
    for token in tokens:
        if not 0 <= token < 64:
            raise ValueError("non-L0 token")
        accumulator = (accumulator << 6) | token
        bits += 6
        while bits >= 8:
            bits -= 8
            output.append((accumulator >> bits) & 0xFF)
            accumulator &= (1 << bits) - 1 if bits else 0
    restored = bytes(output[:original_length])
    if len(restored) != original_length:
        raise ValueError("feature length mismatch")
    return restored


def floor_text(sequence: list[int], block_symbols: int = 256) -> str:
    characters = [chr(TOKEN_CHARACTER_BASE + token) for token in sequence]
    return " ".join(
        "".join(characters[index : index + block_symbols])
        for index in range(0, len(characters), block_symbols)
    )


def train_token_floor(
    sequence: list[int],
    input_vocabulary_size: int,
    output_cap: int,
    opportunities: int,
    name: str,
    block_symbols: int = 256,
) -> tuple[list[int], list[list[int]], dict[str, Any]]:
    if input_vocabulary_size <= 0 or input_vocabulary_size > 4096:
        raise ValueError("invalid input vocabulary size")
    if any(token < 0 or token >= input_vocabulary_size for token in sequence):
        raise ValueError("input token outside declared floor alphabet")

    target_vocabulary = min(output_cap, input_vocabulary_size + opportunities)
    text = floor_text(sequence, block_symbols)
    tokenizer = Tokenizer(token_models.BPE(unk_token=None))
    tokenizer.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
    trainer = trainers.BpeTrainer(
        vocab_size=target_vocabulary,
        min_frequency=2,
        show_progress=False,
        initial_alphabet=[
            chr(TOKEN_CHARACTER_BASE + index)
            for index in range(input_vocabulary_size)
        ],
        special_tokens=[],
    )
    started = time.perf_counter()
    tokenizer.train_from_iterator([text], trainer)
    training_seconds = time.perf_counter() - started
    encoding = tokenizer.encode(text, add_special_tokens=False)
    output_vocabulary_size = tokenizer.get_vocab_size()

    mappings: list[list[int]] = []
    for token_id in range(output_vocabulary_size):
        token_text = tokenizer.id_to_token(token_id)
        if token_text is None:
            raise ValueError(f"missing token definition {token_id}")
        expansion = [
            ord(character) - TOKEN_CHARACTER_BASE for character in token_text
        ]
        if not expansion or any(
            value < 0 or value >= input_vocabulary_size for value in expansion
        ):
            raise ValueError("floor token expansion leaves input alphabet")
        mappings.append(expansion)

    restored: list[int] = []
    for token_id in encoding.ids:
        restored.extend(mappings[token_id])
    if restored != sequence:
        raise AssertionError(f"{name}: token-floor inverse mismatch")

    accepted = output_vocabulary_size - input_vocabulary_size
    if accepted < 0 or accepted > opportunities:
        raise AssertionError("invalid accepted-refinement count")
    trace = {
        "transition": name,
        "input_vocab_size": input_vocabulary_size,
        "output_cap": output_cap,
        "target_vocab_size": target_vocabulary,
        "output_vocab_size": output_vocabulary_size,
        "opportunities": opportunities,
        "accepted": accepted,
        "held": opportunities - accepted,
        "input_tokens": len(sequence),
        "output_tokens": len(encoding.ids),
        "mapping_units": sum(len(mapping) for mapping in mappings),
        "block_symbols": block_symbols,
        "train_s": training_seconds,
    }
    return list(encoding.ids), mappings, trace


def hypercube_encode(
    data: bytes, opportunities: int = 800
) -> tuple[dict[str, Any], bytes, bytes, list[list[list[int]]]]:
    sequence, padding = bytes_to_6bit(data)
    floors = [64, 256, 1024, 4096]
    all_mappings: list[list[list[int]]] = []
    traces: list[dict[str, Any]] = []
    current_vocabulary = 64

    for transition_index, output_cap in enumerate(floors[1:], start=1):
        name = (
            f"L{transition_index - 1}_{floors[transition_index - 1]}"
            f"_TO_L{transition_index}_{output_cap}"
        )
        sequence, mappings, trace = train_token_floor(
            sequence,
            current_vocabulary,
            output_cap,
            opportunities,
            name,
        )
        current_vocabulary = trace["output_vocab_size"]
        all_mappings.append(mappings)
        traces.append(trace)

    catalog = bytearray(b"VHC2")
    catalog.extend(struct.pack(">QBB", len(data), padding, len(all_mappings)))
    input_vocabulary = 64
    for output_cap, mappings in zip(floors[1:], all_mappings):
        catalog.extend(
            struct.pack(
                ">HHHH",
                input_vocabulary,
                output_cap,
                len(mappings),
                opportunities,
            )
        )
        for mapping in mappings:
            if len(mapping) > 65535:
                raise ValueError("floor mapping too long")
            catalog.extend(struct.pack(">H", len(mapping)))
            for token in mapping:
                catalog.extend(struct.pack(">H", token))
        input_vocabulary = len(mappings)

    packed = (
        struct.pack(">" + ("H" * len(sequence)), *sequence) if sequence else b""
    )
    payload = zstd.ZstdCompressor(level=19).compress(packed)

    raw = zstd.ZstdDecompressor().decompress(
        payload, max_output_size=len(sequence) * 2
    )
    decoded = (
        list(struct.unpack(">" + ("H" * len(sequence)), raw))
        if sequence
        else []
    )
    for mappings in reversed(all_mappings):
        previous: list[int] = []
        for token_id in decoded:
            previous.extend(mappings[token_id])
        decoded = previous
    restored = tokens6_to_bytes(decoded, padding, len(data))
    if restored != data:
        raise AssertionError("hypercube feature restore mismatch")

    result = {
        "schema": "VIDEO-HYPERCUBE-64-256-1024-4096-v2",
        "raw_feature_bytes": len(data),
        "raw_feature_sha256": sha256_bytes(data),
        "floors": floors,
        "transitions": traces,
        "opportunities_per_transition": opportunities,
        "total_refinement_opportunities": opportunities * 3,
        "catalog_bytes": len(catalog),
        "payload_bytes": len(payload),
        "total_bytes": len(catalog) + len(payload),
        "bpc": (len(catalog) + len(payload)) * 8 / max(1, len(data)),
        "token_count": len(sequence),
        "max_token": max(sequence, default=0),
        "restore": True,
        "catalog_sha256": sha256_bytes(bytes(catalog)),
        "payload_sha256": sha256_bytes(payload),
        "training_engine": "HUGGINGFACE_TOKENIZERS_RUST_BPE_BOUNDED_BLOCKS",
    }
    return result, bytes(catalog), payload, all_mappings
