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

def explane_arguments():
    global ip, operation, address, datatype_input, scale, endianess_input, id

    print("\n" + "="*40)
    print("ARGUMENTS EXPLANATION")
    print("It is possible to provide the initial register setup as arguments when starting the script.")
    print("When the arguments are not provided, the script will prompt for the missing values.")
    print("-"*40)
    print(" --ip / -ip : IP address of the Modbus TCP server (slave).")
    print(" --operation / -o : Modbus operation to perform (1-5).")
    print(" --address / -a : Register address to read from or write to.")
    print(" --unit_id / -id : Unit ID (slave ID) of the Modbus device.")
    print(" --datatype / -dt : Datatype for reading/writing (1-6).")
    print(" --scale / -s : Scale factor to apply to the value.")
    print(" --endianess / -e : Endianess for word order (1 for Big Endian, 2 for Little Endian).")
    print("-"*40)
    print(f"Arguments for current setup: --ip {ip} -o {operation} -a {address} -id {id} -dt {datatype_input} -s {scale} -e {endianess_input}")
    print("\n")

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
    global operation, address, datatype_input, datatype, scale, endianess_input, endianess, id, register_count

    if clear:
        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
        operation = None
        address = None
        datatype_input = None
        datatype = None
        scale = None
        endianess_input = None
        endianess = None
        id = None

    print("\n" + "="*40)
    print("REGISTER SETUP")
    print("-"*40)

    if id == None:
        print("\n" + "="*40)
        id = int(input('Enter the unit id (slave id): ').strip())

    if operation == None:
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
    print("-"*40)
    print(f'Selected operation: {translate_operation_code(operation)}')
    print("-"*40)

    if address == None:
        print("\n" + "="*40)
        address = int(input("Enter address: ").strip())
    print("-"*40)
    print(f'Register address: {address}')
    print("-"*40)

    if datatype_input == None:
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
    print("-"*40)
    print(f'Selected datatype: {get_datatype_code(datatype_input)}')
    print("-"*40)

    register_count = get_register_count(datatype_input)
    print(f'Register count: {register_count}')
    print("-"*40)

    if scale == None:
        print("\n" + "="*40)
        scale = float(input("Enter scale factor: ").strip())
    print("-"*40)
    print(f'Scale factor: {scale}')
    print("-"*40)

    if endianess_input == None:
        print("\n" + "="*40)
        print("Choose endianess:")
        print("-"*40)
        print("1. Word: Big Endian")
        print("2. Word: Little Endian")
        print("-"*40)
        endianess_input = int(input("Enter choice endianess (1-2): ").strip())

    if endianess_input == 1:
        endianess = Endian.BIG
    elif endianess_input == 2:
        endianess = Endian.LITTLE
    else:
        print("Invalid endianess choice, defaulting to big endian.")
        endianess = Endian.BIG
    print("-"*40)
    print(f'Selected word endianess: {"Big Endian" if endianess == Endian.BIG else "Little Endian"}')
    print("-"*40)

    print("\n")
    print("Register setup complete.")


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

def check_inputs():
    global operation, address, datatype_input, scale, endianess_input, id

    if operation == None or operation not in [1, 2, 3, 4, 5]:
        print("Invalid operation input. It should be between 1 and 5.")
        return False
    if address == None or address < 0:
        print("Invalid address. It should be a non-negative integer.")
        return False
    if datatype == None or datatype_input not in [1, 2, 3, 4, 5, 6]:
        print("Invalid datatype input. It should be between 1 and 6.")
        return False
    if scale == None or scale <= 0:
        print("Invalid scale factor. It should be a positive number.")
        return False
    if endianess == None or endianess_input not in [1, 2]:
        print("Invalid endianess input. It should be 1 (Big Endian) or 2 (Little Endian).")
        return False
    if id == None or id < 0:
        print("Invalid unit ID. It should be a non-negative integer.")
        return False

    return True

def check_connection(client:ModbusTcpClient, ip):

    # Check connection
    print("\n")
    print(f'Connecting with {ip}...')
    print("-"*60)
    print("Press 'q', ESC, or SPACE to stop...")
    print("-"*60)
    while not client.connected:
        # Check if user pressed a key to break out
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'q' or key == b'Q' or key == b'\x1b' or key == b' ':  # 'q' or ESC
                print("\n" + "="*40)
                print("Exiting connection attempt...")
                print("="*40)
                return None, False
        if client.connect():
            print(" ")
            print(f"CONNECTED :D")
            # print("-"*40)
            print("\n")
            return ip, True
        time.sleep(1)

    # If already connected, return success
    return ip, True



# BEGIN
print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
print("MODBUS TINKER")
print("Play around with Modbus TCP")

# explane_arguments()



client = ModbusTcpClient(
    host='0.0.0.0',
    port=502,
)
connected = False

ip = None
if args.ip:
    ip = args.ip.strip()

while not connected:

    if ip == None:
        print("\n" + "="*40)
        ip = input('Enter the IP address of the server (slave): ').strip()

    # TODO: add support for other framers (rtu, ascii)

    client = ModbusTcpClient(
        host=ip,
        port=502,
        # framer='rtu',
    )

    ip, connected = check_connection(client, ip)

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

