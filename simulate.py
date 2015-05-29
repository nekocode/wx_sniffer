__author__ = 'nekocode'

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import sys
import time

print '\n======================================='
print 'start simulate(use monkeyrunner)'
print '=======================================\n'
device = MonkeyRunner.waitForConnection(5, 'emulator-' + str(sys.argv[1]))
device.touch(234, 342, MonkeyDevice.DOWN_AND_UP)
time.sleep(5)
device.press('KEYCODE_BACK', MonkeyDevice.DOWN_AND_UP)
time.sleep(5)
device.touch(234, 586, MonkeyDevice.DOWN_AND_UP)
time.sleep(5)
device.press('KEYCODE_BACK', MonkeyDevice.DOWN_AND_UP)
print '\n======================================='
print 'simulate ended'
print '=======================================\n'