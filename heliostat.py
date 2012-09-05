#!/usr/bin/env python2

import logging
import serial
import struct
import time

logging.basicConfig(format="[%(asctime)s] %(levelname)s %(filename)s(%(lineno)d) %(message)s",
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

## Device limits
SPEED_MIN = 0x0a
SPEED_MAX = 0x14
AZIMUTH_MIN = 0x00b4
AZIMUTH_MAX = 0x0168
ELEVATION_MIN = 0x15
ELEVATION_MAX = 0x5a

## Command bytes
AZIMUTH_CMD = 0x10
ELEVATION_CMD = 0x20
STOP_CMD = 0x55

## Constants
BAUD_RATE = 38400               # Baud rate for serial connection
MAX_SENDS = 10                  # Max times to try to send command before raising exception
MAX_WRITES = 50                 # Max times to try to write command to port
RESPONSE_LEN = 11               # Length of response packet
SLEEP_BETWEEN_CHECKS = 3.0      # Seconds to sleep between checks for repositioned heliostat
SPEED_NORMAL = 0x12             # Normal speed
SYNC_BYTE = 0x41                # Synchronization byte
WRITE_TIMEOUT = 0.030           # Seconds after which port write will time out

class Encoder(struct.Struct):
    """Encode a command packet to be written to the controller."""
    def __init__(self):
        super(Encoder, self).__init__('> 3b 1H 1b 1b 1b 1b')

    def _validate_speed(self, speed):
        if not SPEED_MIN <= speed <= SPEED_MAX:
            raise RuntimeError("Speed {0} out of bounds {1}-{2}".format(speed, SPEED_MIN, SPEED_MAX))

    def azimuth(self, value, speed):
        if not AZIMUTH_MIN <= value <= AZIMUTH_MAX:
            raise RuntimeError("Azimuth {0} out of bounds {1}-{2}".format(value, AZIMUTH_MIN, AZIMUTH_MAX))
        self._validate_speed(speed)
        return self.pack(SYNC_BYTE, SYNC_BYTE, SYNC_BYTE, value, speed, 0, 0, AZIMUTH_CMD)

    def elevation(self, value, speed):
        if not ELEVATION_MIN <= value <= ELEVATION_MAX:
            raise RuntimeError("Azimuth {0} out of bounds {1}-{2}".format(value, ELEVATION_MIN, ELEVATION_MAX))
        self._validate_speed(speed)
        return self.pack(SYNC_BYTE, SYNC_BYTE, SYNC_BYTE, 0, 0, value, speed, ELEVATION_CMD)

    def stop(self):
        return self.pack(SYNC_BYTE, SYNC_BYTE, SYNC_BYTE, 0, 0, 0, 0, STOP_CMD)

class Decoder(struct.Struct):
    """Decode a response packet from the controller."""
    def __init__(self):
        super(Decoder, self).__init__('> 3b 4H')

    def decode(self, msge):
        (sync1, sync2, sync3, azimuth, elevation, temperature, humidity) = self.unpack(msge)
        for byte in (sync1, sync2, sync3):
            assert byte == SYNC_BYTE

        # These magic calculations come from Jeff.
        temperature = ((temperature * 0.0048875) * 100) - 273.15
        humidity = ((humidity * 0.0048875) - 0.8) * (100 / 3.75)

        response = { 'azimuth': azimuth,
                     'elevation': elevation,
                     'temperature': round(temperature, 2),
                     'humidity': round(humidity, 2) }

        logger.debug("AZ {azimuth} EL {elevation} TEMP {temperature} HUM {humidity}".format(**response))
        return response

class Controller(object):
    """Control the heliostat. Tries to get the heliostat to a known
    state by issuing a stop command from the constructor.
    """

    def __init__(self, device):
        self.sends = 0          # Number of messages sent
        self.writes = 0         # Number of port writes (including failed attempts to write)
        self.failed_tries = 0   # Number of times MAX_WRITES exceeded

        self.port = serial.Serial(device, baudrate=BAUD_RATE, timeout=WRITE_TIMEOUT)
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.stop()             # Make sure we're stopped before doing anything else.


    def report_stats(self):
        logger.info("%d commands sent", self.sends)
        logger.info("%d port writes", self.writes)
        logger.info("%d failed tries", self.failed_tries)
        if self.sends > 0:
            logger.info("%d writes/send", self.writes/self.sends)

    def try_to_write(self, command):
        """Write a command to the controller. The controller does't
        listen for incoming commands very often, so we try writing the
        command multiple times until the controller responds. If the
        command is written successfully, return the response from the
        controller. If we end up trying too many times, return None.
        """
        count = 1
        while True:
            self.port.write(command)
            self.writes += 1
            buffer = self.port.read(RESPONSE_LEN)
            if len(buffer) == RESPONSE_LEN:
                logger.debug("Got response after %d tries", count)
                response = self.decoder.decode(buffer)
                return response
            elif count >= MAX_WRITES:
                logger.warning("Exceeded maximum writes")
                self.failed_tries += 1
                return None
            else:
                count += 1
    
    def send(self, command):
        """Invoke try_to_write multiple times. If no attempt succeeds,
        try to stop the heliostat, and finally raise an exception.

        Other methods should use this one to send commands and may
        assume that the message will be delivered successfully. Of
        course, if it isn't delivered, the caller won't get control
        again anyhow, but it's a convenient fiction.
        """
        count = 1
        while count < MAX_SENDS:
            response = self.try_to_write(command)
            if response is not None:
                self.sends += 1
                return response
            else:
                count += 1

        logger.error("Failed to send command")
        self.stop()             # Last ditch effort
        self.stop()
        self.report_stats()
        raise RuntimeError("Failed to send command")

    def stop(self):
        """Stop the heliostat."""
        logger.info("Stop")
        command = self.encoder.stop()
        return self.send(command)

    def azimuth(self, new_azimuth, speed=SPEED_NORMAL):
        """Rotate the heliostat to a new azimuth."""
        logger.info("Change azimuth to %d", new_azimuth)
        command = self.encoder.azimuth(new_azimuth, speed)
        in_position = False
        while not in_position:
            response = self.send(command)
            logger.debug("Azimuth now %d", response['azimuth'])
            if response['azimuth'] == new_azimuth:
                in_position = True
            else:
                time.sleep(SLEEP_BETWEEN_CHECKS)
        self.stop()
        return response

    def elevation(self, new_elevation, speed=SPEED_NORMAL):
        """Tip the heliostat to a new elevation."""
        logger.info("Change elevation to %d", new_elevation)
        command = self.encoder.elevation(new_elevation, speed)
        in_position = False
        while not in_position:
            response = self.send(command)
            logger.debug("Elevation now %d", response['elevation'])
            if response['elevation'] == new_elevation:
                in_position = True
            else:
                time.sleep(SLEEP_BETWEEN_CHECKS)
        self.stop()
        return response

logger.info("Azimuth range %d-%d", AZIMUTH_MIN, AZIMUTH_MAX)
logger.info("Elevation range %d-%d", ELEVATION_MIN, ELEVATION_MAX)
logger.info("Speed range %d-%d", SPEED_MIN, SPEED_MAX)

controller = Controller('/dev/ttyUSB0')
controller.elevation(70)

# for i in range(2):
#     controller.elevation(60)
#     controller.azimuth(195)
#     controller.elevation(65)
#     controller.azimuth(200)
# controller.elevation(50)

controller.report_stats()
