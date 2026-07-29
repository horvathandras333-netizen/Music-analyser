from typing import Literal

PING_PONG_ADVISORY = (
    "Ping-pong playback reverses motion. Safe for sways, turns, and breathing. "
    "Not safe for hair fall, smoke, or particles - switch to true-cycle."
)

TRUE_CYCLE_ADVISORY = (
    "True-cycle playback requires identical start and end poses. "
    "Ensure final frame matches initial pose seamlessly."
)


def get_loop_mode_advisory(loop_mode: Literal["ping_pong", "true_cycle"]) -> str:
    """Return human-readable advisory warning text for selected loop mode."""
    if loop_mode == "ping_pong":
        return PING_PONG_ADVISORY
    return TRUE_CYCLE_ADVISORY
