import json

import koji_cli.lib as kl
from koji.plugin import export_cli


@export_cli
def handle_image_builder_build(gopts, session, args):
    "[build] Build images through `image-builder`:"

    usage = "usage: %prog image-builder-build [options] <target> <name> <version> <type> [<type>...]"
    usage += (
        "\n(Specify the --help global option for a list of other help options)"
    )

    parser = kl.OptionParser(usage=usage)

    kl.activate_session(session, gopts)
    if not session.hasPerm("image") and not session.hasPerm("admin"):
        parser.error("this action requires image or admin privileges")

    parser.add_option(
        "--scratch",
        action="store_true",
        default=False,
        help="Perform a scratch build",
    )
    parser.add_option(
        "--arch",
        action="append",
        dest="arches",
        default=[],
        help="Only build provided architectures",
    )
    parser.add_option(
        "--repo",
        action="append",
        help="Specify a repo that will override the repo used to install "
        "RPMs in the image. May be used multiple times. The "
        "build tag repo associated with the target is the default.",
    )

    parser.add_option(
        "--ostree-parent",
        type=str,
        dest="ostree_parent",
        help="The OSTree commit parent for OSTree commit image types",
    )
    parser.add_option(
        "--ostree-ref",
        type=str,
        dest="ostree_ref",
        help="The OSTree commit ref for OSTree commit image types",
    )
    parser.add_option(
        "--ostree-url",
        type=str,
        dest="ostree_url",
        help="URL to the OSTree repo for OSTree commit image types",
    )

    parser.add_option(
        "--release",
        help="Override release of the output, otherwise determined based on 'target' and 'name'",
    )

    parser.add_option(
        "--distro",
        help="Override distro of the output, otherwise determined based on the 'target' and its buildroot",
    )

    parser.add_option(
        "--blueprint",
        help="Provide a blueprint to customize the build. This is a path to a JSON file",
    )

    parser.add_option(
        "--seed",
        help="Set a seed. Influences repeatability of generated UUIDs.",
        type=int,
    )

    (opts, args) = parser.parse_args(args)

    if len(args) < 4:
        parser.error("incorrect number of arguments")
        assert False

    (target, name, version, *types) = args

    task_args = [
        target,
        opts.arches,
        types,
        name,  # e.g. Fedora-Minimal
        version,
    ]

    ostree = {}

    if opts.ostree_parent:
        ostree["parent"] = opts.ostree_parent

    if opts.ostree_ref:
        ostree["ref"] = opts.ostree_ref

    if opts.ostree_url:
        ostree["url"] = opts.ostree_url

    task_opts = {
        "scratch": opts.scratch,
    }

    if ostree:
        task_opts["ostree"] = ostree

    if opts.repo:
        task_opts["repos"] = opts.repo

    if opts.release:
        task_opts["release"] = opts.release

    if opts.distro:
        task_opts["distro"] = opts.distro

    if opts.seed:
        task_opts["seed"] = opts.seed

    if opts.blueprint:
        with open(opts.blueprint, "r") as f:
            task_opts["blueprint"] = json.load(f)

    task_id = session.imageBuilderBuild(
        *task_args,
        opts=task_opts,
    )

    return kl.watch_tasks(
        session,
        [task_id],
        quiet=gopts.quiet,
        poll_interval=gopts.poll_interval,
        topurl=gopts.topurl,
    )
