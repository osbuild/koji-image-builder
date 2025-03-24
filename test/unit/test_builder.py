import pytest


class MockOptions:
    def __init__(self, *, topurl=None):
        self.topurl = topurl


def test_arches_for_config(koji_mock_kojid):
    import plugin.builder.image_builder as builder

    assert builder.arches_for_config({"arches": "x86_64"}) == set(["x86_64"])
    assert builder.arches_for_config({"arches": "x86_64 aarch64"}) == set(
        ["x86_64", "aarch64"]
    )


def test_build_arch_task(koji_mock_kojid):
    import plugin.builder.image_builder as builder

    t = builder.ImageBuilderBuildArchTask()

    t.id = None
    t.session = None
    t.options = MockOptions(topurl="/")
    t.workdir = None

    t.handler(
        "Fedora-Minimal",
        "42",
        "1",
        "x86_64",
        ["minimal-raw"],
        {"build_tag": "f42-build", "build_tag_name": "f42-build"},
        {"extra": {"mock.new_chroot": 0}},
        {"id": 1},
        {},
    )


def test_build_arch_task_with_data_url_is_exception(koji_mock_kojid):
    import plugin.builder.image_builder as builder

    t = builder.ImageBuilderBuildArchTask()

    t.id = None
    t.session = None
    t.options = MockOptions(topurl="/")
    t.workdir = None

    with pytest.raises(NotImplementedError):
        t.handler(
            "Fedora-Minimal",
            "42",
            "1",
            "x86_64",
            ["minimal-raw"],
            {"build_tag": "f42-build", "build_tag_name": "f42-build"},
            {"extra": {"mock.new_chroot": 0}},
            {"id": 1},
            {"data_url": "data"},
        )
