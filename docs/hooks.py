"""Convert semantic traceability markers into site-relative Markdown links."""

import re

from mkdocs.plugins import event_priority


_TRACE_TARGETS = {
    "ARCH:UC-05": (
        "UC-05（シミュレーションする）",
        "../architecture_design/#uc-05",
    ),
    "CODE:simulation.SimulationController.start": (
        "SimulationController.start",
        "../api/#simulation.SimulationController.start",
    ),
    "CODE:simulation.SimulationView.start_animation": (
        "SimulationView.start_animation",
        "../api/#simulation.SimulationView.start_animation",
    ),
    "CODE:simulation.SimulationView._update_playback_button": (
        "SimulationView._update_playback_button",
        "../api/#simulation.SimulationView._update_playback_button",
    ),
    "TEST:TEST-UNIT-126": (
        "TEST-UNIT-126",
        "../test_specification/#test-unit-126",
    ),
    "UCTEST:UC-05": (
        "UC-05のユースケーステスト",
        "../test_specification/#test-uc-05",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_start_sets_playing_state_at_first_point": (
        "test_start_sets_playing_state_at_first_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_start_sets_playing_state_at_first_point",
    ),
}

_MARKER = re.compile(r"\[\[(" + "|".join(map(re.escape, _TRACE_TARGETS)) + r")\]\]")


@event_priority(100)
def on_page_markdown(markdown, page, config, files):
    """Replace semantic trace markers while MkDocs builds each page."""
    del page, config, files

    def replace(match):
        label, target = _TRACE_TARGETS[match.group(1)]
        return f"[{label}]({target})"

    return _MARKER.sub(replace, markdown)
