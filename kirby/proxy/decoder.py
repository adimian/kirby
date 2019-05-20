from smart_getenv import getenv


TEXT_ENCODING = getenv("TEXT_ENCODING", type=str)


def decode_bytes(value):
    if isinstance(value, bytes):
        return value.decode(TEXT_ENCODING)

    elif isinstance(value, list):
        decoded_value = []

        for val in value:
            if isinstance(val, bytes):
                val = val.decode(TEXT_ENCODING)
            decoded_value.append(val)

        return decoded_value

    return value
