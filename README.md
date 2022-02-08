# RP2-all-in-one-MicroPython
 One example with all GPIO types for the Raspberry Pi Pico written in MicroPython.

## What does it aim for?
The project aims to bring together in one (basic) example all the topics covered in the official [Raspberry Pi Pico Python SDK](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf) document.

## What is it useful for?
For learning and consultation. An excessively commented example with a little bit of everything that, if well understood, elucidates the basics for developing applications in MicroPython for the Raspberry Pi Pico board.

## How to use?
With the board ready for programming in MicroPython (if in doubt, see chapter 1.2 of the [Raspberry Pi Pico Python SDK](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf) document):
1. Create a 'lib' folder on your Raspberry Pi Pico and copy the files from the project's 'lib' folder there.
2. Run the file 'all_in_one_example.py' from Thonny (or any other IDE) or copy this file to your board with the name 'main.py', which will make the file start running as soon as the board is powered up, without depending of IDEs.

## What topics does it contain?

## What topics does it not contain?

## What hardware is used?
Adaptations can be made and you can test just what you have, the way you prefer.
However, the code was tested on the following circuit:
![HW Project wiring](HW_Project\All_in_one_example_wiring_bb.png)

PS: it is possible to minimize the use of components covering exactly the same topics, for example:
* Not using an SD card module, but soldering pins to a MicroSD adapter and connecting directly to the breadboard. No software changes required.
* Not using a bidirectional logic level shifter for the I2C-LCD module. No software changes required. (It works, but the most correct and safe way to use it is with the shifter)
* Not using the potentiometer, since the on-board temperature sensor is already an example of ADC-type GPIO. So, for the PWM example, it will be necessary to generate a random number for the duty cycle.