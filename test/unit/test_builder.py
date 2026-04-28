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
            "--with-rpmlist",
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
            "--with-rpmlist",
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
            "--with-rpmlist",
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
            "--with-rpmlist",
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
            "--with-rpmlist",
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
            "--with-rpmlist",
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
            "--with-rpmlist",
            "--preview", "false",
            "--output-dir",
            "/builddir/output",
            "--output-name",
            "Fedora-Minimal-42-1.x86_64",
            "minimal-raw",
        ],
    ]


def test_load_rpmlist_from_output_missing(koji_mock_kojid, tmp_path):
    import plugin.builder.image_builder as builder

    missing = tmp_path / "not-a-dir"
    assert builder.load_rpmlist_from_output(str(missing)) == []


def test_load_rpmlist_from_output(koji_mock_kojid, tmp_path):
    import plugin.builder.image_builder as builder

    out = tmp_path / "output"
    out.mkdir()
    (out / "img.rpmlist.json").write_text(
        '[{"name":"mpfr","version":"4.1.0","release":"10.el9","epoch":0,"arch":"x86_64","buildtime":1770637270,"size":331788,"payloadhash":"11c1d6b33b7e64ddc40faf45b949618c829bd2e3d3661132417e4c8aee6ab0fd"}]',
        encoding="utf-8",
    )
    assert builder.load_rpmlist_from_output(str(out)) == [
        {"name":"mpfr","version":"4.1.0","release":"10.el9","epoch":0,"arch":"x86_64","buildtime":1770637270,"size":331788,"payloadhash":"11c1d6b33b7e64ddc40faf45b949618c829bd2e3d3661132417e4c8aee6ab0fd"},
    ] 
