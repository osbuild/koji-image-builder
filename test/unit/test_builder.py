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

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]

def test_build_arch_task_with_repos(koji_mock_kojid):
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
        {"repos": ["a/$arch/b", "c/$basearch/d"]},
    )

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "a/x86_64/b",
            "--force-repo",
            "c/x86_64/d",
            "--with-sbom",
            "--with-manifest",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]

def test_build_arch_task_multiple_types(koji_mock_kojid):
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
        ["minimal-raw", "minimal-raw-zst"],
        {"build_tag": "f42-build", "build_tag_name": "f42-build"},
        {"extra": {"mock.new_chroot": 0}},
        {"id": 1},
        {},
    )

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw-zst",
        ],
    ]


def test_build_arch_task_ostree(koji_mock_kojid):
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
        {
            "ostree": {
                "ref": "fedora/rawhide/$arch/iot",
                "url": "https://kojipkgs.fedoraproject.org/compose/iot/repo/",
            }
        },
    )

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--ostree-url",
            "https://kojipkgs.fedoraproject.org/compose/iot/repo/",
            "--ostree-ref",
            "fedora/rawhide/x86_64/iot",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]


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


def test_build_arch_task_seed(koji_mock_kojid):
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
        {
            "seed": 1234,
        },
    )

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--seed", "1234",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]


def test_build_arch_task_preview(koji_mock_kojid):
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
        {
            "preview": False,
        },
    )

    assert koji_mock_kojid.buildroot.mock_calls == [
        [
            "--cwd",
            str(koji_mock_kojid.buildroot._tmpdir),
            "--chroot",
            "--",
            "sh",
            str(koji_mock_kojid.buildroot._tmpdir) + "/mock-wrap",
            "image-builder",
            "-v",
            "build",
            "--use-librepo=false",
            "--force-repo",
            "//repos/f42-build/1/$arch",
            "--with-sbom",
            "--with-manifest",
            "--preview", "false",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]


