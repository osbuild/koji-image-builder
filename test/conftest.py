import pytest


class MockBaseBuildTask:
    pass


class MockBuildImageTask:
    pass


class MockBuildRoot:
    def __init__(self, *args, **kwargs):
        pass

    def init(self):
        pass

    def tmpdir(self, within=False):
        return ""

    def rootdir(self):
        return ""

    def expire(self):
        pass

    def mock(self, args):
        return 0


@pytest.fixture
def koji_mock_kojid(mocker):
    """Provide things that are *usually* imported from `__main__` in koji
    builder plugins. Which means that `__main__` resolves to `kojid`."""

    mocker.patch("__main__.BaseBuildTask", MockBaseBuildTask, create=True)
    mocker.patch("__main__.BuildImageTask", MockBuildImageTask, create=True)
    mocker.patch("__main__.BuildRoot", MockBuildRoot, create=True)

    return mocker
