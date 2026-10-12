# -*- coding: utf-8 -*-
"""
دفتر ديون الزهوب - الإصدار 16.0
--------------------------------
+ تسجيل الدخول من أي جهاز: الفهرس رسالة مثبّتة تُقرأ بـ getChat،
  وبيانات كل مستخدم تُقرأ بـ forwardMessage (لا نستخدم getUpdates للقراءة
  فلا شيء يُفرَّغ من القناة أبداً).
+ بيانات العملاء مضغوطة ومقسّمة على عدة رسائل (لا حد 4096 حرف).
+ شاشة إعدادات: معلومات الحساب، الوضع الليلي، تسجيل الخروج، حذف الحساب.
+ جلسة واحدة: يبقى المستخدم مسجلاً حتى يخرج أو يحذف حسابه.
+ الفواتير والسندات وكشف الحساب كصورة PNG و PDF مع إرسال واتساب.
+ المزامنة تدعم الحذف (tombstones) وآخر تعديل (mod) بدل الضم الأعمى.
"""

import os
import sys
import json
import subprocess
import random
import string
import urllib.request
import urllib.parse
import urllib.error
import threading
import time
import hashlib
import base64
import zlib
import re
import textwrap
from datetime import datetime


# ============================================================
# 1) تثبيت المكتبات
# ============================================================
def ensure_package(pip_name, import_name=None):
    if import_name is None:
        import_name = pip_name
    # [إصلاح كراش] على أندرويد لا يوجد pip ولا sys.executable صالح؛ المكتبات
    # يجب أن تكون في requirements داخل buildozer.spec، فلا نحاول التثبيت هنا.
    if "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ:
        return
    try:
        __import__(import_name)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        except Exception:
            pass


ensure_package("kivy")
ensure_package("pillow", "PIL")

# ============================================================
# 2) الاستيرادات
# ============================================================
from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase, Label as CoreLabel
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label as KLabel
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.graphics import (Color, Rectangle, RoundedRectangle, Ellipse, Line,
                           PushMatrix, PopMatrix, Translate)
from kivy.animation import Animation
import math
import weakref
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import Clock


# ############################################################
# ############################################################
# ##                                                        ##
# ##     >>>>>>>>>>   شروط الاستخدام - ضع نصك هنا   <<<<<<<<<< ##
# ##                                                        ##
# ############################################################
# ############################################################
TERMS_TEXT = """
شروط الاستخدام – تطبيق دفتر ديون الزهوب
آخر تحديث: 2026

مرحباً بك في تطبيق "دفتر ديون الزهوب". باستخدامك للتطبيق أو التسجيل فيه فإنك تقر وتوافق على جميع الشروط والأحكام الواردة أدناه. يرجى قراءتها بعناية قبل الاستخدام، فإن لم توافق على أي بند منها )لا يمكنك المتابعه(.

١( التعريفات
يقصد بالمصطلحات التالية المعاني الموضحة قرينها:
- "التطبيق": تطبيق دفتر ديون الزهوب بجميع إصداراته وخدماته.
- "المستخدم": كل شخص يقوم بإنشاء حساب أو يستخدم التطبيق بأي شكل.
- "البيانات": كل ما يدخله المستخدم من أسماء عملاء، أرقام، فواتير، سندات، مبالغ، ملاحظات، أو أي معلومات أخرى.
- "الخدمة": الوظائف التي يوفرها التطبيق من تسجيل ديون، إصدار فواتير وسندات وكشوفات، ومزامنة البيانات.

٢( طبيعة التطبيق
- التطبيق أداة مساعدة لتنظيم وتسجيل الديون والفواتير وسندات القبض وكشوف الحساب.
- التطبيق ليس جهة تمويل ولا وسيطاً مالياً ولا يقدم أي خدمات مصرفية أو ائتمانية.
- التطبيق لا يتحمل أي مسؤولية عن صحة البيانات التي يدخلها المستخدم، وعليه وحده تقع مسؤولية دقتها وصدقها.

٣( التسجيل والحساب
- يجب على المستخدم إدخال بيانات صحيحة وكاملة عند التسجيل )الاسم الرباعي، اسم المشروع، الموقع، رقم التاجر، بريد إلكتروني من نوع Gmail، وكلمة مرور(.
- يلتزم المستخدم بالحفاظ على سرية كلمة المرور وعدم مشاركتها مع أي شخص آخر.
- المستخدم مسؤول مسؤولية كاملة عن كل نشاط يحدث من خلال حسابه.
- يحق للإدارة إيقاف أو حذف أي حساب يثبت استخدامه لأغراض مخالفة أو ضارة.

٤( استخدام التطبيق
يلتزم المستخدم بما يلي:
- عدم استخدام التطبيق في أي نشاط غير قانوني أو مخالف للأنظمة السارية.
- عدم محاولة اختراق التطبيق أو التلاعب ببياناته أو بيانات المستخدمين الآخرين.
- عدم إدخال بيانات كاذبة أو مضللة أو مسيئة.
- عدم استخدام التطبيق للإضرار بالآخرين أو التشهير بهم أو انتهاك خصوصيتهم.
- الالتزام بعدم إرسال رسائل واتساب أو غيرها لأشخاص دون موافقتهم ووفق الأنظمة المعمول بها.

٥( البيانات والخصوصية
- تُخزَّن بيانات المستخدم محلياً على جهازه، كما تُخزَّن نسخة منها في السحابه الألكترونيه بحيث تتحدث البيانات كلما عملت مزامنه من داخل التطبيق.
- يتم نقل البيانات بين الجهاز السحابه الألكترونية عن طريق المزامنه اليدويه.
- لا نبيع البيانات ولا نشاركها مع أطراف تجارية، ولا نستخدمها إلا لتشغيل الخدمة.
- يمكن للمستخدم حذف حسابه نهائياً من داخل التطبيق، وسيتم عندها حذف بياناته من الجهاز ومن السحابه الألكترونيه قدر الإمكان التقني.

٦( المزامنة والأجهزة
- يدعم التطبيق المزامنة بين عدة أجهزة لنفس الحساب، كما يدعم تعدد الحسابات على الجهاز نفسه.
- عند المزامنة يتم دمج البيانات وفق أحدث تعديل، مع دعم حذف العمليات )خاصية الحذف النهائي(.
- المستخدم مسؤول عن إجراء المزامنة بشكل دوري لضمان تحديث البيانات.
- عند تغيير كلمة المرور يتم إنهاء الجلسات على الأجهزة الأخرى تلقائياً.
- يمكن للمستخدم طرد أي جهاز من قائمة الأجهزة المتصلة بحسابه.

٧( الفواتير والسندات وكشوف الحساب
- يقوم التطبيق بإنشاء الفواتير والسندات وكشوف الحساب على شكل صور PNG وملفات PDF.
- تكون هذه المستندات صادرة بناءً على البيانات التي أدخلها المستخدم، ولا تُعد سنداً قانونياً بحد ذاتها إلا إذا اعتُمدت رسمياً من الجهات المختصة.
- يتحمل المستخدم مسؤولية أي مستند يرسله لأي طرف ثالث، ويقر بأن التطبيق وسيلة تنظيمية فقط.

٨( حدود المسؤولية
- يقدم التطبيق "كما هو" دون أي ضمانات صريحة أو ضمنية.
- لا يتحمل التطبيق أو مطوّره أي مسؤولية عن أي خسارة مالية أو ضرر مباشر أو غير مباشر ناتج عن استخدام التطبيق أو تعطل الخدمة أو فقدان البيانات.
- لا يتحمل التطبيق مسؤولية انقطاع خدمة الإنترنت أو تعطل خدمات تليجرام أو واتساب أو أي طرف ثالث.
- المستخدم مسؤول عن أخذ نسخ احتياطية من بياناته المهمة، ويمكنه استخدام المزامنة لذلك.

٩( التعديلات على الشروط
- يحق للإدارة تعديل هذه الشروط في أي وقت، وسيتم إشعار المستخدم بذلك داخل التطبيق.
- استمرار المستخدم في استخدام التطبيق بعد التعديل يُعد موافقة ضمنية على الشروط المحدَّثة.

١٠( إنهاء الخدمة
- يحق للمستخدم التوقف عن استخدام التطبيق في أي وقت، كما يمكنه حذف حسابه نهائياً.
- يحق للإدارة إيقاف الخدمة أو أي حساب مخالف دون إشعار مسبق.
- عند حذف الحساب تُحذف البيانات من الجهاز ومن قنوات المزامنة قدر الإمكان التقني.

١١( حقوق الملكية
- جميع حقوق التطبيق من تصميم وبرمجة وواجهات تعود لمطوّره.
- لا يجوز نسخ التطبيق أو إعادة نشره أو تعديله أو بيعه دون إذن كتابي مسبق.

١٢( القانون الواجب التطبيق
- تخضع هذه الشروط وتُفسَّر وفقاً للأنظمة المعمول بها في بلد المستخدم، وأي نزاع ينشأ عنها يُحل ودياً، فإن تعذّر ذلك فيُحال إلى الجهات المختصة.

١٣( إقرار المستخدم
- بالضغط على "أوافق" عند التسجيل، فإنك تقر بأنك قرأت هذه الشروط كاملة وفهمتها ووافقت عليها، وتتحمل مسؤولية استخدام التطبيق وفق ما ورد فيها.
"""
# ############################################################
# ############################################################
# ##                 نهاية شروط الاستخدام                   ##
# ############################################################
# ############################################################


# ============================================================
# 3) إعدادات تليجرام
# ============================================================
# ملاحظة مهمة: البوت لازم يكون مشرفاً في القناتين بصلاحيات:
#   نشر الرسائل + تعديل الرسائل + حذف الرسائل
# وفي القناة الخاصة (USERS_CHANNEL_ID) أيضاً صلاحية "تثبيت الرسائل".
SEND_BOT_TOKEN = "8978024468:AAEcB6xVLXxLNduToBHDvLfM0sgjMHDe-z0"
USERS_CHANNEL_ID = "-1004361387248"
CLIENTS_CHANNEL_ID = "-1004442637860"
DOWNLOADS_CHANNEL_ID = "-1003753120351"   # الخطوط (وبعدها الإعلانات)

CHUNK_SIZE = 3600          # حجم الجزء الواحد (حد تليجرام 4096 حرف)


def tg_api(token, method, params=None, timeout=20):
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        if params:
            data = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(url, data=data)
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def hash_password(password):
    return hashlib.sha256(("zhoob|" + password).encode("utf-8")).hexdigest()


class TgError(Exception):
    pass


