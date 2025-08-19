# xp_learn.py
import time
from dataclasses import dataclass

@dataclass
class RankInfo:
    name: str
    low: int
    high: float

# XP values
XP_PER_ACTION = {
    "quiz": 10,
    "note": 5,
    "flashcard": 1,
    "minute": 1
}

# Rank thresholds
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
        self._last_active_ts = time.time()
        self._carry_seconds = 0

    # ---------- Add XP ----------
    def add(self, action_or_amount):
        if isinstance(action_or_amount, int):
            self.xp += action_or_amount
        else:
            self.xp += XP_PER_ACTION.get(action_or_amount, 0)

    # ---------- Time-based XP ----------
    def tick_time(self):
        now = time.time()
        elapsed = now - self._last_active_ts
        total = elapsed + self._carry_seconds
        minutes = int(total // 60)
        self._carry_seconds = total - (minutes * 60)
        self._last_active_ts = now
        if minutes > 0:
            self.add("minute")

    # ---------- Rank & Progress ----------
    def get_rank(self):
        for name, low, high in RANKS:
            if low <= self.xp <= high:
                return RankInfo(name, low, high)
        return RankInfo("Beginner", 0, 99)

    def progress(self):
        r = self.get_rank()
        current_in_segment = self.xp - r.low
        segment_size = r.high - r.low if r.high != float("inf") else 1
        return r.name, self.xp, current_in_segment, segment_size
