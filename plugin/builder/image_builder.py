#!/usr/bin/python3

# `image-builder` tasks. These tasks are shipped within `koji-osbuild`'s
# `osbuild` plugin to make deployment on pre-existing `koji` instances
# easier. The eventual goal for the `image-builder` tasks is to be upstreamed
# into `koji` itself but first they have to prove themselves stability wise.

import os
import json
import logging

import koji

from koji.tasks import ServerExit

from __main__ import BaseBuildTask, BuildImageTask, BuildRoot

logger = logging.getLogger("koji.plugin.image_builder")


# When `image-builder` is ran inside `mock` (which is what `koji` uses for its
# build roots) there are complications. `mock` can run with various isolation
# levels, "simple", and "nspawn". The "simple" isolation level is a `chroot` and
# the "nspawn" level is ... well "nspawn".

# `image-builder` (and other build tools) generally don't work inside `mock` with
# "nspawn" isolation because propagation of new device nodes in /dev seems to be
# non-functional. See [issue](https://github.com/rpm-software-management/mock/issues/1554).

# With "simple" isolation `image-builder` *does* work, however its underlying
# `osbuild` wants to use `bubblewrap`, the latter *expects* `/` to be a mountpoint
# which is not the case under `mock`. To work around this we have the following
# script which sets up a temporary extra chroot with appropriate mount points.

# This wrapper is written into the build root. It is only used when the `koji`
# build tag has the property "mock.new_croot" set to False (or non-existent).
# When "mock.new_chroot" is set to false "simple" isolation is used, when it is
# set to true then "nspawn" isolation is used.

# In the future there might be yet another `mock` isolation level, we should
# keep track of it in the upstream issue here: https://github.com/rpm-software-management/mock/issues/1559
# as it will likely allow us to get rid of these shenanigans.
MOCK_SIMPLE_WRAPPER = """
#!/bin/bash
#
# taken from https://gist.github.com/jlebon/fb6e7c6dcc3ce17d3e2a86f5938ec033
# and very lightly tweaked
set -euo pipefail

# This is a small compatibility script that ensures mock
# chroots are compatible with applications that expect / to
# be a mount point, such as bubblewrap.

NEW_ROOT=$(mktemp -d mock-compat-root-XXXXXX)

cleanup() {
    for mnt in sys proc dev; do
        umount "$NEW_ROOT"/$mnt
    done

    umount "$NEW_ROOT"
    umount "$NEW_ROOT"

    rm -r "$NEW_ROOT"
}

trap cleanup EXIT

# The parent of mount in which we'll chroot can't be shared
# or pivot_root will barf. So we just remount onto itself,
# but make sure to make the first parent mount private.

mkdir -p "$NEW_ROOT"

mount --bind / "$NEW_ROOT"

mount --make-private "$NEW_ROOT"
mount --bind "$NEW_ROOT" "$NEW_ROOT"

for mnt in proc sys dev; do
    mount --bind /$mnt "$NEW_ROOT"/$mnt
done

chroot "$NEW_ROOT" "$@"
"""


# Helpers
def arches_for_config(build_config):
    """The architectures field for a build tag is a string. Verify that there
    are architectures, and split them."""

    arches = build_config["arches"]

    if not arches:
        name = build_config["name"]
        raise koji.BuildError(f"Missing arches for tag '%{name}'")

    return set(koji.canonArch(a) for a in arches.split())


def target_repo(topdir, target_info, repo_info):
    """Translate a target tag plus repository info into a baseurl that can be
    used as a repository."""

    path = koji.PathInfo(topdir=topdir)
    repo = path.repo(repo_info["id"], target_info["build_tag_name"])

    return f"{repo}/$arch"


