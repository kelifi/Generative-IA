from source.helpers.blob_storage_helper import create_local_model_folder_if_not_exists


def test_create_local_model_folder_if_not_exists_exists(monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda _: True)
    result = create_local_model_folder_if_not_exists()
    assert result is False


def test_create_local_model_folder_if_not_exists_not_exists(monkeypatch):
    monkeypatch.setattr(target="os.path.exists", name=lambda _: False)
    result = create_local_model_folder_if_not_exists()
    assert result is True
