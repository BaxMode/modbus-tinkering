#!/usr/bin/env python3
# TCP Modbus Server with holding registers
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import logging
import threading
import time

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARNING)

# Custom ModbusSequentialDataBlock with callback support
class CallbackDataBlock(ModbusSequentialDataBlock):
    def __init__(self, address, values):
        super().__init__(address, values)
        print("CallbackDataBlock initialized")

    def setValues(self, address, values):
        # Print before change
        for idx, value in enumerate(values):
            reg_address = address + idx
            if 0 <= reg_address <= 10:
                old_value = self.getValues(reg_address, 1)[0] if reg_address < len(self.values) else "N/A"
                print(f"Register {reg_address} changing from {old_value} to {value}")

        # Call the parent implementation
        super().setValues(address, values)

        # Print after change
        for idx, value in enumerate(values):
            reg_address = address + idx
            if 0 <= reg_address <= 10:
                binary = format(value, '016b')
                print(f"Register {reg_address} now set to: {value} (binary: {binary})")

    # Override getValues to log reads as well
    def getValues(self, address, count=1):
        values = super().getValues(address, count)
        # Uncomment to see reads as well
        # print(f"Reading registers {address}-{address+count-1}: {values}")
        return values

def update_context(context):
    """Periodically check values in the store"""
    while True:
        time.sleep(2)
        values = context[0].getValues(3, 0, 10)  # Get registers 0-9 (holding registers)
        print(f"Current register values: {values}")

def run_server():
    # Define the address space with our custom data block for holding registers
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=CallbackDataBlock(0, [0]*50),  # Use custom block for holding registers
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
    context = ModbusServerContext(slaves=store, single=True)

    # Set up device identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName = 'Pymodbus TCP Server'
    identity.MajorMinorRevision = '3.0.0'

    # Set register values
    context[0].setValues(3, 1, [224])  # Register 1 = 224

    # Create boolean list and set register 2
    list_of_booleans = [0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1]
    string_of_bits = ''.join(['1' if b else '0' for b in list_of_booleans])
    print(f"Boolean list as string of bits: {string_of_bits}")

    # Convert boolean list to integer value
    bit_value = sum((1 << i) for i, v in enumerate(list_of_booleans) if v)
    context[0].setValues(3, 2, [bit_value])

    # Start a thread to monitor register values
    # monitor_thread = threading.Thread(target=update_context, args=(context,), daemon=True)
    # monitor_thread.start()

    # Start server
    print("Starting Modbus TCP Server on localhost:502")
    print("Register 1 = 224")
    print(f"Register 2 = {bit_value} (bit-wise boolean values)")
    StartTcpServer(context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    run_server()