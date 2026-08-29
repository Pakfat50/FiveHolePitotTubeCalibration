"""Convert semantic traceability markers into site-relative Markdown links."""

import re

from mkdocs.plugins import event_priority


_TRACE_TARGETS = {
    "ARCH:UC-01": ("UC-01（較正条件を入力・更新する）", "../architecture_design/#uc-01"),
    "ARCH:UC-02": ("UC-02（初期化Gコードを読み込む）", "../architecture_design/#uc-02"),
    "ARCH:UC-03": ("UC-03（設定を保存する）", "../architecture_design/#uc-03"),
    "ARCH:UC-04": ("UC-04（設定を読み込む）", "../architecture_design/#uc-04"),
    "ARCH:UC-05": (
        "UC-05（シミュレーションする）",
        "../architecture_design/#uc-05",
    ),
    "ARCH:UC-06": (\n        "UC-06（Gコードを生成する）",\n        "../architecture_design/#uc-06",\n    ),\n    "CODE:simulation.SimulationController.start": (
        "SimulationController.start",
        "../api/#simulation.SimulationController.start",
    ),
    "CODE:simulation.SimulationView.start_animation": (
        "SimulationView.start_animation",
        "../api/#simulation.SimulationView.start_animation",
    ),
    "CODE:simulation.SimulationView.set_playback_state": (
        "SimulationView.set_playback_state",
        "../api/#simulation.SimulationView.set_playback_state",
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
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_start_frame_is_first_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_start_frame_is_first_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_end_frame_is_last_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_end_frame_is_last_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_middle_progress_maps_to_scan_order": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_middle_progress_maps_to_scan_order",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_playback_duration_is_independent_of_hold_time": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_playback_duration_is_independent_of_hold_time",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_side_view_is_initialized": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_side_view_is_initialized",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_front_view_is_initialized": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_front_view_is_initialized",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_render_frame_updates_required_information": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_render_frame_updates_required_information",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_calibration_map_displays_all_points_without_legend": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_calibration_map_displays_all_points_without_legend",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_current_calibration_point_color_tracks_rendered_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_current_calibration_point_color_tracks_rendered_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_start_sets_playing_state_at_first_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_start_sets_playing_state_at_first_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_playback_button_label_follows_state": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_playback_button_label_follows_state",
    ),
    "TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_progress_text_uses_point_count_not_time": (
        "テストコード",
        "../test-api/#tests.test_simulation.TestSimulation.test_progress_text_uses_point_count_not_time",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_start_frame_is_first_point": (
        "test_start_frame_is_first_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_start_frame_is_first_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_end_frame_is_last_point": (
        "test_end_frame_is_last_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_end_frame_is_last_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_middle_progress_maps_to_scan_order": (
        "test_middle_progress_maps_to_scan_order",
        "../test-api/#tests.test_simulation.TestSimulation.test_middle_progress_maps_to_scan_order",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_playback_duration_is_independent_of_hold_time": (
        "test_playback_duration_is_independent_of_hold_time",
        "../test-api/#tests.test_simulation.TestSimulation.test_playback_duration_is_independent_of_hold_time",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_side_view_is_initialized": (
        "test_side_view_is_initialized",
        "../test-api/#tests.test_simulation.TestSimulation.test_side_view_is_initialized",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_front_view_is_initialized": (
        "test_front_view_is_initialized",
        "../test-api/#tests.test_simulation.TestSimulation.test_front_view_is_initialized",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_render_frame_updates_required_information": (
        "test_render_frame_updates_required_information",
        "../test-api/#tests.test_simulation.TestSimulation.test_render_frame_updates_required_information",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_calibration_map_displays_all_points_without_legend": (
        "test_calibration_map_displays_all_points_without_legend",
        "../test-api/#tests.test_simulation.TestSimulation.test_calibration_map_displays_all_points_without_legend",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_current_calibration_point_color_tracks_rendered_point": (
        "test_current_calibration_point_color_tracks_rendered_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_current_calibration_point_color_tracks_rendered_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point": (
        "test_pause_stops_animation_and_keeps_current_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point": (
        "test_resume_restarts_from_current_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point": (
        "test_seek_while_paused_selects_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically": (
        "test_seek_while_playing_pauses_automatically",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately": (
        "test_seek_renders_selected_point_immediately",
        "../test-api/#tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point": (
        "test_animation_completion_stays_at_last_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point": (
        "test_resume_after_completion_restarts_at_first_point",
        "../test-api/#tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle": (
        "test_view_has_point_based_seek_bar_with_large_handle",
        "../test-api/#tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_playback_button_label_follows_state": (
        "test_playback_button_label_follows_state",
        "../test-api/#tests.test_simulation.TestSimulation.test_playback_button_label_follows_state",
    ),
    "TESTCODE:tests.test_simulation.TestSimulation.test_progress_text_uses_point_count_not_time": (
        "test_progress_text_uses_point_count_not_time",
        "../test-api/#tests.test_simulation.TestSimulation.test_progress_text_uses_point_count_not_time",
    ),
}

_SHORT_MARKER = re.compile(r"\[\[TESTCODE_SHORT:([A-Za-z0-9_.]+)\]\]")
_ARCHREQ_MARKER = re.compile(r"\[\[ARCHREQ:(REQ-[A-Z]+-\d+)\]\]")
_TESTSPEC_MARKER = re.compile(r"\[\[TESTSPEC:(TEST-(?:UNIT|UC)-[A-Z0-9-]+)\]\]")
_UCTEST_MARKER = re.compile(r"\[\[UCTEST:(UC-\d+)\]\]")
_API_MARKER = re.compile(r"\[\[API:([A-Za-z0-9_.]+)\]\]")


_MARKER = re.compile(r"\[\[(" + "|".join(map(re.escape, _TRACE_TARGETS)) + r")\]\]")


@event_priority(100)
def on_page_markdown(markdown, page, config, files):
    """Replace semantic trace markers while MkDocs builds each page."""
    del page, config, files

    def replace_short(match):
        target = match.group(1)
        return f"[テストコード](../test-api/#{target})"

    def replace(match):
        label, target = _TRACE_TARGETS[match.group(1)]
        return f"[{label}]({target})"

    def replace_archreq(match):
        target = match.group(1).lower()
        return f"[{match.group(1)}](../architecture_design/#architecture-{target})"

    def replace_testspec(match):
        test_id = match.group(1)
        return f"[{test_id}](../test_specification/#{test_id.lower()})"

    def replace_uctest(match):
        target = match.group(1).lower()
        return f"[テスト仕様](../test_specification/#test-uc-{target[3:]}-01)"

    def replace_api(match):
        target = match.group(1)
        parts = target.split(".")
        label = ".".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        return f"[{label}](../api/#{target})"

    markdown = _API_MARKER.sub(replace_api, markdown)
    markdown = _SHORT_MARKER.sub(replace_short, markdown)
    markdown = _ARCHREQ_MARKER.sub(replace_archreq, markdown)
    markdown = _TESTSPEC_MARKER.sub(replace_testspec, markdown)
    markdown = _UCTEST_MARKER.sub(replace_uctest, markdown)
    return _MARKER.sub(replace, markdown)
