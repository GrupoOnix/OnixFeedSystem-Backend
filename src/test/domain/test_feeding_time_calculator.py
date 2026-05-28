from domain.services.feeding_time_calculator import calculate_cyclic_wait_duration


def test_cyclic_wait_duration_for_single_cage_excludes_last_visit():
    assert calculate_cyclic_wait_duration(
        total_rounds=3,
        active_cage_count=1,
        wait_after_visit_seconds=60,
    ) == 120


def test_cyclic_wait_duration_for_multiple_cages_excludes_last_execution():
    assert calculate_cyclic_wait_duration(
        total_rounds=2,
        active_cage_count=2,
        wait_after_visit_seconds=15,
    ) == 45


def test_cyclic_wait_duration_without_active_visits_is_zero():
    assert calculate_cyclic_wait_duration(
        total_rounds=0,
        active_cage_count=0,
        wait_after_visit_seconds=60,
    ) == 0
