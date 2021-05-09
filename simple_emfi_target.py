import re
import serial
import time


PRINTER_COM = "COM5"
CHIPSHOUTER_COM = "COM3"

Z_MAX        = 2.0     # mm
Z_STEP       = -1.0    # mm
X_MIN        = 0.0     # mm, use to dial in a specific region
X_STEP       = 1.0     # mm
Y_MIN        = 0.0     # mm, use to dial in a specific region
Y_STEP       = 1.0     # mm
PULSE_WIDTH  = 80      # ns
MOVE_DWELL   = 1.0     # s, time to wait after sending move command
GLITCH_DWELL = 0.5     # s, time to wait after pulsing 



def get_axis_max(printer_serial):
    '''Get max position for X and Y'''
    printer_serial.reset_input_buffer()
    printer_serial.write(b"M208\n")
    result = printer_serial.readline()  # Axis limits X0.0:6.0, Y0.0:6.0, Z0.0:300.0
    result = result.decode("utf-8")     # we receive bytes
    match = re.match(r"Axis limits X([\d.]+):([\d.]+), Y([\d.]+):([\d.]+), Z([\d.]+):([\d.]+)",
                     result)
    if match:
        _ = printer_serial.readline()  # ok
        floats = [float(x) for x in match.groups()]
        return (floats[1], floats[3])  # X and Y max
    else:
        return None


def move(printer_serial, x, y, z):
    printer_serial.reset_input_buffer()
    printer_serial.write(f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f}\n".encode("ascii"))
    printer_serial.readline()  # ok


def arm(chipshouter_serial):
    chipshouter_serial.reset_input_buffer()
    chipshouter_serial.write(b"arm\n")


def disarm(chipshouter_serial):
    chipshouter_serial.reset_input_buffer()
    chipshouter_serial.write(b"disarm\n")


def pulse(chipshouter_serial):
    chipshouter_serial.reset_input_buffer()
    chipshouter_serial.write(b"pulse\n")


def glitch_loop(printer_serial, chipshouter_serial, x_max, y_max):
    x_pos = X_MIN
    y_pos = Y_MIN
    z_pos = Z_MAX
    move(printer_serial, x_pos, y_pos, z_pos)

    while z_pos >= 0.0:  # move Z down
        x_pos = X_MIN
        y_pos = Y_MIN

        while y_pos <= y_max:  # move y
            x_pos = X_MIN
            while x_pos <= x_max:  # move x
                print(f"Moving to: ({x_pos:.2f}, {y_pos:.2f}, {z_pos:.2f})")
                move(printer_serial, x_pos, y_pos, z_pos)
                time.sleep(MOVE_DWELL)
                pulse(chipshouter_serial)
                time.sleep(GLITCH_DWELL)
                x_pos += X_STEP
            y_pos += Y_STEP
        z_pos += Z_STEP


def main():
    printer_serial = serial.Serial(PRINTER_COM, 115200)
    chipshouter_serial = serial.Serial(CHIPSHOUTER_COM, 115200)

    # you need to set axis max beforehand. see README
    x_max, y_max = get_axis_max(printer_serial)
    print(f"X, Y max = ({x_max}, {y_max})")

    time.sleep(3)
    arm(chipshouter_serial)
    time.sleep(1)
    # set pulse width here maybe
    glitch_loop(printer_serial, chipshouter_serial, x_max, y_max)
    disarm(chipshouter_serial)

    move(printer_serial, X_MIN, Y_MIN, Z_MAX)


if __name__ == "__main__":
    main()