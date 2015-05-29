#微信公众号uin，key捕获脚本

环境：`Windows`, `Python 2.7`, `Android SDK`, `Winpcap`, `dkpt`, `httplib2`

**执行步骤：**
- 创建并打开（多个）Android虚拟机
- 修改模拟点击脚本 `simulate.py`   
```
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
```
- 修改 `wxsniffer.py` 脚本主逻辑   
```
sniffer = WxSniffer()
sniffer.start_winpcap()
while True:
	# 5554为虚拟机设备号
	sniffer.simulate_open_wxarticle(5554)
	time.sleep(5)
	print sniffer.get_wxarticle_state('MzAwNTA2NjE2OA==', '205059655', '9fb1b7d533d39b65dde7c1d9eb9ab9c7', '1')
	time.sleep(30)
```
- 执行脚本 `wxsniffer.py`