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


def cli(args):
    return [
        "podman",
        "run",
        "--pod",
        "koji-dev",
        "--rm",
        "-v",
        "./test/data/confs/cli:/opt/cli:z",
        "-v",
        "./plugin/cli/image_builder.py:/usr/lib/python3.13/site-packages/koji_cli_plugins/image_builder.py:z",
        "-it",
        "koji-image-builder",
        "/opt/cli/koji",
    ] + args


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

    # TODO THESE CAN MOVE
    print("- patch: copying comps")
    shutil.copyfile(
        "./test/data/comps.xml",
        pathlib.Path(path) / "koji-container-dev/scripts/f33_comps.xml",
    )

    print("- patch: copying buildroot setup script")
    shutil.copyfile(
        "./test/data/scripts/setup_fedora_buildroot",
        pathlib.Path(path)
        / "koji-container-dev/scripts/setup_fedora_buildroot",
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
        cwd=pathlib.Path(path),
    )

    print("- setup: basedir (chmod)")
    run_quiet(
        [
            "chmod",
            "-R",
            "777",
            "basedir",
        ],
        cwd=pathlib.Path(path),
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
            f"{path}/db/data:/var/lib/postgresql/data:z",
            "-v",
            f"./test/data/confs/database:/docker-entrypoint-initdb.d:z",
            "-v",
            f"{path}/koji:/opt:z",
            "docker.io/library/postgres:12",
        ],
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
            f"{path}/basedir:/mnt/koji:z",
            "-v",
            "./test/data/confs/hub:/opt/cfg:z",
            "-v",
            f"{path}/koji:/opt/koji",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ]
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
        cli(["grant-permission", "repo", "kojira"]),
    )

    print("- run: set buildroot options")
    run_quiet(
        cli(["edit-tag", "-x", "mock.new_chroot=0", "fedora-42-build"]),
    )

    print("- run: add pkg")
    run_quiet(
        cli(
            [
                "add-pkg",
                "--owner",
                "kojiadmin",
                "fedora-42",
                "Fedora-Minimal",
            ]
        ),
    )

    print("- run: start builder")
    run_quiet(
        ["mkdir", "mock"],
        cwd=pathlib.Path(path),
    )

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
            f"{path}/basedir:/mnt/koji:z",
            "-v",
            "./test/data/confs/builder:/opt/cfg:z",
            "-v",
            f"{path}/koji:/opt/koji",
            "-v",
            f"{path}/mock:/var/lib/mock:rw",
            "--env",
            "HOSTIP=127.0.0.1",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ],
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
            f"{path}/basedir:/mnt/koji:z",
            "-v",
            "./test/data/confs/kojira:/opt/cfg:z",
            "-v",
            f"{path}/koji:/opt/koji",
            "--name",
            "koji-kojira",
            "koji-image-builder",
            "/bin/sh",
            "/opt/cfg/entrypoint.sh",
        ],
    )


def build(path):
    # Do a build, wait for it to exit succesfully
    try:
        subprocess.run(
            cli(
                [
                    "image-builder-build",
                    "fedora-42",
                    "Fedora-Minimal",
                    "42",
                    "minimal-raw",
                ]
            ),
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
    print(
        "koji has started, kojiweb is available at http://localhost:8080/koji and"
    )
    print(
        f"the koji cli is available at {path}/koji-container-dev/cli to interact"
    )
    print("press ctrl+C to exit and tear down")


def teardown(path):
    print("- teardown: stopping pod")
    run_quiet(["podman", "pod", "stop", "koji-dev"])

    print("- teardown: removing pod")
    run_quiet(["podman", "pod", "rm", "koji-dev"])


def border():
    print("=" * 64)


def main():
    test = "test" in sys.argv
    stay = "stay" in sys.argv

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

            if stay:
                loop(path)
        else:
            loop(path)

        border()

        teardown(path)


if __name__ == "__main__":
    raise SystemExit(main())
