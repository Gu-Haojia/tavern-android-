# -*- coding: utf-8 -*-
"""
tavern-android / main.py —— 酒馆版手机端（Kivy）。
聊天 + 互动小说 + 世界书管理 + 设置，全部复用 ai_core 纯内核。
打包：buildozer android debug（见 README + GitHub Actions）。
"""
import os
import threading
import time

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.metrics import dp, sp

import ai_core


# Kivy/SDL2_ttf 不会稳定地从 MuMu 或真机系统字体回退到中文字体。
# 将 SIL OFL 许可的 Noto Sans CJK 简体中文字体随 APK 打包，并设为文本控件的统一字体。
_FONT_NAME = 'NotoSansCJKsc'
_FONT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'assets',
    'NotoSansCJKsc-Regular.otf',
)
if os.path.isfile(_FONT_PATH):
    LabelBase.register(name=_FONT_NAME, fn_regular=_FONT_PATH)
    Builder.load_string("""
<Label>:
    font_name: 'NotoSansCJKsc'
<Button>:
    font_name: 'NotoSansCJKsc'
<TextInput>:
    font_name: 'NotoSansCJKsc'
<Spinner>:
    font_name: 'NotoSansCJKsc'
""")

# 主题色
BLUE = (0.18, 0.43, 1.0, 1.0)
AI_BG = (0.92, 0.93, 0.95, 1.0)
USER_BG = (0.18, 0.43, 1.0, 1.0)
TEXT_DARK = (0.13, 0.15, 0.18, 1.0)
TEXT_WHITE = (1, 1, 1, 1)
BG = (0.96, 0.97, 0.98, 1.0)


class BubbleButton(Button):
    """聊天气泡：长按（≥0.5s）触发菜单。不 disabled（disabled 会吞掉触摸事件）。"""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.long_press_cb = None
        self._press_at = None
        self.background_normal = ''
        self.background_down = ''
        self.background_disabled = ''

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._press_at = time.time()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self._press_at is not None:
            dt = time.time() - self._press_at
            self._press_at = None
            if dt >= 0.5 and self.long_press_cb:
                self.long_press_cb()
                return True
        return super().on_touch_up(touch)


def _bubble(text, is_user):
    """生成一条聊天气泡（BubbleButton 充当圆角气泡，长按弹操作菜单）。"""
    btn = BubbleButton(
        text=text,
        size_hint=(0.78, None),
        # NumericProperty 不接受 None；先给气泡一个最小高度，随后按文本高度调整。
        height=dp(44),
        halign='left' if not is_user else 'right',
        valign='middle',
        text_size=(None, None),
        background_color=USER_BG if is_user else AI_BG,
        color=TEXT_WHITE if is_user else TEXT_DARK,
        padding=(dp(14), dp(10)),
    )
    btn.text_size = (dp(280), None)

    def update_bubble_height(widget, _):
        text_height = widget.texture_size[1] or 0
        widget.height = max(dp(44), text_height + dp(24))

    btn.bind(texture_size=update_bubble_height)
    return btn


class ChatScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.hm = None          # ai_core.HistoryManager
        self.busy = False
        self.cur_bubble = None  # 流式中正在更新的气泡
        self._reasoning_parts = []  # 本回合思维链片段（工作线程收集，主线程展示）
        self.build_ui()

    # ---------- UI ----------
    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        # 顶部栏：标题 + 小说开关 + 新对话
        top = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(10), 0))
        self.title_lbl = Label(text='酒馆', size_hint_x=0.5, halign='left',
                               color=TEXT_DARK, bold=True, font_size=sp(18))
        top.add_widget(self.title_lbl)
        self.tavern_btn = Button(text='小说: 关', size_hint_x=None, width=dp(110),
                                 background_color=(0.75, 0.78, 0.82, 1), color=TEXT_DARK)
        self.tavern_btn.bind(on_release=lambda *_: self.toggle_tavern())
        top.add_widget(self.tavern_btn)
        regen_btn = Button(text='重', size_hint_x=None, width=dp(44),
                           background_color=(0.85, 0.87, 0.9, 1), color=TEXT_DARK)
        regen_btn.bind(on_release=lambda *_: self.regen())
        top.add_widget(regen_btn)
        new_btn = Button(text='新对话', size_hint_x=None, width=dp(80),
                         background_color=(0.85, 0.87, 0.9, 1), color=TEXT_DARK)
        new_btn.bind(on_release=lambda *_: self.new_chat())
        top.add_widget(new_btn)
        root.add_widget(top)

        # 消息滚动区
        self.scroll = ScrollView()
        self.msg_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                 spacing=dp(8), padding=(dp(10), dp(10)))
        self.msg_box.bind(minimum_height=self.msg_box.setter('height'))
        self.scroll.add_widget(self.msg_box)
        root.add_widget(self.scroll)

        # 小说选项区（动态，隐藏）
        self.choices_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                     spacing=dp(6), padding=(dp(10), 0))
        self.choices_box.height = 0
        root.add_widget(self.choices_box)

        # 输入区
        bottom = BoxLayout(size_hint_y=None, height=dp(56), padding=(dp(8), dp(6)), spacing=dp(8))
        self.input = TextInput(hint_text='说点什么…', multiline=False,
                               size_hint_x=0.78, background_color=(1, 1, 1, 1),
                               foreground_color=TEXT_DARK)
        self.input.bind(on_text_validate=lambda *_: self.send())
        bottom.add_widget(self.input)
        send_btn = Button(text='发送', size_hint_x=0.22, background_color=BLUE,
                          color=TEXT_WHITE)
        send_btn.bind(on_release=lambda *_: self.send())
        bottom.add_widget(send_btn)
        root.add_widget(bottom)
        self.add_widget(root)

    # ---------- 启动 ----------
    def on_enter(self):
        if self.hm is None:
            self.hm = ai_core.HistoryManager()
            self.load_history()
            self.refresh_tavern_btn()

    def load_history(self):
        for m in self.hm.current():
            if m.get('role') in ('user', 'assistant'):
                self.add_bubble(m.get('content') or '', m['role'] == 'user')

    # ---------- 气泡 ----------
    def add_bubble(self, text, is_user):
        b = _bubble(text, is_user)
        b.long_press_cb = lambda: self.show_bubble_menu(b, is_user)
        self.msg_box.add_widget(b)
        self.scroll_to_bottom()
        return b

    def rebuild_bubbles(self):
        """清空并重画当前页全部气泡（编辑/删除/重新生成后调用）。"""
        self.msg_box.clear_widgets()
        self.choices_box.clear_widgets()
        self.choices_box.height = 0
        self.load_history()

    def scroll_to_bottom(self):
        Clock.schedule_once(lambda *_: self.scroll.scroll_y if hasattr(self.scroll, 'scroll_y')
                            else None, 0.05)
        # Kivy ScrollView 用 scroll_to
        try:
            self.scroll.scroll_to(self.msg_box.children[-1] if self.msg_box.children else None)
        except Exception:
            pass

    # ---------- 发送 ----------
    def send(self):
        if self.busy or not self.hm:
            return
        text = (self.input.text or '').strip()
        if not text:
            return
        self.input.text = ''
        self.add_bubble(text, True)
        self.busy = True
        self.set_input_enabled(False)
        t = threading.Thread(target=self._run, args=(text,), daemon=True)
        t.start()

    def set_input_enabled(self, enabled):
        self.input.disabled = not enabled
        self.input.opacity = 1.0 if enabled else 0.5

    def _run(self, text, append_user=True):
        try:
            if append_user:
                self.hm.append_user(text)
            if self.hm.cfg.get('tavern_mode'):
                text = '> ' + text
            msgs = self.hm.build_context()
            self.cur_bubble = None
            self._reasoning_parts = []

            def on_token(tok):
                Clock.schedule_once(lambda *_: self.append_stream(tok), 0)

            def on_reasoning(r):
                if r:
                    self._reasoning_parts.append(r)

            ai_text, reasoning, usage = ai_core.run_model_session(
                msgs, self.hm.cfg, on_token=on_token, on_reasoning=on_reasoning)
            if reasoning:
                self._reasoning_parts.append(reasoning)
            # 流式结束后收尾
            Clock.schedule_once(lambda *_: self.on_finished(ai_text, usage), 0)
        except Exception as e:
            err = '出错了: %s' % e
            Clock.schedule_once(lambda *_: self.add_bubble(err, False), 0)
            Clock.schedule_once(lambda *_: self.on_finished('', None), 0)

    def append_stream(self, tok):
        if self.cur_bubble is None:
            self.cur_bubble = self.add_bubble('', False)
        self.cur_bubble.text += tok

    def on_finished(self, ai_text, usage):
        self.busy = False
        self.set_input_enabled(True)
        # 若流式已渲染则回写完整文本（保证与存档一致）
        if self.cur_bubble is not None:
            self.cur_bubble.text = ai_text or self.cur_bubble.text
        else:
            self.add_bubble(ai_text or '(空回复)', False)
        self.cur_bubble = None
        self.hm.append_assistant(ai_text)
        # 思维链简化展示：灰色小字追加在 AI 气泡下方（便于观察 AI 是否入戏）
        self._render_reasoning()
        if usage:
            stats = ai_core.load_token_stats()
            for k in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
                stats[k] = int(stats.get(k, 0)) + int(usage.get(k, 0) or 0)
            stats['turns'] = int(stats.get('turns', 0)) + 1
            ai_core.save_token_stats(stats)
        # 小说模式：解析选项
        if self.hm.cfg.get('tavern_mode'):
            self.render_choices(ai_text)
        # 分页：达到上限自动翻页（后台）
        if len([m for m in self.hm.current() if m.get('role')]) >= ai_core.PAGE_SIZE:
            threading.Thread(target=self._rollover_bg, daemon=True).start()

    def _render_reasoning(self):
        """把本回合思维链渲染成气泡下方的灰色小字（有才显示）。"""
        parts = [p for p in self._reasoning_parts if (p or '').strip()]
        self._reasoning_parts = []
        if not parts:
            return
        rtext = '\n'.join(parts).strip()
        if not rtext:
            return
        tip = Label(text='思考：' + rtext, font_size=sp(11), color=(0.55, 0.57, 0.63, 1),
                    halign='left', valign='top', size_hint=(0.78, None),
                    text_size=(dp(280), None), padding=(dp(16), 0))
        tip.bind(size=lambda w, _: setattr(w, 'height', w.text_size[1] + dp(8)))
        self.msg_box.add_widget(tip)
        self.scroll_to_bottom()

    def _rollover_bg(self):
        try:
            self.hm.rollover()
        except Exception as e:
            print('翻页失败:', e)

    # ---------- 互动小说 ----------
    def toggle_tavern(self):
        if not self.hm:
            return
        self.hm.cfg['tavern_mode'] = not self.hm.cfg.get('tavern_mode', False)
        ai_core.save_config(self.hm.cfg)
        self.refresh_tavern_btn()

    def refresh_tavern_btn(self):
        on = bool(self.hm and self.hm.cfg.get('tavern_mode'))
        self.tavern_btn.text = '小说: 开' if on else '小说: 关'
        self.tavern_btn.background_color = (0.28, 0.55, 1.0, 1) if on else (0.75, 0.78, 0.82, 1)
        self.tavern_btn.color = TEXT_WHITE if on else TEXT_DARK

    def render_choices(self, ai_text):
        self.choices_box.clear_widgets()
        self.choices_box.height = 0
        _, choices = ai_core.parse_choices(ai_text or '')
        if not choices:
            return
        for c in choices:
            b = Button(text=c, size_hint_y=None, height=dp(42),
                       background_color=(0.9, 0.92, 0.95, 1), color=TEXT_DARK,
                       halign='left', padding=(dp(10), 0))
            b.bind(on_release=lambda w, choice=c: self.choose(choice))
            self.choices_box.add_widget(b)
        self.choices_box.height = dp(42) * len(choices) + dp(6) * (len(choices) - 1)

    def choose(self, choice):
        self.choices_box.clear_widgets()
        self.choices_box.height = 0
        self.input.text = choice
        self.send()

    # ---------- 气泡操作（长按菜单 / 重新生成 / 编辑 / 删除） ----------
    def _find_msg_index(self, content, is_user):
        """按内容从后往前定位消息索引（用于编辑/删除）。"""
        role = 'user' if is_user else 'assistant'
        for i in range(len(self.hm.messages) - 1, -1, -1):
            m = self.hm.messages[i]
            if m.get('role') == role and (m.get('content') or '') == content:
                return i
        return None

    def regen(self):
        """重新生成：删掉最后一条 AI 回复，重发最后一条用户消息。"""
        if self.busy or not self.hm:
            return
        text = self.hm.truncate_after_last_user()
        if text is None:
            return
        self.rebuild_bubbles()
        self.busy = True
        self.set_input_enabled(False)
        threading.Thread(target=self._run, args=(text, False), daemon=True).start()

    def show_bubble_menu(self, bubble, is_user):
        if self.busy or not self.hm:
            return
        pop = Popup(title='气泡操作', size_hint=(0.8, None), height=dp(240))
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        if is_user:
            b_edit = Button(text='编辑并重新生成',
                            background_color=(0.9, 0.92, 0.95, 1), color=TEXT_DARK)
            b_edit.bind(on_release=lambda *_: (pop.dismiss(), self.edit_bubble(bubble)))
            box.add_widget(b_edit)
        else:
            b_regen = Button(text='重新生成',
                             background_color=(0.9, 0.92, 0.95, 1), color=TEXT_DARK)
            b_regen.bind(on_release=lambda *_: (pop.dismiss(), self.regen()))
            box.add_widget(b_regen)
        b_del = Button(text='删除', background_color=(0.9, 0.6, 0.6, 1), color=TEXT_WHITE)
        b_del.bind(on_release=lambda *_: (pop.dismiss(), self.delete_bubble(bubble, is_user)))
        box.add_widget(b_del)
        b_cancel = Button(text='取消', background_color=(0.85, 0.87, 0.9, 1), color=TEXT_DARK)
        b_cancel.bind(on_release=lambda *_: pop.dismiss())
        box.add_widget(b_cancel)
        pop.add_widget(box)
        pop.open()

    def edit_bubble(self, bubble):
        """编辑用户消息：改内容 → 其后的对话作废 → 自动重新生成。"""
        idx = self._find_msg_index(bubble.text, True)
        if idx is None:
            return
        pop = Popup(title='编辑消息', size_hint=(0.9, 0.6))
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        t_input = TextInput(text=bubble.text, multiline=True, foreground_color=TEXT_DARK)
        box.add_widget(t_input)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        ok = Button(text='保存并重新生成', background_color=BLUE, color=TEXT_WHITE)
        cancel = Button(text='取消', background_color=(0.85, 0.87, 0.9, 1), color=TEXT_DARK)

        def on_save(_):
            new_text = t_input.text.strip()
            if not new_text:
                return
            self.hm.messages[idx]['content'] = new_text
            del self.hm.messages[idx + 1:]  # 旧内容衍生的后续对话作废
            ai_core.save_page_file(self.hm.max_page, self.hm.messages)
            pop.dismiss()
            self.rebuild_bubbles()
            self.busy = True
            self.set_input_enabled(False)
            threading.Thread(target=self._run, args=(new_text, False), daemon=True).start()

        ok.bind(on_release=on_save)
        cancel.bind(on_release=lambda *_: pop.dismiss())
        btns.add_widget(ok)
        btns.add_widget(cancel)
        box.add_widget(btns)
        pop.add_widget(box)
        pop.open()

    def delete_bubble(self, bubble, is_user):
        idx = self._find_msg_index(bubble.text, is_user)
        if idx is None:
            return
        self.hm.messages.pop(idx)
        ai_core.save_page_file(self.hm.max_page, self.hm.messages)
        self.rebuild_bubbles()

    # ---------- 新对话 ----------
    def new_chat(self):
        if self.busy or not self.hm:
            return
        self.msg_box.clear_widgets()
        self.choices_box.clear_widgets()
        self.choices_box.height = 0
        self.hm.new_chat()