datatype = None
if args.datatype:
    datatype_input = int(args.datatype)
else:
    datatype_input = None

if args.scale:
    scale = float(args.scale)
else:
    scale = None

endianess = None
if args.endianess:
    endianess_input = int(args.endianess)
else:
    endianess_input = None

register_count = 1

setup_start = time.time()
setup_register_info()

print("\033[2J\033[H", end="")  # Clear screen and move cursor to top

setup_end = time.time()
if setup_end - setup_start < 1:
    print("Register setup completed at startup with arguments, scroll up to check settings")

continues_read_active = False
continues_write_active = False

try:
    while True:

        if not check_inputs():
            setup_register_info(clear=True)
            continue

        # extra validation for the retarded type checker in VS code
        if address == None:
            print("Address is not set. Exiting to main menu.")
            continue
        if operation == None:
            print("Operation is not set. Exiting to main menu.")
            continue
        if datatype == None:
            print("Datatype is not set. Exiting to main menu.")
            continue
        if scale == None or scale <= 0 or type(scale) not in [int, float]:
            print("Scale factor is not set. Exiting to main menu.")
            continue
        if endianess == None:
            print("Endianess is not set. Exiting to main menu.")
            continue
        if id == None:
            print("Unit ID is not set. Exiting to main menu.")
            continue

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
        print("4. Show script run arguments for instant register setup at next script start")
        print("5. Quit")
        print("-"*40)

        try:
            choice = input("Enter choice (1-5): ").strip()

            if choice != '1' and choice != '2' and choice != '3' and choice != '4' and choice != '5':
                print('Not a valid operation, try again!')
                continue

            if choice == '4':
                explane_arguments()
                continue

            if choice == '5':
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
                if value != None and scale != None:
                    value = int(value/scale)
                print(f'Writing value (scaled): {value} to address {address}')

                if value == None:
                    print("Invalid value to write, exiting to main menu.")
                    continue


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
                    print(f"{translate_operation_code(operation)}")
                    print(f'from address: {address}')
                    print(f'datatype: {datatype}')
                    print(f'scale: {scale}')
                elif operation in [3, 4]:
                    print(f"{translate_operation_code(operation)}")
                    print(f'value: {value}')
                    print(f'to address: {address}')
                    print(f'datatype: {datatype}')
                    print(f'scale: {scale}')

                print("-"*60)

                # print("-"*40)
                print(f' ')

                if operation in [1,2,5]:
                    print('RESPONSE: ')
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
                        if isinstance(reading_value, (int, float)):
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
                        if isinstance(reading_value, (int, float)):
                            reading_value = reading_value * scale
                        print(f"Holding register values: {result.registers}")
                        print(f"Decoded value: {reading_value}")
                    else:
                        print(f"Modbus error: {translate_exception_code(result.exception_code)}")

                if operation == 3:

                    payload = client.convert_to_registers(value=value, data_type=datatype, word_order='big' if endianess == Endian.BIG else 'little')
                    print(f'Payload to write register: {payload}')
                    print(' ')
                    start = time.time()
                    response = client.write_register(address, payload[0], slave=id)
                    end = time.time()
                    # print(f'Response time: {end - start} seconds')
                    if response.isError():
                        print(f"Error details: {translate_exception_code(response.exception_code)}")
                    else:
                        print('RESPONSE:')
                        print(' ')
                        print('SUCCESS')

                if operation == 4:

                    payload = client.convert_to_registers(value=value, data_type=datatype, word_order='big' if endianess == Endian.BIG else 'little')
                    print(f'Payload to write multiple registers: {payload}')
                    print(' ')
                    start = time.time()
                    response = client.write_registers(address, payload, slave=id)
                    end = time.time()
                    # print(f'Response time: {end - start} seconds')
                    if response.isError():
                        print(f"Error details: {translate_exception_code(response.exception_code)}")
                    else:
                        print('RESPONSE:')
                        print(' ')
                        print('SUCCESS')


                print("\n" + f'Response time: {end - start} seconds')

                if choice == '2':
                    print("\n" +"-"*60)
                    print('\n'+f'Count: {loop_count}')
                    print(f'Interval: {interval} seconds')
                    print("\n"+"-"*60)
                    print("Press 'q', ESC, or SPACE to stop...")

                print("*"*60)

                # print("\n" + "*"*60)
                # # print("*"*60)
                # print("\n"+"\n")

                if choice == '1':
                    break
                elif choice == '2':
                    time.sleep(interval)
                    print("\033[2J\033[H", end="")  # Clear screen and move cursor to top

        except Exception as e:
            print("\n" +"-"*60)
            print("\n")
            print(f"An error occurred: {e}")
            print("\n")
            print("*"*60)

            ip, connected = check_connection(client, ip)



    print("\n")
    print("*"*60)
    print("Closing the Modbus connection")
    print("\n")
    print("SEE YA!")


    client.close()


except Exception as e:
    print(f"An error occurred: {e}")
finally:
    client.close()

