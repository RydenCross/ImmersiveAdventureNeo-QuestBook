from enum import StrEnum
class TaskType(StrEnum):
    ITEM="item"; CHECKMARK="checkmark"; ADVANCEMENT="advancement"; KILL="kill"; LOCATION="location"; STATISTIC="statistic"; XP="xp"; DIMENSION="dimension"; CUSTOM="custom"
class RewardType(StrEnum):
    ITEM="item"; XP="xp"; COMMAND="command"; LOOT_CRATE="loot_crate"; CHOICE="choice"; CUSTOM="custom"
class Difficulty(StrEnum):
    TRIVIAL="trivial"; EASY="easy"; NORMAL="normal"; HARD="hard"; EXPERT="expert"; ENDGAME="endgame"
