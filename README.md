#微信公众号 uin，key 捕获脚本（获取微信公众号文章阅读量）

## 更完善的解决方案
**使用 Android System Exploit 配合虚拟机抓取，成功率高达 90% 以上，且能拓展到其他一些用处上。** 

详情请看：[**wechat_webview_launch.md**](wechat_webview_launch.md)


---

## Old version
环境：`Windows`, `Python 2.7`, `Android SDK`, `Winpcap`, `dpkt`, `httplib2`

**执行步骤：**
- 创建并打开（多个）Android虚拟机
- 修改模拟点击脚本 `simulate.py`   

``` python
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


``` python
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
