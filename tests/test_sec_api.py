def test_can_list_amcs():
    from sec_opendata_client import get_amcs
    amcs = get_amcs()
    assert isinstance(amcs, list)
    assert len(amcs) > 0
    assert "comp_name_th" in amcs[0]
