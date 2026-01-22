from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
import argparse
import time
import msvcrt  # For Windows keyboard input detection

parser = argparse.ArgumentParser(description="Start Modbus TCP client.")

parser.add_argument('--ip', '-ip', required=False, help='IP')
parser.add_argument('--operation', '-o', required=False, help='Operation')
parser.add_argument('--address', '-a', required=False, help='Address')
parser.add_argument('--unit_id', '-id', required=False, help='Unit ID')
parser.add_argument('--datatype', '-dt', required=False, help='Datatype')
parser.add_argument('--scale', '-s', required=False, help='Scale factor')
parser.add_argument('--endianess', '-e', required=False, help='Endianess')

args = parser.parse_args()

# UTILS FUNCTIONS

def get_datatype_code(datatype_nr):
    datatype_map = {
        1 : ModbusTcpClient.DATATYPE.INT16,
        2 : ModbusTcpClient.DATATYPE.UINT16,
        3 : ModbusTcpClient.DATATYPE.INT32,
        4 : ModbusTcpClient.DATATYPE.UINT32,
        5 : ModbusTcpClient.DATATYPE.FLOAT32,
        6 : ModbusTcpClient.DATATYPE.FLOAT64,
    }
    return datatype_map.get(datatype_nr, ModbusTcpClient.DATATYPE.INT16)

def get_register_count(datatype_nr):
    register_count_map = {
        1 : 1,
        2 : 1,
        3 : 2,
        4 : 2,
        5 : 2,
        6 : 4,
    }
    return register_count_map.get(datatype_nr, 1)

def translate_operation_code(op):
    operation_map = {
        1: "Read Coils",
        2: "Read Input Registers",
        3: "Write Single Register (FC 0x06)",
        4: "Write Multiple Registers (FC 0x10)",
        5: "Read Holding Registers"
    }
    return operation_map.get(op, "Unknown Operation")

def setup_register_info(clear=False):
    global operation, address, datatype, scale, endianess, id, register_count

    print("\n" + "="*40)
    print("REGISTER SETUP")
    print("-"*40)

    print("\n" + "="*40)
    id = int(input('Enter the unit id (slave id): ').strip())

    print("\n" + "="*40)
    print("Choose Modbus Operation:")
    print("-"*40)
    print("1. Read Coils")
    print("2. Read Input Registers")
    print("3. Write Single Register (FC 0x06)")
    print("4. Write Multiple Registers (FC 0x10)")
    print("5. Read Holding Registers")
    print("-"*40)
    operation = int(input("Enter choice (1-5): ").strip())

    print("\n" + "="*40)
    address = int(input("Enter address: ").strip())


    print("\n" + "="*40)
    print("Choose datatype:")
    print("-"*40)
    print("1. int16")
    print("2. uint16")
    print("3. int32")
    print("4. uint32")
    print("5. float32")
    print("6. float64")
    print("-"*40)
    datatype_input = int(input("Enter choice datatype (1-6): ").strip())
    datatype = get_datatype_code(datatype_input)

    register_count = get_register_count(datatype_input)

    print("\n" + "="*40)
    scale = float(input("Enter scale factor: ").strip())

    print("\n" + "="*40)
    print("Choose endianess:")
    print("-"*40)
    print("1. Word: Big Endian")
    print("2. Word: Little Endian")
    print("-"*40)
    endianess = int(input("Enter choice endianess (1-2): ").strip())
    if endianess == 1:
        endianess = Endian.BIG
    elif endianess == 2:
        endianess = Endian.LITTLE
    else:
        print("Invalid endianess choice, defaulting to big endian.")
        endianess = Endian.BIG

def translate_exception_code(code):
    exception_map = {
        1: "Illegal Function",
        2: "Illegal Data Address",
        3: "Illegal Data Value",
        4: "Slave Device Failure",
        5: "Acknowledge",
        6: "Slave Device Busy",
        8: "Memory Parity Error",
        10: "Gateway Path Unavailable",
        11: "Gateway Target Device Failed to Respond"
    }
    return exception_map.get(code, "Unknown Exception Code")

