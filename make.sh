#!/bin/bash

set -euxo pipefail

# Latest jar from https://projects.eclipse.org/projects/technology.lemminx
wget https://mirrors.dotsrc.org/eclipse//lemminx/releases/0.27.0/org.eclipse.lemminx-uber.jar

# Turn it into a statically linked native image binary
docker run \
    --rm \
    -v"$(pwd):/app" \
    container-registry.oracle.com/graalvm/native-image:21-muslib \
    -jar org.eclipse.lemminx-uber.jar \
    --static \
    --libc=musl

# Now there will be a file org.eclipse.lemminx-uber
file org.eclipse.lemminx-uber

# Build the container image
docker buildx build -t test --load .

# invoke like this
docker run --rm -it -v "$(pwd):/src" --workdir /src test Format.xml
