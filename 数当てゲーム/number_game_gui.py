import random
import threading
import tkinter as tk
from tkinter import font


PAGE_BG = "#eef1f5"
CHAT_BG = "#ffffff"
HEADER_BG = "#3f6ef0"
HEADER_SUBTITLE = "#dbe4ff"
FOOTER_BG = "#f7f8fa"
INPUT_BG = "#f1f3f6"

COMPUTER_BUBBLE = "#eef1f5"
COMPUTER_BORDER = "#d5dbe3"
USER_BUBBLE = "#3f6ef0"
TEXT_COLOR = "#2b2b2b"

BUTTON_ACTIVE_BG = "#3f6ef0"
BUTTON_INACTIVE_BG = "#c9d3e0"

MIN_NUM = 1
MAX_NUM = 100

# (フレーズ, リアクション絵文字) の組み合わせ。近さによって熱量が変わる
BIGGER_REACTIONS = {
    "hot": [("🔥 熱い！もう少し上だよ！", "🔥"), ("🔥 かなり近い、上を狙って！", "🔥")],
    "warm": [("😳 惜しい、上だね！", "😳"), ("👀 上の方だよ、近づいてる！", "👀")],
    "cold": [("🙌 まだまだ上だよ！", "🙌"), ("🚀 もっと上を狙ってみて！", "🚀")],
}
SMALLER_REACTIONS = {
    "hot": [("🔥 熱い！もう少し下だよ！", "🔥"), ("🔥 かなり近い、下を狙って！", "🔥")],
    "warm": [("😳 惜しい、下だね！", "😳"), ("👀 下の方だよ、近づいてる！", "👀")],
    "cold": [("🙌 まだまだ下だよ！", "🙌"), ("🚀 もっと下を狙ってみて！", "🚀")],
}

CORRECT_MESSAGES = [
    "正解です！🎉",
    "やった、大正解！🎊",
    "ピンポン！当たりです！✨",
]


def round_rectangle(canvas, x1, y1, x2, y2, radius=14, **kwargs):
    """角丸の四角形をcanvasに描画するヘルパー"""
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class ChatBubble(tk.Frame):
    """吹き出し風（角丸＋しっぽ付き）のチャットメッセージ部品。
    コンピューターのメッセージには、右下に絵文字の「リアクション」を付けられる。"""

    PAD_X = 12
    PAD_Y = 9
    TAIL_W = 9
    TAIL_H = 12
    MAX_TEXT_WIDTH = 210
    REACTION_R = 13

    def __init__(self, parent, text, sender, msg_font, reaction=None):
        super().__init__(parent, bg=CHAT_BG)

        is_user = sender == "user"
        anchor_side = "e" if is_user else "w"
        bubble_fill = USER_BUBBLE if is_user else COMPUTER_BUBBLE
        text_fill = "white" if is_user else TEXT_COLOR
        border = None if is_user else COMPUTER_BORDER

        canvas = tk.Canvas(self, bg=CHAT_BG, highlightthickness=0)
        canvas.pack(anchor=anchor_side, padx=10, pady=(4, 12 if reaction else 4))

        pad_x, pad_y = self.PAD_X, self.PAD_Y
        tail_w = self.TAIL_W

        text_origin_x = pad_x if is_user else pad_x + tail_w
        text_id = canvas.create_text(
            text_origin_x, pad_y, anchor="nw", text=text,
            font=(msg_font, 11), fill=text_fill, width=self.MAX_TEXT_WIDTH,
            justify="left",
        )
        canvas.update_idletasks()
        _, _, text_right, text_bottom = canvas.bbox(text_id)

        if is_user:
            rect_x1, rect_y1 = 0, 0
            rect_x2, rect_y2 = text_right + pad_x, text_bottom + pad_y
            canvas_w = rect_x2 + tail_w
        else:
            rect_x1, rect_y1 = tail_w, 0
            rect_x2, rect_y2 = text_right + pad_x, text_bottom + pad_y
            canvas_w = rect_x2

        if reaction:
            # リアクションの丸バッジが bubble の右下からはみ出す分の余白を確保する
            canvas_w += self.REACTION_R + 6
            canvas_h = rect_y2 + self.REACTION_R + 4
        else:
            canvas_h = rect_y2

        canvas.configure(width=canvas_w, height=canvas_h)

        rect_id = round_rectangle(
            canvas, rect_x1, rect_y1, rect_x2, rect_y2, radius=14,
            fill=bubble_fill, outline=border or bubble_fill,
        )
        canvas.tag_lower(rect_id, text_id)

        if is_user:
            tail_points = [
                rect_x2, rect_y2 - self.TAIL_H - 4,
                rect_x2, rect_y2 - 4,
                rect_x2 + tail_w, rect_y2 - 2,
            ]
        else:
            tail_points = [
                rect_x1, rect_y2 - self.TAIL_H - 4,
                rect_x1, rect_y2 - 4,
                0, rect_y2 - 2,
            ]
        tail_id = canvas.create_polygon(tail_points, fill=bubble_fill, outline=bubble_fill)
        canvas.tag_lower(tail_id, text_id)

        if reaction:
            r = self.REACTION_R
            cx, cy = rect_x2 - 6, rect_y2
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="white", outline="#dddddd", width=1,
            )
            canvas.create_text(cx, cy, text=reaction, font=(msg_font, 13))