# --------------------------------------------------------------------------- #
# 世界书管理页
# --------------------------------------------------------------------------- #
class WorldbookScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        top = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(10), 0))
        top.add_widget(Label(text='世界书', bold=True, color=TEXT_DARK, font_size=sp(18)))
        root.add_widget(top)

        self.list_scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6),
                                  padding=(dp(10), dp(10)))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.list_scroll.add_widget(self.list_box)
        root.add_widget(self.list_scroll)

        add_btn = Button(text='＋ 新增条目', size_hint_y=None, height=dp(48),
                         background_color=BLUE, color=TEXT_WHITE)
        add_btn.bind(on_release=lambda *_: self.edit_entry(None))
        root.add_widget(add_btn)
        self.add_widget(root)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        for wb in ai_core.load_worldbooks():
            for i, e in enumerate(wb.get('entries', [])):
                title = e.get('title') or '未命名'
                kw = '，'.join(e.get('primary_keywords') or []) or '（无关键词·常驻）'
                row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(6))
                info = Label(text='[b]%s[/b]\n%s' % (title, kw),
                             markup=True, halign='left', color=TEXT_DARK, size_hint_x=0.6)
                row.add_widget(info)
                ebtn = Button(text='编辑', size_hint_x=0.2, background_color=(0.85, 0.87, 0.9, 1),
                              color=TEXT_DARK)
                ebtn.bind(on_release=lambda w, bk=wb, en=e: self.edit_entry(en, bk))
                row.add_widget(ebtn)
                dbtn = Button(text='删', size_hint_x=0.2, background_color=(0.9, 0.6, 0.6, 1),
                              color=TEXT_WHITE)
                dbtn.bind(on_release=lambda w, bk=wb, en=e: self.delete_entry(bk, en))
                row.add_widget(dbtn)
                self.list_box.add_widget(row)

    def edit_entry(self, entry, wb=None):
        """新增或编辑条目（Popup 表单）。"""
        if wb is None:
            books = ai_core.load_worldbooks()
            if not books:
                wb = ai_core.save_worldbook(ai_core.default_worldbook())
            else:
                wb = books[0]
        e = dict(entry or ai_core.default_entry())

        content = Popup(title='世界书条目', size_hint=(0.92, 0.9))
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        t_title = TextInput(text=e.get('title') or '', hint_text='标题', multiline=False)
        t_content = TextInput(text=e.get('content') or '', hint_text='内容（触发后注入的设定）',
                              multiline=True)
        t_kw = TextInput(text='，'.join(e.get('primary_keywords') or []),
                         hint_text='关键词（逗号分隔，聊到才触发）', multiline=False)
        t_order = TextInput(text=str(e.get('order', 100)), hint_text='顺序值（越大越靠下越强）',
                            multiline=False)
        st_spin = Spinner(text=e.get('status', 'green'), values=('blue', 'green', 'red'))
        pos_spin = Spinner(text=e.get('position', 'before_char'),
                           values=('before_char', 'after_char', 'after_an', 'depth'))
        box.add_widget(Label(text='标题', color=TEXT_DARK, size_hint_y=None, height=dp(22)))
        box.add_widget(t_title)
        box.add_widget(Label(text='内容', color=TEXT_DARK, size_hint_y=None, height=dp(22)))
        box.add_widget(t_content)
        box.add_widget(Label(text='关键词', color=TEXT_DARK, size_hint_y=None, height=dp(22)))
        box.add_widget(t_kw)
        box.add_widget(Label(text='状态(蓝=常驻 绿=关键词 红=禁用) / 位置', color=TEXT_DARK,
                             size_hint_y=None, height=dp(22)))
        box.add_widget(BoxLayout(size_hint_y=None, height=dp(40),
                                 children=[st_spin, pos_spin]))
        box.add_widget(Label(text='顺序值', color=TEXT_DARK, size_hint_y=None, height=dp(22)))
        box.add_widget(t_order)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        ok = Button(text='保存', background_color=BLUE, color=TEXT_WHITE)
        cancel = Button(text='取消', background_color=(0.85, 0.87, 0.9, 1), color=TEXT_DARK)

        def on_save(_):
            e['title'] = t_title.text.strip() or '未命名条目'
            e['content'] = t_content.text
            e['primary_keywords'] = [k.strip() for k in t_kw.text.split('，') if k.strip()] \
                if t_kw.text.strip() else []
            e['status'] = st_spin.text
            e['position'] = pos_spin.text
            try:
                e['order'] = int(t_order.text.strip())
            except Exception:
                e['order'] = 100
            wb['entries'] = [x for x in wb.get('entries', []) if x is not entry]
            wb['entries'].append(e)
            ai_core.save_worldbook(wb)
            content.dismiss()
            self.refresh()

        ok.bind(on_release=on_save)
        cancel.bind(on_release=lambda *_: content.dismiss())
        btns.add_widget(ok)
        btns.add_widget(cancel)
        box.add_widget(btns)
        content.add_widget(box)
        content.open()

    def delete_entry(self, wb, entry):
        wb['entries'] = [x for x in wb.get('entries', []) if x is not entry]
        ai_core.save_worldbook(wb)
        self.refresh()