class ImageBuilderBuildTask(BuildImageTask):
    """Spawns imageBuilderBuildArch tasks."""

    _taskWeight = 0.2
    Methods = ["imageBuilderBuild"]

    def handler(
        self,
        target,  # f43
        arches,  # ["ppc64le", ...]
        types,  # ["minimal-raw"]
        name,  # Fedora-Minimal
        version,  # Rawhide
        opts=None,
    ):
        self.opts = {} if opts is None else opts

        target_info = self.session.getBuildTarget(target, strict=True)

        if target_info is None:
            raise koji.BuildError(f"target '{target}' not found")

        build_tag_id = target_info["build_tag"]
        build_config = self.session.getBuildConfig(build_tag_id)

        if not build_config["arches"]:
            raise koji.BuildError("no arches")

        # If no specific architectures were requested for this task we use the
        # set of architectures as they are defined for the build tag.
        if not arches:
            arches = arches_for_config(build_config)
        else:
            # However, when specific architectures *are* requested we verify
            # that those are defined for the build tag.
            diff = set(arches) - arches_for_config(build_config)
            if diff:
                raise koji.BuildError(
                    "Unsupported architecture(s): " + str(diff)
                )

        repo_info = self.getRepo(build_tag_id)

        if not self.opts.get("scratch"):
            self.opts["scratch"] = False

        if self.opts.get("version"):
            version = self.opts["version"]

        if self.opts.get("release"):
            release = self.opts["release"]
        else:
            release = self.session.getNextRelease(
                {"name": name, "version": version}
            )

        if not self.opts["scratch"]:
            build_info = self.initImageBuild(
                name, version, release, target_info, self.opts
            )

            release = build_info["release"]
        else:
            build_info = {}

        try:
            subtasks = {}
            canfails = []

            for arch in arches:
                subtasks[arch] = self.session.host.subtask(
                    method="imageBuilderBuildArch",
                    arglist=[
                        name,
                        version,
                        release,
                        arch,
                        types,
                        target_info,
                        build_config,
                        repo_info,
                        self.opts,
                    ],
                    label=arch,
                    parent=self.id,
                    arch=arch,
                )

            results = self.wait(
                list(subtasks.values()),
                all=True,
                canfail=canfails,
            )

            all_failed = True

            for result in results.values():
                if not isinstance(result, dict) or "faultCode" not in result:
                    all_failed = False
                    break

            if all_failed:
                raise koji.GenericError("all subtasks failed")

            results = {str(k): v for k, v in results.items()}

            if self.opts["scratch"]:
                self.session.host.moveImageBuildToScratch(self.id, results)
            else:
                self.session.host.completeImageBuild(
                    self.id, build_info["id"], results
                )
        except (SystemExit, ServerExit, KeyboardInterrupt):
            raise
        except Exception:
            if not self.opts["scratch"]:
                self.session.host.failBuild(self.id, build_info["id"])
            raise

        if not self.opts["scratch"] and not self.opts.get("skip_tag"):
            tag_task_id = self.session.host.subtask(
                method="tagBuild",
                arglist=[
                    target_info["dest_tag"],
                    build_info["id"],
                    False,
                    None,
                    True,
                ],
                label="tag",
                parent=self.id,
                arch="noarch",
            )

            self.wait(tag_task_id)

        report = ""

        if self.opts["scratch"]:
            respath = ", ".join(
                [
                    os.path.join(
                        koji.pathinfo.work(), koji.pathinfo.taskrelpath(tid)
                    )
                    for tid in subtasks.values()
                ]
            )
            report += "Scratch "
        else:
            respath = koji.pathinfo.imagebuild(build_info)

        report += "image build results in: %s" % respath
        return report


