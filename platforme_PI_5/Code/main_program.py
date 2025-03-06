import RPi.GPIO as GPIO
import time
from grove_rgb_lcd import *
from wifi_measurement import *
from datetime import datetime

# Global state variables
measure_execute = False
current_position = (0, 0)
measurement_count = 10
running = True
cpt=0

# GPIO pin setup for 3x4 keypad
ROW_PINS = [20, 6, 19, 26]    # example row pins (BCM numbering)
COL_PINS = [13, 12, 16]        # example col pins (BCM numbering)
GPIO.setmode(GPIO.BCM)
# Initialize column pins as outputs (start LOW)
for col in COL_PINS:
    GPIO.setup(col, GPIO.OUT)
    GPIO.output(col, GPIO.LOW)
# Initialize row pins as inputs with pull-ups
for row in ROW_PINS:
    GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Helper function to get a key press (scans the keypad matrix)
def get_key():
    """Wait for a key press and return the key symbol (as a string)."""
    while True:
        for col_index, col_pin in enumerate(COL_PINS):
            # Drive this column LOW, others HIGH
            GPIO.output(col_pin, GPIO.LOW)
            for other_col in COL_PINS:
                if other_col != col_pin:
                    GPIO.output(other_col, GPIO.HIGH)
            # Check rows for a LOW signal (key press)
            for row_index, row_pin in enumerate(ROW_PINS):
                if GPIO.input(row_pin) == GPIO.LOW:
                    # Debounce and wait for release
                    time.sleep(0.02)
                    while GPIO.input(row_pin) == GPIO.LOW:
                        time.sleep(0.01)
                    # Reset columns to default LOW
                    for c in COL_PINS:
                        GPIO.output(c, GPIO.LOW)
                    # Map row,col index to key character
                    key_map = [
                        ['1','2','3'],
                        ['4','5','6'],
                        ['7','8','9'],
                        ['*','0','#']
                    ]
                    return key_map[row_index][col_index]
        time.sleep(0.01)

# Define functions for each menu action
def start_measurement():
    """Start the measurement routine."""
    global measure_execute
    measure_execute = True
    setText("Measurement \n   started")

def pause_measurement():
    """Pause the ongoing measurement routine."""
    global measure_execute
    measure_execute = False
    setText("Measurement \n    paused")

def _read_number(label, max_digits, min_val, max_val):
    """
    Read a multi-digit number via keypad, updating LCD live.
    Stops on '*' (confirm) or '#' (cancel).
    """
    num_str = ""
    setText(f"{label}: _\n" + " " * 16)  # Initial empty input on LCD
    while True:
        key = get_key()
       
        if key.isdigit():
            if len(num_str) < max_digits:
                num_str += key  # Append digit
                # ✅ Update LCD in real-time with user input
                setText(f"{label}: {num_str}_\n" + " " * 16)
            else:
                # ✅ Max length reached → Reset and restart input
                setText(f"  Max {max_digits} digits!\n Try again")
                time.sleep(1)
                num_str = ""  # Reset input
                setText(f"{label}: _\n" + " " * 16)
       
        elif key == '*':  # ✅ Confirm input
            if num_str == "":
                # ✅ No input → Ask user to enter again
                setText("  No input!  \n Enter number")
                time.sleep(1)
                num_str = ""  # Reset
                setText(f"{label}: _\n" + " " * 16)
                continue

            value = int(num_str)
            if value < min_val or value > max_val:
                # ✅ Out of range → Reset and restart
                setText(f"Out of range!\n({min_val}-{max_val})")
                time.sleep(1)
                num_str = ""  # Reset
                setText(f"{label}: _\n" + " " * 16)
                continue
            else:
                # ✅ Valid input → Return number
                return value
       
        elif key == '#':  # ✅ Cancel entry
            setText(" Entry cancelled.\nReturning..")
            time.sleep(1)
            return None
       
        else:
            # ✅ Ignore any other keys (for safety)
            continue