# BEGIN

if args.ip:
    ip = args.ip
else:
    print("\n" + "="*40)
    ip = input('Enter the IP address of the server (slave): ').strip()

# TODO: add support for other framers (rtu, ascii)

client = ModbusTcpClient(
    host=ip,
    port=502,
    # framer='rtu',
)

# Check connection
connected = False
print("\n")
print(f'Connecting with {ip}...')
while not connected:
    time.sleep(1)
    connected = client.connect()

print(" ")
print(f"CONNECTED :D")
# print("-"*40)
print("\n")

if args.operation:
    operation = int(args.operation)
else:
    operation = None

if args.address:
    address = int(args.address)
else:
    address = None

if args.unit_id:
    id = int(args.unit_id)
else:
    id = None

if args.datatype:
    datatype = get_datatype_code(int(args.datatype))
else:
    datatype = None

if args.scale:
    scale = float(args.scale)
else:
    scale = None

if args.endianess:
    endianess = int(args.endianess)
    if endianess == 1:
        endianess = Endian.BIG
    elif endianess == 2:
        endianess = Endian.LITTLE
    else:
        print("Invalid endianess choice, defaulting to big endian.")
        endianess = Endian.BIG
else:
    endianess = None

register_count = 1

setup_register_info()

continues_read_active = False
continues_write_active = False

