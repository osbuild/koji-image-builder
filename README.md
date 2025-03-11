# koji-image-builder

> [!WARNING]  
> This is a work-in-progress repository. There is no CI, nor is there any guarantees. Work can be pushed directly to main. We hope to transition out of this soon.

This project provides [`image-builder`](https://github.com/osbuild/image-builder-cli) integration with [Koji](https://pagure.io/koji). `image-builder` is a tool that builds images (as the name says).

## koji configuration

To use `koji-image-builder` you need the following things in your `koji` instance:

1. Create the `image-builder-build` group which contains `image-builder` and `distribution-gpg-keys`.
2. Create `fXX-image-builder-build` tags, which contain the `image-builder-build` group and have `mock.set_new_chroot` set to `0`.
3. Create `fXX-image-builder` targets, which use the `fXX-image-builder-build` tags as their build tag and the `fXX` tag as their target.

After this you can enable the `image_builder` plugin in your hub, and builder configuration files.
