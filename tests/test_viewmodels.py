import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.mission_validation_service import Mission
from app.application.viewmodels import MissionsViewModel, SquadronViewModel


def test_missions_viewmodel_states_and_filter():
    vm = MissionsViewModel()

    empty_state = vm.state_for_loaded_missions([])
    assert empty_state.state == "empty"

    loaded_state = vm.state_for_loaded_missions([Mission(description="A")])
    assert loaded_state.state == "success"

    vis = vm.filter_visibility(
        [Mission(description="escort mission")],
        [["01/01/1918", "12:00", "Spad", "Escort"]],
        "spad",
    )
    assert vis == [True]

    vis2 = vm.filter_visibility(
        [Mission(description="escort mission")],
        [["01/01/1918", "12:00", "Spad", "Escort"]],
        "bomber",
    )
    assert vis2 == [False]


def test_squadron_viewmodel_states_and_filter():
    vm = SquadronViewModel()

    st = vm.state_for_members([])
    assert st.state == "empty"

    st2 = vm.state_for_members([{"name": "A"}])
    assert st2.state == "success"

    rows = [{"name": "Pilot A", "rank": "Lt", "victories": "3", "missions": "8", "status": "Ativo"}]
    assert vm.filter_visibility(rows, "pilot") == [True]
    assert vm.filter_visibility(rows, "pow") == [False]
