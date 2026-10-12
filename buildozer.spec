[app]
title = دفتر ديون الزهوب
package.name = dukkandebt
package.domain = org.dukkan
source.dir = .
source.include_exts = py,png,jpg,otf,ttf
source.exclude_dirs = .github,.buildozer,bin,tools,__pycache__
version = 16.0
requirements = python3,kivy==2.3.0,pillow,pyjnius,android,openssl,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.logcat_filters = *:S python:D
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