# --------------------------------------------------------------------------- #
# 设置页
# --------------------------------------------------------------------------- #
class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.fields = {}
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        top = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(10), 0))
        top.add_widget(Label(text='设置', bold=True, color=TEXT_DARK, font_size=sp(18)))
        root.add_widget(top)

        scroll = ScrollView()
        form = BoxLayout(orientation='vertical', spacing=dp(10), padding=(dp(14), dp(12)),
                         size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        def field(label, key, hint='', multiline=False):
            form.add_widget(Label(text=label, color=TEXT_DARK, size_hint_y=None, height=dp(22),
                                  halign='left'))
            if multiline:
                ti = TextInput(hint_text=hint, multiline=True, height=dp(90),
                               size_hint_y=None, background_color=(1, 1, 1, 1),
                               foreground_color=TEXT_DARK)
            else:
                ti = TextInput(hint_text=hint, multiline=False, height=dp(44),
                               size_hint_y=None, background_color=(1, 1, 1, 1),
                               foreground_color=TEXT_DARK)
            form.add_widget(ti)
            self.fields[key] = ti

        field('API 地址', 'base_url')
        field('API Key', 'api_key', 'sk-...')
        field('模型名', 'model')
        field('人设提示词', 'persona_prompt', multiline=True)
        field('世界观（会迁入世界书蓝灯条目）', 'worldview_prompt', multiline=True)
        field('玩家身份', 'player_identity', multiline=True)
        field('示例对话（few-shot 声线示范）', 'dialogue_examples', multiline=True)
        field('开场白（首条 AI 消息）', 'opening_message', multiline=True)
        field('前置提示词 raw_prefix', 'raw_prefix', multiline=True)
        field('温度（0~2）', 'temperature', '0.8')

        form.add_widget(Label(text='采样/功能开关', color=TEXT_DARK, size_hint_y=None,
                              height=dp(22), bold=True))
        self.ck_thinking = CheckBox(active=False)
        self.ck_bm25 = CheckBox(active=True)
        self.ck_search = CheckBox(active=True)
        self.ck_delai = CheckBox(active=False)
        row = BoxLayout(size_hint_y=None, height=dp(40))
        row.add_widget(Label(text='先想再答', color=TEXT_DARK))
        row.add_widget(self.ck_thinking)
        row.add_widget(Label(text='BM25记忆', color=TEXT_DARK))
        row.add_widget(self.ck_bm25)
        row.add_widget(Label(text='翻旧账工具', color=TEXT_DARK))
        row.add_widget(self.ck_search)
        form.add_widget(row)
        row2 = BoxLayout(size_hint_y=None, height=dp(40))
        row2.add_widget(Label(text='去AI味', color=TEXT_DARK))
        row2.add_widget(self.ck_delai)
        form.add_widget(row2)

        save_btn = Button(text='保存设置', size_hint_y=None, height=dp(50),
                          background_color=BLUE, color=TEXT_WHITE)
        save_btn.bind(on_release=lambda *_: self.save_cfg())
        form.add_widget(save_btn)
        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        cfg = ai_core.load_config()
        for k, ti in self.fields.items():
            v = cfg.get(k)
            if isinstance(v, (int, float)):
                ti.text = str(v)
            else:
                ti.text = str(v or '')
        self.ck_thinking.active = bool(cfg.get('enable_thinking'))
        self.ck_bm25.active = bool(cfg.get('enable_bm25', True))
        self.ck_search.active = bool(cfg.get('enable_search_tool', True))
        self.ck_delai.active = bool(cfg.get('enable_delai'))

    def save_cfg(self):
        cfg = ai_core.load_config()
        for k, ti in self.fields.items():
            if k == 'temperature':
                try:
                    cfg[k] = float(ti.text.strip())
                except Exception:
                    pass
            else:
                cfg[k] = ti.text.strip() if k != 'api_key' else ti.text.strip()
        cfg['enable_thinking'] = self.ck_thinking.active
        cfg['enable_bm25'] = self.ck_bm25.active
        cfg['enable_search_tool'] = self.ck_search.active
        cfg['enable_delai'] = self.ck_delai.active
        ai_core.save_config(cfg)
        if App.get_running_app() and hasattr(App.get_running_app(), 'chat'):
            App.get_running_app().chat.hm.cfg = cfg
        popup = Popup(title='已保存', content=Label(text='设置已保存，重启生效。',
                                                    color=TEXT_DARK),
                      size_hint=(0.6, 0.35))
        Clock.schedule_once(lambda *_: popup.dismiss(), 1.2)
        popup.open()


# --------------------------------------------------------------------------- #
# 底部导航 + App
# --------------------------------------------------------------------------- #
class NavBar(BoxLayout):
    pass


class PetApp(App):
    def build(self):
        self.title = '酒馆'
        sm = ScreenManager()
        self.chat = ChatScreen(name='chat')
        self.world = WorldbookScreen(name='world')
        self.settings = SettingsScreen(name='settings')
        sm.add_widget(self.chat)
        sm.add_widget(self.world)
        sm.add_widget(self.settings)

        root = BoxLayout(orientation='vertical')
        root.add_widget(sm)
        nav = BoxLayout(size_hint_y=None, height=dp(56))

        def go(name):
            sm.current = name

        for text, name in (('聊天', 'chat'), ('世界书', 'world'), ('设置', 'settings')):
            b = Button(text=text, background_color=(0.9, 0.92, 0.95, 1), color=TEXT_DARK)
            b.bind(on_release=lambda w, n=name: go(n))
            nav.add_widget(b)
        root.add_widget(nav)
        return root


if __name__ == '__main__':
    PetApp().run()
