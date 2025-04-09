# koji-image-builder

This project provides [`image-builder`](https://github.com/osbuild/image-builder-cli) integration with [Koji](https://pagure.io/koji). `image-builder` is a tool that builds images (as the name says).

## Installation and Configuration

To use `koji-image-builder` you need the following things for your `koji` instance:

1. Install `koji-image-builder-builder` on your builders (those that run `kojid`).
2. Enable the `image_builder` plugin in your builder configuration (`/etc/kojid/kojid.conf`).
3. Install `koji-image-builder-hub` on your hub.
2. Enable the `image_builder` plugin in your hub configuration (`/etc/koji-hub/hub.conf`).

Once this is done you can proceed to configuring your instance:

1. Create the `image-builder-build` group which contains `image-builder` and `distribution-gpg-keys`.
2. Create `fXX-image-builder-build` tags, which contain the `image-builder-build` group and have `mock.new_chroot` set to `0`.
3. Create `fXX-image-builder` targets, which use the `fXX-image-builder-build` tags as their build tag and the `fXX` tag as their target.
4. Add the `image-builder-build` group to your build tag.
4. Create packages for the things you want to build in the target tag, for example `Fedora-Minimal`

# TODO

- patch koji to accept zst (docs/schema.sql, archivetypes table + migration?)

## Test

## Unit

The unittests mock out the majority of `koji`-provied classes and run quickly, you can run them with:

```console
$ pytest test/unit
# ...
```

## Integration

These tests set up a full containerized `koji` environment and does image builds in it. `sudo` is required for this. The tests take long, especially if the containers need to be built. The following does a quick smoke test by setting up the entire environment and doing a build from the command line.

```console
$ python3 run.py test
# ...
```

Leaving out the `test` argument lets you run a local koji environment to interact with.
