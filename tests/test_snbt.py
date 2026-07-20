from generator.snbt import loads


def test_parses_ftb_compound_and_typed_array() -> None:
    data = loads("{ version: 13, enabled: true, position: [I; 0, 1, 2], scale: 0.5d }")
    assert data == {"version": 13, "enabled": True, "position": [0, 1, 2], "scale": 0.5}
