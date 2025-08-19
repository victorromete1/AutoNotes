# xp_learn.py
import time

XP_VALUES = {
    "quiz": 10,
    "note": 5,
    "flashcard": 1,
    "minute": 1,
}

RANKS = [
    ("Beginner", 0, 99),
    ("Learner", 100, 299),
    ("Advanced", 300, 599),
    ("Expert", 600, 999),
    ("Master", 1000, float("inf")),
]

class XPSystem:
    def __init__(self, xp=0):
        self.xp = xp
        self.last_tick = time.time()

    def add(self, action):
        """Add XP based on an action key: quiz, note, flashcard, minute"""
        self.xp += XP_VALUES.get(action, 0)

    def tick_time(self):
        """Grant 1 XP per full minute the app is open"""
        now = time.time()
        elapsed = now - self.last_tick
        if elapsed >= 60:
            minutes = int(elapsed // 60)
            self.xp += minutes * XP_VALUES["minute"]
            self.last_tick = now

    def rank(self):
        for name, low, high in RANKS:
            if low <= self.xp <= high:
                return name, low, high
        return "Beginner", 0, 99

    def progress(self):
        rank, low, high = self.rank()
        current_in_rank = self.xp - low
        needed = high - low if high != float("inf") else 0
        return rank, self.xp, current_in_rank, needed
    def show_xp_bar():
        xp_system = st.session_state.xp_system
        rank, total_xp, current_in_segment, needed = xp_system.progress()
        st.subheader(f"🏅 Rank: {rank}")
        if needed > 0:
            st.progress(current_in_segment / needed)
        st.markdown(f"**{total_xp} XP**")