class TgDB:
    """
    قاعدة بيانات فوق Bot API بدون getUpdates (فلا شيء يُفرَّغ أبداً):

      القناة الخاصة:
        - رسالة #INDEX مثبّتة (pinned) فيها {email: message_id}
          تُقرأ بـ getChat من أي جهاز، في أي وقت، وبدون حذف شيء.
        - رسالة #USER:email لكل مستخدم فيها الاسم وهاش كلمة المرور
          وقائمة أرقام رسائل العملاء "cl".
      القناة العامة:
        - بيانات العملاء مضغوطة (zlib + base64) ومقسّمة على عدة رسائل.

      القراءة بالـ message_id تتم عبر forwardMessage (يرجع النص) ثم
      deleteMessage للنسخة المحوّلة، فلا يبقى أي أثر في القناة.
    """

    def __init__(self, token, users_ch, clients_ch, api=tg_api, sleep=time.sleep):
        self.token = token
        self.users_ch = str(users_ch)
        self.clients_ch = str(clients_ch)
        self._api = api
        self._sleep = sleep

    # ---------- طبقة الاتصال ----------
    def call(self, method, params=None):
        r = {}
        for attempt in range(4):
            r = self._api(self.token, method, params)
            if r.get("ok"):
                return r
            retry = (r.get("parameters") or {}).get("retry_after")
            if r.get("error_code") == 429 and retry:
                self._sleep(min(int(retry) + 1, 15))
                continue
            break
        return r

    @staticmethod
    def _err(r):
        return str(r.get("description") or r.get("error") or r)[:120]

    @staticmethod
    def _gone(r):
        d = str(r.get("description", "")).lower()
        return ("not found" in d or "can't be forwarded" in d
                or "message_id_invalid" in d or "message to edit" in d
                or "message to delete" in d or "message to forward" in d)

    def send(self, ch, text):
        r = self.call("sendMessage", {"chat_id": ch, "text": text,
                                      "disable_web_page_preview": "true"})
        if not r.get("ok"):
            raise TgError(self._err(r))
        return r["result"]["message_id"]

    def edit(self, ch, mid, text):
        """يرجع True لو نجح (أو لم يتغير النص)، False لو الرسالة غير موجودة."""
        r = self.call("editMessageText", {"chat_id": ch, "message_id": mid,
                                          "text": text,
                                          "disable_web_page_preview": "true"})
        if r.get("ok"):
            return True
        if "not modified" in str(r.get("description", "")).lower():
            return True
        if self._gone(r):
            return False
        raise TgError(self._err(r))

    def delete(self, ch, mid):
        r = self.call("deleteMessage", {"chat_id": ch, "message_id": mid})
        return bool(r.get("ok"))

    def read_message(self, ch, mid):
        """يقرأ نص رسالة بالـ id بدون أي تفريغ: forward ثم حذف النسخة."""
        r = self.call("forwardMessage", {"chat_id": ch, "from_chat_id": ch,
                                         "message_id": mid,
                                         "disable_notification": "true"})
        if not r.get("ok"):
            if self._gone(r):
                return None
            raise TgError(self._err(r))
        msg = r["result"]
        self.delete(ch, msg.get("message_id"))
        return msg.get("text")

    # ---------- الفهرس (الرسالة المثبّتة) ----------
    def read_index(self):
        """يرجع (message_id أو None, dict)."""
        r = self.call("getChat", {"chat_id": self.users_ch})
        if not r.get("ok"):
            raise TgError("تعذر الاتصال بالنت: ")
        pm = (r.get("result") or {}).get("pinned_message")
        if pm and (pm.get("text") or "").startswith("#INDEX"):
            try:
                body = pm["text"].split("\n", 1)[1]
                return pm["message_id"], json.loads(body)
            except Exception:
                return pm["message_id"], {}
        return None, {}

    def write_index(self, mid, idx):
        text = "#INDEX\n" + json.dumps(idx, ensure_ascii=False,
                                       separators=(",", ":"), sort_keys=True)
        if len(text) > 4000:
            raise TgError("وصلت القناة للحد الأقصى من الحسابات")
        if mid and self.edit(self.users_ch, mid, text):
            return mid
        new_mid = self.send(self.users_ch, text)
        r = self.call("pinChatMessage", {"chat_id": self.users_ch,
                                         "message_id": new_mid,
                                         "disable_notification": "true"})
        if not r.get("ok"):
            raise TgError("امنح البوت صلاحية تثبيت الرسائل في القناة الخاصة")
        return new_mid

    def _index_set(self, email, user_mid):
        mid, idx = self.read_index()
        idx[email] = user_mid
        self.write_index(mid, idx)

    def _index_remove(self, email):
        mid, idx = self.read_index()
        if email in idx:
            del idx[email]
            self.write_index(mid, idx)

    # ---------- المستخدمون ----------
    @staticmethod
    def _parse_json_text(text):
        return json.loads(text[text.index("{"):text.rindex("}") + 1])

    def get_user(self, email):
        """يرجع (record, user_mid) أو (None, None)."""
        email = email.strip().lower()
        _pin, idx = self.read_index()
        mid = idx.get(email)
        if mid:
            text = self.read_message(self.users_ch, mid)
            if text and text.startswith("#USER:"):
                try:
                    return self._parse_json_text(text), mid
                except Exception:
                    pass
        return self._legacy_find(email)

    def create_user(self, email, name, password, shop="", loc="", phone="",
                    dev_id="", dev_name=""):
        email = email.strip().lower()
        rec, _m = self.get_user(email)
        if rec:
            raise TgError("البريد مستخدم مسبقاً")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rec = {"type": "user", "email": email, "name": name,
               "shop": shop, "loc": loc, "phone": phone,
               "pw": hash_password(password), "cl": [],
               "sv": 1,
               "dev": ({dev_id: {"n": dev_name, "t": now}} if dev_id else {}),
               "created": now}
        text = f"#USER:{email}\n" + json.dumps(rec, ensure_ascii=False)
        mid = self.send(self.users_ch, text)
        try:
            self._index_set(email, mid)
        except Exception:
            self.delete(self.users_ch, mid)
            raise
        return rec, mid

    def save_user(self, rec, mid):
        rec = {k: v for k, v in rec.items() if not k.startswith("_")}
        if rec.get("password") and not rec.get("pw"):      # ترقية حساب قديم
            rec["pw"] = hash_password(rec.pop("password"))
        rec.pop("password", None)
        text = f"#USER:{rec['email']}\n" + json.dumps(rec, ensure_ascii=False)
        if not self.edit(self.users_ch, mid, text):
            mid = self.send(self.users_ch, text)
            self._index_set(rec["email"], mid)
        return mid

    @staticmethod
    def check_password(rec, password):
        if rec.get("pw"):
            return rec["pw"] == hash_password(password)
        return rec.get("password") == password          # حسابات قديمة

    # ---------- العملاء ----------
    @staticmethod
    def _pack(data):
        raw = json.dumps(data, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        b64 = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
        return [b64[i:i + CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)] or [""]

    def read_clients(self, rec):
        """يرجع (dict البيانات, قائمة نصوص الأجزاء). {} لو ما فيه شيء."""
        mids = rec.get("cl") or []
        if not mids:
            return {}, []
        parts, texts = [], []
        for m in mids:
            t = self.read_message(self.clients_ch, m)
            if t is None:
                raise TgError("جزء من بيانات العملاء مفقود في القناة")
            texts.append(t)
            parts.append(t.split("\n", 1)[1] if "\n" in t else "")
        try:
            raw = zlib.decompress(base64.b64decode("".join(parts)))
            return json.loads(raw.decode("utf-8")), texts
        except Exception:
            raise TgError("بيانات العملاء في القناة تالفة")

    def write_clients(self, rec, user_mid, data, old_texts=None):
        """يرفع data على أجزاء، ويحدّث رسائل الأجزاء الموجودة. يرجع rec المحدّث."""
        email = rec["email"]
        chunks = self._pack(data)
        total = len(chunks)
        old_mids = list(rec.get("cl") or [])
        old_texts = old_texts or []
        new_mids = []
        for i, ch in enumerate(chunks):
            text = f"#CL:{email}:{i + 1}/{total}\n{ch}"
            if i < len(old_mids):
                if i < len(old_texts) and old_texts[i] == text:
                    new_mids.append(old_mids[i])
                    continue
                if self.edit(self.clients_ch, old_mids[i], text):
                    new_mids.append(old_mids[i])
                    continue
            new_mids.append(self.send(self.clients_ch, text))
        for m in old_mids[total:]:
            self.delete(self.clients_ch, m)
        if new_mids != old_mids:
            rec = dict(rec)
            rec["cl"] = new_mids
            self.save_user(rec, user_mid)
        return rec

    # ---------- حذف الحساب ----------
    def delete_account(self, rec, user_mid):
        email = rec["email"]
        for m in rec.get("cl") or []:
            self.delete(self.clients_ch, m)
        self._index_remove(email)
        self.delete(self.users_ch, user_mid)

    # ---------- ترحيل الحسابات القديمة (قبل الفهرس) ----------
    def _legacy_find(self, email):
        """يبحث عن #USER:email القديمة عبر getUpdates بدون offset
        (لا تُفرّغ شيئاً)، وإن وجدها ينقلها للفهرس. يرجع (record, mid)."""
        try:
            r = self.call("getUpdates", {"limit": 100, "timeout": 0})
            if not r.get("ok"):
                return None, None
            users, clients = {}, {}
            for u in r.get("result", []):
                p = u.get("channel_post") or u.get("edited_channel_post")
                if not p:
                    continue
                txt = p.get("text") or ""
                chat = str((p.get("chat") or {}).get("id"))
                if txt.startswith("#USER:") and chat == self.users_ch:
                    users[txt.split("\n", 1)[0][6:].strip().lower()] = (txt, p["message_id"])
                elif txt.startswith("#CLIENTS:") and chat == self.clients_ch:
                    clients[txt.split("\n", 1)[0][9:].strip().lower()] = (txt, p["message_id"])
            if email not in users:
                return None, None
            txt, mid = users[email]
            rec = self._parse_json_text(txt)
            rec.setdefault("cl", [])
            rec["email"] = email
            if email in clients:
                ctxt, cmid = clients[email]
                try:
                    rec["_legacy_clients"] = self._parse_json_text(ctxt)
                    rec["_legacy_clients_mid"] = cmid
                except Exception:
                    pass
            try:
                self._index_set(email, mid)
            except Exception as e:
                print(f"[LEGACY INDEX] {e}")
            return rec, mid
        except Exception as e:
            print(f"[LEGACY] {e}")
            return None, None


DB = TgDB(SEND_BOT_TOKEN, USERS_CHANNEL_ID, CLIENTS_CHANNEL_ID)


# ---------- التحميلات (خطوط / إعلانات لاحقاً) ----------
def dl_probe(mid):
    """يقرأ بيانات الملف في الرسالة mid بدون أي أثر. يرجع (gone, doc)."""
    r = DB.call("forwardMessage", {"chat_id": DB.users_ch,
                                   "from_chat_id": DOWNLOADS_CHANNEL_ID,
                                   "message_id": mid,
                                   "disable_notification": "true"})
    if not r.get("ok"):
        d = str(r.get("description", "")).lower()
        if ("chat not found" in d or "not a member" in d
                or r.get("error_code") in (401, 403)):
            raise TgError("تعذر الوصول إلى الخطوط المتاحة")
        if r.get("error_code") == 429 or "retry" in d:
            raise TgError("تعذر الاتصال، حاول لاحقاً")
        if DB._gone(r) or r.get("error_code") == 400:
            return True, None
        raise TgError(DB._err(r))
    msg = r["result"]
    DB.delete(DB.users_ch, msg.get("message_id"))
    return False, (msg.get("document") or {})


def scan_downloads(catalog, tolerance=25):
    """يمسح الرسائل الجديدة ويضيف الملفات للفهرس المحلي (تراكمي)."""
    items = catalog.setdefault("items", {})
    mid = int(catalog.get("last", 0))
    newest = mid
    misses = 0
    while misses < tolerance:
        mid += 1
        gone, doc = dl_probe(mid)
        if gone:
            misses += 1
            continue
        misses = 0
        newest = mid
        if doc and doc.get("file_name"):
            items[doc["file_name"]] = {"mid": mid,
                                       "size": int(doc.get("file_size") or 0)}
    catalog["last"] = newest
    return catalog


def download_font(name, item):
    gone, doc = dl_probe(int(item["mid"]))
    if gone or not doc or doc.get("file_name") != name:
        raise TgError("الخط غير متاح حالياً")
    r = DB.call("getFile", {"file_id": doc["file_id"]})
    if not r.get("ok"):
        raise TgError("تعذر تحميل الخط")
    url = "https://api.telegram.org/file/bot%s/%s" % (
        DB.token, r["result"]["file_path"])
    os.makedirs(FONT_STORE, exist_ok=True)
    tmp = os.path.join(FONT_STORE, name + ".part")
    final = os.path.join(FONT_STORE, name)
    with urllib.request.urlopen(url, timeout=60) as resp, open(tmp, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    if os.path.getsize(tmp) < 1000:
        os.remove(tmp)
        raise TgError("الملف غير صالح")
    os.replace(tmp, final)
    register_user_fonts()


def merge_client_data(server_data, local_clients, local_deleted):
    """يضم بالـ id مع دعم الحذف (tombstones) وآخر تعديل (mod).
    يرجع (قائمة العملاء المدمجة، قائمة المحذوفات)."""
    server_data = server_data or {}
    deleted = []
    seen_d = set()
    for x in list(server_data.get("deleted", []) or []) + list(local_deleted or []):
        if x not in seen_d:
            seen_d.add(x)
            deleted.append(x)
    deleted = deleted[-2000:]
    dset = set(deleted)

    def newer(a, b):
        """يرجع الأحدث؛ عند التعادل يفضَّل a (السيرفر)."""
        return b if (b.get("mod", "") > a.get("mod", "")) else a

    s_map, l_map, order = {}, {}, []
    for c in server_data.get("clients", []) or []:
        c.setdefault("id", gen_id())
        s_map[c["id"]] = c
        order.append(c["id"])
    for c in local_clients or []:
        c.setdefault("id", gen_id())
        l_map[c["id"]] = c
        if c["id"] not in s_map:
            order.append(c["id"])

    out = []
    for cid in order:
        if cid in dset:
            continue
        sc, lc = s_map.get(cid), l_map.get(cid)
        if sc and lc:
            base = dict(newer(sc, lc))
            invs = {}
            for inv in (sc.get("invoices") or []):
                inv.setdefault("id", gen_id())
                invs[inv["id"]] = inv
            for inv in (lc.get("invoices") or []):
                inv.setdefault("id", gen_id())
                if inv["id"] in invs:
                    invs[inv["id"]] = newer(invs[inv["id"]], inv)
                else:
                    invs[inv["id"]] = inv
            merged_invs = list(invs.values())
        else:
            base = dict(sc or lc)
            merged_invs = list(base.get("invoices") or [])
            for inv in merged_invs:
                inv.setdefault("id", gen_id())
        merged_invs = [i for i in merged_invs if i.get("id") not in dset]
        merged_invs.sort(key=lambda x: x.get("date", ""))
        base["invoices"] = merged_invs
        bal = 0
        for inv in merged_invs:
            t = inv.get("total", 0)
            bal += t if inv.get("kind", "فاتورة") == "فاتورة" else -t
        base["balance"] = bal
        out.append(base)
    return out, deleted


# ============================================================
# 4) أدوات مساعدة
# ============================================================
def _auto_padding():
    try:
        w = Window.width
        if w <= 0:
            return dp(14)
        p = w * 0.03
        p = max(dp(10), min(dp(20), p))
        return p
    except Exception:
        return dp(14)


def gen_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}_{rand}"


def get_device_name():
    try:
        if platform == "android":
            from jnius import autoclass
            B = autoclass("android.os.Build")
            return ("%s %s" % (B.MANUFACTURER, B.MODEL)).strip()[:40] or "جهاز"
    except Exception:
        pass
    try:
        import socket
        return socket.gethostname()[:40] or "جهاز"
    except Exception:
        return "جهاز"


# بيانات البائع الحالي (تظهر أسفل الفواتير وكشف الحساب وسند القبض)
SELLER = {"name": "", "shop": "", "loc": "", "phone": ""}


def set_seller(user):
    user = user or {}
    for k in SELLER:
        SELLER[k] = str(user.get(k, "") or "")


def seller_lines():
    out = []
    if SELLER.get("shop"):
        out.append(SELLER["shop"])
    if SELLER.get("phone"):
        out.append("للتواصل: " + SELLER["phone"])
    return out


# ============================================================
# 5) الألوان
# ============================================================
WHITE = (1, 1, 1, 1)
SOFT_WHITE = (1, 1, 1, 0.85)
GLASS = (1, 1, 1, 0.22)

_LIGHT = dict(
    PRIMARY=(0.09, 0.29, 0.49, 1),
    HEADER=(0.09, 0.29, 0.49, 1),
    TEXT=(0.12, 0.16, 0.24, 1),
    MUTED=(0.46, 0.51, 0.59, 1),
    BG=(0.95, 0.96, 0.98, 1),
    CARD=(1, 1, 1, 1),
    SOFT_BLUE=(0.90, 0.94, 0.99, 1),
    INPUT_BG=(0.985, 0.988, 0.995, 1),
    INPUT_BORDER=(0.80, 0.83, 0.88, 1),
    HINT=(0.62, 0.65, 0.70, 1),
    BORDER=(0.90, 0.92, 0.95, 1),
    RED=(0.80, 0.22, 0.22, 1),
    INV_RED=(0.86, 0.33, 0.30, 1),
    GREEN=(0.13, 0.60, 0.36, 1),
    ORANGE=(0.92, 0.55, 0.12, 1),
    BLUE=(0.18, 0.47, 0.80, 1),
    GRAY_BTN=(0.45, 0.47, 0.52, 1),
)

_DARK = dict(
    PRIMARY=(0.49, 0.74, 1.00, 1),
    HEADER=(0.09, 0.15, 0.27, 1),
    TEXT=(0.91, 0.93, 0.97, 1),
    MUTED=(0.58, 0.65, 0.76, 1),
    BG=(0.043, 0.059, 0.098, 1),
    CARD=(0.078, 0.102, 0.157, 1),
    SOFT_BLUE=(0.11, 0.17, 0.29, 1),
    INPUT_BG=(0.055, 0.075, 0.12, 1),
    INPUT_BORDER=(0.20, 0.26, 0.37, 1),
    HINT=(0.40, 0.47, 0.58, 1),
    BORDER=(0.15, 0.20, 0.30, 1),
    RED=(0.90, 0.33, 0.35, 1),
    INV_RED=(0.90, 0.35, 0.38, 1),
    GREEN=(0.16, 0.66, 0.45, 1),
    ORANGE=(0.95, 0.60, 0.18, 1),
    BLUE=(0.27, 0.54, 0.93, 1),
    GRAY_BTN=(0.26, 0.31, 0.41, 1),
)

THEMES = {"light": _LIGHT, "dark": _DARK}
CURRENT_THEME = "light"


def is_dark():
    return CURRENT_THEME == "dark"


def apply_theme(name):
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else "light"
    globals().update(THEMES[CURRENT_THEME])
    try:
        Window.clearcolor = THEMES[CURRENT_THEME]["BG"]
    except Exception:
        pass


apply_theme("light")

AVATAR_COLORS = [
    (0.18, 0.47, 0.80, 1),
    (0.55, 0.36, 0.75, 1),
    (0.13, 0.60, 0.36, 1),
    (0.92, 0.55, 0.12, 1),
    (0.80, 0.30, 0.45, 1),
    (0.10, 0.58, 0.64, 1),
]


# ============================================================
# 6) أشكال الحروف العربية
# ============================================================
ARABIC_FORMS = {
    '\u0627': ('\uFE8D', '\uFE8D', '\uFE8E', '\uFE8E', False),
    '\u0622': ('\uFE81', '\uFE81', '\uFE82', '\uFE82', False),
    '\u0623': ('\uFE83', '\uFE83', '\uFE84', '\uFE84', False),
    '\u0625': ('\uFE87', '\uFE87', '\uFE88', '\uFE88', False),
    '\u0624': ('\uFE85', '\uFE85', '\uFE86', '\uFE86', False),
    '\u0629': ('\uFE93', '\uFE93', '\uFE94', '\uFE94', False),
    '\u062F': ('\uFEA9', '\uFEA9', '\uFEAA', '\uFEAA', False),
    '\u0630': ('\uFEAB', '\uFEAB', '\uFEAC', '\uFEAC', False),
    '\u0631': ('\uFEAD', '\uFEAD', '\uFEAE', '\uFEAE', False),
    '\u0632': ('\uFEAF', '\uFEAF', '\uFEB0', '\uFEB0', False),
    '\u0648': ('\uFEED', '\uFEED', '\uFEEE', '\uFEEE', False),
    '\u0649': ('\uFEEF', '\uFEEF', '\uFEF0', '\uFEF0', False),
    '\u0621': ('\uFE80', '\uFE80', '\uFE80', '\uFE80', False),
    '\u0626': ('\uFE89', '\uFE8B', '\uFE8C', '\uFE8A', True),
    '\u0628': ('\uFE8F', '\uFE91', '\uFE92', '\uFE90', True),
    '\u062A': ('\uFE95', '\uFE97', '\uFE98', '\uFE96', True),
    '\u062B': ('\uFE99', '\uFE9B', '\uFE9C', '\uFE9A', True),
    '\u062C': ('\uFE9D', '\uFE9F', '\uFEA0', '\uFE9E', True),
    '\u062D': ('\uFEA1', '\uFEA3', '\uFEA4', '\uFEA2', True),
    '\u062E': ('\uFEA5', '\uFEA7', '\uFEA8', '\uFEA6', True),
    '\u0633': ('\uFEB1', '\uFEB3', '\uFEB4', '\uFEB2', True),
    '\u0634': ('\uFEB5', '\uFEB7', '\uFEB8', '\uFEB6', True),
    '\u0635': ('\uFEB9', '\uFEBB', '\uFEBC', '\uFEBA', True),
    '\u0636': ('\uFEBD', '\uFEBF', '\uFEC0', '\uFEBE', True),
    '\u0637': ('\uFEC1', '\uFEC3', '\uFEC4', '\uFEC2', True),
    '\u0638': ('\uFEC5', '\uFEC7', '\uFEC8', '\uFEC6', True),
    '\u0639': ('\uFEC9', '\uFECB', '\uFECC', '\uFECA', True),
    '\u063A': ('\uFECD', '\uFECF', '\uFED0', '\uFECE', True),
    '\u0641': ('\uFED1', '\uFED3', '\uFED4', '\uFED2', True),
    '\u0642': ('\uFED5', '\uFED7', '\uFED8', '\uFED6', True),
    '\u0643': ('\uFED9', '\uFEDB', '\uFEDC', '\uFEDA', True),
    '\u0644': ('\uFEDD', '\uFEDF', '\uFEE0', '\uFEDE', True),
    '\u0645': ('\uFEE1', '\uFEE3', '\uFEE4', '\uFEE2', True),
    '\u0646': ('\uFEE5', '\uFEE7', '\uFEE8', '\uFEE6', True),
    '\u0647': ('\uFEE9', '\uFEEB', '\uFEEC', '\uFEEA', True),
    '\u064A': ('\uFEF1', '\uFEF3', '\uFEF4', '\uFEF2', True),
}

DIACRITICS = set('\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670\u0640')

LAM_ALEF = {
    '\u0644\u0622': ('\uFEF5', '\uFEF6'),
    '\u0644\u0623': ('\uFEF7', '\uFEF8'),
    '\u0644\u0625': ('\uFEF9', '\uFEFA'),
    '\u0644\u0627': ('\uFEFB', '\uFEFC'),
}


def is_arabic_char(ch):
    return ('\u0600' <= ch <= '\u06FF') or ('\uFB50' <= ch <= '\uFEFF')


def _prev_element_connects(chars, idx):
    for j in range(idx - 1, -1, -1):
        kind, ch = chars[j]
        if kind == 'C':
            if ch in DIACRITICS:
                continue
            if ch in ARABIC_FORMS:
                return ARABIC_FORMS[ch][4]
            return False
        if kind == 'PAIR':
            return False
    return False


def _has_element_after(chars, idx):
    for j in range(idx + 1, len(chars)):
        kind, ch = chars[j]
        if kind == 'C':
            if ch in DIACRITICS:
                continue
            if ch in ARABIC_FORMS:
                return True
            return False
        if kind == 'PAIR':
            return True
    return False


def shape_word(word):
    if not word:
        return ""
    chars = []
    i = 0
    while i < len(word):
        if i + 1 < len(word):
            pair = word[i:i + 2]
            if pair in LAM_ALEF:
                chars.append(('PAIR', pair))
                i += 2
                continue
        chars.append(('C', word[i]))
        i += 1
    result = []
    for idx in range(len(chars)):
        kind, value = chars[idx]
        if kind == 'PAIR':
            prev_conn = _prev_element_connects(chars, idx)
            iso, fin = LAM_ALEF[value]
            result.append(fin if prev_conn else iso)
            continue
        ch = value
        if ch in DIACRITICS:
            result.append(ch)
            continue
        if ch in ARABIC_FORMS:
            isolated, initial, medial, final, connects_fwd = ARABIC_FORMS[ch]
            prev_conn = _prev_element_connects(chars, idx)
            next_exists = _has_element_after(chars, idx)
            if prev_conn and connects_fwd and next_exists:
                result.append(medial)
            elif prev_conn:
                result.append(final)
            elif connects_fwd and next_exists:
                result.append(initial)
            else:
                result.append(isolated)
        else:
            result.append(ch)
    result.reverse()
    return ''.join(result)


def ar(text):
    if not text:
        return ""
    text = str(text)
    segments = []
    current = []
    current_is_ar = None
    for ch in text:
        if ch.isspace():
            if current:
                segments.append((current_is_ar, ''.join(current)))
                current = []
                current_is_ar = None
            segments.append((None, ch))
        else:
            ch_is_ar = is_arabic_char(ch)
            if current_is_ar is None:
                current_is_ar = ch_is_ar
                current.append(ch)
            elif ch_is_ar == current_is_ar:
                current.append(ch)
            else:
                segments.append((current_is_ar, ''.join(current)))
                current = [ch]
                current_is_ar = ch_is_ar
    if current:
        segments.append((current_is_ar, ''.join(current)))
    out = []
    for is_ar, seg in segments:
        if is_ar is True:
            out.append(shape_word(seg))
        else:
            out.append(seg)
    has_ar = any(x is True for x, _ in segments)
    if has_ar:
        out.reverse()
    return ''.join(out)


# ============================================================
# 7) تحميل الخط
# ============================================================
FONT_NAME = "AppFont"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def get_font_dir():
    # [إصلاح كراش 1] حُذفت كل محاولات الكتابة في /sdcard/ و /storage/emulated/0
    # لأنها ممنوعة في أندرويد 11+ (Scoped Storage). نستخدم مجلد التطبيق الخاص فقط،
    # وعند أي فشل نرجع APP_DIR بدل أن يتوقف التطبيق.
    try:
        if platform == "android":
            from android.storage import app_storage_path
            d = os.path.join(app_storage_path(), "fonts")
        else:
            d = os.path.join(APP_DIR, "fonts")
        os.makedirs(d, exist_ok=True)
        return d
    except Exception as e:
        print(f"[FONT] get_font_dir failed: {e}")
        return APP_DIR


FONT_DIR = get_font_dir()
print(f"[FONT] DIR: {FONT_DIR}")

FONT_CANDIDATES = [
    os.path.join(APP_DIR, "font.ttf"),
    os.path.join(APP_DIR, "font.otf"),
    os.path.join(APP_DIR, "font.ttc"),
    os.path.join(APP_DIR, "font.ttf"),
    os.path.join(APP_DIR, "fonts", "font.ttf"),
    os.path.join(APP_DIR, "fonts", "font.otf"),
    os.path.join(APP_DIR, "fonts", "font.ttf"),
    os.path.join(FONT_DIR, "font.ttf"),
    # [إصلاح كراش 3] حُذفت مسارات /sdcard/ نهائياً (تفشل على أندرويد 11+)
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/DroidSansArabic.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
    "/system/fonts/DroidSansFallback.ttf",
    "/system/fonts/DroidNaskh-Regular.ttf",
]


def _scan_dir(d, only_names=None):
    found = []
    if not os.path.isdir(d):
        return found
    try:
        for f in sorted(os.listdir(d)):
            low = f.lower()
            if not low.endswith((".ttf", ".otf", ".ttc")):
                continue
            if only_names and not any(k in low for k in only_names):
                continue
            found.append(os.path.join(d, f))
    except Exception:
        pass
    return found


def _iter_font_candidates():
    seen = set()
    pool = list(FONT_CANDIDATES)
    # [إصلاح كراش 4] نمسح فقط المجلدات الآمنة (مجلد التطبيق)، بدون /sdcard/
    for d in [APP_DIR, os.path.join(APP_DIR, "fonts"), FONT_DIR]:
        pool.extend(_scan_dir(d))
    pool.extend(_scan_dir("/system/fonts",
                          only_names=("arab", "naskh", "kufi", "fallback")))
    for p in pool:
        if p in seen:
            continue
        seen.add(p)
        try:
            if os.path.exists(p) and os.path.getsize(p) > 1000:
                yield p
        except Exception:
            continue


def _font_has_arabic(name):
    try:
        a = CoreLabel(text="\uFEE1\uFEE3\uFEE4\uFEA3", font_size=28, font_name=name)
        a.refresh()
        ta = a.texture
        if ta is None or ta.width < 4:
            return False
    except Exception as e:
        print(f"[FONT TEST ERR] {e}")
        return False
    try:
        b = CoreLabel(text="\U0010FFFD\U0010FFFD\U0010FFFD\U0010FFFD",
                      font_size=28, font_name=name)
        b.refresh()
        tb = b.texture
    except Exception:
        tb = None
    if tb is None:
        return True
    if ta.size != tb.size:
        return True
    try:
        return ta.pixels != tb.pixels
    except Exception:
        return True


FONT_PATH = None
FONT_REGISTERED = False


def init_fallback_font():
    """يبحث عن أول خط عربي صالح (مجلد التطبيق ثم خطوط النظام).
    [إصلاح كراش 6] كل LabelBase.register داخل try/except مع log واضح، فلو فشل
    خط واحد ننتقل للتالي ولا يتوقف التطبيق. وتعمل الدالة فقط لو font.otf
    الأساسي غير موجود (فلا نختبر الخطوط عند كل تشغيل)."""
    global FONT_NAME, FONT_PATH, FONT_REGISTERED
    n = 0
    for p in _iter_font_candidates():
        n += 1
        name = "AppFont%d" % n
        try:
            LabelBase.register(name=name, fn_regular=p)
        except Exception as e:
            print(f"[FONT] register FAILED {p}: {e}")
            continue
        try:
            ok = _font_has_arabic(name)
        except Exception as e:
            print(f"[FONT] glyph test FAILED {p}: {e}")
            continue
        if ok:
            FONT_NAME, FONT_PATH, FONT_REGISTERED = name, p, True
            print(f"[FONT] OK: {p}")
            return True
        print(f"[FONT] no arabic glyphs: {p}")
    print("[FONT] WARN: no usable Arabic font found!")
    return False


def _font_name():
    return FONT_NAME if FONT_REGISTERED else "Roboto"


# ---- الخطوط: font.otf هو الأساسي، والباقي (font1.otf ...) يُنزَّل من الإعدادات ----
USER_FONTS = {}        # اسم الملف -> (الاسم المسجّل، المسار)
FONT_NAME_RE = re.compile(r"font\d*\.otf")


def font_sort_key(fn):
    m = re.fullmatch(r"font(\d*)\.otf", fn)
    return int(m.group(1) or 0) if m else 10 ** 6


def font_label(fn):
    m = re.fullmatch(r"font(\d*)\.otf", fn)
    n = int(m.group(1) or 0) if m else 0
    return "الخط الأساسي" if n == 0 else "خط %d" % n


def _find_font_file(fn):
    # [إصلاح كراش 4] مجلدات التطبيق فقط، بدون /sdcard/
    for d in (APP_DIR, os.path.join(APP_DIR, "fonts"), FONT_DIR):
        p = os.path.join(d, fn)
        try:
            if os.path.exists(p) and os.path.getsize(p) > 1000:
                return p
        except Exception:
            pass
    return None


def register_user_fonts():
    """يسجّل font.otf الأساسي + أي خط تم تنزيله سابقاً."""
    cands = {}
    base = _find_font_file("font.otf")
    if base:
        cands["font.otf"] = base
    try:
        for f in os.listdir(FONT_STORE):
            p = os.path.join(FONT_STORE, f)
            if (FONT_NAME_RE.fullmatch(f) and f != "font.otf"
                    and os.path.getsize(p) > 1000):
                cands[f] = p
    except Exception:
        pass
    for fn, p in cands.items():
        if USER_FONTS.get(fn, (None, None))[1] == p:
            continue
        nm = "UF_" + fn.replace(".", "_")
        try:
            LabelBase.register(name=nm, fn_regular=p)
            USER_FONTS[fn] = (nm, p)
        except Exception as e:
            print(f"[FONT] register FAILED for user font {fn} ({p}): {e}")


def set_app_font(fn):
    """يفعّل الخط fn لكل التطبيق (الشاشة + صور الفواتير). يرجع True لو نجح."""
    global FONT_NAME, FONT_PATH, FONT_REGISTERED
    info = USER_FONTS.get(fn)
    if not info:
        return False
    FONT_NAME, FONT_PATH = info
    FONT_REGISTERED = True
    return True


# ============================================================
# 8) مسار البيانات
# ============================================================
if platform == "android":
    try:
        from android.storage import app_storage_path
        DATA_DIR = app_storage_path()
    except Exception:
        DATA_DIR = APP_DIR
else:
    DATA_DIR = APP_DIR

DATA_FILE = os.path.join(DATA_DIR, "debtbook_data.json")
FONT_STORE = os.path.join(DATA_DIR, "dl_fonts")
try:
    os.makedirs(FONT_STORE, exist_ok=True)
except Exception:
    pass

# [إصلاح كراش 7] تهيئة الخطوط كلها محمية بـ try/except: أي خطأ هنا لا يُسقط التطبيق.
try:
    register_user_fonts()
    if not set_app_font("font.otf"):
        init_fallback_font()
except Exception as _fe:
    print(f"[FONT] init failed (ignored): {_fe}")

# ---- سجل الأعطال: يُكتب في مجلد التطبيق ويُعرض عند التشغيل التالي ----
import traceback
CRASH_LOG = os.path.join(DATA_DIR, "crash.log")


def _write_crash(text):
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n" + text + "\n\n")
    except Exception:
        pass


def _excepthook(tp, val, tb):
    _write_crash("".join(traceback.format_exception(tp, val, tb)))
    sys.__excepthook__(tp, val, tb)


sys.excepthook = _excepthook
try:
    threading.excepthook = lambda a: _write_crash(
        "".join(traceback.format_exception(a.exc_type, a.exc_value, a.exc_traceback)))
except Exception:
    pass


def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path, data):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        print(f"[SAVE] {e}")