try:
    while True:

        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top

        print("\n" + "="*40)
        print("Choose next operation:")
        print("-"*40)
        if operation in [1, 2, 5]:
            print("1. Perform single read")
        elif operation in [3, 4]:
            print("1. Perform single write")
        if operation in [1, 2, 5]:
            print("2. Perform continuous read")
        elif operation in [3, 4]:
            print("2. Perform continuous write")

        print("3. Change register setup")
        print("4. Quit")
        print("-"*40)

        choice = input("Enter choice (1-4): ").strip()

        if choice != '1' and choice != '2' and choice != '3' and choice != '4':
            print('Not a valid operation, try again!')
            continue

        if choice == '4':
            break

        print(f' ')

        value = 0
        interval = 1

        if choice == '3':
            setup_register_info(clear=True)
            continue





        if operation in [1, 2, 5]:
            print(f'Reading from address {address}')

        elif operation in [3, 4]:
            print("\n" + "="*40)
            value = float(input("Enter value to write: ").strip())
            value = int(value/scale)
            print(f'Writing value (scaled): {value} to address {address}')


        if choice == '2':
            print("\n" + "="*40)
            interval = float(input("Enter interval in seconds: ").strip())

        # Store the initial output for continuous mode
        loop_count = 0

        while True:

            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
            loop_count += 1

            # Check if user pressed a key to break out
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'q' or key == b'Q' or key == b'\x1b' or key == b' ':  # 'q' or ESC
                    print("\n" + "="*40)
                    print("Exiting continuous operation...")
                    print("="*40)
                    break


            print(f' ')

            start = 0
            end = 0

            print("\n" + "*"*60)

            if operation in [1, 2, 5]:
                print(f"{translate_operation_code(operation)}: from address: {address}, datatype: {datatype}, scale: {scale}")
            elif operation in [3, 4]:
                print(f"{translate_operation_code(operation)}: value: {value}, to address: {address}, datatype: {datatype}, scale: {scale}")

            print("-"*60)

            # print("-"*40)
            print(f' ')

            if operation == 1:
                start = time.time()
                result = client.read_coils(address=address, count=register_count, slave=1)
                end = time.time()

                if not result.isError():
                    print(f"Coil values: {result.bits}")
                else:
                    print(f"Modbus error: {translate_exception_code(result.exception_code)}")

            if operation == 2:
                start = time.time()
                result = client.read_input_registers(address=address, count=register_count, slave=1)
                end = time.time()

                reading_value = None
                if not result.isError():
                    reading_value = client.convert_from_registers(result.registers, datatype, word_order='big' if endianess == Endian.BIG else 'little')
                    reading_value = reading_value * scale
                    print(f"Input register values: {result.registers}")
                    print(f"Decoded value: {reading_value}")
                else:
                    print(f"Modbus error: {translate_exception_code(result.exception_code)}")

            if operation == 5:
                start = time.time()
                result = client.read_holding_registers(address=address, count=register_count, slave=1)
                end = time.time()

                reading_value = None
                if not result.isError():
                    reading_value = client.convert_from_registers(result.registers, datatype, word_order='big' if endianess == Endian.BIG else 'little')
                    reading_value = reading_value * scale
                    print(f"Holding register values: {result.registers}")
                    print(f"Decoded value: {reading_value}")
                else:
                    print(f"Modbus error: {translate_exception_code(result.exception_code)}")

            if operation == 3:

                payload = client.convert_to_registers(value=value, data_type=datatype, word_order='big' if endianess == Endian.BIG else 'little')
                print(f'Payload to write register: {payload}')
                start = time.time()
                response = client.write_register(address, payload[0], slave=id)
                end = time.time()
                # print(f'Response time: {end - start} seconds')
                if response.isError():
                    print(f"Error details: {translate_exception_code(response.exception_code)}")
                else:
                    print('SUCCESS')

            if operation == 4:

                payload = client.convert_to_registers(value=value, data_type=datatype, word_order='big' if endianess == Endian.BIG else 'little')
                print(f'Payload to write multiple registers: {payload}')
                start = time.time()
                response = client.write_registers(address, payload, slave=id)
                end = time.time()
                # print(f'Response time: {end - start} seconds')
                if response.isError():
                    print(f"Error details: {translate_exception_code(response.exception_code)}")
                else:
                    print('SUCCESS')


            print("\n" + f'Response time: {end - start} seconds')

            if choice == '2':
                print(f'\nLoop count: {loop_count}')
                print(f'Interval: {interval} seconds')
                print("-"*60)
                print("Press 'q', ESC, or SPACE to stop...")

            print("*"*60)

            # print("\n" + "*"*60)
            # # print("*"*60)
            # print("\n"+"\n")

            if choice == '1':
                break
            elif choice == '2':
                time.sleep(interval)

        # time.sleep(2)

        # Write to coil example

        # client.write_coil(address=1, value=True, slave=17)

        # Read coils example
        # result = client.read_coils(address=2, count=3, slave=17)
        # if not result.isError():
        #     print(f"Coil values: {result.bits}")

        # Read holding registers
        # result = client.read_holding_registers(address=35, count=1, slave=17)
        # if not result.isError():
        #     print(f"Register values: {result.registers}")

        # Read input registers example
        # result = client.read_input_registers(address=1080, count=1, slave=1)
        # if not result.isError():
        #     decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        #     reading_value = decoder.decode_16bit_int()
        #     print(f"Input register values: {result.registers}")
        #     print(f"Decoded value: {reading_value}")
        # else:
        #     print(f"Modbus error: {result}")



        # if operation == 'write' or operation == 'w':
        #     print('')
        #     print('Writing with function code 6 (write single register)...')
        #     response = client.write_register(address, value, slave=id)
        #     if response.isError():
        #         print(f"Error details: {response}")
        #         # print(f"Function code: {response.function_code}")
        #         # print(f"Exception code: {response.exception_code}")
        #     else:
        #         print('success')

        #     print('')
        #     payload = client.convert_to_registers(value=value, data_type=client.DATATYPE.INT16, word_order='big')
        #     print(f'Payload to write multiple registers: {payload}')
        #     print('Writing with function code 16 (write multiple registers)...')
        #     response = client.write_registers(address, payload, slave=id)
        #     if response.isError():
        #         print(f"Error details: {response}")
        #         # print(f"Function code: {response.function_code}")
        #         # print(f"Exception code: {response.exception_code}")
        #     else:
        #         print('success')
    client.close()


except Exception as e:
    print(f"An error occurred: {e}")
finally:
    client.close()

