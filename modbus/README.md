# Modbus TCP Master (Python Socket)

## Overview

This project implements a **Modbus TCP Master (Client)** using Python's built-in `socket` library.
The program allows a user to send Modbus TCP requests to a Modbus slave device and display the response in a human-readable format.

The implementation manually constructs the **Modbus TCP frame**, including:

- MBAP (Modbus Application Protocol) Header
- PDU (Protocol Data Unit)

This code demonstrates how Modbus communication works at the **protocol level without using external Modbus libraries**.

---

## Features

- Socket-based Modbus TCP communication
- Interactive command-line interface
- Manual construction of Modbus TCP frames
- Supports common Modbus function codes
- Decodes and prints responses similar to packet analysis tools (e.g., Wireshark)

---

## Supported Modbus Function Codes

| Function Code | Description |
|---------------|-------------|
| 01 | Read Coil Status |
| 02 | Read Discrete Inputs |
| 03 | Read Holding Registers |
| 04 | Read Input Registers |
| 05 | Write Single Coil |
| 06 | Write Single Register |

---

## How It Works

### 1. User Input

The user selects:

- Function Code
- Register / Coil Address
- Quantity (for read operations)
- Value (for write operations)

The program validates inputs according to **Modbus protocol limits**.

---

### 2. Modbus TCP Frame Construction

A Modbus TCP packet consists of:

```
MODBUS TCP ADU
├── MBAP Header
│   ├── Transaction ID (2 bytes)
│   ├── Protocol ID (2 bytes)
│   ├── Length (2 bytes)
│   └── Unit ID (1 byte)
│
└── PDU
    ├── Function Code
    └── Data
```

The program builds these fields manually before sending them to the server.

---

### 3. Communication

The client connects to a Modbus server using TCP:

```
IP:   127.0.0.1
Port: 502
```

After sending the request, the response is received and decoded.

---

### 4. Response Decoding

The program parses the returned frame:

- MBAP header
- Function code
- Register / coil values

Example output:

```
Modbus/TCP Response:
Transaction Identifier: 1
Protocol Identifier: 0
Length: 7
Unit Identifier: 1

Modbus Response:
Function Code: 3 - Read Holding Registers
Byte Count: 4
Register 40001: 120
Register 40002: 350
```

---

## Requirements

- Python 3.x
- A Modbus TCP server or simulator (e.g., Modbus Slave)

---

## Notes

- Default connection settings:

```
Server IP: 127.0.0.1
Port: 502
Unit ID: 1