def load_data():
    d = load_json(DATA_FILE, None)
    if d is None:
        return {"clients": [], "user": None, "_tg_meta": {},
                "_deleted": [], "owner": None}
    if "clients" not in d:
        d["clients"] = []
    if "user" not in d:
        d["user"] = None
    if "_tg_meta" not in d:
        d["_tg_meta"] = {}
    if "_deleted" not in d:
        d["_deleted"] = []
    if not d.get("owner") and (d.get("user") or {}).get("email"):
        d["owner"] = d["user"]["email"]
    for c in d.get("clients", []):
        if "invoices" not in c:
            c["invoices"] = []
        if "id" not in c:
            c["id"] = gen_id()
        for inv in c["invoices"]:
            if "id" not in inv:
                inv["id"] = gen_id()
    return d


def save_data(data):
    save_json(DATA_FILE, data)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def now_full():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(v):
    try:
        return f"{v:,.0f}"
    except Exception:
        return "0"


def money_signed(v):
    try:
        if v < 0:
            return "-" + f"{abs(v):,.0f}"
        return f"{v:,.0f}"
    except Exception:
        return "0"


# ============================================================
# 9) DrawnText
# ============================================================
_ALL_TEXTS = weakref.WeakSet()


class DrawnText(Widget):
    _tex_cache = {}

    def __init__(self, text="", font_size=dp(15), color=None,
                 halign="right", valign="middle", padding_x=None,
                 min_size=dp(9), line_gap=dp(3), font_override=None, **kwargs):
        super().__init__(**kwargs)
        self._font_override = font_override
        if color is None:
            color = TEXT
        self._raw_text = ""
        self._lines = []
        self._font_size = float(font_size)
        self._color = color
        self._halign = halign
        self._valign = valign
        if padding_x is None:
            self._padding_x = _auto_padding()
        else:
            self._padding_x = padding_x
        self._min_size = float(min_size)
        self._line_gap = line_gap
        self._rendered = None
        self._rects = []
        self._trans = None
        _ALL_TEXTS.add(self)
        self.bind(size=self._on_size, pos=self._on_pos)
        self.text = text
        Clock.schedule_once(lambda dt: self.force_refresh(), 0.1)

    @property
    def text(self):
        return self._raw_text

    @text.setter
    def text(self, value):
        self._raw_text = str(value) if value is not None else ""
        self._lines = [ar(line) for line in self._raw_text.split("\n")]
        self._rendered = None
        self._redraw()

    def _get_tex(self, display, size_int):
        fname = getattr(self, "_font_override", None) or _font_name()
        key = (display, size_int, fname, tuple(self._color))
        cached = DrawnText._tex_cache.get(key)
        if cached is not None:
            return cached
        tex = None
        attempts = [
            dict(text=display, font_size=size_int, font_name=fname,
                 color=self._color, halign="left", valign="middle",
                 padding=(0, 0, 0, 0)),
            dict(text=display, font_size=size_int, font_name=fname,
                 color=self._color),
            dict(text=display, font_size=size_int, font_name=fname),
        ]
        for opts in attempts:
            try:
                cl = CoreLabel(**opts)
                cl.refresh()
                tex = cl.texture
                if tex is not None:
                    break
            except Exception as e:
                print(f"[TEX ERR] {e}")
        if tex is not None:
            DrawnText._tex_cache[key] = tex
        return tex

    def _measure_line_height(self, size_int):
        t = self._get_tex("م", size_int)
        if t is not None and t.height > 0:
            return int(t.height)
        return int(size_int * 1.35)

    def _render_at(self, size_int):
        h = self._measure_line_height(size_int)
        out = []
        for line in self._lines:
            tex = self._get_tex(line, size_int) if line else None
            out.append((tex, h))
        return out

    def _compute_locked(self, avail):
        size = float(self._font_size)
        for _ in range(6):
            size_int = max(int(self._min_size), int(round(size)))
            rendered = self._render_at(size_int)
            widest = 0
            for tex, _h in rendered:
                if tex is not None and tex.width > widest:
                    widest = tex.width
            if widest <= avail or size_int <= int(self._min_size):
                return size_int, rendered
            ratio = avail / float(widest)
            new_size = max(self._min_size, size * ratio * 0.98)
            if new_size >= size - 0.5:
                return size_int, rendered
            size = new_size
        size_int = max(int(self._min_size), int(round(size)))
        return size_int, self._render_at(size_int)

    def _on_size(self, *args):
        if self.width < 2 or self.height < 2:
            return
        self._rendered = None
        self._redraw()

    def _on_pos(self, *args):
        t = getattr(self, "_trans", None)
        if t is not None:
            t.xy = (int(round(self.x)), int(round(self.y)))

    def force_refresh(self):
        self._rendered = None
        self._redraw()

    def _redraw(self):
        if self.width < 2 or self.height < 2:
            return
        if not any(self._lines):
            self.canvas.clear()
            self._rects = []
            self._rendered = None
            self._trans = None
            return
        try:
            W, H = self.width, self.height
            avail = max(W - 2 * self._padding_x, dp(4))
            size_int, rendered = self._compute_locked(avail)
            self._rendered = rendered
            self.canvas.clear()
            self._rects = []
            heights = [h for _t, h in rendered]
            total_h = sum(heights) + self._line_gap * (len(heights) - 1)
            if self._valign == "top":
                y_top = H
            elif self._valign == "bottom":
                y_top = total_h
            else:
                y_top = (H + total_h) / 2.0
            with self.canvas:
                PushMatrix()
                self._trans = Translate(int(round(self.x)), int(round(self.y)))
                Color(1, 1, 1, 1)
                for i, (tex, h) in enumerate(rendered):
                    y_bottom = y_top - h
                    if tex is not None:
                        tw = tex.width
                        th = tex.height
                        if tw > avail:
                            k = avail / float(tw)
                            tw, th = tw * k, th * k
                        if self._halign == "right":
                            x = W - tw - self._padding_x
                        elif self._halign == "center":
                            x = W / 2.0 - tw / 2.0
                        else:
                            x = self._padding_x
                        y_draw = y_bottom + (h - th) / 2.0
                        rect = Rectangle(texture=tex,
                                         pos=(int(x), int(y_draw)),
                                         size=(tw, th))
                        self._rects.append(rect)
                    else:
                        self._rects.append(None)
                    y_top = y_bottom - self._line_gap
                PopMatrix()
        except Exception as e:
            print(f"[DrawnText redraw] {e}")


def refresh_all_texts(*args):
    for w in list(_ALL_TEXTS):
        try:
            w.force_refresh()
        except Exception:
            pass


def schedule_refresh(delay=0.05):
    Clock.schedule_once(refresh_all_texts, delay)


