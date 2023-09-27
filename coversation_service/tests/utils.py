def assert_custom_equality_between_objects(object1: list[dict] | dict, object2: list[dict] | dict,
                                           fields_to_exclude: list[str]):
    """A custom assertor that compares either two dicts or two lists of dicts, while ignoring a few fields.
    This is crucial to comparing results from the database that created random uuid and new creation dates for every db call"""
    if isinstance(object1, list) and isinstance(object2, list):
        for elem1, elem2 in zip(object1, object2):
            for field in fields_to_exclude:
                assert field in elem1
            for key in elem1:
                if key not in fields_to_exclude:
                    assert elem1[key] == elem2[key]

    elif isinstance(object1, dict) and isinstance(object2, dict):
        assert all(
            object1[key] == object2[key] for key in object1 if key not in fields_to_exclude)

        for field in fields_to_exclude:
            assert field in object1

    else:
        raise TypeError(
            f"Make sure both objects are of the same type, object1 is {type(object1).__name__} and object2 is {type(object2).__name__}")
