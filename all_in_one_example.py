import machine
import os
import errno
import time
import math
import _thread
import sdcard  # oficial driver from MicroPython project but not built-in, so need to added by programmer inside 'lib' folder.
from lcd_api import LcdApi  # module not built-in MicroPython, added by the programmer, inside 'lib' folder.
from pico_i2c_lcd import I2cLcd  # module not built-in MicroPython, added by the programmer, inside 'lib' folder.


# GPIO definitons

# GP00 - GP01 - UART
uart0 = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))
# GP02
# GP03
# GP04 - GP05 - UART
uart1 = machine.UART(1, baudrate=9600, tx=machine.Pin(4), rx=machine.Pin(5))
# GP06
# GP07
# GP08 - GP09 - I2C
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)
# GP10
# GP11
# GP12 - GP13 - GP14 - GP15 - SPI
spi = machine.SPI(1, sck=machine.Pin(14), mosi=machine.Pin(15), miso=machine.Pin(12))
spiCS = machine.Pin(13, mode=machine.Pin.OUT, value=1)  # Chip selection starting with value 1 wich means SPI communication deactivated.
# GP16
# GP17
# GP18
# GP19
# GP20
# GP21
# GP22 - INPUT - tactile push-button
button = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_DOWN)
# GP23 - OUTPUT - RP2040 on-board SMPS power save pin control
# GP24 - INPUT - RP2040 VBUS sense (High if VBUS is present)
# GP25 - PWM - RP2040 on-board LED
pwm = machine.PWM(machine.Pin(25))
# GP26
# GP27
# GP28 - ADC - pontetiometer
potentiometer = machine.ADC(machine.Pin(28))
# GP29 - ADC - RP2040 ADC3 used to measure VSYS/3
# GP?? - ADC 4 - RP2040 on-board temperature sensor
onBoardTemperatureSens = machine.ADC(4)  # ADC channel 4 is dedicated to on-board temperature sensor built-in RP2040


# Global definitions

## Main recurrent call
mainRunning = False
virtualTimer = machine.Timer(-1)  # id -1 construct a virtual timer.
## Multicore
multicoreActive = False
semaphore = _thread.allocate_lock()  # lock definition to avoid running conflicts from multicore threads.
## I2C - LCD
I2C_ADDR     = 0x27  # i2c device address in hexadecimal.
I2C_NUM_ROWS = 2  # lcd display number of rows.
I2C_NUM_COLS = 16  # lcd display number of columns.
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)  # display lcd with i2c conversion module definition.
## PWM
pwm.freq(1000)  # define as global if only one setup is necessary, avoiding repeating setups in loop.
## SPI - SD Card
sd = sdcard.SDCard(spi, spiCS)  # SD card object definition.
vfs = os.VfsFat(sd)  # file system FAT definition as the SD card is formatted as FAT32.
print("SD Card Size: {} MB".format(sd.sectors/2048))  # checking the access to the sd card by looking for its size.


# Function declarations

def startStop(pin):
    """Called by and interruption handler triggered by the 'pin' passed as argument, this function initialize/deinitizalize a timer that recurrently calls the main function.
    
    A timer repeatedly calling the main function is a better solution than an infinite main loop, as the classic while loop that is always true for example. This is because through a timer, the serial communication through USB, including the python REPL remains available between calls to the main function, which does not happen when having an infinite loop, which prevents sending a reset signal for example. When there is a file named 'main.py', which automatically executes when the board is powered up, and it contains an infinite main loop, it is impossible to intentionally stop the loop execution to download a new software version, for example, it ends up being necessary to format the board. Using timer for recurring call, a command like Ctrl+C via REPL or through an IDE, stops the software and allow modifications and testing."""

    global mainRunning  # because mainRunning is assigned inside this function, its considered local by default, so if you want to use the global variable, explicit it.
    if mainRunning:
        virtualTimer.deinit()  # stops Timer that calls main function
        mainRunning = not(mainRunning)  # change from True to False
        try:  # safe exit
            os.umount("/sd_root")
        except:
            pass
    else:
        virtualTimer.init(period=1000, callback=main)  # set a Timer for periodic calling main function, acting like a main loop.
        mainRunning = not(mainRunning)  # change from False to True

def convUIntToV(uIntValue, bits=16, vRef=3.3):
    """Convert the unsigned integer value read by an ADC GPIO, which reads a maximum 'bits' size value to a maximum 'vRef' voltage,
    to a voltage value to be used in another conversion, for example, for temperature based on the temperature sensor parameters."""
    return uIntValue * (vRef / ((math.pow(2, bits) - 1)))

