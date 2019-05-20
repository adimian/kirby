from smart_getenv import getenv


TEXT_ENCODING = getenv("TEXT_ENCODING", type=str)


def decode_bytes(value):
    if isinstance(value, bytes):
        return value.decode(TEXT_ENCODING)

    elif isinstance(value, list):
        decoded_values = []

        for val in value:
            decoded_values.append(decode_bytes(val))

        return decoded_values

    return value