class TitleScreen(tk.Frame):
    """タイトル画面：「数当てゲームで遊ぶ」＋「ゲームスタート」ボタン"""

    def __init__(self, parent, msg_font, on_start):
        super().__init__(parent, bg=PAGE_BG)

        tk.Label(self, text="🎯", font=(msg_font, 64), bg=PAGE_BG).pack(pady=(100, 10))
        tk.Label(
            self, text="数当てゲームで遊ぶ",
            font=(msg_font, 20, "bold"), fg="#2b2b2b", bg=PAGE_BG,
        ).pack(pady=(0, 8))
        tk.Label(
            self, text=f"{MIN_NUM}〜{MAX_NUM}の数字を当ててね",
            font=(msg_font, 11), fg="#666666", bg=PAGE_BG,
        ).pack(pady=(0, 50))

        tk.Button(
            self, text="ゲームスタート",
            font=(msg_font, 14, "bold"), fg="white", bg=HEADER_BG,
            activebackground="#3560d8", activeforeground="white",
            relief="flat", padx=24, pady=12, command=on_start,
        ).pack()


class GameScreen(tk.Frame):
    """チャット形式の数当てゲーム画面"""

    def __init__(self, parent, root, msg_font, on_quit_to_title):
        super().__init__(parent, bg=CHAT_BG)
        self.root = root
        self.msg_font = msg_font
        self.on_quit_to_title = on_quit_to_title

        self.answer = None
        self.tries = 0
        self.game_over = False

        self._build_widgets()

    def _build_widgets(self):
        # ヘッダー（青、アイコン＋タイトル＋サブタイトル＋リセットボタン）
        self.header = tk.Frame(self, bg=HEADER_BG, height=64)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        title_box = tk.Frame(self.header, bg=HEADER_BG)
        title_box.pack(side="left", padx=14, pady=8)
        tk.Label(
            title_box, text="🎯 数当てゲーム", font=(self.msg_font, 13, "bold"),
            fg="white", bg=HEADER_BG, anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_box, text=f"{MIN_NUM}〜{MAX_NUM}の数字を当ててね",
            font=(self.msg_font, 9), fg=HEADER_SUBTITLE, bg=HEADER_BG, anchor="w",
        ).pack(anchor="w")

        self.reset_btn = tk.Button(
            self.header, text="リセット", font=(self.msg_font, 9, "bold"),
            fg="white", bg="#5c85f2", activebackground="#5c85f2",
            activeforeground="white", relief="flat", padx=10,
            command=self.start_new_game,
        )
        self.reset_btn.pack(side="right", padx=14)

        # チャット表示エリア（スクロール可能・白背景）
        self.chat_container = tk.Frame(self, bg=CHAT_BG)
        self.chat_container.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(self.chat_container, bg=CHAT_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.chat_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.messages_frame = tk.Frame(self.canvas, bg=CHAT_BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.messages_frame, anchor="nw"
        )

        self.messages_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # 試行回数バー
        self.footer = tk.Frame(self, bg=FOOTER_BG, height=28)
        self.footer.pack(side="bottom", fill="x")
        self.footer.pack_propagate(False)
        self.tries_label = tk.Label(
            self.footer, text="試行回数: 0回", font=(self.msg_font, 9),
            fg="#888888", bg=FOOTER_BG,
        )
        self.tries_label.pack(pady=4)

        # 入力エリア
        input_area = tk.Frame(self, bg=CHAT_BG, height=60)
        input_area.pack(side="bottom", fill="x")
        input_area.pack_propagate(False)

        self.entry = tk.Entry(
            input_area, font=(self.msg_font, 11), bg=INPUT_BG, fg=TEXT_COLOR,
            relief="flat", highlightthickness=1, highlightbackground="#dde3ea",
            highlightcolor="#9db4f0",
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(14, 6), pady=13, ipady=4)
        self._set_placeholder()
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self.entry.bind("<Key>", self._on_key_press)
        self.entry.bind("<KeyRelease>", lambda e: self._update_send_button())
        self.entry.bind("<Return>", lambda e: self._on_send())

        self.send_btn = tk.Button(
            input_area, text="送信", font=(self.msg_font, 10, "bold"),
            fg="white", bg=BUTTON_INACTIVE_BG, activeforeground="white",
            activebackground=BUTTON_ACTIVE_BG, relief="flat", padx=16,
            command=self._on_send,
        )
        self.send_btn.pack(side="right", padx=(0, 14), pady=13)

    # ---- プレースホルダー付き入力欄 ----

    PLACEHOLDER = f"数字を入力 ({MIN_NUM}〜{MAX_NUM})"

    def _set_placeholder(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.PLACEHOLDER)
        self.entry.configure(fg="#9aa4b2")
        self._showing_placeholder = True

    def _clear_placeholder(self, event=None):
        if getattr(self, "_showing_placeholder", False):
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=TEXT_COLOR)
            self._showing_placeholder = False

    def _restore_placeholder(self, event=None):
        if not self.entry.get().strip():
            self._set_placeholder()
        self._update_send_button()

    _IGNORED_KEYSYMS = {
        "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R",
        "Alt_L", "Alt_R", "Return", "Escape", "Up", "Down", "Left", "Right",
    }

    def _on_key_press(self, event):
        # フォーカスが既に入力欄にある状態でリセットされた場合など、
        # <FocusIn> が発生しないまま入力され、プレースホルダーが残るのを防ぐ
        if event.keysym in self._IGNORED_KEYSYMS:
            return
        self._clear_placeholder()

    def _update_send_button(self):
        has_text = bool(self.entry.get().strip()) and not getattr(self, "_showing_placeholder", False)
        if has_text and not self.game_over:
            self.send_btn.configure(bg=BUTTON_ACTIVE_BG)
        else:
            self.send_btn.configure(bg=BUTTON_INACTIVE_BG)

    def start_new_game(self):
        """新しいゲームを開始する（初回表示時／リセット／もう一度遊ぶ時に呼ぶ）"""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

        # 古いスクロール位置・スクロール範囲が残らないようにリセットする
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0.0)

        self.answer = random.randint(MIN_NUM, MAX_NUM)
        self.tries = 0
        self.game_over = False
        self.tries_label.configure(text="試行回数: 0回")

        self.entry.configure(state="normal")
        self._set_placeholder()
        self._update_send_button()

        self._add_computer_message(
            f"こんにちは！{MIN_NUM}〜{MAX_NUM} の間で数字を1つ決めました。当ててみてください！"
        )

    def _add_bubble(self, text, sender, reaction=None):
        bubble = ChatBubble(self.messages_frame, text, sender, self.msg_font, reaction=reaction)
        bubble.pack(fill="x", pady=2)
        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)

    def _add_user_message(self, text):
        self._add_bubble(text, "user")

    def _add_computer_message(self, text, reaction=None):
        self._add_bubble(text, "computer", reaction=reaction)

    def _hint_for(self, guess):
        diff = abs(guess - self.answer)
        table = BIGGER_REACTIONS if guess < self.answer else SMALLER_REACTIONS

        if diff <= 3:
            tier = "hot"
        elif diff <= 12:
            tier = "warm"
        else:
            tier = "cold"

        return random.choice(table[tier])

    def _on_send(self):
        if getattr(self, "_showing_placeholder", False):
            return
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._update_send_button()

        self._add_user_message(text)

        if self.game_over:
            return

        if not text.isdigit():
            self._add_computer_message("数字を入力してください。")
            return

        guess = int(text)
        if guess < MIN_NUM or guess > MAX_NUM:
            self._add_computer_message(f"{MIN_NUM}〜{MAX_NUM}の範囲で入力してください。")
            return

        self.tries += 1
        self.tries_label.configure(text=f"試行回数: {self.tries}回")

        if guess == self.answer:
            self._add_computer_message(
                f"{random.choice(CORRECT_MESSAGES)}\n{self.tries}回目で当たりました。",
                reaction="🎉",
            )
            self.game_over = True
            self._update_send_button()
            self._celebrate()
        else:
            phrase, reaction = self._hint_for(guess)
            self._add_computer_message(phrase, reaction=reaction)

    # ---- 正解時のエフェクト ----

    def _celebrate(self):
        self._flash_header()
        self._play_sound()
        self._add_celebration_card()
        self._add_replay_prompt()

    def _add_replay_prompt(self):
        self._add_computer_message("もう一度遊びますか？それともゲームを終了しますか？")

        outer = tk.Frame(self.messages_frame, bg=CHAT_BG)
        outer.pack(anchor="w", padx=16, pady=(0, 8))

        replay_btn = tk.Button(
            outer, text="🔁 もう一度遊ぶ", font=(self.msg_font, 10, "bold"),
            bg=HEADER_BG, fg="white", relief="flat", command=self.start_new_game,
        )
        replay_btn.pack(side="left", padx=(0, 6))

        quit_btn = tk.Button(
            outer, text="❌ ゲームを終了する", font=(self.msg_font, 10, "bold"),
            bg="#e57373", fg="white", relief="flat", command=self.on_quit_to_title,
        )
        quit_btn.pack(side="left")

        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)

    def _flash_header(self, count=0):
        colors = ["#ffd700", HEADER_BG]
        if count >= 6:
            self.header.configure(bg=HEADER_BG)
            return
        self.header.configure(bg=colors[count % 2])
        self.root.after(120, self._flash_header, count + 1)

    def _play_sound(self):
        def beep():
            try:
                import winsound
                for freq in (784, 988, 1175, 1568):
                    winsound.Beep(freq, 90)
            except Exception:
                pass

        threading.Thread(target=beep, daemon=True).start()

    def _add_celebration_card(self):
        """チャットの流れの中に、その場に残る「祝福カード」を追加する（画面は消さない）"""
        self.root.update_idletasks()
        width = max(self.canvas.winfo_width() - 60, 200)
        height = 130

        outer = tk.Frame(self.messages_frame, bg=CHAT_BG)
        outer.pack(fill="x", pady=6)

        card = tk.Canvas(
            outer, bg="#fff8e1", highlightthickness=2,
            highlightbackground="#ffd54f", width=width, height=height,
        )
        card.pack(padx=20)

        colors = ["#ff6b6b", "#feca57", "#1dd1a1", "#54a0ff", "#ff9ff3", "#f368e0", "#ff9f43"]
        pieces = []
        for _ in range(30):
            x = random.randint(0, width)
            y = random.randint(-height, 0)
            size = random.randint(6, 12)
            color = random.choice(colors)
            if random.random() < 0.5:
                item = card.create_oval(x, y, x + size, y + size, fill=color, outline="")
            else:
                item = card.create_rectangle(x, y, x + size, y + size, fill=color, outline="")
            pieces.append([item, random.uniform(3, 6), random.uniform(-1, 1), size])

        title_id = card.create_text(
            width / 2, height / 2 - 12, text="🎉 GAME CLEAR 🎉",
            font=(self.msg_font, 16, "bold"), fill="#ff5252",
        )
        card.create_text(
            width / 2, height / 2 + 16, text=f"{self.tries}回目で正解！おめでとうございます！",
            font=(self.msg_font, 10), fill="#555555",
        )

        def animate(frame=0):
            still_falling = False
            for piece in pieces:
                item, speed, drift, size = piece
                y_bottom = card.coords(item)[3]
                if y_bottom < height:
                    card.move(item, drift, speed)
                    still_falling = True
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.yview_moveto(1.0)
            if frame == 10:
                card.itemconfig(title_id, fill=HEADER_BG)
            if still_falling and frame < 45:
                self.root.after(40, animate, frame + 1)

        animate()
        self.canvas.yview_moveto(1.0)


class App:
    """タイトル画面とゲーム画面を切り替えるコントローラー"""

    def __init__(self, root):
        self.root = root
        self.root.title("数当てゲーム")
        self.root.geometry("420x640")
        self.root.configure(bg=PAGE_BG)
        self.msg_font = font.nametofont("TkDefaultFont").actual("family")

        self.title_screen = TitleScreen(self.root, self.msg_font, self.show_game)
        self.game_screen = GameScreen(self.root, self.root, self.msg_font, self.show_title)

        self.show_title()

    def show_title(self):
        self.game_screen.pack_forget()
        self.title_screen.pack(fill="both", expand=True)

    def show_game(self):
        self.title_screen.pack_forget()
        self.game_screen.pack(fill="both", expand=True)
        self.game_screen.start_new_game()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
