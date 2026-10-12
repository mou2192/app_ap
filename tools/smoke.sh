#!/bin/bash
PKG=org.dukkan.dukkandebt
APK=$(ls bin/*.apk | head -n 1)
adb install -r "$APK" || exit 1
adb logcat -c
adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1
sleep 60
adb logcat -d > logcat.txt
if adb shell pidof $PKG | grep -q '[0-9]'; then
  echo "OK: app is still running after 60s"
  exit 0
fi
echo "FAIL: app is not running (crashed or exited)"
grep -n -i -E "Traceback|AndroidRuntime|FATAL|python" logcat.txt | tail -n 60
exit 1
