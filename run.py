#!/usr/bin/env python3

"""Sets up `koji` in containers and runs an integration test for the
`koji-image-builder` plugin if requested."""

import subprocess
import tempfile
import pathlib
import time
import shutil
import shlex
import sys


def run_quiet(args, **kwargs):
    print(" ", shlex.join(args))

    if "check" in kwargs:
        check = kwargs["check"]
        del kwargs["check"]
    else:
        check = True

    try:
        return subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            **kwargs,
        )
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        raise e
    except:
        raise


def pre_unit():
    """Run the normal (quick) unittests first."""
    print("- test: unit")
    run_quiet(["pytest", "test/unit"])


def pre_clone(path):
    """Clone the integration testing repository."""

    print("- clone: koji-container-dev")
    run_quiet(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/tkopecek/koji-container-dev",
            "koji-container-dev",
        ],
        cwd=pathlib.Path(path),
    )

    print("- clone: koji")
    run_quiet(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://pagure.io/koji",
            "koji",
        ],
        cwd=pathlib.Path(path),
    )


def pre_patch(path):
    """Apply patches to the integration testing checkouts."""

    shutil.copyfile(
        "./test/data/confs/hub/hub.conf",
        pathlib.Path(path) / "koji-container-dev/hub/koji-hub/hub.conf",
    )

    shutil.copyfile(
        "./test/data/confs/builder/kojid.conf",
        pathlib.Path(path) / "koji-container-dev/builder/kojid.conf",
    )

    print("- patch: copying comps")
    shutil.copyfile(
        "./test/data/comps.xml",
        pathlib.Path(path) / "koji-container-dev/scripts/f33_comps.xml",
    )

    # Add our modules
    print("- patch: copying plugins: builder")
    shutil.copyfile(
        "./plugin/builder/image_builder.py",
        pathlib.Path(path) / "koji/plugins/builder/image_builder.py",
    )

    print("- patch: copying plugins: hub")
    shutil.copyfile(
        "./plugin/hub/image_builder.py",
        pathlib.Path(path) / "koji/plugins/hub/image_builder.py",
    )

    # XXX cli plugin comes from local :(


