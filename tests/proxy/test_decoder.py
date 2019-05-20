from kirby.proxy.decoder import decode_bytes, TEXT_ENCODING


def test_it_decodes_text():
    finish_value = "Hello this is a text."
    encoded_value = finish_value.encode(TEXT_ENCODING)

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, str)
    assert result == finish_value


def test_it_decodes_list():
    finish_value = ["This is", "a list"]
    encoded_value = [b"This is", b"a list"]

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, list)
    for r in result:
        assert isinstance(r, str)
    assert result == finish_value


def test_it_decodes_list_with_decoded_entry():
    finish_value = ["This is", "not all", "encoded."]
    encoded_value = [b"This is", b"not all", "encoded."]

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, list)
    for r in result:
        assert isinstance(r, str)
    assert result == finish_value


def test_it_decodes_list_in_list():
    finish_value = [["This is", "all"], "encoded."]
    encoded_value = [[b"This is", b"all"], b"encoded."]

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, list)
    assert isinstance(result[0], list)
    assert isinstance(result[0][0], str)

    assert result == finish_value


def test_it_returns_original_value_if_not_supported():
    finish_value = ["This is", "not all", {"thingy": "majiggy"}]
    encoded_value = [b"This is", b"not all", {"thingy": "majiggy"}]

    result = decode_bytes(encoded_value)

    assert encoded_value != result
    assert isinstance(result, list)
    assert isinstance(result[2], dict)

    assert result == finish_value
