"""Streak-based achievement badges."""

from dataclasses import dataclass

ACHIEVEMENT_MILESTONES = frozenset({3, 7, 14, 30})


@dataclass(frozen=True, slots=True)
class Achievement:
    emoji: str
    title: str

    def label(self) -> str:
        return f"{self.emoji} {self.title}"


def get_achievement(streak_count: int) -> Achievement:
    if streak_count <= 2:
        return Achievement("🌱", "Новичок")
    if streak_count <= 6:
        return Achievement("⚡️", "На опыте")
    if streak_count <= 13:
        return Achievement("🔥", "Мастер дисциплины")
    if streak_count <= 29:
        return Achievement("🛡", "Легенда")
    return Achievement("👑", "Повелитель привычек")


def is_achievement_milestone(streak_count: int) -> bool:
    """True when the user has just reached a new achievement tier boundary."""
    return streak_count in ACHIEVEMENT_MILESTONES


def milestone_congrats_message(streak_count: int) -> str:
    achievement = get_achievement(streak_count)
    return (
        f"🎉 Поздравляем! Ты получил новую ачивку: {achievement.label()}!"
    )