# ============================================================
# 10) DrawnLabel / DrawnButton / CardBox / Avatar / ArabicTextInput
# ============================================================
class DrawnLabel(FloatLayout):
    def __init__(self, text="", font_size=dp(15), color=None,
                 halign="right", **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(28))
        super().__init__(**kwargs)
        self._dt = DrawnText(text=text, font_size=font_size, color=color,
                             halign=halign,
                             size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._dt.disabled = True
        self.add_widget(self._dt)

    @property
    def text(self):
        return self._dt.text

    @text.setter
    def text(self, value):
        self._dt.text = value


class DrawnButton(FloatLayout):
    def __init__(self, text="", font_size=dp(15), color=WHITE,
                 background_color=(0.3, 0.5, 0.7, 1),
                 halign="center", on_release=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        self._on_release_cbs = []
        super().__init__(**kwargs)
        self._bg_color = tuple(background_color)
        self._pressed_rect = None

        with self.canvas.before:
            self._bg_col = Color(*self._bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(12)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self._dt = DrawnText(text=text, font_size=font_size, color=color,
                             halign=halign,
                             size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._dt.disabled = True
        self.add_widget(self._dt)

        if on_release:
            self._on_release_cbs.append(on_release)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        if self._pressed_rect:
            self._pressed_rect.pos = self.pos
            self._pressed_rect.size = self.size

    def bind(self, **kwargs):
        if "on_release" in kwargs:
            self._on_release_cbs.append(kwargs.pop("on_release"))
        if kwargs:
            return super().bind(**kwargs)

    def set_bg(self, rgba):
        self._bg_color = tuple(rgba)
        self._bg_col.rgba = tuple(rgba)

    def _show_pressed(self):
        if self._pressed_rect:
            return
        try:
            r, g, b = self._bg_color[:3]
            a = self._bg_color[3] if len(self._bg_color) > 3 else 1
            with self.canvas.before:
                Color(r * 0.75, g * 0.75, b * 0.75, min(1, a + 0.15))
                self._pressed_rect = RoundedRectangle(pos=self.pos,
                                                      size=self.size,
                                                      radius=[dp(12)])
        except Exception:
            pass

    def _hide_pressed(self):
        if self._pressed_rect:
            try:
                self.canvas.before.remove(self._pressed_rect)
            except Exception:
                pass
            self._pressed_rect = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self._show_pressed()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self._hide_pressed()
            for cb in list(self._on_release_cbs):
                try:
                    cb(self)
                except Exception as e:
                    print(f"[CB] {e}")
            return True
        self._hide_pressed()
        return super().on_touch_up(touch)

    @property
    def text(self):
        return self._dt.text

    @text.setter
    def text(self, value):
        self._dt.text = value


def mk_btn(text, **kw):
    font_size = kw.pop("font_size", dp(15))
    color = kw.pop("color", WHITE)
    bg = kw.pop("background_color", (0.3, 0.5, 0.7, 1))
    on_release = kw.pop("on_release", None)
    height = kw.pop("height", None)
    if height is not None and "size" not in kw:
        kw["height"] = height
    return DrawnButton(text=text, font_size=font_size, color=color,
                       background_color=bg, on_release=on_release, **kw)


def mk_text(text, size=dp(15), color=None, halign="right",
            height=None, hint_y=None, width=None, hint_x=1, pad=None):
    if color is None:
        color = TEXT
    kw = {}
    if height is not None:
        kw["size_hint_y"] = None
        kw["height"] = height
    elif hint_y is not None:
        kw["size_hint_y"] = hint_y
    else:
        kw["size_hint_y"] = 1
    if width is not None:
        kw["size_hint_x"] = None
        kw["width"] = width
    else:
        kw["size_hint_x"] = hint_x
    w = DrawnText(text=text, font_size=size, color=color,
                  halign=halign, padding_x=pad, **kw)
    w.disabled = True
    return w


class CardBox(BoxLayout):
    def __init__(self, on_tap=None, bg=None, radius=dp(14),
                 shadow=True, **kwargs):
        super().__init__(**kwargs)
        if bg is None:
            bg = CARD
        self._on_tap = on_tap
        self._bg = tuple(bg)
        self._border_on = bool(is_dark() and shadow)
        self._inset = dp(1) if self._border_on else 0
        self._radius = radius
        self._down = False
        self._start = (0, 0)
        self._has_shadow = shadow

        with self.canvas.before:
            if shadow:
                Color(0, 0, 0, 0.035)
                self._sh1 = RoundedRectangle(
                    pos=(self.x - dp(2), self.y - dp(4)),
                    size=(self.width + dp(4), self.height + dp(4)),
                    radius=[radius + dp(2)])
                Color(0, 0, 0, 0.05)
                self._sh2 = RoundedRectangle(
                    pos=(self.x - dp(1), self.y - dp(2)),
                    size=(self.width + dp(2), self.height + dp(2)),
                    radius=[radius + dp(1)])
            if self._border_on:
                Color(*BORDER)
                self._bd = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[radius])
            self._col = Color(*self._bg)
            i = self._inset
            self._rect = RoundedRectangle(
                pos=(self.x + i, self.y + i),
                size=(self.width - 2 * i, self.height - 2 * i),
                radius=[radius])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        if self._has_shadow:
            self._sh1.pos = (self.x - dp(2), self.y - dp(4))
            self._sh1.size = (self.width + dp(4), self.height + dp(4))
            self._sh2.pos = (self.x - dp(1), self.y - dp(2))
            self._sh2.size = (self.width + dp(2), self.height + dp(2))
        i = self._inset
        if self._border_on:
            self._bd.pos = self.pos
            self._bd.size = self.size
        self._rect.pos = (self.x + i, self.y + i)
        self._rect.size = (self.width - 2 * i, self.height - 2 * i)

    def _pressed_color(self):
        r, g, b, a = self._bg
        if is_dark():
            return (min(1, r + 0.05), min(1, g + 0.05), min(1, b + 0.07), a)
        return (r * 0.94, g * 0.94, b * 0.95, a)

    def on_touch_down(self, touch):
        if self._on_tap is None:
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self._down = True
            self._start = touch.pos
            self._col.rgba = self._pressed_color()
            return True
        return False

    def on_touch_move(self, touch):
        if self._on_tap is None:
            return super().on_touch_move(touch)
        if self._down:
            if (abs(touch.y - self._start[1]) > dp(12)
                    or abs(touch.x - self._start[0]) > dp(12)):
                self._down = False
                self._col.rgba = self._bg
        return False

    def on_touch_up(self, touch):
        if self._on_tap is None:
            return super().on_touch_up(touch)
        if self._down:
            self._down = False
            self._col.rgba = self._bg
            if self.collide_point(*touch.pos):
                cb = self._on_tap
                Clock.schedule_once(lambda dt: cb(), 0)
            return True
        self._col.rgba = self._bg
        return False
# ============================================================
# 11) Avatar
# ============================================================
class Avatar(FloatLayout):
    def __init__(self, name="", diameter=dp(48), **kwargs):
        kwargs["size_hint"] = (None, None)
        kwargs["size"] = (diameter, diameter)
        super().__init__(**kwargs)
        name = (name or "").strip()
        letter = name[0] if name else "?"
        idx = sum(ord(c) for c in name) % len(AVATAR_COLORS)
        with self.canvas.before:
            Color(*AVATAR_COLORS[idx])
            self._circle = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        t = DrawnText(text=letter.upper(), font_size=dp(21), color=WHITE,
                      halign="center", padding_x=0,
                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        t.disabled = True
        self.add_widget(t)

    def _upd(self, *a):
        self._circle.pos = self.pos
        self._circle.size = self.size


# ============================================================
# 12) ArabicTextInput
# ============================================================
class ArabicTextInput(FloatLayout):
    def __init__(self, hint_text="", multiline=False, input_filter=None,
                 font_size=dp(15), **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        super().__init__(**kwargs)
        self._font_size = font_size
        self._padding_x = _auto_padding()
        self._cursor_visible = False
        self._blink_event = None

        with self.canvas.before:
            self._border_col = Color(*INPUT_BORDER)
            self._border = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(10)])
            Color(*INPUT_BG)
            self._bg = RoundedRectangle(
                pos=(self.x + dp(1), self.y + dp(1)),
                size=(self.width - dp(2), self.height - dp(2)),
                radius=[dp(9)])

        self._input = TextInput(
            multiline=multiline, input_filter=input_filter,
            font_size=font_size,
            background_color=(0, 0, 0, 0), background_normal="",
            background_active="",
            foreground_color=(0, 0, 0, 0), cursor_color=(0, 0, 0, 0),
            cursor_width=0, use_bubble=False, use_handles=False,
            hint_text="", padding=[dp(8), dp(10), dp(8), dp(10)],
            size_hint=(1, 1), pos_hint={"x": 0, "y": 0})

        self._display = DrawnText(text="", font_size=font_size, color=TEXT,
                                  halign="right", padding_x=self._padding_x,
                                  size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._display.disabled = True

        self._hint = DrawnText(text=hint_text, font_size=font_size, color=HINT,
                               halign="right", padding_x=self._padding_x,
                               size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._hint.disabled = True

        with self.canvas:
            self._cursor_color = Color(0, 0, 0, 0)
            self._cursor_rect = Rectangle(pos=(0, 0), size=(0, 0))

        self.add_widget(self._hint)
        self.add_widget(self._display)
        self.add_widget(self._input)
        self._input.bind(text=self._on_text_change)
        self._input.bind(focus=self._on_focus)
        try:
            self._input.bind(cursor=self._on_cursor_move)
        except Exception:
            pass
        self.bind(pos=self._on_resize, size=self._on_resize)
        self._update_display()

    def _on_resize(self, *args):
        self._border.pos = self.pos
        self._border.size = self.size
        self._bg.pos = (self.x + dp(1), self.y + dp(1))
        self._bg.size = (self.width - dp(2), self.height - dp(2))
        Clock.schedule_once(lambda dt: self._redraw_cursor(), 0)

    def _on_text_change(self, instance, value):
        self._update_display()

    def _on_focus(self, instance, value):
        self._update_display()
        if value:
            self._border_col.rgba = BLUE
            self._start_cursor_blink()
        else:
            self._border_col.rgba = INPUT_BORDER
            self._stop_cursor_blink()

    def _on_cursor_move(self, instance, value):
        Clock.schedule_once(lambda dt: self._redraw_cursor(), 0)

    def _start_cursor_blink(self):
        self._stop_cursor_blink()
        self._cursor_visible = True
        self._blink_event = Clock.schedule_interval(self._blink_cursor, 0.5)
        Clock.schedule_once(lambda dt: self._redraw_cursor(), 0)

    def _stop_cursor_blink(self):
        if self._blink_event:
            self._blink_event.cancel()
            self._blink_event = None
        self._cursor_visible = False
        self._cursor_color.a = 0

    def _blink_cursor(self, dt):
        self._cursor_visible = not self._cursor_visible
        self._redraw_cursor()

    def _measure_text_width(self, text):
        if not text:
            return 0
        try:
            cl = CoreLabel(text=text, font_size=int(self._font_size),
                           font_name=_font_name(), padding=(0, 0, 0, 0))
            cl.refresh()
            if cl.texture:
                return cl.texture.size[0]
        except Exception:
            pass
        return 0

    def _redraw_cursor(self):
        if not self._input.focus or not self._cursor_visible:
            self._cursor_color.a = 0
            return
        try:
            raw = self._input.text
            if not raw:
                cursor_x = self.right - self._padding_x
            else:
                display = ar(raw.split("\n")[-1])
                text_width = self._measure_text_width(display)
                cursor_x = self.right - self._padding_x - text_width - dp(2)
            min_x = self.x + dp(2)
            max_x = self.right - dp(2)
            if cursor_x < min_x:
                cursor_x = min_x
            if cursor_x > max_x:
                cursor_x = max_x
            cursor_y = self.y + dp(9)
            cursor_h = self.height - dp(18)
            self._cursor_color.rgba = BLUE
            self._cursor_rect.pos = (cursor_x, cursor_y)
            self._cursor_rect.size = (dp(2), cursor_h)
        except Exception as e:
            print(f"[Cursor] {e}")

    def _update_display(self):
        raw = self._input.text
        if raw:
            self._display.text = raw
            self._hint.opacity = 0
        else:
            self._display.text = ""
            self._hint.opacity = 1
        Clock.schedule_once(lambda dt: self._redraw_cursor(), 0)

    @property
    def text(self):
        return self._input.text

    @text.setter
    def text(self, value):
        self._input.text = value

    def bind(self, **kwargs):
        if "text" in kwargs:
            self._input.bind(text=kwargs["text"])
            kwargs = {k: v for k, v in kwargs.items() if k != "text"}
        if kwargs:
            return super().bind(**kwargs)


def mk_input(**kw):
    hint = kw.pop("hint_text", "")
    multiline = kw.pop("multiline", False)
    input_filter = kw.pop("input_filter", None)
    font_size = kw.pop("font_size", dp(15))
    return ArabicTextInput(hint_text=hint, multiline=multiline,
                           input_filter=input_filter,
                           font_size=font_size, **kw)


# ============================================================
# 13) Popup عربي
# ============================================================
def make_arabic_popup(title_text, content, size_hint=(0.9, 0.7),
                      title_color=None, separator_color=None,
                      auto_dismiss=True):
    if title_color is None:
        title_color = PRIMARY
    if separator_color is None:
        separator_color = PRIMARY
    wrapper = BoxLayout(orientation="vertical", spacing=0)
    title_widget = DrawnText(text=title_text, font_size=dp(18),
                             color=title_color, halign="center",
                             size_hint_y=None, height=dp(44))
    title_widget.disabled = True
    wrapper.add_widget(title_widget)

    sep = Widget(size_hint_y=None, height=dp(2))
    with sep.canvas:
        Color(*separator_color)
        sep_rect = Rectangle(pos=sep.pos, size=sep.size)

    def _update_sep(*a):
        sep_rect.pos = sep.pos
        sep_rect.size = sep.size
    sep.bind(pos=_update_sep, size=_update_sep)
    wrapper.add_widget(sep)
    wrapper.add_widget(Widget(size_hint_y=None, height=dp(8)))
    content.size_hint_y = 1
    wrapper.add_widget(content)

    popup = Popup(title="", content=wrapper, size_hint=size_hint,
                  separator_color=(0, 0, 0, 0),
                  background="", background_color=CARD,
                  auto_dismiss=auto_dismiss)
    popup.bind(on_open=lambda *a: schedule_refresh(0.05))
    return popup


# ============================================================
# 14) مكونات مشتركة
# ============================================================
class _FadeOverlay(Widget):
    def __init__(self, color, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", Window.size)
        kwargs.setdefault("pos", (0, 0))
        super().__init__(**kwargs)
        with self.canvas:
            Color(*color)
            Rectangle(pos=(0, 0), size=Window.size)

    def on_touch_down(self, touch):
        return False

    def on_touch_up(self, touch):
        return False


def make_header(title, color, on_back=None, right_widget=None,
                height=dp(58), on_back_text="رجوع"):
    bar = FloatLayout(size_hint_y=None, height=height)
    with bar.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=bar.pos, size=bar.size,
                                radius=[0, 0, dp(20), dp(20)])

    def _u(*a):
        rect.pos = bar.pos
        rect.size = bar.size
    bar.bind(pos=_u, size=_u)

    t = DrawnText(text=title, font_size=dp(19), color=WHITE, halign="center",
                  size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
    t.disabled = True
    bar.add_widget(t)

    if on_back is not None:
        back = mk_btn(on_back_text, size_hint=(None, None),
                      size=(dp(76), dp(38)), font_size=dp(14),
                      background_color=GLASS,
                      pos_hint={"x": 0.02, "center_y": 0.5})
        back.bind(on_release=on_back)
        bar.add_widget(back)

    if right_widget is not None:
        right_widget.pos_hint = {"right": 0.98, "center_y": 0.5}
        bar.add_widget(right_widget)
    return bar


def make_body(**kw):
    kw.setdefault("orientation", "vertical")
    kw.setdefault("padding", [dp(12), dp(2), dp(12), dp(10)])
    kw.setdefault("spacing", dp(8))
    return BoxLayout(**kw)


def make_scroll_list(spacing=dp(10)):
    layout = GridLayout(cols=1, spacing=spacing, size_hint_y=None,
                        padding=[dp(2), dp(4), dp(2), dp(16)])
    layout.bind(minimum_height=layout.setter("height"))
    scroll = ScrollView(size_hint=(1, 1), bar_width=dp(3))
    scroll.add_widget(layout)
    return scroll, layout


# ============================================================
# 15) عناصر الفواتير والعملاء
# ============================================================
def item_total(it):
    gross = it.get("qty", 1) * it.get("price", 0)
    return max(0, gross - it.get("discount", 0))


def make_item_row(item, on_delete=None, show_qty=True):
    name = item.get("name", "")
    qty = item.get("qty", 1)
    note = item.get("note", "")
    disc = item.get("discount", 0)
    total = item_total(item)

    row = CardBox(orientation="horizontal", size_hint_y=None, height=dp(64),
                  padding=[dp(12), dp(6)], spacing=dp(8), radius=dp(12))
    if on_delete is not None:
        del_btn = mk_btn("X", size_hint=(None, None), size=(dp(38), dp(38)),
                         background_color=RED, font_size=dp(15),
                         pos_hint={"center_y": 0.5})
        del_btn.bind(on_release=lambda *a: on_delete())
        row.add_widget(del_btn)

    total_col = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(96))
    total_col.add_widget(mk_text(money(total), dp(16), PRIMARY,
                                 halign="left", hint_y=0.58))
    total_col.add_widget(mk_text("ريال", dp(11), MUTED,
                                 halign="left", hint_y=0.42))
    row.add_widget(total_col)

    name_col = BoxLayout(orientation="vertical")
    name_col.add_widget(mk_text(name, dp(15), TEXT, hint_y=0.58))
    if show_qty:
        sub = f"العدد: {qty:g}"
        if disc:
            sub += f" - خصم: {money(disc)}"
        if note:
            sub += f" - {note}"
        name_col.add_widget(mk_text(sub, dp(12), MUTED, hint_y=0.42))
    row.add_widget(name_col)
    return row


def build_item_form(on_add):
    row1 = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
    ncol = BoxLayout(orientation="vertical", spacing=dp(4))
    ncol.add_widget(mk_text("اسم الصنف", dp(13), MUTED, height=dp(20)))
    name_in = mk_input(hint_text="اكتب هنا الصنف", size_hint_y=None, height=dp(46))
    ncol.add_widget(name_in)
    row1.add_widget(ncol)

    row2 = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
    pcol = BoxLayout(orientation="vertical", spacing=dp(4))
    pcol.add_widget(mk_text("السعر", dp(13), MUTED, height=dp(20)))
    price_in = mk_input(hint_text="0", input_filter="float",
                        size_hint_y=None, height=dp(46))
    pcol.add_widget(price_in)
    qcol = BoxLayout(orientation="vertical", spacing=dp(4))
    qcol.add_widget(mk_text("الكمية", dp(13), MUTED, height=dp(20)))
    qty_in = mk_input(hint_text="1", input_filter="float",
                      size_hint_y=None, height=dp(46))
    qcol.add_widget(qty_in)
    row2.add_widget(pcol)
    row2.add_widget(qcol)

    row3 = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
    dcol = BoxLayout(orientation="vertical", spacing=dp(4))
    dcol.add_widget(mk_text("الخصم )مبلغ يُخصم من مجموع الصنف(",
                            dp(13), MUTED, height=dp(20)))
    disc_in = mk_input(hint_text="0", input_filter="float",
                       size_hint_y=None, height=dp(46))
    dcol.add_widget(disc_in)
    row3.add_widget(dcol)

    row4 = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
    note_col = BoxLayout(orientation="vertical", spacing=dp(4))
    note_col.add_widget(mk_text("ملاحظة )اختياري(", dp(13), MUTED,
                                height=dp(20)))
    note_in = mk_input(hint_text="اكتب هنا الملاحظه",
                       size_hint_y=None, height=dp(46))
    note_col.add_widget(note_in)
    row4.add_widget(note_col)

    total_height = dp(72 * 4) + dp(46) + dp(10) + dp(20)
    card = CardBox(orientation="vertical", size_hint_y=None,
                   height=total_height,
                   padding=[dp(12), dp(10), dp(12), dp(12)], spacing=dp(6))
    card.add_widget(row1)
    card.add_widget(row2)
    card.add_widget(row3)
    card.add_widget(row4)
    add_btn = mk_btn("+ إضافة الصنف", height=dp(46), background_color=BLUE)
    add_btn.bind(on_release=lambda *a: on_add())
    card.add_widget(add_btn)
    return card, name_in, qty_in, price_in, note_in, disc_in


def parse_item(name_in, qty_in, price_in, note_in=None, disc_in=None):
    name = name_in.text.strip()
    try:
        qty = float(qty_in.text.strip() or "1")
    except ValueError:
        qty = 1
    try:
        price = float(price_in.text.strip() or "0")
    except ValueError:
        price = 0
    try:
        disc = float(disc_in.text.strip() or "0") if disc_in is not None else 0
    except ValueError:
        disc = 0
    disc = max(0, disc)
    if not name or price <= 0 or qty <= 0:
        return None
    if disc > qty * price:
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        box.add_widget(mk_text("الخصم أكبر من مجموع الصنف", dp(16), RED,
                               halign="center", height=dp(36)))
        box.add_widget(mk_text(f"مجموع الصنف: {money(qty * price)}",
                               dp(14), MUTED,
                               halign="center", height=dp(28)))
        box.add_widget(Widget())
        ok = mk_btn("حسناً", height=dp(46), background_color=GRAY_BTN)
        box.add_widget(ok)
        pop = make_arabic_popup("تنبيه", box, size_hint=(0.85, 0.36),
                                title_color=RED, separator_color=RED)
        ok.bind(on_release=lambda *a: pop.dismiss())
        pop.open()
        return None
    note = note_in.text.strip() if note_in is not None else ""
    name_in.text = ""
    qty_in.text = ""
    price_in.text = ""
    if disc_in is not None:
        disc_in.text = ""
    if note_in is not None:
        note_in.text = ""
    item = {"name": name, "qty": qty, "price": price}
    if disc:
        item["discount"] = disc
    if note:
        item["note"] = note
    return item


def make_invoice_card(inv, on_tap):
    kind = inv.get("kind", "فاتورة")
    total = inv.get("total", 0)
    date = inv.get("date", "")
    items = inv.get("items", [])
    color = INV_RED if kind == "فاتورة" else GREEN

    card = CardBox(orientation="vertical", size_hint_y=None, height=dp(112),
                   padding=0, spacing=0, on_tap=on_tap, radius=dp(14))
    head = BoxLayout(size_hint_y=None, height=dp(34),
                     padding=[dp(14), 0], spacing=dp(6))
    with head.canvas.before:
        Color(*color)
        head_rect = RoundedRectangle(pos=head.pos, size=head.size,
                                     radius=[dp(14), dp(14), 0, 0])

    def _uh(*a):
        head_rect.pos = head.pos
        head_rect.size = head.size
    head.bind(pos=_uh, size=_uh)
    head.add_widget(mk_text(date, dp(12), SOFT_WHITE,
                            halign="left", hint_x=0.55))
    head.add_widget(mk_text(kind, dp(15), WHITE,
                            halign="right", hint_x=0.45))
    card.add_widget(head)

    body = BoxLayout(orientation="vertical", padding=[dp(14), dp(6)], spacing=0)
    body.add_widget(mk_text(f"{money(total)} ريال", dp(22), color,
                            height=dp(38)))
    sub = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
    if kind == "فاتورة":
        sub_text = f"عدد الأصناف: {len(items)}"
    else:
        sub_text = items[0].get("name", "") if items else ""
    sub.add_widget(mk_text("عرض التفاصيل", dp(12), BLUE,
                           halign="left", hint_x=0.4))
    sub.add_widget(mk_text(sub_text, dp(13), MUTED,
                           halign="right", hint_x=0.6))
    body.add_widget(sub)
    card.add_widget(body)
    return card


def make_client_row(client, on_tap):
    name = client.get("name", "بدون اسم")
    phone = client.get("phone", "") or "بدون رقم"
    bal = client.get("balance", 0)
    if bal > 0:
        amount_color = RED
        status = "عليه دين"
    elif bal < 0:
        amount_color = GREEN
        status = "له رصيد"
    else:
        amount_color = GREEN
        status = "لا يوجد دين"

    row = CardBox(orientation="horizontal", size_hint_y=None, height=dp(78),
                  padding=[dp(12), dp(8)], spacing=dp(10), on_tap=on_tap)
    left = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(118))
    left.add_widget(mk_text(f"{money_signed(bal)} ريال", dp(16), amount_color,
                            halign="left", hint_y=0.55))
    left.add_widget(mk_text(status, dp(12), MUTED,
                            halign="left", hint_y=0.45))
    row.add_widget(left)
    mid = BoxLayout(orientation="vertical")
    mid.add_widget(mk_text(name, dp(17), TEXT, hint_y=0.55))
    mid.add_widget(mk_text(phone, dp(12), MUTED, hint_y=0.45))
    row.add_widget(mid)
    av = Avatar(name)
    av.pos_hint = {"center_y": 0.5}
    row.add_widget(av)
    return row


# ============================================================
# 16) منشئ المستندات (PDF/صورة) — للـ WhatsApp فقط
# ============================================================
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة",
           "السبت", "الأحد"]


def parse_dt(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        return datetime.now()


def build_invoice_text(c, inv):
    d = parse_dt(inv.get("date", ""))
    prev, after = inv_snapshot(c, inv)
    sep = "~" * 15
    lines = [
        f"أخي {first_name(c.get('name', ''))}",
        f"تم شراء فاتورة بـ {money(inv.get('total', 0))}",
        f"{d.day} {MONTHS_AR[d.month - 1]}",
        sep,
    ]
    for i, it in enumerate(inv.get("items", []), 1):
        total = item_total(it)
        line = f"{i} {it.get('name', '')} - {money(total)} - {it.get('qty', 1):g} حبة"
        if it.get("discount"):
            line += f" - بعد خصم {money(it['discount'])}"
        if it.get("note"):
            line += f" - {it['note']}"
        lines.append(line)
    lines.append(sep)
    lines.append(f"اصبح حسابكم {money_signed(after)}")
    lines.append("يرجى السداد في اقرب وقت")
    lines.append(str(d.year))
    lines.extend(seller_lines())
    return "\n".join(lines)


def build_receipt_text(c, inv):
    d = parse_dt(inv.get("date", ""))
    prev, after = inv_snapshot(c, inv)
    return "\n".join([
        f"فاتورة سند قبض بمبلغ {money(inv.get('total', 0))}",
        f"في تاريخ {DAYS_AR[d.weekday()]} {d.day} {MONTHS_AR[d.month - 1]} {d.year}",
        f"الحساب السابق: {money_signed(prev)}",
        f"الحساب المتبقي: {money_signed(after)}",
        "شكرا على تعاملك",
    ] + seller_lines())


def build_statement_text(c):
    return "\n".join([
        f"أخي {first_name(c.get('name', ''))} هذا كشف حسابك",
        f"المطلوب منك {money_signed(c.get('balance', 0))}",
        "يرجى السداد في اقرب وقت",
        str(datetime.now().year),
    ] + seller_lines())


def open_whatsapp(phone, message):
    phone_clean = "".join(ch for ch in str(phone) if ch.isdigit())
    if phone_clean.startswith("0"):
        phone_clean = "967" + phone_clean[1:]
    from urllib.parse import quote
    url = "https://wa.me/{}?text={}".format(phone_clean, quote(message))
    if platform == "android":
        try:
            from jnius import autoclass
            from android import mActivity
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(url))
            mActivity.startActivity(intent)
            return
        except Exception as e:
            print(f"[WA] {e}")
    print("URL:", url)
# ============================================================
# 16-ب) الفواتير كصورة و PDF (مع المشاركة عبر واتساب)
# ============================================================
DOC_DIR = os.path.join(DATA_DIR, "docs")


def first_name(name):
    parts = (name or "").split()
    return parts[0] if parts else "عميل"


def inv_snapshot(c, inv):
    """يرجع (الحساب السابق، الحساب بعد العملية) محسوباً من تسلسل الفواتير،
    ومربوطاً برصيد العميل الحالي، فيبقى صحيحاً بعد التعديل والحذف والمزامنة."""
    invs = c.get("invoices", [])
    running = c.get("balance", 0)
    for it in reversed(invs):
        t = it.get("total", 0)
        delta = t if it.get("kind", "فاتورة") == "فاتورة" else -t
        after = running
        prev = after - delta
        same = (it is inv) or (it.get("id") and it.get("id") == inv.get("id"))
        if same:
            return prev, after
        running = prev
    return c.get("balance", 0), c.get("balance", 0)


def _pil_font(size):
    from PIL import ImageFont
    try:
        if FONT_PATH:
            try:
                return ImageFont.truetype(FONT_PATH, size,
                                          layout_engine=ImageFont.Layout.BASIC)
            except Exception:
                return ImageFont.truetype(FONT_PATH, size)
    except Exception as e:
        print(f"[PIL FONT] {e}")
    return ImageFont.load_default()


def _save_image_as_pdf(img, pdf_path):
    """يضع صورة الفاتورة داخل صفحات A4 (الـ PDF = نفس الصورة بالضبط)."""
    from PIL import Image as PImage
    PW, PH = 1240, 1754            # A4 بدقة 150
    M = 70
    iw = PW - 2 * M
    scale = iw / float(img.width)
    pic = img.resize((iw, max(1, int(img.height * scale))), PImage.LANCZOS)
    usable = PH - 2 * M
    pages = []
    top = 0
    while top < pic.height or not pages:
        part = pic.crop((0, top, iw, min(pic.height, top + usable)))
        page = PImage.new("RGB", (PW, PH), (255, 255, 255))
        page.paste(part, (M, M))
        pages.append(page)
        top += usable
    pages[0].save(pdf_path, "PDF", resolution=150.0,
                  save_all=True, append_images=pages[1:])


def render_document(c, inv, mode, number=0):
    """ينشئ صورة PNG و PDF مرتبة. يرجع (png, pdf, (w,h)).
    mode: invoice | receipt | statement"""
    from PIL import Image as PImage, ImageDraw
    os.makedirs(DOC_DIR, exist_ok=True)
    for fn in os.listdir(DOC_DIR):
        try:
            os.remove(os.path.join(DOC_DIR, fn))
        except Exception:
            pass

    W = 900
    L, R = 50, W - 50
    rows_n = len(inv.get("items", [])) if inv else min(len(c.get("invoices", [])), 20)
    H = 1350 + rows_n * 110
    img = PImage.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    f_title, f_big = _pil_font(60), _pil_font(52)
    f_mid, f_sm, f_xs = _pil_font(36), _pil_font(30), _pil_font(25)
    DARK, GRAY = (31, 41, 61), (118, 130, 150)
    LINE, SOFT = (228, 231, 236), (240, 243, 248)
    colors = {"invoice": (219, 84, 77), "receipt": (33, 153, 92),
              "statement": (23, 74, 125)}
    titles = {"invoice": "فاتورة", "receipt": "سند قبض", "statement": "كشف حساب"}
    color = colors[mode]

    def tw(s, font):
        try:
            return d.textlength(ar(s), font=font)
        except Exception:
            return len(s) * 14

    def rt(right, y, s, font, fill=DARK):
        d.text((right - tw(s, font), y), ar(s), font=font, fill=fill)

    def lt(left, y, s, font, fill=DARK):
        d.text((left, y), ar(s), font=font, fill=fill)

    def ct(cx, y, s, font, fill=DARK):
        d.text((cx - tw(s, font) / 2.0, y), ar(s), font=font, fill=fill)

    def fit(s, font, maxw):
        s = str(s)
        if tw(s, font) <= maxw:
            return s
        while s and tw(s + "…", font) > maxw:
            s = s[:-1]
        return s + "…"

    def kv(y, label, value, vcolor=DARK, font=None):
        font = font or f_sm
        rt(R - 20, y, label, font, GRAY)
        lt(L + 20, y, value, font, vcolor)

    # ---- الترويسة ----
    d.rectangle([0, 0, W, 170], fill=color)
    ct(W / 2, 22, titles[mode], f_title, (255, 255, 255))
    ct(W / 2, 108, "دفتر ديون الزهوب", f_xs, (235, 240, 250))

    dt = parse_dt(inv.get("date", "")) if inv else datetime.now()
    date_s = f"{DAYS_AR[dt.weekday()]} {dt.day} {MONTHS_AR[dt.month - 1]} {dt.year}"
    y = 205
    rt(R, y, f"العميل: {c.get('name', '')}", f_mid)
    if number:
        lt(L, y + 6, f"رقم: {number}", f_sm, GRAY)
    y += 56
    rt(R, y, f"التاريخ: {date_s}", f_sm, GRAY)
    if c.get("phone"):
        lt(L, y, str(c.get("phone")), f_sm, GRAY)
    y += 58
    d.line([L, y, R, y], fill=LINE, width=3)
    y += 22

    prev = after = None
    if inv:
        prev, after = inv_snapshot(c, inv)

    if mode == "invoice":
        d.rectangle([L, y, R, y + 58], fill=SOFT)
        rt(R - 14, y + 12, "م", f_sm, GRAY)
        rt(R - 90, y + 12, "الصنف", f_sm, GRAY)
        ct(L + 260, y + 12, "العدد", f_sm, GRAY)
        ct(L + 95, y + 12, "المبلغ", f_sm, GRAY)
        y += 58
        name_max = (R - 90) - (L + 350)
        for i, it in enumerate(inv.get("items", []), 1):
            total = item_total(it)
            rt(R - 14, y + 14, str(i), f_sm, GRAY)
            rt(R - 90, y + 10, fit(it.get("name", ""), f_mid, name_max), f_mid)
            ct(L + 260, y + 14, f"{it.get('qty', 1):g}", f_sm)
            ct(L + 95, y + 14, money(total), f_sm, color)
            rh = 66
            extras = []
            if it.get("discount"):
                extras.append(f"خصم {money(it['discount'])}")
            if it.get("note"):
                extras.append(str(it["note"]))
            if extras:
                rt(R - 90, y + 54, fit(" - ".join(extras), f_xs, name_max), f_xs, GRAY)
                rh = 92
            y += rh
            d.line([L, y, R, y], fill=LINE, width=2)
        y += 26
        d.rounded_rectangle([L, y, R, y + 250], radius=18, fill=SOFT)
        kv(y + 22, "إجمالي الفاتورة", money(inv.get("total", 0)), DARK, f_mid)
        kv(y + 92, "الحساب السابق", money_signed(prev), GRAY)
        d.line([L + 20, y + 150, R - 20, y + 150], fill=LINE, width=2)
        kv(y + 168, "الحساب الحالي", money_signed(after), color, f_mid)
        y += 290
        ct(W / 2, y, "يرجى السداد في أقرب وقت", f_sm, GRAY)
        y += 50

    elif mode == "receipt":
        d.rounded_rectangle([L, y, R, y + 210], radius=18, fill=SOFT)
        ct(W / 2, y + 22, "المبلغ المقبوض", f_sm, GRAY)
        ct(W / 2, y + 85, money(inv.get("total", 0)), f_title, color)
        y += 240
        note = (inv.get("items") or [{}])[0].get("name", "")
        if note:
            kv(y, "ملاحظة", fit(note, f_sm, 480))
            y += 66
        d.line([L, y, R, y], fill=LINE, width=2)
        y += 24
        kv(y, "الحساب السابق", money_signed(prev))
        y += 66
        kv(y, "الحساب المتبقي", money_signed(after), color, f_mid)
        y += 90
        ct(W / 2, y, "شكراً على تعاملك", f_sm, GRAY)
        y += 50

    else:  # statement
        d.rectangle([L, y, R, y + 58], fill=SOFT)
        rt(R - 14, y + 12, "التاريخ", f_sm, GRAY)
        ct(W / 2 + 40, y + 12, "البيان", f_sm, GRAY)
        lt(L + 14, y + 12, "المبلغ", f_sm, GRAY)
        y += 58
        invs = c.get("invoices", [])
        for it in invs[-20:]:
            k = it.get("kind", "فاتورة")
            amt = it.get("total", 0)
            dd = parse_dt(it.get("date", ""))
            rt(R - 14, y + 14, f"{dd.day} {MONTHS_AR[dd.month - 1]} {dd.year}", f_sm, DARK)
            ct(W / 2 + 40, y + 14, k, f_sm, DARK)
            if k == "فاتورة":
                lt(L + 14, y + 14, "+" + money(amt), f_sm, (219, 84, 77))
            else:
                lt(L + 14, y + 14, "-" + money(amt), f_sm, (33, 153, 92))
            y += 66
            d.line([L, y, R, y], fill=LINE, width=2)
        if len(invs) > 20:
            ct(W / 2, y + 10, f"و {len(invs) - 20} عملية سابقة", f_xs, GRAY)
            y += 50
        y += 24
        d.rounded_rectangle([L, y, R, y + 130], radius=18, fill=SOFT)
        kv(y + 36, "المطلوب منك", money_signed(c.get("balance", 0)), color, f_big)
        y += 160
        ct(W / 2, y, "يرجى السداد في أقرب وقت", f_sm, GRAY)
        y += 50

    _shop, _sphone = SELLER.get("shop", ""), SELLER.get("phone", "")
    if _shop or _sphone:
        y += 14
        d.line([L, y, R, y], fill=LINE, width=2)
        y += 22
        if _shop:
            ct(W / 2, y, fit(_shop, f_mid, W - 100), f_mid, DARK)
            y += 58
        if _sphone:
            ct(W / 2, y, "للتواصل: " + _sphone, f_sm, GRAY)
            y += 48
        y += 6
    ct(W / 2, y + 10, str(dt.year), f_xs, GRAY)
    y += 70
    img = img.crop((0, 0, W, min(y, H)))

    stamp = datetime.now().strftime("%H%M%S")
    png = os.path.join(DOC_DIR, f"doc_{mode}_{stamp}.png")
    pdf = os.path.join(DOC_DIR, f"doc_{mode}_{stamp}.pdf")
    img.save(png)
    try:
        _save_image_as_pdf(img, pdf)
    except Exception as e:
        print(f"[PDF] {e}")
        pdf = None
    return png, pdf, img.size


def _publish_media(path, mime):
    """ينسخ الملف إلى مخزن الجهاز العام ويرجع Uri يقبله واتساب."""
    from jnius import autoclass
    from android import mActivity
    sdk = autoclass("android.os.Build$VERSION").SDK_INT
    JFile = autoclass("java.io.File")
    if sdk >= 29:
        ContentValues = autoclass("android.content.ContentValues")
        resolver = mActivity.getContentResolver()
        v = ContentValues()
        v.put("_display_name", os.path.basename(path))
        v.put("mime_type", mime)
        if mime.startswith("image"):
            v.put("relative_path", "Pictures/DebtBook")
            coll = autoclass("android.provider.MediaStore$Images$Media").EXTERNAL_CONTENT_URI
        else:
            v.put("relative_path", "Download/DebtBook")
            coll = autoclass("android.provider.MediaStore$Downloads").EXTERNAL_CONTENT_URI
        uri = resolver.insert(coll, v)
        if uri is None:
            raise RuntimeError("MediaStore insert returned null")
        out = resolver.openOutputStream(uri)
        try:
            autoclass("java.nio.file.Files").copy(JFile(path).toPath(), out)
        finally:
            out.close()
        return uri

    # [إصلاح كراش 5] أندرويد 9 وأقدم (SDK < 29): حُذف الكتابة في
    # getExternalStorageDirectory()/Download. نستخدم مجلد التطبيق الخارجي الخاص
    # getExternalFilesDir(null) (لا يحتاج أي صلاحية)، ونمرّر Uri.fromFile لواتساب.
    ext = mActivity.getExternalFilesDir(None)
    base = ext.getAbsolutePath() if ext is not None else os.path.dirname(path)
    pub_dir = os.path.join(base, "DebtBook")
    os.makedirs(pub_dir, exist_ok=True)
    pub_path = os.path.join(pub_dir, os.path.basename(path))
    import shutil
    shutil.copyfile(path, pub_path)
    StrictMode = autoclass("android.os.StrictMode")
    Builder = autoclass("android.os.StrictMode$VmPolicy$Builder")
    StrictMode.setVmPolicy(Builder().build())
    return autoclass("android.net.Uri").fromFile(JFile(pub_path))


def share_file(path, mime, phone=""):
    """يشارك ملفاً (صورة/PDF) عبر واتساب، وإن لم يتوفر يفتح قائمة المشاركة.
    يرجع None عند النجاح، أو نص الخطأ عند الفشل."""
    if platform != "android":
        print("[SHARE]", path)
        return None
    try:
        from jnius import autoclass, cast
        from android import mActivity
        Intent = autoclass("android.content.Intent")
        uri = _publish_media(path, mime)

        def make():
            it = Intent(Intent.ACTION_SEND)
            it.setType(mime)
            it.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
            it.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            return it

        p = "".join(ch for ch in str(phone) if ch.isdigit())
        if p.startswith("0"):
            p = "967" + p[1:]
        for pkg in ("com.whatsapp", "com.whatsapp.w4b"):
            try:
                it = make()
                it.setPackage(pkg)
                if p:
                    it.putExtra("jid", p + "@s.whatsapp.net")
                mActivity.startActivity(it)
                return None
            except Exception as e:
                print(f"[SHARE {pkg}] {e}")
        chooser = Intent.createChooser(make(), "إرسال")
        chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        mActivity.startActivity(chooser)
        return None
    except Exception as e:
        print(f"[SHARE] {e}")
        return str(e)[:160]


def make_doc_image(path, size):
    from kivy.uix.image import Image as KImage
    try:
        img = KImage(source=path, fit_mode="contain", size_hint=(1, None))
    except Exception:
        img = KImage(source=path, allow_stretch=True, keep_ratio=True,
                     size_hint=(1, None))
    ratio = size[1] / float(size[0])
    img.height = Window.width * 0.9 * ratio
    img.bind(width=lambda w, v: setattr(w, "height", v * ratio))
    return img


def _share_and_report(path, mime, phone):
    err = share_file(path, mime, phone)
    if err:
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        box.add_widget(mk_text("تعذر الإرسال. سبب الخطأ:", dp(15), RED,
                               halign="center", height=dp(30)))
        lbl = KLabel(text=err, color=(0.3, 0.3, 0.3, 1), font_size=dp(12),
                     halign="center", valign="middle")
        lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
        box.add_widget(lbl)
        ok = mk_btn("حسناً", height=dp(46), background_color=GRAY_BTN)
        box.add_widget(ok)
        pop = make_arabic_popup("خطأ في الإرسال", box, size_hint=(0.88, 0.42),
                                title_color=RED, separator_color=RED)
        ok.bind(on_release=lambda *a: pop.dismiss())
        pop.open()


def show_document_popup(c, inv, mode, number=0, send=True):
    """يعرض الفاتورة/السند/الكشف كصورة مرتبة مع أزرار (صورة / PDF / نص)."""
    try:
        png, pdf, size = render_document(c, inv, mode, number)
    except Exception as e:
        print(f"[RENDER] {e}")
        png = pdf = size = None

    if mode == "receipt":
        text = build_receipt_text(c, inv)
        title = "معاينة سند القبض"
    elif mode == "invoice":
        text = build_invoice_text(c, inv)
        title = "معاينة الفاتورة"
    else:
        text = build_statement_text(c)
        title = "معاينة كشف الحساب"
    phone = c.get("phone", "")

    content = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(4))
    if png:
        sv = ScrollView(size_hint=(1, 1), bar_width=dp(3))
        sv.add_widget(make_doc_image(png, size))
        content.add_widget(sv)
    else:
        content.add_widget(mk_text("تعذر إنشاء الصورة، يمكنك الإرسال كنص",
                                   dp(14), RED, halign="center"))

    b_img = b_pdf = b_txt = None
    if send:
        r1 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        b_img = mk_btn("إرسال صورة", background_color=GREEN, font_size=dp(14))
        b_pdf = mk_btn("إرسال PDF", background_color=ORANGE, font_size=dp(14))
        r1.add_widget(b_img)
        r1.add_widget(b_pdf)
        content.add_widget(r1)
    r2 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
    if send:
        b_txt = mk_btn("إرسال كنص", background_color=BLUE, font_size=dp(14))
        r2.add_widget(b_txt)
    b_close = mk_btn("إغلاق", background_color=GRAY_BTN, font_size=dp(14))
    r2.add_widget(b_close)
    content.add_widget(r2)

    popup = make_arabic_popup(title, content, size_hint=(0.96, 0.94))
    if send:
        if png:
            b_img.bind(on_release=lambda *a: _share_and_report(png, "image/png", phone))
        if pdf:
            b_pdf.bind(on_release=lambda *a: _share_and_report(pdf, "application/pdf", phone))
        b_txt.bind(on_release=lambda *a: open_whatsapp(phone, text))
    b_close.bind(on_release=lambda *a: popup.dismiss())
    popup.open()


# ============================================================
# 17) شاشة تسجيل الدخول
# ============================================================
class LoginScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        head = FloatLayout(size_hint_y=None, height=dp(200))
        with head.canvas.before:
            Color(*HEADER)
            head_rect = RoundedRectangle(pos=head.pos, size=head.size,
                                         radius=[0, 0, dp(30), dp(30)])

        def _uh(*a):
            head_rect.pos = head.pos
            head_rect.size = head.size
        head.bind(pos=_uh, size=_uh)

        t = DrawnText(text="دفتر ديون الزهوب",
                      font_size=dp(26), color=WHITE, halign="center",
                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0.65})
        t.disabled = True
        head.add_widget(t)

        st = DrawnText(text="سجل دخولك للمتابعة",
                       font_size=dp(14), color=SOFT_WHITE, halign="center",
                       size_hint=(1, 1), pos_hint={"x": 0, "y": 0.35})
        st.disabled = True
        head.add_widget(st)
        if getattr(self.app, "_adding", False):
            cb = mk_btn("إلغاء", size_hint=(None, None),
                        size=(dp(76), dp(38)), font_size=dp(14),
                        background_color=GLASS,
                        pos_hint={"x": 0.03, "top": 0.95})
            cb.bind(on_release=lambda *a: self.app.cancel_add_account())
            head.add_widget(cb)
        root.add_widget(head)

        body = BoxLayout(orientation="vertical", spacing=dp(10),
                         padding=[dp(24), dp(24), dp(24), dp(20)])

        body.add_widget(mk_text("البريد الإلكتروني", dp(13), MUTED,
                                height=dp(22)))
        self.email_in = mk_input(hint_text="example@mail.com",
                                 size_hint_y=None, height=dp(50))
        body.add_widget(self.email_in)

        body.add_widget(mk_text("كلمة المرور", dp(13), MUTED, height=dp(22)))
        self.pass_in = mk_input(hint_text="********",
                                size_hint_y=None, height=dp(50))
        body.add_widget(self.pass_in)

        self.msg_dt = mk_text("", dp(13), RED, halign="center", height=dp(28))
        body.add_widget(self.msg_dt)

        body.add_widget(Widget(size_hint_y=None, height=dp(8)))

        login_btn = mk_btn("دخول", height=dp(52), font_size=dp(18),
                           background_color=GREEN)
        login_btn.bind(on_release=self.do_login)
        body.add_widget(login_btn)

        reg_btn = mk_btn("تسجيل بحساب جديد", height=dp(48), font_size=dp(15),
                         background_color=GRAY_BTN)
        reg_btn.bind(on_release=lambda *a: self.app.go_register())
        body.add_widget(reg_btn)

        body.add_widget(Widget())
        root.add_widget(body)
        self.add_widget(root)

    def do_login(self, *a):
        email = self.email_in.text.strip().lower()
        password = self.pass_in.text.strip()
        if not email or not password:
            self.msg_dt.text = "الرجاء إدخال البريد وكلمة المرور"
            return
        self.msg_dt.text = "جاري التحقق..."
        self.msg_dt.text = self.msg_dt.text  # forced redraw

        def worker():
            ok, data = self.app.verify_login(email, password)
            Clock.schedule_once(lambda dt: self._on_result(ok, data), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_result(self, ok, data):
        if ok:
            self.msg_dt.text = ""
            self.app.on_login_success(data)
        else:
            self.msg_dt.text = data or "فشل التحقق"


# ============================================================
# 18) شاشة التسجيل
# ============================================================
class RegisterScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.agreed = False
        self.build_ui()

    def _field(self, body, label, hint, **kw):
        body.add_widget(mk_text(label, dp(13), MUTED, height=dp(22)))
        w = mk_input(hint_text=hint, size_hint_y=None, height=dp(50), **kw)
        body.add_widget(w)
        return w

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        head = make_header("حساب جديد", HEADER,
                           on_back=lambda *a: self.app.go_login())
        root.add_widget(head)

        sv = ScrollView(size_hint=(1, 1))
        body = BoxLayout(orientation="vertical", spacing=dp(8),
                         padding=[dp(24), dp(16), dp(24), dp(20)],
                         size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        self.name_in = self._field(body, "الاسم الرباعي", "الاسم الكامل )أربعة أسماء(")
        self.shop_in = self._field(body, "اسم المشروع أو اسم الدكان", "مثال: بقالة النور")
        self.loc_in = self._field(body, "موقع الدكان )المنطقة(", "المنطقة التي يوجد فيها الدكان")
        self.phone_in = self._field(body, "رقم التاجر", "771234567", input_filter="int")
        self.email_in = self._field(body, "البريد الإلكتروني (Gmail)", "example@gmail.com")
        self.pass_in = self._field(body, "كلمة المرور", "********")
        self.confirm_in = self._field(body, "تأكيد كلمة المرور", "********")

        # ---- الموافقة على شروط الاستخدام ----
        body.add_widget(Widget(size_hint_y=None, height=dp(4)))
        self.terms_btn = mk_btn("شروط الاستخدام )اضغط للقراءة والموافقة(",
                                height=dp(48), font_size=dp(15),
                                background_color=BLUE)
        self.terms_btn.bind(on_release=lambda *a: self.app.open_terms())
        body.add_widget(self.terms_btn)
        self.terms_state = mk_text("لم تتم الموافقة على شروط الاستخدام بعد",
                                   dp(12), RED, halign="center", height=dp(26))
        body.add_widget(self.terms_state)

        self.msg_dt = mk_text("", dp(13), RED, halign="center", height=dp(28))
        body.add_widget(self.msg_dt)

        self.save_btn = mk_btn("تسجيل", height=dp(52), font_size=dp(18),
                               background_color=GRAY_BTN)
        self.save_btn.disabled = True
        self.save_btn.bind(on_release=self.do_register)
        body.add_widget(self.save_btn)

        sv.add_widget(body)
        root.add_widget(sv)
        self.add_widget(root)
        if self.agreed:
            self.set_agreed()

    def set_agreed(self):
        self.agreed = True
        self.save_btn.disabled = False
        self.save_btn.set_bg(GREEN)
        self.terms_state._color = tuple(GREEN)
        self.terms_state.text = "تمت الموافقة على شروط الاستخدام"

    def do_register(self, *a):
        name = self.name_in.text.strip()
        shop = self.shop_in.text.strip()
        loc = self.loc_in.text.strip()
        phone = self.phone_in.text.strip()
        email = self.email_in.text.strip().lower()
        password = self.pass_in.text.strip()
        confirm = self.confirm_in.text.strip()

        if len(name.split()) < 4:
            self.msg_dt.text = "الرجاء إدخال الاسم الرباعي كاملاً"
            return
        if not shop:
            self.msg_dt.text = "أدخل اسم المشروع أو الدكان"
            return
        if not loc:
            self.msg_dt.text = "أدخل موقع الدكان"
            return
        if len(phone) < 7:
            self.msg_dt.text = "أدخل رقم التاجر بشكل صحيح"
            return
        if not re.fullmatch(r"[a-z0-9._+\-]+@gmail\.com", email):
            self.msg_dt.text = "يجب أن يكون البريد من نوع @gmail.com"
            return
        if len(password) < 4:
            self.msg_dt.text = "كلمة المرور قصيرة جداً"
            return
        if password != confirm:
            self.msg_dt.text = "كلمتا المرور غير متطابقتين"
            return
        if not self.agreed:
            self.msg_dt.text = "يجب الموافقة على شروط الاستخدام"
            return

        self.msg_dt.text = "جاري التسجيل..."

        def worker():
            ok, msg = self.app.do_register(name, email, password,
                                           shop, loc, phone)
            Clock.schedule_once(
                lambda dt: self._on_result(ok, msg, email, name,
                                           shop, loc, phone), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_result(self, ok, msg, email, name, shop, loc, phone):
        if ok:
            self.msg_dt.text = ""
            self.app.on_register_success(email, name, shop, loc, phone)
        else:
            self.msg_dt.text = msg or "فشل التسجيل"


class TermsScreen(Screen):
    """صفحة شروط الاستخدام الكاملة. زر \"أوافق\" يتفعّل عند الوصول للنهاية."""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.can_agree = False
        self.build_ui()

    @staticmethod
    def _wrap(text, width=34):
        out = []
        for para in text.strip().split("\n"):
            para = para.strip()
            if not para:
                out.append("")
                continue
            out.extend(textwrap.wrap(para, width=width) or [""])
        return out

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header("شروط الاستخدام", HEADER,
                                    on_back=lambda *a: self.app.terms_back()))
        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4))
        self.lay = GridLayout(cols=1, spacing=dp(2), size_hint_y=None,
                              padding=[dp(14), dp(12), dp(14), dp(16)])
        self.lay.bind(minimum_height=self.lay.setter("height"))
        for line in self._wrap(TERMS_TEXT):
            if line:
                self.lay.add_widget(mk_text(line, dp(15), TEXT, height=dp(28)))
            else:
                self.lay.add_widget(Widget(size_hint_y=None, height=dp(12)))
        self.scroll.add_widget(self.lay)
        root.add_widget(self.scroll)

        bar = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(96), padding=[dp(14), dp(6), dp(14), dp(10)],
                        spacing=dp(4))
        self.hint = mk_text("اقرأ الشروط حتى النهاية لتفعيل زر الموافقة",
                            dp(12), MUTED, halign="center", height=dp(22))
        bar.add_widget(self.hint)
        self.agree_btn = mk_btn("أوافق", height=dp(52), font_size=dp(18),
                                background_color=GRAY_BTN)
        self.agree_btn.disabled = True
        self.agree_btn.bind(on_release=lambda *a: self.app.terms_agreed())
        bar.add_widget(self.agree_btn)
        root.add_widget(bar)
        self.add_widget(root)

        self.scroll.bind(scroll_y=self._check, height=self._check)
        self.lay.bind(height=self._check)
        Clock.schedule_once(self._check, 0.5)

    def _check(self, *a):
        if self.can_agree:
            return
        if (self.lay.height <= self.scroll.height + dp(6)
                or self.scroll.scroll_y <= 0.03):
            self.can_agree = True
            self.agree_btn.disabled = False
            self.agree_btn.set_bg(GREEN)
            self.hint.text = "يمكنك الآن الموافقة"


