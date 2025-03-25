import pytest


class MockBaseBuildTask:
    pass


class MockBuildImageTask:
    pass


class MockBuildRoot:
    mock_calls = []

    def __init__(self, *args, **kwargs):
        pass

    def init(self):
        pass

    def tmpdir(self, within=False):
        return self._tmpdir

    def rootdir(self):
        return ""

    def expire(self):
        pass

    def mock(self, args):
        self.mock_calls.append(args)

        return 0


@pytest.fixture
def koji_mock_kojid(mocker, tmpdir):
    """Provide things that are *usually* imported from `__main__` in koji
    builder plugins. Which means that `__main__` resolves to `kojid`."""

    mocker.patch("__main__.BaseBuildTask", MockBaseBuildTask, create=True)
    mocker.patch("__main__.BuildImageTask", MockBuildImageTask, create=True)
    mocker.patch("__main__.BuildRoot", MockBuildRoot, create=True)

    mocker.buildroot = MockBuildRoot
    mocker.buildroot._tmpdir = tmpdir

    mocker.buildroot.mock_calls = []

    return mocker