def pre_setup(path):
    """Run setup scripts as necessary for the integration containers."""

    print("- setup: basedir")
    run_quiet(
        [
            "mkdir",
            "-p",
            "basedir/packages",
            "basedir/repos",
            "basedir/work",
            "basedir/scratch",
            "db/data",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    print("- setup: basedir (chmod)")
    run_quiet(
        [
            "chmod",
            "-R",
            "777",
            "basedir",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    print("- setup: certificates")
    shutil.copytree(
        "./test/data/certs",
        pathlib.Path(path) / "koji-container-dev/certs/certs",
    )

    print("- setup: certificates (chmod)")
    run_quiet(
        [
            "chmod",
            "-R",
            "777",
            "certs/certs",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    # copy hub
    print("- setup: certificates (hub)")
    run_quiet(
        ["mkdir", "hub/certs"], cwd=pathlib.Path(path) / "koji-container-dev"
    )

    shutil.copy(
        pathlib.Path(path)
        / "koji-container-dev/certs/certs/root-ca/koji-ca.crt",
        pathlib.Path(path) / "koji-container-dev/hub/certs/koji-ca.crt",
    )

    shutil.copy(
        pathlib.Path(path)
        / "koji-container-dev/certs/certs/localhost/localhost.crt",
        pathlib.Path(path) / "koji-container-dev/hub/certs/koji-hub.crt",
    )

    shutil.copy(
        pathlib.Path(path)
        / "koji-container-dev/certs/certs/localhost/localhost.key",
        pathlib.Path(path) / "koji-container-dev/hub/certs/koji-hub.key",
    )

    # copy builder
    print("- setup: certificates (builder)")
    run_quiet(
        ["mkdir", "builder/certs"],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    shutil.copy(
        pathlib.Path(path)
        / "koji-container-dev/certs/certs/kojibuilder/kojibuilder.pem",
        pathlib.Path(path) / "koji-container-dev/builder/certs/kojibuilder.pem",
    )

    # copy kojira
    print("- setup: certificates (kojira)")
    run_quiet(
        ["mkdir", "kojira/certs"], cwd=pathlib.Path(path) / "koji-container-dev"
    )

    shutil.copy(
        pathlib.Path(path) / "koji-container-dev/certs/certs/kojira/kojira.pem",
        pathlib.Path(path) / "koji-container-dev/kojira/certs/kojira.pem",
    )

    print("- setup: config")
    with open(pathlib.Path(path) / "koji-container-dev/config.local", "w") as f:
        p = pathlib.Path(path) / "koji"
        f.write(f"CODEDIR='{p!s}'")


def pre_build(path):
    print("- building container")
    run_quiet(
        ["podman", "build", "-t", "koji-image-builder", "."],
        cwd="./test/data",
    )


def prune(path):
    print("- prune: stop pod")
    run_quiet(["podman", "pod", "stop", "koji-dev"], check=False)
    print("- prune: rm pod")
    run_quiet(["podman", "pod", "rm", "koji-dev"], check=False)


def run(path):
    # TODO: replace with direct podman calls so we can control pod naming?
    print("- run: pod create")
    run_quiet(
        [
            "podman",
            "pod",
            "create",
            "-p",
            "5432:5432",
            "-p",
            "8080:80",
            "-p",
            "8081:443",
            "koji-dev",
        ]
    )

    print("- run: postgres")
    run_quiet(
        [
            "podman",
            "run",
            "-id",
            "--rm",
            "--name",
            "koji-postgres",
            "--pod",
            "koji-dev",
            "-e",
            "POSTGRES_USER=koji",
            "-e",
            "POSTGRES_DB=koji",
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=password",
            "-e",
            "POSTGRES_PASSWORD=mypassword",
            "-e",
            "DB_SCHEMA=/opt/schemas/schema.sql",
            "-v",
            "./db/data:/var/lib/postgresql/data:z",
            "-v",
            "./db:/docker-entrypoint-initdb.d:z",
            "-v",
            "../koji:/opt:z",
            "postgres:12",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    time.sleep(1)

    print("- run: hub")
    run_quiet(
        [
            "podman",
            "run",
            "-d",
            "--rm",
            "--name",
            "koji-hub",
            "--pod",
            "koji-dev",
            "--security-opt",
            "label=disable",
            "-v",
            "./basedir:/mnt/koji:z",
            "-v",
            "./hub:/opt/cfg:z",
            "-v",
            "../koji:/opt/koji",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    print("- run: hub (wait)")
    time.sleep(2.5)

    print("- run: setup tags")
    run_quiet(
        ["./setup_fedora_buildroot", "42"],
        cwd=pathlib.Path(path) / "koji-container-dev/scripts",
    )

    print("- run: grant permissions to kojira")
    run_quiet(
        ["./koji", "grant-permission", "repo", "kojira"],
        cwd=pathlib.Path(path) / "koji-container-dev/cli",
    )

    print("- run: set buildroot options")
    run_quiet(
        ["./koji", "edit-tag", "-x", "mock.new_chroot=0", "fedora-42-build"],
        cwd=pathlib.Path(path) / "koji-container-dev/cli",
    )

    print("- run: add pkg")
    run_quiet(
        [
            "./koji",
            "add-pkg",
            "--owner",
            "kojiadmin",
            "fedora-42",
            "Fedora-Minimal",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev/cli",
    )

    print("- run: start builder")
    run_quiet(
        [
            "podman",
            "run",
            "-d",
            "--rm",
            "--cap-add",
            "SYS_ADMIN",
            "--privileged",
            "--security-opt",
            "label=type:unconfined_t",
            "--name",
            "koji-builder",
            "--pod",
            "koji-dev",
            "-v",
            "./basedir:/mnt/koji:z",
            "-v",
            "./builder:/opt/cfg:z",
            "-v",
            "../koji:/opt/koji",
            "-v",
            "/home/user/mock:/var/lib/mock:rw",
            "--env",
            "HOSTIP=127.0.0.1",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )

    print("- run: start kojira")
    run_quiet(
        [
            "podman",
            "run",
            "-d",
            "-it",
            "--rm",
            "--pod",
            "koji-dev",
            "--security-opt",
            "label=disable",
            "--cap-add=SYS_ADMIN",
            "-v",
            "./basedir:/mnt/koji:z",
            "-v",
            "./kojira:/opt/cfg:z",
            "-v",
            "../koji:/opt/koji",
            "--name",
            "koji-kojira",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ],
        cwd=pathlib.Path(path) / "koji-container-dev",
    )


def build(path):
    # Do a build, wait for it to exit succesfully
    try:
        subprocess.run(
            [
                "./koji",
                "image-builder-build",
                "fedora-42",
                "Fedora-Minimal",
                "42",
                "minimal-raw",
            ],
            cwd=pathlib.Path(path) / "koji-container-dev/cli",
            check=True,
        )
    except KeyboardInterrupt:
        pass


def loop(path):
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def info(path):
    print("koji has started, kojiweb is available at http://localhost:8080/koji and")
    print(f"the koji cli is available at {path}/koji-container-dev/cli to interact")
    print("press ctrl+C to exit and tear down")


def teardown(path):
    print("- teardown: stopping pod")
    run_quiet(["podman", "pod", "stop", "koji-dev"])

    print("- teardown: removing pod")
    run_quiet(["podman", "pod", "rm", "koji-dev"])


def border():
    print("=" * 64)


def main():
    pre_unit()

    test = len(sys.argv) > 1 and sys.argv[1] == "test"

    with tempfile.TemporaryDirectory() as path:
        pre_clone(path)  # clone
        pre_patch(path)  # configure
        pre_setup(path)
        pre_build(path)

        prune(path)

        run(path)

        border()

        info(path)

        if test:
            border()
            build(path)
        else:
            loop(path)

        border()

        teardown(path)


if __name__ == "__main__":
    raise SystemExit(main())
