"""
Modbus TCP Master using socket library in Python.
"""

import socket


FUNCTION_CODES = {
    '01': 'Read Coil Status',
    '02': 'Read Discrete Inputs',
    '03': 'Read Holding Registers',
    '04': 'Read Input Registers',
    '05': 'Write Single Coil',
    '06': 'Write Single Register'
}

# References to convert address to PLC address
REFERENCES = {
    '01': '0',
    '02': '1',
    '03': '4',
    '04': '3',
    '05': '0',
    '06': '4'
}


def get_user_input():
    """
    Gets user input for function code, register address, quantity and value.
    Handles validation and prints the PLC-style address for clarity.
    :return: function_code, register_address, (quantity), (value)
    """

    # Display available function codes
    print("\nAvailable Function Codes:")
    for key, value in FUNCTION_CODES.items():
        print(f"{key}: {value}")

    # Get function code from user
    while True:
        function_code = input("Select Function Code: ")

        if function_code in FUNCTION_CODES:
            break
        print("Unsupported Function Code")

    # Get Register Number/address
    while True:
        register_address = int(input("\nEnter Register Number / Data Address: "))

        # Limit to 16-bit unsigned integer
        if 0 <= register_address <= 65535:
            break
        print("Register Number must be between 0 and 65535")

    # Convert Register Number to PLC Address and print to user
    plc_address = 0
    if len(str(register_address)) < 5:
        if REFERENCES[function_code] == '0':
            plc_address = "0" + str(register_address + 1).zfill(4)
        else:
            plc_address = register_address
            plc_address += int(REFERENCES[function_code]) * 10000 + 1

    print(f"Target PLC Address: {plc_address}")

    # Get Quantity of Registers/Coils
    while True:

        # For write functions, quantity is always 1 because only single write is supported
        if function_code in ['05', '06']:
            quantity = 1
            break

        quantity = int(input("\nEnter Quantity of Registers/Coils: "))

        # Limit quantity to 1-125 (Modbus protocol limit)
        if 1 <= quantity <= 125:
            break
        print("Quantity must be between 1 and 125")

    # Get value for write functions
    value = 0

    # For write coil (05)
    if function_code == '05':
        while True:
            value = int(input("\nEnter New Value of Coil (1 or 0): "))
            if value in [0, 1]:
                break
            print("Value must be 1 or 0")

    # For write register (06)
    elif function_code == '06':
        while True:
            value = int(input("\nEnter New Value of Register (-32767 - +32767): "))

            # Limit value to -32767 - +32767 (16-bit signed integer)
            if -32767 <= value <= 32767:
                break
            print("Value must be between -32767 and +32767")

    return function_code, register_address, quantity, value


def send_modbus_request(function_code, register_address, quantity, value):
    """
    Builds and sends Modbus TCP request through socket connection to Modbus slave.
    Modbus TCP/IP ADU = MBAP header + PDU = MBAP header + Function code + data.

    :param function_code: string
    :param register_address: int
    :param quantity: int
    :param value: int
    :return: None
    """

    # Modbus slave server
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 502

    # PDU construction --->
    pdu = bytearray()

    # Adding function code to PDU
    pdu.append(int(function_code))

    # Adding register address to PDU
    pdu += register_address.to_bytes(2, byteorder='big')

    # Adding quantity to PDU for read functions FC(01, 02, 03, 04)
    if function_code in ['01', '02', '03', '04']:
        pdu += quantity.to_bytes(2, byteorder='big')

    # Adding coil value to PDU (only FC 05)
    elif function_code == '05':
        if value == 1:
            coil_value = 0xFF00
        else:
            coil_value = 0x0000
        pdu += coil_value.to_bytes(2, byteorder='big')

    # Adding new register value to PDU (only FC 06)
    elif function_code == '06':
        pdu += value.to_bytes(2, byteorder='big', signed=True)

    # MBAP header construction --->

    # Transaction identifier can be set any value. We used 1.
    transaction_id = 1
    # Protocol identifier is always 0 for Modbus TCP
    protocol_id = 0
    # Unit identifier is used to identify the slave device. Modbus slave uses 1 by default.
    unit_id = 1

    mbap = bytearray()
    mbap += transaction_id.to_bytes(2, byteorder='big')
    mbap += protocol_id.to_bytes(2, byteorder='big')

    length = len(pdu) + 1  # PDU + Unit identifier
    mbap += length.to_bytes(2, byteorder='big')
    mbap.append(unit_id)

    # Complete MODBUS TCP data packet
    request_frame = mbap + pdu

    # Send request with socket and receive response
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        s.sendall(request_frame)
        response = s.recv(260)

    print_response(response, register_address, quantity)
    return


def print_response(response, register_address, quantity):
    """
    Prints the Modbus TCP response in a similar format to wireshark.
    Decodes MBAP header and PDU based on the function code.
    :param response: bytes
    :param register_address: int
    :param quantity: int
    :return: None
    """

    # MBAP header
    transaction_id = int.from_bytes(response[0:2], 'big')
    protocol_id = int.from_bytes(response[2:4], 'big')
    length = int.from_bytes(response[4:6], 'big')
    unit_id = response[6]

    # PDU
    response_function_code = response[7]  # "1", "2"
    str_function_code = "0" + str(response_function_code) # "01", "02"

    print("\nModbus/TCP Response:")
    print(f"Transaction Identifier: {transaction_id}")
    print(f"Protocol Identifier: {protocol_id}")
    print(f"Length: {length}")
    print(f"Unit Identifier: {unit_id}")

    print("\nModbus Response:")
    print(f"Function Code: {response_function_code} - {FUNCTION_CODES[str_function_code]}")

    # Decode based on function code
    if function_code in ['01', '02']:
        byte_count = response[8]
        print(f"Byte Count: {byte_count}")

        # Print each bit
        data = response[9:9 + byte_count]
        for i in range(quantity):
            bit = (data[i // 8] >> (i % 8)) & 1
            print(f"Bit {register_address + i} : {bit}")

    elif function_code in ['03', '04']:
        byte_count = response[8]
        print(f"Byte Count: {byte_count}")
        registers = []

        for i in range(0, byte_count, 2):
            reg = int.from_bytes(response[9+i:11+i], 'big', signed=True)
            registers.append(reg)
        for i, reg in enumerate(registers):
            print(f"Register {register_address + i}: {reg}")

    elif function_code == '05':
        ref_number = int.from_bytes(response[8:10], 'big')
        value = response[10:12]
        print(f"Reference Number: {ref_number}")
        print(f"Data: {value.hex()}")

    elif function_code =='06':
        ref_number = int.from_bytes(response[8:10], 'big')
        value = int.from_bytes(response[10:12], 'big', signed=True)
        print(f"Reference Number: {ref_number}")
        print(f"Register {ref_number}: {value}")
    return


if __name__ == "__main__":
    print("Python Modbus TCP Master")
    function_code, register_address, quantity, value = get_user_input()
    send_modbus_request(function_code, register_address, quantity, value)