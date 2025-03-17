import pytest


@pytest.fixture
def koji_mock_kojid(mocker):
    """Provide things that are *usually* imported from `__main__` in koji
    builder plugins. Which means that `__main__` resolves to `kojid`."""

    mocker.patch("__main__.BaseBuildTask", 1, create=True)
    mocker.patch("__main__.BuildImageTask", 1, create=True)
    mocker.patch("__main__.BuildRoot", 1, create=True)
