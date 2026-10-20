#!/usr/bin/env bash
# Run INSIDE WSL (Ubuntu 22.04) without root. Installs a user-space C/C++ toolchain with micromamba (conda-forge) into ~/opp-toolchain
# and builds a headless OMNeT++ 6.0.3 (no Qt/IDE/OSG) into ~/omnetpp-6.0.3. Everything lives in the WSL home; delete both folders to remove.
set -ex
cd ~
if [ ! -x ~/bin/micromamba ]; then
  mkdir -p ~/bin
  curl -fsSL -o ~/bin/micromamba https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
  chmod +x ~/bin/micromamba
fi
export MAMBA_ROOT_PREFIX=~/mamba-root
if [ ! -d ~/opp-toolchain ]; then
  ~/bin/micromamba create -y -p ~/opp-toolchain -c conda-forge gxx_linux-64 gcc_linux-64 make bison flex perl python=3.11 libxml2 zlib pkg-config sysroot_linux-64
fi
export PATH=~/opp-toolchain/bin:$PATH
~/bin/micromamba install -y -p ~/opp-toolchain -c conda-forge numpy scipy pandas matplotlib posix_ipc
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-gcc ~/opp-toolchain/bin/gcc
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-g++ ~/opp-toolchain/bin/g++
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-gcc ~/opp-toolchain/bin/cc
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-g++ ~/opp-toolchain/bin/c++
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-ar ~/opp-toolchain/bin/ar 2>/dev/null || true
ln -sf ~/opp-toolchain/bin/x86_64-conda-linux-gnu-ld ~/opp-toolchain/bin/ld 2>/dev/null || true
gcc --version | head -1; g++ --version | head -1; make --version | head -1; bison --version | head -1; flex --version
V=6.0.3
[ -d omnetpp-$V ] || tar xzf omnetpp-$V-linux-x86_64.tgz
cd omnetpp-$V
. ./setenv
export PATH=~/opp-toolchain/bin:$PATH
./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no WITH_LIBXML=no WITH_PYTHON=no
make clean MODE=release || true
make -j12 MODE=release base
echo BUILD_DONE
opp_run -v | head -3