def set_position():
    """
    Prompt user to set a new X, Y position and measurement count,
    showing live input on the LCD.
    """
    global current_position, measurement_count

    x = _read_number(label="X", max_digits=2, min_val=0, max_val=10)
    if x is None: return  # If cancelled, exit
   
    y = _read_number(label="Y", max_digits=2, min_val=0, max_val=10)
    if y is None: return  # If cancelled, exit
   
    count = _read_number(label="N", max_digits=3, min_val=1, max_val=999)
    if count is None: return  # If cancelled, exit
   
    # ✅ Successfully set new position and count
    current_position = (x, y)
    measurement_count = count
    setText(f"X:{x}, Y:{y}\nCount:{measurement_count}")
    time.sleep(2)
    setText("type # to go \n back to the menu")

def stop_program():
    """Stop all execution and terminate the program."""
    global running
    running = False
    setText("Program terminating...")

def config_menu():
    """Handle configuration menu triggered by '#' key."""
    setText("* Config Menu * \nchoose an option")
    time.sleep(3)
    setText("1:Start,2:Pause,3:New Pos,4:Stop")
    while True:
        choice = get_key()
        if choice == '1':
            start_measurement()
            break
        elif choice == '2':
            pause_measurement()
            break
        elif choice == '3':
            set_position()
            break
        elif choice == '4':
            stop_program()
            break
        else:
            setText("Invalid choice, enter a valid one:")
            time.sleep(3)
            setText("1:Start,2:Pause,3:New Pos,4:Stop")

# Interrupt callback for '#' key press (on row pin 16)
def on_hash_pressed(channel):
    """GPIO interrupt callback for '#' key pressed (enter configuration mode)."""
    global measure_execute

    # ? Temporarily disable the interrupt to prevent multiple triggers
    GPIO.remove_event_detect(26)

    # ? Manually scan the keypad to confirm that '#' was pressed
    time.sleep(0.05)  # Small debounce delay
    key = get_key()  # Read the actual pressed key

    if key == "#":
        #print("\n'#' pressed - entering configuration mode.")
        measure_execute = False  # ? Optionally pause measurement
        config_menu()  # Call configuration menu
        #print(f"\nInterrupt triggered by row, but detected key is '{key}', ignoring.")

    # ? Re-enable the interrupt after finishing the config menu
    GPIO.add_event_detect(26, GPIO.FALLING, callback=on_hash_pressed, bouncetime=200)

def close_file():
    """Safely closes the global file when program exits."""
    global file
    if file:
        file.close()
        setText("File closed \n successfully.")
        time.sleep(2)

def save_measurement(measurement_vector,position, timestamp):
    """Writes measurement data to the global file."""
    global file  # Ensure we access the global file variable
    # Format the measurement data
    measurement_data = f"Values: {measurement_vector},Position : {position}, Time:{timestamp}\n"
    file.write(measurement_data)
    file.flush()  # ? Immediately save data to disk (prevents data loss)

# Setup interrupt on the '#' row (GPIO16)
GPIO.add_event_detect(26, GPIO.FALLING, callback=on_hash_pressed, bouncetime=200)

# Main execution loop
try:
    # ? Open file at the start
    file = open("/mnt/nvme/measurements_wifi.txt", "a")
    file.write("Test measurement data\n")
    setRGB(255, 255, 255)
    setText("Press # to enter configuration")
    while running:
        if measure_execute:
            # Perform measurement_count measurements at current_position
            setText(f"Measure {cpt+1}/{measurement_count} \nposition{current_position}")
            #---------programme de mesure -------------#
                       
            scan_results=wifi_scan_5ghz()
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            save_measurement(scan_results,current_position, timestamp)  # ? Save to file
           
            #------- fin d'une mesure individuelle------#
            cpt+=1
            time.sleep(0.5)
            if(cpt>=measurement_count):
                # Completed one batch (if not paused early)
                measure_execute = False
                cpt=0
                setText("  Measurements  \n   completed  ")
                time.sleep(2)
                setText("type # to go  \n   to the menu")
        else:
            # Idle state - short sleep to reduce CPU usage
            time.sleep(1)
finally:
    # Cleanup GPIO on program exit
    GPIO.cleanup()
    close_file()
    setText("Program stoped.")