def readTemperature():
    """Read the on-board temperature sensor value as unsigned integer 16 bits, convert it to Temperature and print the value."""
    semaphore.acquire()  # in case of multicore enabled, it is important to acquire read/write permission on a shared resource/variable between cores.
    digitalTemperature = onBoardTemperatureSens.read_u16()  # get ADC actual reading in u16 bits
    voltageTemperature = convUIntToV(digitalTemperature)  # convert u16 to voltage, based on the board's reference voltage and ADC's bits resolution.
    Temperature = 27 - (voltageTemperature - 0.706)/0.001721  # convert voltage in temperature based on sensor parameters. Vbe = 0.706V
    print("Board temperature: {:.2f}ºC".format(Temperature))
    semaphore.release()  # releases the previously acquired permission to use a resource so that others can use it.


# Main function

def main(timer):

    startTimestamp = time.ticks_us()  # start to measure time of execution.
    
    ## Multicore
    global multicoreActive  # since multicoreActive value must be retained between main execution, it was made global.
    multicoreActive = not multicoreActive  # one loop with multicore, one loop without multicore.
    if multicoreActive:
        _thread.start_new_thread(readTemperature, ())  # calling a function to be executed in the second core, core1.
    else:
        readTemperature()  # calling a function normally, to be execute in the main core, core0.
    
    ## ADC
    duty = potentiometer.read_u16()  # convertion of analogic data to u16 (0-65535)

    ## PWM
    pwm.duty_u16(duty)  # apply value of dutycycle in u16 (0-65535 -> 0-100%)
    
    ## UART
    ### UART1 - SEND
    txData = b'hello world via UART\n\r'  # data to send
    uart1.write(txData)  # load data into transmit register and send it (parallel in - serial out)
    time.sleep(0.1)  # wait for data to be sent
    ### UART0 - RECEIVE
    rxData = bytes()  # because UART.read returns a bytes object
    while uart0.any() > 0:  # UART.any() returns the number of characters available to read.
        rxData += uart0.read(1)  # load 1 byte into receiver register and return it (serial in - parallel out)
    #rxData = uart0.readline()  # read until the CR (\r) and NL (\n) characters.
    print(rxData.decode('utf-8', 'ignore'))  # decode bytes into utf-8 string ignoring invalid convertions
    
    ## I2C - LCD
    """for examples of the I2C communication specifically, check the file 'pico_i2c_lcd.py' from 'lib' folder."""
    lcd.clear()  # clear the LCD display printed informations.
    localTime = time.localtime()  # get the actual timestamp.
    lcd.putstr("{year:>04d}/{month:>02d}/{day:>02d} {HH:>02d}:{MM:>02d}:{SS:>02d}".format(
        year=localTime[0], month=localTime[1], day=localTime[2],
        HH=localTime[3], MM=localTime[4], SS=localTime[5]))  # print timestamp in the LCD display.
    
    ## SPI - SD Card
    """for examples of the SPI communication specifically, check the file 'sdcard.py' from 'lib' folder."""
    dataToLog = str("{year:>04d}/{month:>02d}/{day:>02d} {HH:>02d}:{MM:>02d}:{SS:>02d} - ADC and PWM duty value: {duty}\n".format(
        year=localTime[0], month=localTime[1], day=localTime[2], HH=localTime[3], MM=localTime[4], SS=localTime[5], duty=duty))
    fileName = "/sd_root/ADC_log.txt"  # name of the file to be created/appended
    
    try:  # try to mount the file system to have access to the SD card by the 'os' library as folder.
        os.mount(vfs, "/sd_root")
    except OSError as e:
        if e.errno == errno.EPERM:  # check if an specific error raised.
            print("Operation not permitted. Is possible that the file sys is already mounted.")
        raise e  # raise the error anyway after printing more about it.
    print("SD card root have the following files: ", os.listdir("/sd_root"))
    
    with open(fileName, "a") as f:  # open as 'a' to append data, open as 'w' to truncate data.
        bytesWritten = f.write(dataToLog)  # write and returns an integer quantity of bytes written
        print(bytesWritten, "bytes written")
    with open(fileName, "r") as f:
        result = f.read()
        print(len(result), "bytes read")
        
    try: # try to unmount the file system to be safe to remove the SD card without damages.
        os.umount("/sd_root")  # always unmount when finished using files because any connection problem while mounted can damage the hardware.
    except OSError as e:
        if e.errno == errno.EINVAL:  # check if an specific error raised.
            print("Invalid argument. Is possible that the file sys is already unmounted.")
        raise e  # raise the error anyway after printing more about it.
    
    ## Measuring execution time
    execTimestamp = time.ticks_diff(time.ticks_us(), startTimestamp)  # execution time is the actual (at the end) timestamp minus the startTimestamp.
    print("Execution time with Multicore = {}: {}us".format(multicoreActive, execTimestamp))


# Main function recurring call

## IRQ
button.irq(handler=startStop, trigger=machine.Pin.IRQ_RISING)  # call function handler when trigger state is active in the Pin defined in button.