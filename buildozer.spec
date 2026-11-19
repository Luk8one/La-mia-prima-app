
[app]

title = Quaderno
package.name = quaderno
package.domain = it.luca

android.sdk_path = /usr/local/lib/android/sdk

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt

version = 0.1

requirements = python3,kivy

orientation = portrait
fullscreen = 0

[buildozer]

log_level = 2
warn_on_root = 1

[android]

android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True
