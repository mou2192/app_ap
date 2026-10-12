# -*- coding: utf-8 -*-
"""
نقطة دخول التطبيق (main.py) - لا تحذفه ولا تغيّر اسمه.
وظيفته: تشغيل الكود الحقيقي (app_main.py) داخل حماية كاملة:
  - أي خطأ أثناء التشغيل يظهر على الشاشة بدل ما يُغلق التطبيق.
  - أي خطأ لاحق (أثناء الاستخدام) يُسجَّل في crash.log ولا يُسقط التطبيق.
"""
import os
import sys
import traceback


def _log_path():
    base = os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "crash.log")


def _log(text):
    try:
        import time
        p = _log_path()
        try:
            if os.path.exists(p) and os.path.getsize(p) > 20000:
                os.remove(p)
        except Exception:
            pass
        with open(p, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + text + "\n\n")
    except Exception:
        pass


# شهادات SSL (بدونها قد يفشل الاتصال بتليجرام على أندرويد)
try:
    import certifi
    if os.path.exists(certifi.where()):
        os.environ["SSL_CERT_FILE"] = certifi.where()
except Exception:
    pass

from kivy.base import ExceptionHandler, ExceptionManager

_err_count = [0]


class _SafeHandler(ExceptionHandler):
    def handle_exception(self, inst):
        if isinstance(inst, (SystemExit, KeyboardInterrupt)):
            return ExceptionManager.RAISE
        _err_count[0] += 1
        _log("".join(traceback.format_exception(type(inst), inst, inst.__traceback__)))
        if _err_count[0] > 300:
            return ExceptionManager.RAISE
        return ExceptionManager.PASS


ExceptionManager.add_handler(_SafeHandler())


def _error_widget(tb):
    from kivy.core.window import Window
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    try:
        Window.clearcolor = (1, 1, 1, 1)
    except Exception:
        pass
    root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
    root.add_widget(Label(text="Startup error - take a screenshot of this screen",
                          size_hint_y=None, height=dp(40), color=(0.8, 0, 0, 1)))
    sv = ScrollView()
    lbl = Label(text=tb, color=(0, 0, 0, 1), font_size=dp(11), size_hint_y=None,
                halign="left", valign="top")
    lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    lbl.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
    sv.add_widget(lbl)
    root.add_widget(sv)
    return root


_import_error = None
try:
    import app_main
    _Base = app_main.DebtBookApp
except BaseException:
    _import_error = traceback.format_exc()
    _log(_import_error)
    from kivy.app import App as _Base


class MainApp(_Base):
    def build(self):
        if _import_error:
            return _error_widget(_import_error)
        try:
            return super().build()
        except BaseException:
            tb = traceback.format_exc()
            _log(tb)
            return _error_widget(tb)


MainApp().run()
