""" Tool for parsing, decoding, and analyzing Profibus-DP/UART frames and telegrams."""

FRAME_LEN = 11

EXAMPLE_SD1 = "0 00001000 11 0 10000000 11 0 01000000 11 0 11000000 01 0 01100000 01 0 01101000 11"

EXAMPLE_SD2 = ("0 00010110 11 0 11100000 11 0 11100000 11 0 00010110 11 0 11111111 01"
               "0 10000001 01 0 01100010 11 0 01011100 01 0 01111100 11 0 00000000 01"
               "0 00000000 01 0 01111100 11 0 01101000 11")

EXAMPLE_SD3 = "0 01000101 11 0 10000000 11 0 01000000 11 0 11000000 01 0 10101010 01 0 11011010 11 0 01101000 11"

EXAMPLE_SD4 =  "0 00111011 11 0 10000000 11 0 01000000 11"


EXAMPLE_STR1 = EXAMPLE_SD1 + "0000"+ EXAMPLE_SD2 + "0000"
EXAMPLE_STR2 = EXAMPLE_SD3 + "000" + EXAMPLE_SD4

def parse_frame(frame):
    """
    Parse a single Profibus/UART frame.
    UART frame structure:
        - 1 Start bit (always 0)
        - 8 Data bits (LSB first)
        - 1 Parity bit
        - 1 Stop bit (always 1)
    Returns:
        dict: Parsed frame data
    """

    # Validate frame length
    if len(frame) != FRAME_LEN:
        return None

    start_bit = frame[0]
    data_bits = frame[1:9]
    parity_bit = frame[9]
    stop_bit = frame[10]

    # Reverse the databits (LSB → MSB)
    data_bits_reversed = data_bits[::-1]

    # Parity check
    ones = data_bits.count("1") + int(parity_bit)
    parity_ok = (ones % 2 == 0)

    return {
        "data": int(data_bits_reversed, 2),
        "parity_ok": parity_ok,
        "start_ok": start_bit == "0",
        "stop_ok": stop_bit == "1",
    }


def decode_bytes(bitstream):
    """
    Decodes a bitstream to bytes with automatic re-alignment.
    Auto alignment makes it possible to decode multiple telegrams from a single bitstream.

    Methodology:
        - Find the best offset
        - Decode the telegram
        - After decoding, find the offset for the next telegram

    Returns:
        list of decoded bytes
    """

    i = 0
    decoded_bytes = []

    # Iterate over the whole bitstream
    while i < len(bitstream) - FRAME_LEN:

        best_offset = None
        best_score = -1
        best_decoded = []

        # Find the best offset/alignment
        for offset in range(FRAME_LEN):

            start = i + offset

            # Select 10 frames
            chunk = bitstream[start:start + FRAME_LEN * 10]

            valid = 0  # Number of valid frames
            invalid = 0 # Number of invalid frames
            j = 0

            # Parse all frames in the chunk
            while j + FRAME_LEN <= len(chunk):
                frame = chunk[j:j + FRAME_LEN]
                result = parse_frame(frame)

                # Check if frame follows UART encoding rules
                if result and result["parity_ok"] and result["start_ok"] and result["stop_ok"]:
                    valid += 1
                else:
                    invalid += 1

                j += FRAME_LEN

            score = valid - invalid

            # Store the best alignment
            if score > best_score:
                best_score = score
                best_offset = offset

        # If no valid frames found, move to the next bit and try again
        if best_score <= 0:
            i += 1
            continue

        # Use the best alignment to decode the telegram --->
        i += best_offset

        # Decode the telegram
        while i + FRAME_LEN <= len(bitstream):
            frame = bitstream[i:i + FRAME_LEN]
            result = parse_frame(frame)

            # Check if the frame is valid
            if result and result["parity_ok"] and result["start_ok"] and result["stop_ok"]:
                decoded_bytes.append(result["data"])
                i += FRAME_LEN
            else:
                # If an invalid frame is found, try to find a new best alignment
                i += 1
                break

    return decoded_bytes


