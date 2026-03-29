from enum import Enum


class MissionResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"
    UNKNOWN = "unknown"