# ============================================================
# 19) شاشة العميل
# ============================================================
class ClientScreen(Screen):
    def __init__(self, app, client_index, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.client_index = client_index
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header("بيانات العميل", HEADER,
                                    on_back=lambda *a: self.app.go_main()))

        info = BoxLayout(orientation="vertical", size_hint_y=None,
                         height=dp(150),
                         padding=[dp(12), dp(8), dp(12), dp(12)], spacing=dp(4))
        with info.canvas.before:
            Color(*HEADER)
            info_rect = RoundedRectangle(pos=info.pos, size=info.size,
                                         radius=[0, 0, dp(22), dp(22)])

        def _ui(*a):
            info_rect.pos = info.pos
            info_rect.size = info.size
        info.bind(pos=_ui, size=_ui)

        top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.name_dt = mk_text("", dp(21), WHITE, halign="right")
        top.add_widget(self.name_dt)
        edit_btn = mk_btn("تعديل", size_hint=(None, None),
                          size=(dp(64), dp(36)), font_size=dp(13),
                          background_color=GLASS,
                          pos_hint={"center_y": 0.5})
        edit_btn.bind(on_release=self.edit_client_data)
        top.add_widget(edit_btn)
        info.add_widget(top)

        self.phone_dt = mk_text("", dp(13), (0.85, 0.91, 0.98, 1),
                                halign="right", height=dp(22))
        info.add_widget(self.phone_dt)

        bal_box = CardBox(orientation="vertical", size_hint_y=None,
                          height=dp(70), padding=[dp(14), dp(4)], spacing=0,
                          bg=(1, 1, 1, 0.16), shadow=False, radius=dp(14))
        bal_box.add_widget(mk_text("الرصيد المستحق", dp(12), SOFT_WHITE,
                                   height=dp(20)))
        self.balance_dt = mk_text("", dp(24), (1, 0.93, 0.65, 1), hint_y=1)
        bal_box.add_widget(self.balance_dt)
        info.add_widget(bal_box)
        root.add_widget(info)

        body = make_body(padding=[dp(12), dp(6), dp(12), dp(10)])
        body.spacing = dp(8)

        actions = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(8))
        specs = [
            ("إضافة\nفاتورة", ORANGE,
             lambda *a: self.app.open_add_invoice_screen(self.client_index)),
            ("سند\nقبض", GREEN,
             lambda *a: self.app.open_add_receipt_screen(self.client_index)),
            ("إرسال\nالدين", BLUE, self.send_debt_whatsapp),
            ("حذف\nالعميل", RED, self.confirm_delete),
        ]
        for label, col, cb in specs:
            b = mk_btn(label, height=dp(62), font_size=dp(13),
                       background_color=col)
            b.bind(on_release=cb)
            actions.add_widget(b)
        body.add_widget(actions)

        sec = BoxLayout(size_hint_y=None, height=dp(28))
        self.count_dt = mk_text("", dp(12), MUTED, halign="left", hint_x=0.35)
        sec.add_widget(self.count_dt)
        sec.add_widget(mk_text("الفواتير والسندات", dp(16), PRIMARY,
                               hint_x=0.65))
        body.add_widget(sec)

        scroll, self.invoices_layout = make_scroll_list()
        body.add_widget(scroll)
        root.add_widget(body)
        self.add_widget(root)

    def refresh(self):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        self.name_dt.text = c.get("name", "بدون اسم")
        self.phone_dt.text = "الرقم: " + (c.get("phone", "") or "غير محدد")
        bal = c.get("balance", 0)
        self.balance_dt.text = f"{money_signed(bal)} ريال"

        self.invoices_layout.clear_widgets()
        invoices = c.get("invoices", [])
        self.count_dt.text = f"{len(invoices)} عملية"
        if not invoices:
            empty = BoxLayout(orientation="vertical", size_hint_y=None,
                              height=dp(90))
            empty.add_widget(mk_text("لا توجد فواتير بعد", dp(16), MUTED,
                                     halign="center", hint_y=0.5))
            empty.add_widget(mk_text("اضغط على إضافة فاتورة للبدء", dp(13),
                                     MUTED, halign="center", hint_y=0.5))
            self.invoices_layout.add_widget(empty)
            return
        for real_i in range(len(invoices) - 1, -1, -1):
            inv = invoices[real_i]
            card = make_invoice_card(
                inv,
                on_tap=lambda idx=real_i: self.app.open_invoice_screen(
                    self.client_index, idx))
            self.invoices_layout.add_widget(card)

    def edit_client_data(self, *a):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        content = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(10))
        content.add_widget(mk_text("اسم العميل", dp(13), MUTED, height=dp(22)))
        name_input = mk_input(size_hint_y=None, height=dp(48),
                              hint_text="الاسم الكامل")
        name_input.text = c.get("name", "")
        content.add_widget(name_input)
        content.add_widget(mk_text("رقم الواتساب", dp(13), MUTED,
                                   height=dp(22)))
        phone_input = mk_input(input_filter="int", size_hint_y=None,
                               height=dp(48), hint_text="0771234567")
        phone_input.text = c.get("phone", "")
        content.add_widget(phone_input)
        content.add_widget(Widget())
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        save_btn = mk_btn("حفظ", background_color=GREEN)
        cancel_btn = mk_btn("إلغاء", background_color=GRAY_BTN)
        btns.add_widget(save_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)
        popup = make_arabic_popup("تعديل بيانات العميل", content,
                                  size_hint=(0.92, 0.55))

        def do_save(*a):
            n = name_input.text.strip()
            if not n:
                return
            c["name"] = n
            c["phone"] = phone_input.text.strip()
            c["mod"] = now_full()
            self.app.save()
            self.refresh()
            popup.dismiss()

        save_btn.bind(on_release=do_save)
        cancel_btn.bind(on_release=lambda *a: popup.dismiss())
        popup.open()

    def send_debt_whatsapp(self, *a):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        show_document_popup(clients[self.client_index], None, "statement")

    def confirm_delete(self, *a):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(mk_text(f"هل تريد حذف العميل: {c.get('name','')} ؟",
                                   dp(16), TEXT, halign="center",
                                   height=dp(44)))
        content.add_widget(Widget())
        bb = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes = mk_btn("نعم", background_color=RED)
        no = mk_btn("إلغاء", background_color=GRAY_BTN)
        bb.add_widget(yes)
        bb.add_widget(no)
        content.add_widget(bb)
        popup = make_arabic_popup("تأكيد الحذف", content,
                                  size_hint=(0.88, 0.4),
                                  title_color=RED, separator_color=RED)

        def do_delete(*a):
            if self.client_index < len(clients):
                gone = clients.pop(self.client_index)
                tomb = self.app.data.setdefault("_deleted", [])
                tomb.append(gone.get("id"))
                tomb.extend(i.get("id") for i in gone.get("invoices", []))
            self.app.save()
            popup.dismiss()
            self.app.go_main()

        yes.bind(on_release=do_delete)
        no.bind(on_release=lambda *a: popup.dismiss())
        popup.open()


