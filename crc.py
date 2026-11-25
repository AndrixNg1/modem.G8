"""CRC-16/CCITT-FALSE : poly 0x1021, init 0xFFFF, sans réflexion ni XOR final."""


def crc16_ccitt(donnees: bytes, init=0xFFFF) -> int:
    crc = init & 0xFFFF
    for octet in donnees:
        crc ^= octet << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


if __name__ == '__main__':
    resultat = crc16_ccitt(b'123456789')
    print(f'CRC("123456789") = 0x{resultat:04X}')
    assert resultat == 0x29B1