def extract_telegrams(byte_stream):
    """
    Extract valid Profibus telegrams from bytes
    Scans the bytes for valid telegram start delimiters and extracts the telegrams.

    returns:
        list of byte arrays: list of telegrams
    """

    telegrams = []
    i = 0
    synced = False

    # Iterate over the byte stream
    while i < len(byte_stream):

        byte = byte_stream[i]

        # Search for a valid start delimiter
        if not synced:
            if byte in (0x68, 0x10, 0xDC, 0xA2, 0xEC):
                # print(f"Found start delimiter: {byte:02X}")
                synced = True
            else:
                i += 1
                continue

        # Start delimiter 1
        if byte == 0x10:
            frame_len = 6

            # Make sure the frame is long enough
            if i + frame_len <= len(byte_stream):
                frame = byte_stream[i:i + frame_len]

                # Check end delimiter and append the frame
                if frame[-1] == 0x16:
                    telegrams.append(frame)
                    i += frame_len
                    continue

        # Start delimiter 2
        elif byte == 0x68:
            if i + 3 >= len(byte_stream):
                break

            length = byte_stream[i + 1]

            if length < 3 or length > 249:
                i += 1
                continue

            frame_len = length + 6

            # Make sure the frame is long enough
            if i + frame_len <= len(byte_stream):
                frame = byte_stream[i:i + frame_len]

                # Check end delimiter and append the frame
                if frame[-1] == 0x16:
                    telegrams.append(frame)
                    i += frame_len
                    continue

        # Start delimiter 3
        elif byte == 0xA2:
            frame_len = 7

            # Make sure the frame is long enough
            if i + frame_len <= len(byte_stream):
                frame = byte_stream[i:i + frame_len]

                # Check end delimiter and append the frame
                if frame[-1] == 0x16:
                    telegrams.append(frame)
                    i += frame_len
                    continue

        # Start delimiter 4
        elif byte == 0xDC:
            frame_len = 3

            # Make sure the frame is long enough and append the frame
            if i + frame_len <= len(byte_stream):
                frame = byte_stream[i:i + frame_len]
                telegrams.append(frame)
                i += frame_len
                continue

        # Search for a new start delimiter
        synced = False
        #print("Not synced")
        i += 1

    return telegrams


def print_sd1(decoded):
    """
    Print a decoded SD1 telegram in a human-readable format.
    Check that the decoded Frame Check Sequence matches the decoded Frame Check Sequence.
    """

    print("Telegram without data field")
    print(f"Start delimiter: {decoded[0]:02X}")
    print(f"Destination address: {decoded[1]:02X}")
    print(f"Source address: {decoded[2]:02X}")
    print(f"Function code: {format(decoded[3], '08b')[::-1]} (LSB first)")
    print(f"Frame Check Sequence: {decoded[4]:02X}")
    print(f"End delimiter: {decoded[5]:02X}")

    fcs_valid = (decoded[4] == ((decoded[1] + decoded[2] + decoded[3]) & 0xFF))
    print(f"FCS valid: {fcs_valid}")


def print_sd2(decoded):
    """
    Print a decoded SD2 telegram in a human-readable format.
    Check validity with is_valid_sd2.
    """

    print("Type: Telegram with variable length")
    print(f"Start delimiter: {decoded[0]:02X}")
    print(f"Length: {decoded[1]:02X}")
    print(f"Length (repeated): {decoded[2]:02X}")
    print(f"Start delimiter (repeated): {decoded[3]:02X}")
    print(f"Destination address: {decoded[4]:02X}")
    print(f"Source address: {decoded[5]:02X}")
    print(f"Function code: {format(decoded[6], '08b')[::-1]} (LSB first)")
    print(f"Destination Service Access Point (DSAP): {decoded[7]:02X}")
    print(f"Source Service Access Point (SSAP): {decoded[8]:02X}")

    # Print data unit
    for i in range(9, len(decoded) - 2):
        print(f"Data {i - 9}: {decoded[i]:02X}")

    print(f"Frame Check Sequence: {decoded[-2]:02X}")
    print(f"End delimiter: {decoded[-1]:02X}")

    # Print validity
    validity = is_valid_sd2(decoded)
    print(f"Valid: {validity}")


