# koji-image-builder

This project provides [`image-builder`](https://github.com/osbuild/image-builder-cli) integration with [Koji](https://pagure.io/koji). `image-builder` is a tool that builds images (as the name says).

## Installation

To use `koji-image-builder` you'll need to install the relevant plugin package for each corresponding service.

### Builder

Install `koji-image-builder-builder` on your builders (the machines that run `kojid`). After installation enable the service by adding to, or updating its configuration file at `/etc/kojid/kojid.conf`.

```
plugins = image_builder
```

### Hub

Install `koji-image-builder-hub` on your hub. After installation enable the service by adding to, or updating its configuration file at `/etc/koji-hub/hub.conf`.

```
Plugins = image_builder
```

## Configuration

Once you have installed the plugins you can proceed to configuring your instance. The below should be adapted to your own tag and target setup. This example is based on Fedora's setup.

1. Create an `image-builder-build` group which contains `image-builder` and `distribution-gpg-keys`.
2. Create `fXX-image-builder-build` tags, which contain the `image-builder-build` group and have `mock.new_chroot` set to `0`.
3. Create `fXX-image-builder` targets, which use the `fXX-image-builder-build` tags as their build tag and the `fXX` tag as their target.
4. Add the `image-builder-build` group to your build tag.
4. Create packages for the things you want to build in the target tag, for example `Fedora-Minimal`

## Usage

On a machine that has access to your koji instance in the `image` channel (or is an `admin`) install `koji-image-builder` which will provide the command line plugin. You can then perform a build with the following command, provided you adjust the values to how you configured your tags, targets, and package names.

```console
$ koji image-builder-build --repo "https://some/compose/repo" fedora-42 Fedora-Minimal 42 minimal-raw
# ... output ...
```

The values mean the following:

```console
$ koji image-builder-build --repo "Repository used to source packages from for the build" $distribution $package-to-store-build $package-version $imagetype
# ... output ...
```


More options are listed under the `--help` argument:

```
$ koji image-builder-build --help
# ... output ...
```

## Test

### Unit

The unittests mock out the majority of `koji`-provied classes and run quickly, you can run them with:

```console
$ pytest test/unit
# ...
```

### Integration

These tests set up a full containerized `koji` environment and does image builds in it. `sudo` is required for this. The tests take long, especially if the containers need to be built. The following does a quick smoke test by setting up the entire environment and doing a build from the command line.

```console
$ sudo python3 run.py test
# ...
```

Leaving out the `test` argument lets you run a local koji environment to interact with.
