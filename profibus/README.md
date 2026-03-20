# PROFIBUS-DP Telegram Decoder

A Python tool for decoding raw PROFIBUS-DP bitstreams captured from an oscilloscope into readable telegrams.

---

## Features

- Decodes raw bitstreams (Directly from oscilloscope)
- Automatic alignment detection
- Adaptive decoding with re-synchronization on errors
- Supports multiple telegrams in one stream
- FCS and message integrity validation

---

## Supported Telegram Types

| Type | Description                  |
|------|------------------------------|
| SD1  | Short frame (no data field)  |
| SD2  | Variable length frame        |
| SD3  | Fixed length frame           |
| SD4  | Token telegram               |

---

## How it works

1. The raw bitstream is split into UART frames:

   [start][8 data bits][parity][stop]

2. The decoder:
   - Detects correct bit alignment
   - Validates parity, start and stop bits

3. The extractor:
   - Synchronizes on PROFIBUS start delimiters:
     - 0x68, 0x10, 0xA2, 0xDC, 0xEC
   - Builds telegrams based on known structure

---

## Usage

Enter raw bitstream (or give '1' for example1, '2' for example2):

Spaces in the input are ignored.

---

## Example Output

```
Decoded 10 bytes:
A2 01 02 03 55 5B 16 DC 01 02

Found 2 telegram(s)

Telegram 1
Telegram with fixed data length
Start delimiter: A2
Destination address: 01
Source address: 02
Function code: 11000000 (LSB first)
PDU: 55
Frame Check Sequence: 5B
End delimiter: 16
FCS valid: True

Telegram 2
Token telegram
Start delimiter: DC
Destination address: 01
Source address: 02
```

---

## How to read bits from an oscilloscope screen

1. Zoom in until individual spike periods are clearly visible
   
2. Start from a falling edge (start bit)

3. Use the time grid or cursors to determine the spike width/time and calculate bit amount (one bit transmit time (s) = 1 / baudrate)

4. Write down the value at each sample point:
   - Low → 0
   - High → 1

Example shown in **Profibus_bitstream_example.PNG**

---

## Note

This is not a perfect or production-ready decoder.

- Intended for debugging and learning purposes
- Works best on short captures
- Can usually handle a few telegrams at a time in one stream

---