def print_sd3(decoded):
    """
    Print a decoded SD3 telegram in a human-readable format.
    Check that the decoded Frame Check Sequence matches the decoded Frame Check Sequence.
    """

    print("Telegram with fixed data length")
    print(f"Start delimiter: {decoded[0]:02X}")
    print(f"Destination address: {decoded[1]:02X}")
    print(f"Source address: {decoded[2]:02X}")
    print(f"Function code: {format(decoded[3], '08b')[::-1]} (LSB first)")
    print(f"PDU: {decoded[4]:02X}")
    print(f"Frame Check Sequence: {decoded[5]:02X}")
    print(f"End delimiter: {decoded[6]:02X}")

    fcs_valid = (decoded[5] == ((decoded[1] + decoded[2] + decoded[3] + decoded[4]) & 0xFF))
    print(f"FCS valid: {fcs_valid}")


def print_sd4(decoded):
    """
    Print a decoded SD4 telegram in a human-readable format.
    Check that the decoded Frame Check Sequence matches the decoded Frame Check Sequence.
    """

    print("Token telegram")
    print(f"Start delimiter: {decoded[0]:02X}")
    print(f"Destination address: {decoded[1]:02X}")
    print(f"Source address: {decoded[2]:02X}")


def is_valid_sd2(decoded):
    """
    Validate the structure of a sd2 telegram based on the decoded bytes.

    returns:
        bool: True if the telegram is valid, False otherwise
    """

    # Check repeated length
    if decoded[1] != decoded[2]:
        print("Repeated length does not match")
        return False

    # Check repeated start delimiter
    if decoded[3] != 0x68:
        print("Repeated start delimiter does not match")
        return False

    computed_fcs = sum(decoded[4:-2]) & 0xFF
    decoded_fcs = decoded[-2]

    if computed_fcs != decoded_fcs:
        print(f"Invalid FCS: computed={computed_fcs:02X}, received={decoded_fcs:02X}")
        return False

    return True


def main():

    print("Profibus Telegram Decoder")
    input_telegram = input("Enter raw bitstream (or give '1' for example1, '2' for example2): ")

    # Use an example bitstream or user input
    if input_telegram == "1":
        telegram = EXAMPLE_STR1
    elif input_telegram == "2":
        telegram = EXAMPLE_STR2
    else:
        telegram = input_telegram

    telegram = telegram.replace(" ", "")

    print("\nRaw bitstream:", telegram)

    bytes = decode_bytes(telegram)

    if not bytes:
        print("No valid data decoded")
        return

    # Print the extracted bytes
    print(f"\nDecoded {len(bytes)} bytes:")
    print(" ".join(f"{b:02X}" for b in bytes))

    telegrams = extract_telegrams(bytes)

    print(f"\nFound {len(telegrams)} telegram(s)")

    # Print the extracted telegrams
    for i, telegram in enumerate(telegrams):
        print(f"\nTelegram {i+1}")

        # SD1 telegram
        if telegram[0] == 0x10:
            print_sd1(telegram)

        # SD2 telegram
        elif telegram[0] == 0x68:
            print_sd2(telegram)

        # SD3 telegram
        elif telegram[0] == 0xA2:
            print_sd3(telegram)

        # SD4 telegram
        elif telegram[0] == 0xDC:
            print_sd4(telegram)

        else:
            print("Unknown telegram:")
            print(" ".join(f"{b:02X}" for b in telegram))


if __name__ == "__main__":
    main()
