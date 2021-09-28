from construct import (
	Struct, BitStruct,
	Byte, Bytes,
	Int8ul, Int16ul, Int32ul, Int64ul,
	Flag, Const, PaddedString
)

Superblock = Struct(
    'magic' / Const(b"##"),
    'blocks_count' / Int32ul,
    'free_blocks_count' / Int32ul,
    'first_free_block' / Int32ul,
    'first_data_block' / Int32ul,
    'block_size' / Int32ul,
    'unused' / Bytes(10)
) # Total - 32 bytes

Block = Struct(
    'data' / Bytes(1020),
    'next' / Int32ul
) # Total - 1024 bytes (2 setores de 512 bytes)

Entry = Struct(
    'name' / Bytes(23),
    'attribute' / Bytes(1),
    'block_location' / Int32ul,
    'size' / Int32ul
) # Total - 32 bytes