# ============================================================
# 20) شاشة إضافة فاتورة
# ============================================================
class AddInvoiceScreen(Screen):
    def __init__(self, app, client_index, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.client_index = client_index
        self.items = []
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            "إضافة فاتورة", ORANGE,
            on_back=lambda *a: self.app.go_client(self.client_index,
                                                  back=True)))
        body = make_body(padding=[dp(12), dp(8), dp(12), dp(10)])
        (form, self.item_name, self.item_qty, self.item_price,
         self.item_note, self.item_disc) = build_item_form(self.add_item)
        body.add_widget(form)
        body.add_widget(mk_text("الأصناف المضافة", dp(14), MUTED,
                                height=dp(24)))
        scroll, self.items_layout = make_scroll_list(spacing=dp(8))
        body.add_widget(scroll)

        total_card = CardBox(orientation="horizontal", size_hint_y=None,
                             height=dp(50), padding=[dp(14), 0],
                             bg=SOFT_BLUE, shadow=False)
        self.total_dt = mk_text("الإجمالي: 0 ريال", dp(18), PRIMARY,
                                halign="center", hint_y=1)
        total_card.add_widget(self.total_dt)
        body.add_widget(total_card)

        save_btn = mk_btn("حفظ الفاتورة", height=dp(52), font_size=dp(17),
                          background_color=GREEN)
        save_btn.bind(on_release=self.save_invoice)
        body.add_widget(save_btn)

        root.add_widget(body)
        self.add_widget(root)
        self.refresh_items()

    def add_item(self):
        it = parse_item(self.item_name, self.item_qty, self.item_price,
                        self.item_note, self.item_disc)
        if it is None:
            return
        self.items.append(it)
        self.refresh_items()

    def refresh_items(self):
        self.items_layout.clear_widgets()
        for i, it in enumerate(self.items):
            self.items_layout.add_widget(
                make_item_row(it,
                              on_delete=lambda idx=i: self.remove_item(idx)))
        total = sum(item_total(it) for it in self.items)
        self.total_dt.text = f"الإجمالي: {money(total)} ريال"

    def remove_item(self, idx):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self.refresh_items()

    def save_invoice(self, *a):
        if not self.items:
            return
        total = sum(item_total(it) for it in self.items)
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        c.setdefault("invoices", []).append({
            "id": gen_id(),
            "kind": "فاتورة",
            "date": now_str(),
            "items": list(self.items),
            "total": total,
            "mod": now_full(),
        })
        c["balance"] = c.get("balance", 0) + total
        self.app.save()
        self.app.go_client(self.client_index, back=True)


# ============================================================
# 21) شاشة سند القبض
# ============================================================
class AddReceiptScreen(Screen):
    def __init__(self, app, client_index, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.client_index = client_index
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            "سند قبض", GREEN,
            on_back=lambda *a: self.app.go_client(self.client_index,
                                                  back=True)))
        body = make_body(padding=[dp(12), dp(8), dp(12), dp(10)], spacing=dp(10))

        clients = self.app.data.get("clients", [])
        c = clients[self.client_index] if self.client_index < len(clients) else {}
        card = CardBox(orientation="vertical", size_hint_y=None, height=dp(250),
                       padding=[dp(14), dp(12)], spacing=dp(4))
        card.add_widget(mk_text(f"العميل: {c.get('name', '')}", dp(17),
                                PRIMARY, height=dp(30)))
        card.add_widget(mk_text(
            f"الرصيد الحالي: {money_signed(c.get('balance', 0))} ريال",
            dp(13), MUTED, height=dp(24)))
        card.add_widget(mk_text("المبلغ المقبوض)ريال(", dp(13), MUTED,
                                height=dp(24)))
        self.amount_input = mk_input(input_filter="float", hint_text="0",
                                     size_hint_y=None, height=dp(50))
        card.add_widget(self.amount_input)
        card.add_widget(mk_text("ملاحظات )اختياري(", dp(13), MUTED,
                                height=dp(24)))
        self.note_input = mk_input(hint_text="مثال: دفعة نقدية",
                                   size_hint_y=None, height=dp(50))
        card.add_widget(self.note_input)
        body.add_widget(card)

        save_btn = mk_btn("حفظ سند القبض", height=dp(52), font_size=dp(17),
                          background_color=GREEN)
        save_btn.bind(on_release=self.save_receipt)
        body.add_widget(save_btn)
        body.add_widget(Widget())
        root.add_widget(body)
        self.add_widget(root)

    def save_receipt(self, *a):
        try:
            amount = float(self.amount_input.text.strip())
        except ValueError:
            return
        if amount <= 0:
            return
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        note = self.note_input.text.strip() or "دفعة نقدية"
        c.setdefault("invoices", []).append({
            "id": gen_id(),
            "kind": "سند قبض",
            "date": now_str(),
            "items": [{"name": note, "qty": 1, "price": amount}],
            "total": amount,
            "mod": now_full(),
        })
        c["balance"] = c.get("balance", 0) - amount
        self.app.save()
        self.app.go_client(self.client_index, back=True)


# ============================================================
# 22) شاشة تفاصيل الفاتورة
# ============================================================
class InvoiceDetailScreen(Screen):
    def __init__(self, app, client_index, invoice_index, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.client_index = client_index
        self.invoice_index = invoice_index
        self.edit_mode = False
        self.items = []
        inv = self._get_invoice() or {}
        self.is_receipt = inv.get("kind", "فاتورة") != "فاتورة"
        self._form_h = dp(176) if self.is_receipt else dp(420)
        self.build_ui()
        self.refresh()

    def _get_invoice(self):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return None
        invoices = clients[self.client_index].get("invoices", [])
        if self.invoice_index >= len(invoices):
            return None
        return invoices[self.invoice_index]

    def build_ui(self):
        accent = GREEN if self.is_receipt else INV_RED
        root = BoxLayout(orientation="vertical", spacing=0)

        self.edit_btn = mk_btn("تعديل", size_hint=(None, None),
                               size=(dp(76), dp(38)), font_size=dp(14),
                               background_color=GLASS)
        self.edit_btn.bind(on_release=self.toggle_edit)
        root.add_widget(make_header(
            "تفاصيل السند" if self.is_receipt else "تفاصيل الفاتورة",
            accent,
            on_back=lambda *a: self.app.go_client(self.client_index,
                                                  back=True),
            right_widget=self.edit_btn))

        body = make_body(padding=[dp(12), dp(8), dp(12), dp(10)])
        summ = CardBox(orientation="vertical", size_hint_y=None, height=dp(76),
                       padding=[dp(14), dp(8)])
        self.client_dt = mk_text("", dp(17), TEXT, hint_y=0.55)
        self.info_dt = mk_text("", dp(13), MUTED, hint_y=0.45)
        summ.add_widget(self.client_dt)
        summ.add_widget(self.info_dt)
        body.add_widget(summ)

        body.add_widget(mk_text(
            "بيانات السند" if self.is_receipt else "الأصناف",
            dp(14), MUTED, height=dp(24)))
        scroll, self.items_layout = make_scroll_list(spacing=dp(8))
        body.add_widget(scroll)

        if self.is_receipt:
            self.form_card = CardBox(orientation="vertical",
                                     size_hint_y=None, height=dp(176),
                                     padding=[dp(12), dp(10), dp(12), dp(12)],
                                     spacing=dp(4))
            self.form_card.add_widget(mk_text("المبلغ المقبوض )ريال(",
                                              dp(13), MUTED, height=dp(20)))
            self.amount_in = mk_input(input_filter="float", hint_text="0",
                                      size_hint_y=None, height=dp(46))
            self.form_card.add_widget(self.amount_in)
            self.form_card.add_widget(mk_text("ملاحظة )اختياري(",
                                              dp(13), MUTED, height=dp(20)))
            self.note_in = mk_input(hint_text="مثال: دفعة نقدية",
                                    size_hint_y=None, height=dp(46))
            self.form_card.add_widget(self.note_in)
        else:
            (self.form_card, self.new_name, self.new_qty, self.new_price,
             self.new_note,
             self.new_disc) = build_item_form(self.add_item)

        total_card = CardBox(orientation="horizontal", size_hint_y=None,
                             height=dp(50), padding=[dp(14), 0],
                             bg=SOFT_BLUE, shadow=False)
        self.total_dt = mk_text("", dp(18), PRIMARY, halign="center", hint_y=1)
        total_card.add_widget(self.total_dt)
        body.add_widget(total_card)

        self.bottom = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.save_btn = mk_btn("حفظ التعديلات", height=dp(52),
                               background_color=BLUE)
        self.save_btn.bind(on_release=self.save_changes)
        self.del_btn = mk_btn("حذف", height=dp(52), background_color=RED)
        self.del_btn.bind(on_release=self.confirm_delete)
        self.wa_btn = mk_btn("إرسال واتساب", height=dp(52),
                             background_color=GREEN)
        self.wa_btn.bind(on_release=self.send_whatsapp)
        self._fill_bottom()

        body.add_widget(self.bottom)
        root.add_widget(body)
        self.add_widget(root)

    def _fill_bottom(self):
        self.bottom.clear_widgets()
        if self.edit_mode:
            self.bottom.add_widget(self.save_btn)
            self.bottom.add_widget(self.del_btn)
        else:
            self.bottom.add_widget(self.wa_btn)
            self.bottom.add_widget(self.del_btn)

    def refresh(self):
        inv = self._get_invoice()
        if inv is None:
            return
        clients = self.app.data.get("clients", [])
        c = clients[self.client_index]
        self.items = [dict(it) for it in inv.get("items", [])]
        self.client_dt.text = c.get("name", "")
        self.info_dt.text = f"{inv.get('kind','فاتورة')}  |  {inv.get('date','')}"
        if self.is_receipt:
            total = inv.get("total", 0)
            self.amount_in.text = f"{total:g}"
            self.note_in.text = self.items[0].get("name", "") if self.items else ""
        self.refresh_items()

    def refresh_items(self):
        self.items_layout.clear_widgets()
        for i, it in enumerate(self.items):
            if self.is_receipt:
                row = make_item_row(it, show_qty=False)
            elif self.edit_mode:
                row = make_item_row(it,
                                    on_delete=lambda idx=i: self.remove_item(idx))
            else:
                row = make_item_row(it)
            self.items_layout.add_widget(row)
        if self.edit_mode:
            self.form_card.height = self._form_h
            self.items_layout.add_widget(self.form_card)
        total = sum(item_total(it) for it in self.items)
        self.total_dt.text = f"الإجمالي: {money(total)} ريال"
        schedule_refresh(0.1)

    def add_item(self):
        it = parse_item(self.new_name, self.new_qty, self.new_price,
                        self.new_note, self.new_disc)
        if it is None:
            return
        self.items.append(it)
        self.refresh_items()

    def remove_item(self, idx):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self.refresh_items()

    def toggle_edit(self, *a):
        self.edit_mode = not self.edit_mode
        self.edit_btn.text = "إلغاء" if self.edit_mode else "تعديل"
        self.edit_btn.set_bg(RED if self.edit_mode else GLASS)
        self._fill_bottom()
        if self.edit_mode:
            self.refresh_items()
        else:
            self.refresh()
        schedule_refresh(0.1)

    def save_changes(self, *a):
        """يحدّث نفس الفاتورة (نفس الـ id) بدل ما يحذف ويضيف."""
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        invoices = c.get("invoices", [])
        if self.invoice_index >= len(invoices):
            return
        old = invoices[self.invoice_index]
        old_kind = old.get("kind", "فاتورة")
        old_total = old.get("total", 0)
        old_id = old.get("id", gen_id())

        if self.is_receipt:
            try:
                amount = float(self.amount_in.text.strip())
            except ValueError:
                return
            if amount <= 0:
                return
            note = self.note_in.text.strip() or "دفعة نقدية"
            new_items = [{"name": note, "qty": 1, "price": amount}]
            new_total = amount
        else:
            if self.new_name.text.strip():
                pending = parse_item(self.new_name, self.new_qty,
                                     self.new_price, self.new_note,
                                     self.new_disc)
                if pending is not None:
                    self.items.append(pending)
            if not self.items:
                return
            new_items = list(self.items)
            new_total = sum(item_total(it) for it in self.items)

        # تحديث في المكان (نفس الـ id)
        if old_kind == "فاتورة":
            c["balance"] = c.get("balance", 0) - old_total + new_total
        else:
            c["balance"] = c.get("balance", 0) + old_total - new_total

        old["items"] = new_items
        old["total"] = new_total
        old["id"] = old_id
        old["mod"] = now_full()
        self.app.save()
        self.app.go_client(self.client_index, back=True)

    def confirm_delete(self, *a):
        content = BoxLayout(orientation="vertical", spacing=dp(10),
                            padding=dp(12))
        content.add_widget(mk_text("هل تريد حذف هذه العملية؟", dp(16), TEXT,
                                   halign="center", height=dp(44)))
        content.add_widget(Widget())
        bb = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes = mk_btn("نعم", background_color=RED)
        no = mk_btn("إلغاء", background_color=GRAY_BTN)
        bb.add_widget(yes)
        bb.add_widget(no)
        content.add_widget(bb)
        popup = make_arabic_popup("تأكيد", content, size_hint=(0.88, 0.38),
                                  title_color=RED, separator_color=RED)

        def do_delete(*a):
            clients = self.app.data.get("clients", [])
            c = clients[self.client_index]
            invs = c.get("invoices", [])
            inv = invs.pop(self.invoice_index)
            self.app.data.setdefault("_deleted", []).append(inv.get("id"))
            if inv.get("kind") == "فاتورة":
                c["balance"] = c.get("balance", 0) - inv.get("total", 0)
            else:
                c["balance"] = c.get("balance", 0) + inv.get("total", 0)
            self.app.save()
            popup.dismiss()
            self.app.go_client(self.client_index, back=True)

        yes.bind(on_release=do_delete)
        no.bind(on_release=lambda *a: popup.dismiss())
        popup.open()

    def send_whatsapp(self, *a):
        clients = self.app.data.get("clients", [])
        if self.client_index >= len(clients):
            return
        c = clients[self.client_index]
        inv = self._get_invoice()
        if inv is None:
            return
        mode = "receipt" if self.is_receipt else "invoice"
        show_document_popup(c, inv, mode, self.invoice_index + 1)


# ============================================================
# 23) شاشة المزامنة
# ============================================================
class SyncScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header("مزامنة", HEADER))
        body = BoxLayout(orientation="vertical", spacing=dp(20),
                         padding=[dp(24), dp(80), dp(24), dp(24)])
        self.msg_dt = mk_text("جاري المزامنة...", dp(20), PRIMARY,
                              halign="center", height=dp(40))
        body.add_widget(self.msg_dt)
        self.sub_dt = mk_text("", dp(14), MUTED, halign="center", height=dp(30))
        body.add_widget(self.sub_dt)
        body.add_widget(Widget())
        self.close_btn = mk_btn("إغلاق", height=dp(52),
                                background_color=GRAY_BTN)
        self.close_btn.bind(on_release=lambda *a: self.app.go_main())
        body.add_widget(self.close_btn)
        root.add_widget(body)
        self.add_widget(root)

    def set_status(self, main, sub=""):
        self.msg_dt.text = main
        self.sub_dt.text = sub


