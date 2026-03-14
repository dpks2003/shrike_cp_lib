# shrike.py (CircuitPython port)
# Engineer - Deepak Sharda - dshardan007@gmail.com
import board
import busio
import digitalio
import time

# Pin definitions
EN = digitalio.DigitalInOut(board.GP13)   # Enable FPGA
EN.direction = digitalio.Direction.OUTPUT

PWR = digitalio.DigitalInOut(board.GP12)  # Power to FPGA
PWR.direction = digitalio.Direction.OUTPUT

# SPI configuration
# CircuitPython busio.SPI takes (clock, MOSI, MISO)
SPI = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP0)

# Lock the SPI bus and configure it (polarity=0, phase=0, bits=8, baudrate=1_600_000)
# Note: configure() must be called after try_lock()
def _configure_spi():
    while not SPI.try_lock():
        pass
    SPI.configure(baudrate=1_600_000, polarity=0, phase=0, bits=8)


def flash(filename: str, word_size: int = 46408):
    """
    Flash the given bitstream file to the FPGA over SPI.

    Args:
        filename (str): Path to the binary bitstream file.
        word_size (int): Number of bytes to send per chunk (default: 46408).
    """
    SS = digitalio.DigitalInOut(board.GP1)   # Slave Select (Chip Select)
    SS.direction = digitalio.Direction.OUTPUT

    reset()
    print("[shrike_fpga] Starting FPGA flash...")
    print(f"[shrike_fpga] flashing: {filename}")
    time.sleep(0.5)

    # Reset and power-up FPGA
    SS.value = False   # CS low (deselect during init)
    EN.value = False
    PWR.value = False
    time.sleep(0.1)
    EN.value = True
    PWR.value = True
    time.sleep(0.1)

    # CS pulse to begin programming
    SS.value = True
    time.sleep(0.002)
    SS.value = False

    # Acquire SPI bus
    _configure_spi()

    # Send the bitstream
    try:
        with open(filename, "rb") as f:
            while True:
                word = f.read(word_size)
                if not word:
                    break
                SPI.write(word)
    except OSError as e:
        print(f"[shrike_flash] File error: {e}")
    except Exception as e:
        print(f"[shrike_flash] Error: {e}")
    finally:
        SPI.unlock()

    SS.value = True
    time.sleep(0.1)
    print("[shrike_flash] FPGA programming done.")


def reset():
    """
    Reset the FPGA by pulling PWR and EN low.
    """
    PWR.value = False
    EN.value = False
    print("[shrike_flash] FPGA reset done")


def blink():
    """
    Blink the LED connected to the RP2040 by flashing the FPGA.
    """
    flash("led_blink.bin")