#!/usr/bin/env python2

import logging
import serial
import struct
import time

logging.basicConfig(format="[%(asctime)s] %(levelname)s %(filename)s(%(lineno)d) %(message)s",
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

## Device limits
SPEED_MIN = 10
SPEED_MAX = 21
AZIMUTH_MIN = 120               # Hard limit ~115
AZIMUTH_MAX = 220               # Hard limit ~224
ELEVATION_MIN = 45              # Hard limit ~41
ELEVATION_MAX = 75              # Hard limit ~75

## Command bytes
AZIMUTH_CMD = 0x10
ELEVATION_CMD = 0x20
STOP_CMD = 0x55

## Constants
BAUD_RATE = 38400               # Baud rate for serial connection
MAX_CHECKS_BEFORE_WIGGLE = 7    # Max checks for repositioned heliostat before wiggling.
MAX_SENDS = 10                  # Max times to try to send command before raising exception
MAX_WRITES = 50                 # Max times to try to write command to port
RESPONSE_LEN = 11               # Length of response packet
SLEEP_AFTER_FAILED_WRITE = 60   # Seconds to sleep after a failed write to the controller.
SLEEP_BETWEEN_CHECKS = 3.0      # Seconds to sleep between checks for repositioned heliostat
SPEED_NORMAL = 21               # Normal speed
SYNC_BYTE = 0x41                # Synchronization byte
WIGGLE_AZ_DELTA = 10            # Number of degrees to wiggle azimuth.
WIGGLE_EL_DELTA = 3             # Number of degrees to wiggle elevation.
WRITE_TIMEOUT = 0.030           # Seconds after which port write will time out

def clamp(value, low_bound, high_bound):
    """Clamp value to be between low and high bound (inclusive)."""
    return max(low_bound, min(value, high_bound))

def clamp_azimuth_elevation(azimuth, elevation):
    return (clamp(azimuth, AZIMUTH_MIN, AZIMUTH_MAX),
            clamp(elevation, ELEVATION_MIN, ELEVATION_MAX))

class Encoder(struct.Struct):
    """Encode a command packet to be written to the controller."""
    def __init__(self):
        super(Encoder, self).__init__('> 3b 1H 1b 1b 1b 1b')

    def _validate_speed(self, speed):
        if not SPEED_MIN <= speed <= SPEED_MAX:
            raise ValueError("Speed {0} out of bounds {1}-{2}".format(speed, SPEED_MIN, SPEED_MAX))

    def azimuth(self, value, speed):
        if not AZIMUTH_MIN <= value <= AZIMUTH_MAX:
            raise ValueError("Azimuth {0} out of bounds {1}-{2}".format(value, AZIMUTH_MIN, AZIMUTH_MAX))
        self._validate_speed(speed)
        return self.pack(SYNC_BYTE, SYNC_BYTE, SYNC_BYTE, value, speed, 0, 0, AZIMUTH_CMD)

    def elevation(self, value, speed):
        if not ELEVATION_MIN <= value <= ELEVATION_MAX:
            raise ValueError("Azimuth {0} out of bounds {1}-{2}".format(value, ELEVATION_MIN, ELEVATION_MAX))
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

class MockController(object):
    def __init__(self, device='/dev/ttyUSB0'):
        pass

    def stop(self):
        logger.debug("Stopped")
        return 180, 45

    def azimuth(self, new_azimuth, speed=SPEED_NORMAL):
        logger.debug("Azimuth %d, speed %d", new_azimuth, speed)
        return new_azimuth

    def elevation(self, new_elevation, speed=SPEED_NORMAL):
        logger.debug("Elevation %d, speed %d", new_elevation, speed)
        return new_elevation

    def report_stats(self):
        logger.debug("Report statistics.")


class Controller(object):
    """Control the heliostat. Tries to get the heliostat to a known
    state by issuing a stop command from the constructor.
    """

    def __init__(self, device='/dev/ttyUSB0'):
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
        """Invoke try_to_write multiple times. Other methods should
        use this one to send commands and may assume that the message
        will be delivered successfully. This a convenient fiction.

        In reality, if no attempt succeeds, sleep for a while before
        trying again.  This should prevent hammering on the heliostat
        controller but will recover in the event of a communication
        failure.
        """
        while True:
            count = 1
            while count < MAX_SENDS:
                response = self.try_to_write(command)
                if response is not None:
                    self.sends += 1
                    return response
                else:
                    count += 1

            logger.error("Failed to send command")
            self.report_stats()
            logger.debug("Sleeping %ds", SLEEP_AFTER_FAILED_WRITE)
            time.sleep(SLEEP_AFTER_FAILED_WRITE)

    def send_and_wait(self, command, which_metric, expected_value, may_wiggle=True):
        """Send a command and wait for the given metric to reach an
        expected value.
        """
        assert(which_metric in ('azimuth', 'elevation'))
        metric_name = which_metric.capitalize()

        check_count = 0
        previous_value = current_value = -1
        while current_value != expected_value:
            if check_count < MAX_CHECKS_BEFORE_WIGGLE:
                response = self.send(command)
                current_value = response[which_metric]
                logger.info("%s %d", metric_name, current_value)

                if current_value != expected_value:
                    # Not there yet
                    if current_value == previous_value:
                        # In the same place as last check
                        check_count += 1
                    else:
                        # Moved since last check
                        previous_value = current_value
                        check_count = 0
                    time.sleep(SLEEP_BETWEEN_CHECKS)
            else:
                logger.warning("Exceeded maximum checks")
                if may_wiggle:
                    self.wiggle(which_metric, expected_value)
                    check_count = 0
                    logger.info("Done wiggling; resume %s to %d", which_metric, expected_value)
                else:
                    logger.debug("Wiggling disabled; giving up.")
                    return response
        self.stop()
        logger.info("%s now %d", metric_name, response[which_metric])
        return response

    def wiggle(self, which_metric, expected_value):
        """When we detect that the mirror isn't moving as expected,
        this method attempts to "dislodge" the mirror.

        Initial strategy is to move the mirror in the opposite
        direction that it was trying to move when it got "stuck."
        """

        assert(which_metric in ('azimuth', 'elevation'))
        logger.info("Was trying to make %s %d; wiggling", which_metric, expected_value)

        current_state = self.send(self.encoder.stop())
        current_value = current_state[which_metric]
        logger.info("Current %s %d", which_metric, current_value)

        # This may seem backwards, but we want to "wiggle" the mirror
        # in the opposite direction that we've been trying to move.
        sign = -1 if current_value < expected_value else +1

        if which_metric == 'azimuth':
            wiggle_value = clamp(current_value + (WIGGLE_AZ_DELTA * sign), AZIMUTH_MIN, AZIMUTH_MAX)
            command = self.encoder.azimuth(wiggle_value, SPEED_NORMAL)
        else:
            wiggle_value = clamp(current_value + (WIGGLE_EL_DELTA * sign), ELEVATION_MIN, ELEVATION_MAX)
            command = self.encoder.elevation(wiggle_value, SPEED_NORMAL)

        logger.info("Wiggle %s to %d", which_metric, wiggle_value)
        self.send_and_wait(command, which_metric, wiggle_value, may_wiggle=False)
        
    def stop(self):
        """Stop the heliostat."""
        logger.info("Stop")
        command = self.encoder.stop()
        response = self.send(command)
        return (response['azimuth'], response['elevation'])

    def azimuth(self, new_azimuth, speed=SPEED_NORMAL):
        """Rotate the heliostat to a new azimuth."""
        logger.info("Change azimuth to %d, speed %d", new_azimuth, speed)
        command = self.encoder.azimuth(new_azimuth, speed)
        response = self.send_and_wait(command, 'azimuth', new_azimuth)
        return response['azimuth']

    def elevation(self, new_elevation, speed=SPEED_NORMAL):
        """Tip the heliostat to a new elevation."""
        logger.info("Change elevation to %d, speed %d", new_elevation, speed)
        command = self.encoder.elevation(new_elevation, speed)
        response = self.send_and_wait(command, 'elevation', new_elevation)
        return response['elevation']

logger.info("Azimuth range %d-%d", AZIMUTH_MIN, AZIMUTH_MAX)
logger.info("Elevation range %d-%d", ELEVATION_MIN, ELEVATION_MAX)
logger.info("Speed range %d-%d", SPEED_MIN, SPEED_MAX)

if __name__ == '__main__':
    controller = Controller('/dev/ttyUSB0')
    controller.elevation(60)
    controller.azimuth(115)
    controller.report_stats()