# ============================================================
# 23-ب) شاشة الإعدادات
# ============================================================
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header("الإعدادات", HEADER,
                                    on_back=lambda *a: self.app.go_main()))
        sv = ScrollView(size_hint=(1, 1), bar_width=dp(3))
        body = BoxLayout(orientation="vertical", spacing=dp(10),
                         padding=[dp(14), dp(12), dp(14), dp(14)],
                         size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        user = self.app.data.get("user") or {}
        card = CardBox(orientation="vertical", size_hint_y=None,
                       height=dp(310), padding=[dp(14), dp(10)],
                       spacing=dp(2))
        card.add_widget(mk_text("معلومات الحساب", dp(16), PRIMARY,
                                height=dp(32)))
        for label, key in (("الاسم", "name"),
                           ("اسم المشروع / الدكان", "shop"),
                           ("موقع الدكان", "loc"),
                           ("رقم التاجر", "phone"),
                           ("البريد الإلكتروني", "email")):
            card.add_widget(mk_text(label, dp(12), MUTED, height=dp(20)))
            card.add_widget(mk_text(user.get(key, "") or "-", dp(15), TEXT,
                                    height=dp(28)))
        body.add_widget(card)

        def add_btn(text, color, cb):
            b = mk_btn(text, height=dp(50), font_size=dp(16),
                       background_color=color)
            b.bind(on_release=cb)
            body.add_widget(b)

        add_btn("تعديل بيانات البائع", BLUE, self.app.open_edit_profile)
        add_btn("تغيير كلمة المرور", BLUE, self.app.open_change_password)
        add_btn("الأجهزة المتصلة بالحساب", BLUE, self.app.open_devices)
        add_btn("الحسابات )تبديل / إضاف(", BLUE, self.app.open_accounts)
        add_btn("تغيير الخط", BLUE, self.app.open_fonts)
        add_btn("الوضع النهاري" if is_dark() else "الوضع الليلي", ORANGE,
                self.app.toggle_theme)
        add_btn("تسجيل الخروج", GRAY_BTN, self.confirm_logout)
        add_btn("حذف الحساب", RED, self.confirm_delete_account)

        body.add_widget(mk_text("تسجيل الخروج يُبقي بياناتك محفوظة على الجهاز "
                                "وعلى الانترنت اذا عملت مزامنه. حذف الحساب يمسح كل شيء نهائياً.",
                                dp(12), MUTED, halign="center", height=dp(48)))
        sv.add_widget(body)
        root.add_widget(sv)
        self.add_widget(root)

    # ---------- تسجيل الخروج ----------
    def confirm_logout(self, *a):
        content = BoxLayout(orientation="vertical", spacing=dp(10),
                            padding=dp(12))
        content.add_widget(mk_text("هل تريد تسجيل الخروج؟", dp(16), TEXT,
                                   halign="center", height=dp(40)))
        content.add_widget(mk_text("اضغط مزامنة قبل الخروج لرفع آخر التغييرات",
                                   dp(13), MUTED, halign="center",
                                   height=dp(44)))
        content.add_widget(Widget())
        bb = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes = mk_btn("نعم", background_color=RED)
        no = mk_btn("إلغاء", background_color=GRAY_BTN)
        bb.add_widget(yes)
        bb.add_widget(no)
        content.add_widget(bb)
        popup = make_arabic_popup("خروج", content, size_hint=(0.88, 0.42),
                                  title_color=RED, separator_color=RED)

        def do(*a):
            popup.dismiss()
            self.app.do_logout()

        yes.bind(on_release=do)
        no.bind(on_release=lambda *a: popup.dismiss())
        popup.open()

    # ---------- حذف الحساب ----------
    def confirm_delete_account(self, *a):
        content = BoxLayout(orientation="vertical", spacing=dp(6),
                            padding=dp(10))
        content.add_widget(mk_text(
            "سيُحذف حسابك وكل عملائك وفواتيرك من هذا الجهاز ومن الانترنت نهائياً",
            dp(14), RED, halign="center", height=dp(64)))
        content.add_widget(mk_text("اكتب كلمة المرور للتأكيد", dp(13), MUTED,
                                   height=dp(22)))
        pw_in = mk_input(hint_text="********", size_hint_y=None,
                         height=dp(48))
        content.add_widget(pw_in)
        msg = mk_text("", dp(13), RED, halign="center", height=dp(28))
        content.add_widget(msg)
        content.add_widget(Widget())
        bb = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes = mk_btn("حذف نهائي", background_color=RED)
        no = mk_btn("إلغاء", background_color=GRAY_BTN)
        bb.add_widget(yes)
        bb.add_widget(no)
        content.add_widget(bb)
        popup = make_arabic_popup("حذف الحساب", content, size_hint=(0.92, 0.62),
                                  title_color=RED, separator_color=RED,
                                  auto_dismiss=False)
        busy = {"v": False}

        def done(ok, err):
            busy["v"] = False
            if ok:
                popup.dismiss()
                self.app.wipe_local_and_restart()
            else:
                msg.text = err or "فشل الحذف"

        def do(*a):
            if busy["v"]:
                return
            password = pw_in.text.strip()
            if not password:
                msg.text = "أدخل كلمة المرور"
                return
            busy["v"] = True
            msg.text = "جاري الحذف..."

            def worker():
                ok, err = self.app.delete_account_remote(password)
                Clock.schedule_once(lambda dt: done(ok, err), 0)

            threading.Thread(target=worker, daemon=True).start()

        yes.bind(on_release=do)
        no.bind(on_release=lambda *a: (None if busy["v"] else popup.dismiss()))
        popup.open()



# ============================================================
# 23-ب) شاشات الإعدادات الفرعية
# ============================================================
ACC_KEYS = ("user", "clients", "_deleted", "_tg_meta", "_sv", "_dev_ok", "owner")


class FormScreen(Screen):
    TITLE = ""
    SAVE_TEXT = "حفظ"
    _busy = False

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def fields(self, body):
        pass

    def labeled(self, body, label, hint="", text="", **kw):
        body.add_widget(mk_text(label, dp(13), MUTED, height=dp(22)))
        w = mk_input(hint_text=hint, size_hint_y=None, height=dp(50), **kw)
        if text:
            w.text = text
        body.add_widget(w)
        return w

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            self.TITLE, HEADER,
            on_back=lambda *a: self.app.open_settings(back=True)))
        sv = ScrollView(size_hint=(1, 1))
        body = BoxLayout(orientation="vertical", spacing=dp(8),
                         padding=[dp(24), dp(16), dp(24), dp(20)],
                         size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        self.fields(body)
        self.msg_dt = mk_text("", dp(13), RED, halign="center", height=dp(28))
        body.add_widget(self.msg_dt)
        btn = mk_btn(self.SAVE_TEXT, height=dp(52), font_size=dp(18),
                     background_color=GREEN)
        btn.bind(on_release=self.on_save)
        body.add_widget(btn)
        sv.add_widget(body)
        root.add_widget(sv)
        self.add_widget(root)

    def on_save(self, *a):
        pass

    def run(self, work, on_ok):
        if self._busy:
            return
        self._busy = True
        self.msg_dt.text = "جاري الحفظ..."

        def w():
            try:
                ok, res = work()
            except TgError as e:
                ok, res = False, str(e)
            except Exception as e:
                ok, res = False, str(e)[:60]
            Clock.schedule_once(lambda dt: self._done(ok, res, on_ok), 0)

        threading.Thread(target=w, daemon=True).start()

    def _done(self, ok, res, on_ok):
        self._busy = False
        if ok:
            self.msg_dt.text = ""
            on_ok()
        else:
            self.msg_dt.text = res or "فشلت العملية"


class ChangePasswordScreen(FormScreen):
    TITLE = "تغيير كلمة المرور"

    def fields(self, body):
        self.old_in = self.labeled(body, "كلمة المرور الحالية", "********")
        self.new_in = self.labeled(body, "كلمة المرور الجديدة", "********")
        self.conf_in = self.labeled(body, "تأكيد كلمة المرور الجديدة", "********")
        body.add_widget(mk_text(
            "عند التغيير سيتم تسجيل الخروج من جميع الأجهزة الأخرى.",
            dp(12), MUTED, halign="center", height=dp(26)))

    def on_save(self, *a):
        old = self.old_in.text.strip()
        new = self.new_in.text.strip()
        if not old:
            self.msg_dt.text = "أدخل كلمة المرور الحالية"
            return
        if len(new) < 4:
            self.msg_dt.text = "كلمة المرور الجديدة قصيرة جداً"
            return
        if new != self.conf_in.text.strip():
            self.msg_dt.text = "كلمتا المرور غير متطابقتين"
            return
        self.run(lambda: self.app.change_password_remote(old, new),
                 lambda: self.app.open_settings(back=True))


class EditProfileScreen(FormScreen):
    TITLE = "تعديل بيانات البائع"

    def fields(self, body):
        u = self.app.data.get("user") or {}
        self.name_in = self.labeled(body, "الاسم", "", u.get("name", ""))
        self.shop_in = self.labeled(body, "اسم المشروع / الدكان", "", u.get("shop", ""))
        self.loc_in = self.labeled(body, "موقع الدكان", "", u.get("loc", ""))
        self.phone_in = self.labeled(body, "رقم التاجر", "", u.get("phone", ""),
                                     input_filter="int")

    def on_save(self, *a):
        name = self.name_in.text.strip()
        shop = self.shop_in.text.strip()
        loc = self.loc_in.text.strip()
        phone = self.phone_in.text.strip()
        if len(name.split()) < 2:
            self.msg_dt.text = "أدخل الاسم كاملاً"
            return
        if not shop or not loc:
            self.msg_dt.text = "أدخل اسم المشروع والموقع"
            return
        if len(phone) < 7:
            self.msg_dt.text = "أدخل رقم التاجر بشكل صحيح"
            return
        self.run(lambda: self.app.update_profile_remote(name, shop, loc, phone),
                 lambda: self.app.open_settings(back=True))


class DevicesScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()
        self.load()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            "الأجهزة المتصلة", HEADER,
            on_back=lambda *a: self.app.open_settings(back=True)))
        body = make_body(padding=[dp(12), dp(10), dp(12), dp(10)])
        self.status = mk_text("جاري التحميل...", dp(13), MUTED,
                              halign="center", height=dp(30))
        body.add_widget(self.status)
        scroll, self.list_layout = make_scroll_list(spacing=dp(8))
        body.add_widget(scroll)
        root.add_widget(body)
        self.add_widget(root)

    def load(self):
        self.status.text = "جاري التحميل..."

        def w():
            try:
                email = (self.app.data.get("user") or {}).get("email", "")
                rec, _m = DB.get_user(email)
                devs = (rec or {}).get("dev") or {}
                Clock.schedule_once(lambda dt: self.show(devs), 0)
            except Exception as e:
                msg = str(e)[:60]
                Clock.schedule_once(lambda dt: self.fail(msg), 0)

        threading.Thread(target=w, daemon=True).start()

    def fail(self, msg):
        self.status.text = msg or "تعذر تحميل الأجهزة )تحقق من الانترنت("

    def show(self, devs):
        self.list_layout.clear_widgets()
        me = self.app.data.get("device_id")
        if not devs:
            self.status.text = "لا توجد أجهزة مسجلة، اضغط مزامنة أولاً"
            return
        self.status.text = f"عدد الأجهزة: {len(devs)}"
        items = sorted(devs.items(), key=lambda kv: (kv[1] or {}).get("t", ""),
                       reverse=True)
        for did, info in items:
            info = info or {}
            row = CardBox(orientation="horizontal", size_hint_y=None,
                          height=dp(74), padding=[dp(12), dp(8)],
                          spacing=dp(8))
            if did != me:
                kb = mk_btn("طرد", size_hint=(None, None),
                            size=(dp(64), dp(38)), font_size=dp(14),
                            background_color=RED,
                            pos_hint={"center_y": 0.5})
                kb.bind(on_release=lambda w, d=did, n=info.get("n", "جهاز"):
                        self.confirm_kick(d, n))
                row.add_widget(kb)
            box = BoxLayout(orientation="vertical")
            nm = info.get("n", "جهاز") + ("  )هذا الجهاز(" if did == me else "")
            box.add_widget(mk_text(nm, dp(15), TEXT, hint_y=0.55))
            box.add_widget(mk_text("آخر مزامنة: " + str(info.get("t", ""))[:16],
                                   dp(12), MUTED, hint_y=0.45))
            row.add_widget(box)
            self.list_layout.add_widget(row)

    def confirm_kick(self, did, name):
        content = BoxLayout(orientation="vertical", spacing=dp(10),
                            padding=dp(12))
        content.add_widget(mk_text(f"طرد الجهاز ({name}) من الحساب؟",
                                   dp(15), TEXT, halign="center",
                                   height=dp(44)))
        content.add_widget(mk_text(
            "سيتم تسجيل خروجه عند أول مزامنة. لقفل الحساب عنه نهائياً غيّر كلمة المرور.",
            dp(12), MUTED, halign="center", height=dp(48)))
        content.add_widget(Widget())
        bb = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes = mk_btn("طرد", background_color=RED)
        no = mk_btn("إلغاء", background_color=GRAY_BTN)
        bb.add_widget(yes)
        bb.add_widget(no)
        content.add_widget(bb)
        popup = make_arabic_popup("طرد جهاز", content, size_hint=(0.9, 0.46),
                                  title_color=RED, separator_color=RED)

        def do(*a):
            popup.dismiss()
            self.status.text = "جاري الطرد..."

            def w():
                try:
                    ok, err = self.app.kick_device_remote(did)
                except Exception as e:
                    ok, err = False, str(e)[:60]
                Clock.schedule_once(
                    lambda dt: (self.load() if ok else self.fail(err)), 0)

            threading.Thread(target=w, daemon=True).start()

        yes.bind(on_release=do)
        no.bind(on_release=lambda *a: popup.dismiss())
        popup.open()


class FontScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.status_text = ""
        self.scanning = False
        self.downloading = None
        self.build_ui()
        self.refresh_catalog()

    def _names(self):
        items = (self.app.data.get("dl") or {}).get("items", {})
        names = set(USER_FONTS) | {n for n in items if FONT_NAME_RE.fullmatch(n)}
        return sorted(names, key=font_sort_key)

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            "تغيير الخط", HEADER,
            on_back=lambda *a: self.app.open_settings(back=True)))
        body = make_body(padding=[dp(12), dp(10), dp(12), dp(10)])
        self.status = mk_text(self.status_text, dp(13), MUTED,
                              halign="center", height=dp(28))
        body.add_widget(self.status)
        scroll, lay = make_scroll_list(spacing=dp(8))
        cur = self.app.data.get("font") or "font.otf"
        items = (self.app.data.get("dl") or {}).get("items", {})
        for fn in self._names():
            info = USER_FONTS.get(fn)
            if info:                       # مثبّت: عرض الاسم بنفس الخط
                sel = (fn == cur)
                row = CardBox(orientation="vertical", size_hint_y=None,
                              height=dp(84), padding=[dp(12), dp(6)],
                              bg=(SOFT_BLUE if sel else None),
                              on_tap=lambda f=fn: self.pick(f))
                sample = DrawnText(text="دفتر ديون الزهوب", font_size=dp(22),
                                   color=TEXT, halign="center",
                                   size_hint_y=0.62, font_override=info[0])
                sample.disabled = True
                row.add_widget(sample)
                label = font_label(fn) + ("  -  المستخدم حالياً" if sel else "")
                row.add_widget(mk_text(label, dp(12),
                                       PRIMARY if sel else MUTED,
                                       halign="center", hint_y=0.38))
            else:                          # غير منزَّل بعد
                row = CardBox(orientation="horizontal", size_hint_y=None,
                              height=dp(74), padding=[dp(12), dp(8)],
                              spacing=dp(8))
                busy = (self.downloading == fn)
                if not busy:
                    btn = mk_btn("تحميل", size_hint=(None, None),
                                 size=(dp(80), dp(38)), font_size=dp(14),
                                 background_color=GREEN,
                                 pos_hint={"center_y": 0.5})
                    btn.bind(on_release=lambda w, f=fn: self.download(f))
                    row.add_widget(btn)
                box = BoxLayout(orientation="vertical")
                kb = max(1, int((items.get(fn) or {}).get("size", 0) / 1024))
                box.add_widget(mk_text(font_label(fn), dp(16), TEXT,
                                       hint_y=0.55))
                box.add_widget(mk_text(
                    "جاري التحميل..." if busy else f"الحجم: {kb} KB",
                    dp(12), MUTED, hint_y=0.45))
                row.add_widget(box)
            lay.add_widget(row)
        body.add_widget(scroll)
        upd = mk_btn("تحديث القائمة", height=dp(46), font_size=dp(15),
                     background_color=BLUE)
        upd.bind(on_release=lambda *a: self.refresh_catalog())
        body.add_widget(upd)
        root.add_widget(body)
        self.add_widget(root)

    def _rebuild(self):
        self.clear_widgets()
        self.build_ui()
        schedule_refresh(0.05)

    def refresh_catalog(self):
        if self.scanning:
            return
        self.scanning = True
        self.status.text = "جاري البحث عن الخطوط المتاحة..."

        def w():
            err = None
            try:
                cat = self.app.data.setdefault("dl", {})
                scan_downloads(cat)
                self.app.save()
            except TgError as e:
                err = str(e)
            except Exception:
                err = "تعذر الاتصال، تحقق من الانترنت"
            Clock.schedule_once(lambda dt: self._after_scan(err), 0)

        threading.Thread(target=w, daemon=True).start()

    def _after_scan(self, err):
        self.scanning = False
        if err:
            self.status_text = err
        else:
            new = [n for n in self._names() if n not in USER_FONTS]
            self.status_text = (f"تتوفر {len(new)} خطوط للتحميل" if new
                                else "لا توجد خطوط جديدة للتحميل")
        self._rebuild()

    def download(self, fn):
        if self.downloading:
            return
        item = ((self.app.data.get("dl") or {}).get("items", {})).get(fn)
        if not item:
            return
        self.downloading = fn
        self._rebuild()

        def w():
            err = None
            try:
                download_font(fn, item)
            except TgError as e:
                err = str(e)
            except Exception:
                err = "فشل التحميل، تحقق من الانترنت"
            Clock.schedule_once(lambda dt: self._after_download(fn, err), 0)

        threading.Thread(target=w, daemon=True).start()

    def _after_download(self, fn, err):
        self.downloading = None
        self.status_text = err or f"تم تحميل {font_label(fn)}"
        self._rebuild()

    def pick(self, fn):
        self.app.set_font(fn)
        self._rebuild()


class AccountsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def _acc_card(self, user, tag, on_switch=None):
        row = CardBox(orientation="horizontal", size_hint_y=None,
                      height=dp(84), padding=[dp(12), dp(8)], spacing=dp(8))
        if on_switch:
            sb = mk_btn("تبديل", size_hint=(None, None),
                        size=(dp(70), dp(38)), font_size=dp(14),
                        background_color=GREEN, pos_hint={"center_y": 0.5})
            sb.bind(on_release=lambda *a: on_switch())
            row.add_widget(sb)
        box = BoxLayout(orientation="vertical")
        title = (user.get("shop") or user.get("name") or user.get("email", ""))
        box.add_widget(mk_text(title + tag, dp(15), TEXT, hint_y=0.4))
        box.add_widget(mk_text(user.get("name", ""), dp(12), MUTED, hint_y=0.3))
        box.add_widget(mk_text(user.get("email", ""), dp(12), MUTED, hint_y=0.3))
        row.add_widget(box)
        return row

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(make_header(
            "الحسابات", HEADER,
            on_back=lambda *a: self.app.open_settings(back=True)))
        body = make_body(padding=[dp(12), dp(10), dp(12), dp(10)])
        scroll, lay = make_scroll_list(spacing=dp(8))
        cur = self.app.data.get("user") or {}
        lay.add_widget(self._acc_card(cur, "  )الحالي("))
        for email, st in (self.app.data.get("accounts") or {}).items():
            u = (st or {}).get("user") or {"email": email}
            lay.add_widget(self._acc_card(
                u, "", on_switch=lambda e=email: self.app.switch_account(e)))
        body.add_widget(scroll)
        body.add_widget(mk_text(
            "التبديل بين الحسابات يعمل بدون انترنت. اضغط مزامنة بعد التبديل لرفع التغييرات.",
            dp(12), MUTED, halign="center", height=dp(40)))
        add = mk_btn("إضافة حساب آخر", height=dp(50), font_size=dp(16),
                     background_color=BLUE)
        add.bind(on_release=lambda *a: self.app.begin_add_account())
        body.add_widget(add)
        root.add_widget(body)
        self.add_widget(root)


