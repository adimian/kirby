from kirby.proxy.decoder import decode_bytes, TEXT_ENCODING


def test_it_decodes_byte_value():
    starter_value = "Hello this is a text."
    encoded_value = starter_value.encode(TEXT_ENCODING)

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, str)
    assert result == starter_value


def test_it_decodes_byte_values():
    starter_value = ("This is", "a list")
    encoded_value = (b"This is", b"a list")

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, list)
    assert result == starter_value
