from sota_dl.infrastructure.errors import InfrastructureError, DownloadError


def test_infrastructure_error_str() -> None:
    err = InfrastructureError("Test", path="/home/test")
    assert str(err) == "Test [path=/home/test]"
    assert repr(err) == "InfrastructureError('Test', **{'path': '/home/test'})"


def test_infrastructure_error_to_dict() -> None:
    err = InfrastructureError("Test", path="/home/test")
    d = err.to_dict()
    assert d["type"] == "InfrastructureError"
    assert d["message"] == "Test"
    assert d["details"] == {"path": "/home/test"}


def test_derived_exception() -> None:
    err = DownloadError("Failed", url="http://...")
    assert isinstance(err, InfrastructureError)
    assert "url=http://..." in str(err)