# ============================================================
# 24) التطبيق
# ============================================================
class DebtBookApp(App):
    def build(self):
        self.title = "دفتر ديون الزهوب"
        self.data = load_data()
        self._adding = False
        if not self.data.get("device_id"):
            self.data["device_id"] = gen_id()
        # الخط: font.otf أول مرة، وبعدها الخط الذي اختاره المستخدم
        if not self.data.get("font"):
            self.data["font"] = "font.otf"
        if not set_app_font(self.data["font"]):
            set_app_font("font.otf")
        set_seller(self.data.get("user"))
        save_data(self.data)
        apply_theme(self.data.get("theme", "light"))
        Window.clearcolor = BG
        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        # [إصلاح كراش 2] حُذف طلب صلاحيات READ/WRITE_EXTERNAL_STORAGE بالكامل:
        # ملفات التطبيق داخل مجلده الخاص، والمشاركة عبر MediaStore، فلا حاجة لها
        # (وهي ممنوعة/بلا أثر في أندرويد 13+).

        self.search_query = ""
        self._seq = 0
        self._cur_client = 0

        self.sm = ScreenManager(transition=SlideTransition(duration=0.18))
        self.sm.add_widget(Screen(name="login"))

        Window.bind(on_keyboard=self._on_back_key)
        Window.bind(size=lambda *a: schedule_refresh(0.1))
        self.sm.transition.bind(on_complete=lambda *a: schedule_refresh(0.02))
        self.sm.bind(current=lambda *a: schedule_refresh(0.25))

        self.sm.current = "login"
        # [إصلاح كراش 7] أي شيء إضافي (عرض سجل الأعطال السابق) يتم بعد بدء التطبيق
        Clock.schedule_once(self._show_last_crash, 1.5)
        # جلسة واحدة: لو فيه مستخدم محفوظ نفتح الرئيسية مباشرة
        if (self.data.get("user") or {}).get("email"):
            Clock.schedule_once(lambda dt: self._build_main_and_show(), 0.1)
        else:
            Clock.schedule_once(lambda dt: self.go_login(), 0.1)
        return self.sm

    def _show_last_crash(self, dt=None):
        """لو توقف التطبيق في المرة السابقة بخطأ، نعرض نصه ليسهل إصلاحه."""
        try:
            if not os.path.exists(CRASH_LOG):
                return
            with open(CRASH_LOG, "r", encoding="utf-8") as f:
                txt = f.read()[-1500:]
            os.remove(CRASH_LOG)
            if not txt.strip():
                return
            box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
            box.add_widget(mk_text("سجل آخر خطأ )صوّره وأرسله للمطوّر(:", dp(14),
                                   RED, halign="center", height=dp(30)))
            lbl = KLabel(text=txt, color=(0.3, 0.3, 0.3, 1), font_size=dp(10),
                         halign="left", valign="top")
            lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
            box.add_widget(lbl)
            ok = mk_btn("حسناً", height=dp(46), background_color=GRAY_BTN)
            box.add_widget(ok)
            pop = make_arabic_popup("تقرير خطأ", box, size_hint=(0.95, 0.7),
                                    title_color=RED, separator_color=RED)
            ok.bind(on_release=lambda *a: pop.dismiss())
            pop.open()
        except Exception as e:
            print(f"[CRASHLOG] {e}")

    # ==========================================================
    # تسجيل / دخول (يعمل من أي جهاز، بدون getUpdates)
    # ==========================================================
    def _dev_id(self):
        if not self.data.get("device_id"):
            self.data["device_id"] = gen_id()
        return self.data["device_id"]

    def do_register(self, name, email, password, shop="", loc="", phone=""):
        try:
            rec, mid = DB.create_user(email, name, password, shop, loc, phone,
                                      self._dev_id(), get_device_name())
            self.data.setdefault("_tg_meta", {})["users_message_id"] = mid
            return True, "OK"
        except TgError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)[:50]

    def verify_login(self, email, password):
        try:
            rec, mid = DB.get_user(email)
            if not rec:
                return False, "البريد غير مسجل"
            if not DB.check_password(rec, password):
                return False, "كلمة المرور خاطئة"
            devs = dict(rec.get("dev") or {})
            devs[self._dev_id()] = {"n": get_device_name(), "t": now_full()}
            rec["dev"] = devs
            rec.setdefault("sv", 1)
            mid = DB.save_user(rec, mid)
            server, _texts = DB.read_clients(rec)
            return True, {"rec": rec, "mid": mid, "server": server}
        except TgError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)[:50]

    def _claim_device(self, email):
        """لو الجهاز كان لحساب آخر نبدأ ببيانات فاضية (لا نخلط الحسابات)."""
        owner = self.data.get("owner")
        if owner and owner != email:
            self.data["clients"] = []
            self.data["_deleted"] = []
            self.data["_tg_meta"] = {}
        self.data["owner"] = email

    # ---------- تعدد الحسابات على الجهاز ----------
    def stash_current(self):
        email = (self.data.get("user") or {}).get("email")
        if not email:
            return
        self.data.setdefault("accounts", {})[email] = {
            k: self.data.get(k) for k in ACC_KEYS}

    def _load_account_state(self, st):
        defaults = {"clients": [], "_deleted": [], "_tg_meta": {}}
        for k in ACC_KEYS:
            v = (st or {}).get(k)
            self.data[k] = v if v is not None else defaults.get(k)

    def _prepare_account_switch(self, email):
        cur = (self.data.get("user") or {}).get("email")
        if self._adding and cur and cur != email:
            self.stash_current()
            accs = self.data.setdefault("accounts", {})
            if email in accs:
                self._load_account_state(accs.pop(email))
            else:
                self._load_account_state({})
        self._adding = False

    def switch_account(self, email):
        accs = self.data.setdefault("accounts", {})
        if email not in accs:
            return
        self.stash_current()
        self._load_account_state(accs.pop(email))
        set_seller(self.data.get("user"))
        self.save()
        self._build_main_and_show()

    def begin_add_account(self):
        self._adding = True
        self.go_login()

    def cancel_add_account(self):
        self._adding = False
        self.go_main()

    @staticmethod
    def _user_from_rec(rec):
        return {"email": rec.get("email", ""), "name": rec.get("name", ""),
                "shop": rec.get("shop", ""), "loc": rec.get("loc", ""),
                "phone": rec.get("phone", "")}

    def on_register_success(self, email, name, shop="", loc="", phone=""):
        self._prepare_account_switch(email)
        self._claim_device(email)
        self.data["user"] = {"email": email, "name": name, "shop": shop,
                             "loc": loc, "phone": phone}
        self.data["_sv"] = 1
        self.data["_dev_ok"] = True
        set_seller(self.data["user"])
        self.save()
        self._build_main_and_show()

    def on_login_success(self, info):
        rec = info["rec"]
        email = rec.get("email", "")
        self._prepare_account_switch(email)
        self._claim_device(email)
        self.data["user"] = self._user_from_rec(rec)
        self.data["_sv"] = rec.get("sv", 1)
        self.data["_dev_ok"] = True
        set_seller(self.data["user"])
        meta = self.data.setdefault("_tg_meta", {})
        meta["users_message_id"] = info["mid"]
        try:
            server = info.get("server") or {}
            legacy = rec.get("_legacy_clients")
            if legacy:                       # بيانات من النظام القديم
                lc, _d = merge_client_data(server, legacy.get("clients", []), [])
                server = {"clients": lc, "deleted": server.get("deleted", [])}
                meta["legacy_clients_mid"] = rec.get("_legacy_clients_mid")
            clients, deleted = merge_client_data(
                server, self.data.get("clients", []),
                self.data.get("_deleted", []))
            self.data["clients"] = clients
            self.data["_deleted"] = deleted
        except Exception as e:
            print(f"[LOGIN SYNC] {e}")
        self.save()
        self._build_main_and_show()

    # ==========================================================
    # المزامنة
    # ==========================================================
    def do_sync(self, *a):
        sync_screen = SyncScreen(self)
        self._show(sync_screen, "left")

        def status(main, sub=""):
            Clock.schedule_once(lambda dt: sync_screen.set_status(main, sub), 0)

        def worker():
            try:
                email = (self.data.get("user") or {}).get("email")
                if not email:
                    status("خطأ", "غير مسجل")
                    return
                status("جاري المزامنة...")
                rec, mid = DB.get_user(email)
                if not rec:
                    status("الحساب غير موجود على الانترنت",
                           "ربما حُذف من جهاز آخر")
                    return
                err = self._session_error(rec)
                if err:
                    status("تم إنهاء الجلسة", err.replace("\n", " - "))
                    Clock.schedule_once(lambda dt: self.force_logout(err), 2.5)
                    return
                devs = dict(rec.get("dev") or {})
                devs[self._dev_id()] = {"n": get_device_name(), "t": now_full()}
                rec["dev"] = devs
                rec.setdefault("sv", 1)
                mid = DB.save_user(rec, mid)
                self.data["_dev_ok"] = True
                self.data["_sv"] = rec["sv"]
                self._apply_profile(rec)
                server, texts = DB.read_clients(rec)

                status("جاري الدمج...")
                clients, deleted = merge_client_data(
                    server, self.data.get("clients", []),
                    self.data.get("_deleted", []))

                status("جاري الرفع...")
                rec2 = DB.write_clients(
                    rec, mid, {"clients": clients, "deleted": deleted}, texts)

                meta = self.data.setdefault("_tg_meta", {})
                meta["users_message_id"] = mid
                meta["clients_message_ids"] = rec2.get("cl", [])
                old = meta.pop("legacy_clients_mid", None)
                if old:
                    DB.delete(DB.clients_ch, old)

                self.data["clients"] = clients
                self.data["_deleted"] = deleted
                self.save()

                status("تمت المزامنة بنجاح ✅", f"{len(clients)} عميل")
                Clock.schedule_once(lambda dt: self._after_sync(), 1.5)
            except TgError as e:
                print(f"[SYNC] {e}")
                status("فشلت المزامنة", str(e)[:60])
            except Exception as e:
                print(f"[SYNC] {e}")
                status("فشلت المزامنة", str(e)[:60])

        threading.Thread(target=worker, daemon=True).start()

    def _after_sync(self):
        self._build_main_and_show()

    # ==========================================================
    # الجلسات والأجهزة وبيانات البائع
    # ==========================================================
    def _session_error(self, rec):
        """يرجع نص الخطأ لو يجب إخراج هذا الجهاز، وإلا None."""
        try:
            sv = int(rec.get("sv", 1) or 1)
        except Exception:
            sv = 1
        local = self.data.get("_sv")
        if local is not None and sv != local:
            return ("لا يمكنك المزامنة\nتم تغيير كلمة المرور من الجهاز (%s)"
                    % (rec.get("pwdev") or "جهاز آخر"))
        devs = rec.get("dev")
        if (self.data.get("_dev_ok") and isinstance(devs, dict)
                and self._dev_id() not in devs):
            return "تم إخراج هذا الجهاز من الحساب\nسجّل الدخول من جديد"
        return None

    def _apply_profile(self, rec):
        u = dict(self.data.get("user") or {})
        new = self._user_from_rec(rec)
        new["email"] = u.get("email") or new["email"]
        if new != u:
            self.data["user"] = new
            set_seller(new)
            return True
        set_seller(u)
        return False

    def force_logout(self, msg):
        self.do_logout()
        try:
            scr = self.sm.get_screen("login")
            scr.msg_dt.height = dp(70)
            scr.msg_dt.text = msg
        except Exception as e:
            print(f"[FORCE LOGOUT] {e}")

    def _fresh_rec(self):
        """(ينفَّذ في خيط) يرجع (rec, mid, error)."""
        email = (self.data.get("user") or {}).get("email", "")
        rec, mid = DB.get_user(email)
        if not rec:
            return None, None, "الحساب غير موجود على الانترنت"
        err = self._session_error(rec)
        if err:
            return None, None, err.replace("\n", " - ")
        return rec, mid, None

    def change_password_remote(self, old, new):
        rec, mid, err = self._fresh_rec()
        if err:
            return False, err
        if not DB.check_password(rec, old):
            return False, "كلمة المرور الحالية خاطئة"
        me = self._dev_id()
        rec["pw"] = hash_password(new)
        rec.pop("password", None)
        rec["sv"] = int(rec.get("sv", 1) or 1) + 1
        rec["pwdev"] = get_device_name()
        rec["dev"] = {me: {"n": get_device_name(), "t": now_full()}}
        DB.save_user(rec, mid)
        self.data["_sv"] = rec["sv"]
        self.data["_dev_ok"] = True
        self.save()
        return True, ""

    def update_profile_remote(self, name, shop, loc, phone):
        rec, mid, err = self._fresh_rec()
        if err:
            return False, err
        rec["name"], rec["shop"], rec["loc"], rec["phone"] = name, shop, loc, phone
        DB.save_user(rec, mid)
        u = dict(self.data.get("user") or {})
        u.update({"name": name, "shop": shop, "loc": loc, "phone": phone})
        self.data["user"] = u
        set_seller(u)
        self.save()
        return True, ""

    def kick_device_remote(self, dev_id):
        rec, mid, err = self._fresh_rec()
        if err:
            return False, err
        devs = dict(rec.get("dev") or {})
        devs.pop(dev_id, None)
        rec["dev"] = devs
        DB.save_user(rec, mid)
        return True, ""

    def set_font(self, fn):
        if set_app_font(fn):
            self.data["font"] = fn
            self.save()
            refresh_all_texts()

    # ==========================================================
    # الشاشة الرئيسية
    # ==========================================================
    def _build_main_and_show(self):
        for s in list(self.sm.screens):
            if s.name == "main":
                self.sm.remove_widget(s)
        main_screen = Screen(name="main")
        self.main_screen = main_screen
        main_screen.add_widget(self._build_main())
        self.sm.add_widget(main_screen)
        self.sm.transition.direction = "left"
        self.sm.current = "main"
        self.refresh_clients()
        Clock.schedule_once(self._cleanup, 0.5)

    def _build_main(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        sync_btn = mk_btn("مزامنة", size_hint=(None, None),
                          size=(dp(76), dp(38)), font_size=dp(14),
                          background_color=GLASS)
        sync_btn.bind(on_release=self.do_sync)

        settings_btn = mk_btn("إعدادات", size_hint=(None, None),
                              size=(dp(76), dp(38)), font_size=dp(14),
                              background_color=GLASS)
        settings_btn.bind(on_release=self.open_settings)

        head = FloatLayout(size_hint_y=None, height=dp(60))
        with head.canvas.before:
            Color(*HEADER)
            hr = RoundedRectangle(pos=head.pos, size=head.size,
                                  radius=[0, 0, dp(20), dp(20)])

        def _uh(*a):
            hr.pos = head.pos
            hr.size = head.size
        head.bind(pos=_uh, size=_uh)

        user_name = (self.data.get("user") or {}).get("name", "")
        title = DrawnText(text=f"مرحباً {first_name(user_name)[:12]}",
                          font_size=dp(17), color=WHITE, halign="center",
                          size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        title.disabled = True
        head.add_widget(title)

        sync_btn.pos_hint = {"right": 0.98, "center_y": 0.5}
        head.add_widget(sync_btn)
        settings_btn.pos_hint = {"x": 0.02, "center_y": 0.5}
        head.add_widget(settings_btn)
        root.add_widget(head)

        body = make_body(padding=[dp(12), dp(8), dp(12), dp(10)])
        stats = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
        debt_card = CardBox(orientation="vertical", padding=[dp(10), dp(8)])
        debt_card.add_widget(mk_text("إجمالي الديون", dp(12), MUTED,
                                     halign="center", hint_y=0.4))
        self.stat_debt = mk_text("0 ريال", dp(18), RED, halign="center",
                                 hint_y=0.6)
        debt_card.add_widget(self.stat_debt)
        count_card = CardBox(orientation="vertical", padding=[dp(10), dp(8)])
        count_card.add_widget(mk_text("عدد العملاء", dp(12), MUTED,
                                      halign="center", hint_y=0.4))
        self.stat_count = mk_text("0", dp(18), PRIMARY, halign="center",
                                  hint_y=0.6)
        count_card.add_widget(self.stat_count)
        stats.add_widget(debt_card)
        stats.add_widget(count_card)
        body.add_widget(stats)

        self.search_input = mk_input(hint_text="ابحث باسم العميل أو رقمه...",
                                     size_hint_y=None, height=dp(48))
        self.search_input.bind(text=self.on_search)
        body.add_widget(self.search_input)

        add_btn = mk_btn("+ إضافة عميل جديد", height=dp(50),
                         font_size=dp(16), background_color=GREEN)
        add_btn.bind(on_release=self.open_add_client_popup)
        body.add_widget(add_btn)

        scroll, self.clients_layout = make_scroll_list(spacing=dp(8))
        body.add_widget(scroll)
        root.add_widget(body)
        return root

    # ==========================================================
    # الإعدادات / الثيم / الخروج / حذف الحساب
    # ==========================================================
    def open_settings(self, *a, back=False):
        self._show(SettingsScreen(self), "right" if back else "left")

    def open_edit_profile(self, *a):
        self._show(EditProfileScreen(self), "left")

    def open_change_password(self, *a):
        self._show(ChangePasswordScreen(self), "left")

    def open_devices(self, *a):
        self._show(DevicesScreen(self), "left")

    def open_accounts(self, *a):
        self._show(AccountsScreen(self), "left")

    def open_fonts(self, *a):
        self._show(FontScreen(self), "left")

    def open_terms(self):
        for s in list(self.sm.screens):
            if s.name == "terms":
                self.sm.remove_widget(s)
        ts = TermsScreen(self, name="terms")
        self.sm.transition.direction = "left"
        self.sm.add_widget(ts)
        self.sm.current = "terms"

    def terms_back(self):
        self._back_to_register(False)

    def terms_agreed(self):
        self._back_to_register(True)

    def _back_to_register(self, agreed):
        try:
            reg = self.sm.get_screen("register")
        except Exception:
            self.go_register()
            return
        if agreed:
            reg.set_agreed()
        self.sm.transition.direction = "right"
        self.sm.current = "register"
        Clock.schedule_once(self._cleanup, 0.5)

    def toggle_theme(self, *a):
        new = "light" if is_dark() else "dark"
        ov = None
        try:
            ov = _FadeOverlay(BG)
            Window.add_widget(ov)
        except Exception as e:
            print(f"[THEME] overlay: {e}")
            ov = None
        apply_theme(new)
        self.data["theme"] = new
        self.save()
        q = self.search_query
        self.main_screen.clear_widgets()
        self.main_screen.add_widget(self._build_main())
        if q:
            self.search_input.text = q
        self.refresh_clients()
        cur = self.sm.current_screen
        if isinstance(cur, SettingsScreen):
            cur.clear_widgets()
            cur.build_ui()
        schedule_refresh(0.1)
        if ov is not None:
            Animation(opacity=0, duration=0.45, t="out_quad").start(ov)
            Clock.schedule_once(lambda dt: Window.remove_widget(ov), 0.5)

    def do_logout(self, *a):
        """يرجع لشاشة الدخول والبيانات تبقى على الجهاز."""
        self.data["user"] = None
        set_seller({})
        self.save()
        for s in list(self.sm.screens):
            if s.name == "main":
                self.sm.remove_widget(s)
        self.go_login()

    def delete_account_remote(self, password):
        """(يعمل في خيط) يتحقق من كلمة المرور ويمسح كل رسائل المستخدم من
        القناتين. يرجع (ok, error)."""
        try:
            email = (self.data.get("user") or {}).get("email", "")
            rec, mid = DB.get_user(email)
            if rec is None:
                return True, ""          # محذوف مسبقاً من تليجرام
            if not DB.check_password(rec, password):
                return False, "كلمة المرور خاطئة"
            DB.delete_account(rec, mid)
            for key in ("_legacy_clients_mid",):
                if rec.get(key):
                    DB.delete(DB.clients_ch, rec[key])
            return True, ""
        except TgError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)[:60]

    def wipe_local_and_restart(self):
        """يحذف data.json بالكامل ويرجع التطبيق كأنه أول مرة."""
        keep = {k: self.data.get(k) for k in
                ("accounts", "device_id", "font", "theme", "dl")
                if self.data.get(k) is not None}
        for p in (DATA_FILE, DATA_FILE + ".tmp"):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception as e:
                print(f"[WIPE] {e}")
        try:
            if os.path.isdir(DOC_DIR):
                for fn in os.listdir(DOC_DIR):
                    os.remove(os.path.join(DOC_DIR, fn))
        except Exception:
            pass
        self.data = load_data()
        self.data.update(keep)
        set_seller({})
        self.save()
        apply_theme(self.data.get("theme", "light"))
        Window.clearcolor = BG
        self.search_query = ""
        for s in list(self.sm.screens):
            if s.name == "main":
                self.sm.remove_widget(s)
        self.go_login()

    # ==========================================================
    # تنقلات
    # ==========================================================
    def go_login(self):
        for s in list(self.sm.screens):
            if s.name == "login":
                self.sm.remove_widget(s)
        ls = LoginScreen(self, name="login")
        self.sm.add_widget(ls)
        self.sm.transition.direction = "right"
        self.sm.current = "login"
        Clock.schedule_once(self._cleanup, 0.5)

    def go_register(self):
        for s in list(self.sm.screens):
            if s.name in ("register", "terms"):
                self.sm.remove_widget(s)
        rs = RegisterScreen(self, name="register")
        self.sm.transition.direction = "left"
        self.sm.add_widget(rs)
        self.sm.current = "register"
        Clock.schedule_once(self._cleanup, 0.5)

    def _cleanup(self, dt=None):
        if self.sm.transition.is_active:
            Clock.schedule_once(self._cleanup, 0.2)
            return
        cur = self.sm.current
        keep = {"login", "register", "main", cur}
        for s in list(self.sm.screens):
            if s.name not in keep:
                try:
                    self.sm.remove_widget(s)
                except Exception:
                    pass

    def _show(self, screen, direction):
        self._seq += 1
        screen.name = "t%d" % self._seq
        self.sm.transition.direction = direction
        self.sm.add_widget(screen)
        self.sm.current = screen.name
        Clock.schedule_once(self._cleanup, 0.5)

    def go_main(self):
        self.refresh_clients()
        self.sm.transition.direction = "right"
        self.sm.current = "main"
        Clock.schedule_once(self._cleanup, 0.5)

    def go_client(self, client_index, back=False):
        self._cur_client = client_index
        self._show(ClientScreen(self, client_index),
                   "right" if back else "left")

    def open_client_screen(self, client_index):
        self.go_client(client_index)

    def open_add_invoice_screen(self, client_index):
        self._show(AddInvoiceScreen(self, client_index), "left")

    def open_add_receipt_screen(self, client_index):
        self._show(AddReceiptScreen(self, client_index), "left")

    def open_invoice_screen(self, client_index, invoice_index):
        self._show(InvoiceDetailScreen(self, client_index, invoice_index),
                   "left")

    def _on_back_key(self, window, key, *args):
        if key != 27:
            return False
        for w in list(Window.children):
            if isinstance(w, Popup):
                w.dismiss()
                schedule_refresh(0.3)
                return True
        cur = self.sm.current_screen
        if cur is None:
            return False
        if cur.name == "terms":
            self.terms_back()
            return True
        if cur.name == "register":
            self.go_login()
            return True
        if cur.name == "login":
            if self._adding:
                self.cancel_add_account()
                return True
            return False
        if cur.name == "main":
            return False
        if isinstance(cur, (ChangePasswordScreen, EditProfileScreen,
                            DevicesScreen, FontScreen, AccountsScreen)):
            self.open_settings(back=True)
        elif isinstance(cur, (ClientScreen, SyncScreen, SettingsScreen)):
            self.go_main()
        else:
            self.go_client(self._cur_client, back=True)
        return True

    # ==========================================================
    # أدوات
    # ==========================================================
    def save(self):
        save_data(self.data)

    def update_stats(self):
        clients = self.data.get("clients", [])
        total = sum(c.get("balance", 0) for c in clients)
        if hasattr(self, "stat_debt"):
            self.stat_debt.text = f"{money_signed(total)} ريال"
        if hasattr(self, "stat_count"):
            self.stat_count.text = str(len(clients))

    def on_search(self, instance, value):
        self.search_query = value.strip().lower()
        self.refresh_clients()

    def refresh_clients(self):
        if not hasattr(self, "clients_layout"):
            return
        self.clients_layout.clear_widgets()
        clients = self.data.get("clients", [])
        self.update_stats()
        if self.search_query:
            indexed = [(i, c) for i, c in enumerate(clients)
                       if self.search_query in c.get("name", "").lower()
                       or self.search_query in c.get("phone", "").lower()]
        else:
            indexed = list(enumerate(clients))
        if not indexed:
            msg = "لا توجد نتائج" if self.search_query else "لا يوجد عملاء بعد"
            sub = "جرّب اسماً آخر" if self.search_query else "اضغط على إضافة عميل جديد"
            empty = BoxLayout(orientation="vertical", size_hint_y=None,
                              height=dp(90))
            empty.add_widget(mk_text(msg, dp(16), MUTED, halign="center",
                                     hint_y=0.5))
            empty.add_widget(mk_text(sub, dp(13), MUTED, halign="center",
                                     hint_y=0.5))
            self.clients_layout.add_widget(empty)
            schedule_refresh(0.1)
            return
        for real_idx, client in indexed:
            self.clients_layout.add_widget(make_client_row(
                client,
                on_tap=lambda i=real_idx: self.open_client_screen(i)))
        schedule_refresh(0.1)

    def open_add_client_popup(self, *args):
        content = BoxLayout(orientation="vertical", spacing=dp(6),
                            padding=dp(10))
        content.add_widget(mk_text("اسم العميل", dp(13), MUTED,
                                   height=dp(22)))
        name_input = mk_input(size_hint_y=None, height=dp(48),
                              hint_text="الاسم الكامل")
        content.add_widget(name_input)
        content.add_widget(mk_text("رقم الواتساب", dp(13), MUTED,
                                   height=dp(22)))
        phone_input = mk_input(input_filter="int", size_hint_y=None,
                               height=dp(48), hint_text="0771234567")
        content.add_widget(phone_input)
        content.add_widget(Widget())
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        save_btn = mk_btn("حفظ", background_color=GREEN)
        cancel_btn = mk_btn("إلغاء", background_color=GRAY_BTN)
        btns.add_widget(save_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)
        popup = make_arabic_popup("إضافة عميل جديد", content,
                                  size_hint=(0.92, 0.55))

        def do_save(*a):
            name = name_input.text.strip()
            if not name:
                return
            self.data.setdefault("clients", []).append({
                "id": gen_id(),
                "name": name,
                "phone": phone_input.text.strip(),
                "balance": 0,
                "invoices": [],
                "mod": now_full(),
            })
            self.save()
            self.refresh_clients()
            popup.dismiss()

        save_btn.bind(on_release=do_save)
        cancel_btn.bind(on_release=lambda *a: popup.dismiss())
        popup.open()


# ============================================================
# 25) التشغيل
# ============================================================
if __name__ == "__main__":
    try:
        DebtBookApp().run()
    except Exception:
        _write_crash(traceback.format_exc())   # يُعرض في التشغيل التالي
        raise


# ============================================================
# 26) ملاحظات الإصلاح (تقرير الكراش)
# ============================================================
# أولاً: الأسباب الجذرية المحتملة للكراش (بالترتيب)
#   1) كتابة/اختبار ملفات في /sdcard/ و /storage/emulated/0 وقت الاستيراد
#      (get_font_dir) - ممنوع في أندرويد 11+ (Scoped Storage).
#   2) طلب READ/WRITE_EXTERNAL_STORAGE في build() - بلا أثر/ممنوع في 13+.
#      ملاحظة: لو كانت الصلاحيتان مكتوبتين أيضاً في buildozer.spec فيجب حذفهما
#      من هناك (انظر "ثالثاً").
#   3) مسح /sdcard/ و /sdcard/Download بحثاً عن خطوط (يفشل أو يتعطل).
#   4) فرع أندرويد 9 وأقدم في _publish_media (getExternalStorageDirectory).
#   5) اختبار الخطوط (CoreLabel) على مستوى الملف عند الاستيراد لكل ملف خط
#      ممكن: بطيء وقد يسقط التطبيق قبل ظهور الشاشة. صار يعمل فقط عند غياب
#      font.otf، وداخل try/except.
#   6) محاولة pip install عند الاستيراد على أندرويد (لا pip هناك).
#
# ثانياً: التعديلات
#   - get_font_dir: app_storage_path()/fonts فقط، وعند الفشل APP_DIR.
#   - حذف request_permissions وكل مسارات /sdcard/ من الخطوط.
#   - _publish_media: MediaStore لـ SDK>=29، و getExternalFilesDir(null)
#     لـ SDK<29. لا شيء يحتاج WRITE_EXTERNAL_STORAGE.
#   - LabelBase.register محاط بـ try/except مع log، وتهيئة الخطوط محمية.
#   - لا شبكة ولا مسح مجلدات داخل build(). المزامنة والتحميلات في خيوط.
#   - سجل أعطال: crash.log في مجلد التطبيق، ويظهر في نافذة عند فتح
#     التطبيق مرة أخرى، ليصبح أي كراش متبقٍ قابلاً للتشخيص.
#
# ثالثاً: توصيات إضافية
#   - في buildozer.spec:  android.permissions = INTERNET  (فقط).
#     وتأكد من:  source.include_exts = py,png,jpg,otf,ttf
#     و requirements تحتوي: python3,kivy,pillow,pyjnius,android,openssl
#   - ابنِ بـ android.archs = arm64-v8a و android.api = 33 أو 34.
#   - عند أي كراش شغّل:  adb logcat -s python:V AndroidRuntime:E
#     فالسطر المهم يظهر عادة بعد "Traceback".
#   - إن ظهر الكراش قبل رسم أي شاشة فالسبب غالباً نقص مكتبة في requirements.
