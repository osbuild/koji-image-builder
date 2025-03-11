"""Koji osbuild integration for Koji Hub"""

import sys
import logging
import jsonschema

import koji
from koji.context import context

sys.path.insert(0, "/usr/share/koji-hub/")
import kojihub  # pylint: disable=import-error, wrong-import-position

logger = logging.getLogger("koji.plugin.image_builder")


IMAGE_BUILDER_BUILD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "imageBuilderBuild argument schema",
    "type": "array",
    "minItems": 6,
    "items": [
        {"type": "string", "description": "Target"},
        {
            "type": "array",
            "description": "Architectures",
            "items": {"type": "string"},
        },
        {
            "type": "array",
            "description": "Image Types",
            "minItems": 1,
            "maxItems": 1,
            "items": {"type": "string"},
        },
        {"type": "string", "description": "Name"},
        {"type": "string", "description": "Version"},
        {"type": "object", "$ref": "#/definitions/options"},
    ],
    "definitions": {
        "ostree": {
            "title": "OSTree specific options",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "parent": {"type": "string"},
                "ref": {"type": "string"},
                "url": {"type": "string"},
            },
        },
        "options": {
            "title": "Optional arguments",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "scratch": {"type": "boolean", "description": "Scratch Build"},
                "repos": {
                    "type": "array",
                    "description": "Repositories",
                    "items": {"type": "string"},
                },
                "release": {
                    "type": "string",
                    "description": "Release override",
                },
                "distro": {
                    "type": "string",
                    "description": "Distribution override",
                },
                "skip_tag": {
                    "type": "boolean",
                    "description": "Omit tagging the result",
                },
                "ostree": {
                    "type": "object",
                    "$ref": "#/definitions/ostree",
                    "descriptions": "Additional ostree options",
                },
                "blueprint": {
                    "type": "object",
                    "description": "Blueprint",
                },
            },
        },
    },
}


@koji.plugin.export
def imageBuilderBuild(
    target,
    arches,
    types,
    name,
    version,
    opts=None,
    priority=None,
):
    """Create an image via image-builder"""
    # XXX why?
    # context.session.assertPerm("image")

    if opts is None:
        opts = {}

    args = [target, arches, types, name, version, opts]
    task = {"channel": "image", "owner": 1}  # XXX remove?

    logger.info("creating imageBuilderBuild task")

    try:
        jsonschema.validate(args, IMAGE_BUILDER_BUILD_SCHEMA)
    except jsonschema.exceptions.ValidationError as err:
        raise koji.ParameterError(str(err)) from None

    if priority and priority < 0 and not context.session.hasPerm("admin"):
        raise koji.ActionNotAllowed(
            "only admins may create high-priority tasks"
        )

    task_id = kojihub.make_task("imageBuilderBuild", args, **task)

    if task_id:
        logger.info("imageBuilderBuild task %i created", task_id)
    else:
        # TODO, what?
        pass

    return task_id