class ImageBuilderBuildArchTask(BaseBuildTask):
    _taskWeight = 0.2

    Methods = ["imageBuilderBuildArch"]

    def handler(
        self,
        name,
        version,
        release,
        arch,
        types,
        target_info,
        build_config,
        repo_info,
        opts=None,
    ):
        self.opts = {} if opts is None else opts

        build_tag_id = target_info["build_tag"]

        # When running in "simple" or "old" mock isolation modes we need to
        # request `mock` to mount `/dev` for us. We don't *always* need access
        # to `/dev` as it's dependent on the image types being built, but it
        # also doesn't hurt.
        bind_opts = {}

        if not build_config["extra"].get("mock.new_chroot", True):
            bind_opts = {"dirs": {"/dev": "/dev"}}

        broot = BuildRoot(
            self.session,
            self.options,
            tag=build_tag_id,
            arch=arch,
            task_id=self.id,
            repo_id=repo_info["id"],
            install_group="image-builder-build",
            setup_dns=True,
            bind_opts=bind_opts,
        )

        broot.workdir = self.workdir
        broot.init()

        cmd = []

        if not build_config["extra"].get("mock.new_chroot", True):
            # We're going to write a wrapper into the mock. Since `image-builder`
            # uses sandboxing we can't really run well inside other sandboxes. In
            # this specific case `bubblewrap` assumes `/` to be a mountpoint.

            # See the comments on `MOCK_SIMPLE_WRAPPER` for a lot more detail on the
            # why and how.

            logger.info(
                "running in 'old' or 'simple' mock isolation. setting up a "
                "wrapper script to deal with mount points"
            )

            path = broot.tmpdir()
            koji.ensuredir(path)

            with open(os.path.join(path, "mock-wrap"), "w") as f:
                f.write(MOCK_SIMPLE_WRAPPER)

            cmd.extend(
                ["sh", os.path.join(broot.tmpdir(within=True), "mock-wrap")]
            )
        else:
            # When we're not running under "simple" isolation we're very likely
            # to fail, depending on the image types being built. We'll continue
            # but we're going to at least log it
            logger.warning(
                "running in 'new' or 'nspawn' mock isolation, this is likely to "
                "break `image-builder`. please set `mock.new_chroot` to `false` "
                "on the build tag"
            )

        # The base command to start with, we want to do a build and we want to
        # be verbose during the build. This disables progress bars and other
        # fancy terminal output.
        cmd.extend(
            [
                "image-builder",
                "-v",
                "build",
            ]
        )

        # We turn off `librepo` fetching, there are some bugs regarding
        # variable replacements and it's not doing anything useful within the
        # koji environment. See issue: https://github.com/osbuild/image-builder-cli/issues/151
        cmd.extend(["--use-librepo=false"])

        # When an optional `data_url` is present we check it out into the
        # the build root and pass it on to `image-builder`. This allows for
        # overriding built-in definitions to those present in the repository.
        if self.opts.get("data_url"):
            raise NotImplementedError("data_url is not available")

        # When an optional `blueprint` is present we write it into the build
        # root and pass it on to `image-builder`. This allows for customizing
        # images. Likely not to be used in practice, but useful for scratch
        # builds and testing.
        blueprint = self.opts.get("blueprint")
        if blueprint:
            path = broot.tmpdir()
            koji.ensuredir(path)

            with open(os.path.join(path, "blueprint.json"), "w") as f:
                json.dump(blueprint, f)

            cmd.extend(
                [
                    "--blueprint",
                    os.path.join(broot.tmpdir(within=True), "blueprint.json"),
                ]
            )

        # Normally the distro that is being built is determined from
        # `/etc/os-release` in the buildroot; however, it is possible to
        # override this to do a cross-distro build. Note that this will likely
        # always need additional repositories containing the right content
        # to be passed along as well.
        distro = self.opts.get("distro")
        if distro:
            cmd.extend(["--distro", distro])

        # Set up repositories that are being used. If there were optional
        # repos provided we use those, otherwise we use the targets repo
        repos = self.opts.get("repos", [])
        if repos:
            for repo in repos:
                cmd.extend(["--force-repo", repo])
        else:
            cmd.extend(
                [
                    "--force-repo",
                    target_repo(self.options.topurl, target_info, repo_info),
                ]
            )

        # We also want most of the extra information we can get out of
        # `image-builder`, the more the better in this case.
        cmd.extend(
            [
                "--with-sbom",
                "--with-manifest",
            ]
        )

        # If ostree information is available pass it on to the command
        ostree = self.opts.get("ostree")
        if ostree:
            ostree_url = ostree.get("url")
            if ostree_url:
                cmd.extend(["--ostree-url", ostree_url])

            ostree_ref = ostree.get("url")
            if ostree_ref:
                cmd.extend(["--ostree-ref", ostree_ref])

            ostree_parent = ostree.get("parent")
            if ostree_parent:
                cmd.extend(["--ostree-parent", ostree_parent])

        cmd.extend(["--output-dir", "/builddir/output"])
        cmd.extend(["--output-name", f"{name}-{version}-{release}"])

        # Finally we add the types we want built to the command as well.
        cmd += types

        # And execute it. The exception message here might look very terse
        # however all output from the build root is logged and attached as log
        # files to the task.
        exit_code = broot.mock(
            ["--cwd", broot.tmpdir(within=True), "--chroot", "--"] + cmd
        )
        if exit_code != 0:
            raise koji.GenericError("`image-builder` failed")

        # We have done our build, now it is time to massage our outputs into
        # the correct formats that koji understands and to make sure we give
        # all data back.

        # First let's lay out the expected result structure for a koji task.
        data = {
            "task_id": self.id,
            "name": name,
            "version": version,
            "release": distro,
            "arch": arch,
            "files": [],
            "logs": [],
            "rpmlist": [],
        }

        output = os.path.join(broot.rootdir(), "builddir/output")

        # Attach and upload all files that are in the output directory generated
        # by `image-builder`.
        for root, _, files in os.walk(output):
            for file in files:
                self.uploadFile(os.path.join(root, file), remoteName=file)
                data["files"].append(file)

        broot.expire()

        return data
