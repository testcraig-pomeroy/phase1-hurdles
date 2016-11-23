#!/bin/bash

REPOSITORY_URL="https://github.com/SpectrumCollaborationChallenge/phase1-hurdles.git"

LXC_NAME=hurdle1_scoring_trusty_lxc
SOLUTION_NAME=hurdle1_solution_trusty_lxc
LXC_PREFIX="$(pwd)"/lxc
LXC_ATTACH_CMD="lxc-attach -P $LXC_PREFIX -n $LXC_NAME --"

echo "Creating LXC Container"
lxc-create -P "$LXC_PREFIX" -t download -n "$LXC_NAME" -- -d ubuntu -r trusty -a amd64

echo "Starting LXC Container"
lxc-start -P "$LXC_PREFIX" -n "$LXC_NAME"

# check that the container has finished booting
result="$($LXC_ATTACH_CMD runlevel)"
while [ "$result" !=  "N 2" ] # trusty default runlevel is 2
  do
    echo "Waiting for container to boot, currently at init level: $result"
    sleep 1
    result="$($LXC_ATTACH_CMD runlevel)"
  done

echo "Container Started"

# speed up updates
MIRRORS="deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-security main restricted universe multiverse
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-backports main restricted universe multiverse
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-updates main restricted universe multiverse
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty main restricted universe multiverse"

# prepend mirrors to sources.list
while read -r line; do
    $LXC_ATTACH_CMD sed -i '1i '"$line" /etc/apt/sources.list
done <<< "$MIRRORS"


# update container packages
$LXC_ATTACH_CMD apt-get update

# workaround for procps upgrade
$LXC_ATTACH_CMD dpkg-divert --local --rename --add /sbin/initctl
$LXC_ATTACH_CMD ln -s /bin/true /sbin/initctl
$LXC_ATTACH_CMD apt-get install procps
# revert workaround after upgrade complete
$LXC_ATTACH_CMD rm /sbin/initctl
$LXC_ATTACH_CMD dpkg-divert --local --rename --remove /sbin/initctl

$LXC_ATTACH_CMD apt-get upgrade -y
$LXC_ATTACH_CMD apt-get install -y openssh-server python2.7 python-pip python-dev git swig
$LXC_ATTACH_CMD pip install --upgrade pip

# install other hurdle 1 dependencies
$LXC_ATTACH_CMD pip install jupyter numpy

# install gnuradio
$LXC_ATTACH_CMD pip install PyBOMBS
$LXC_ATTACH_CMD pybombs recipes add gr-recipes git+https://github.com/gnuradio/gr-recipes.git  
$LXC_ATTACH_CMD pybombs recipes add gr-etcetera git+https://github.com/gnuradio/gr-etcetera.git
$LXC_ATTACH_CMD pybombs config keep_builddir False
$LXC_ATTACH_CMD pybombs prefix init /usr/local -a sys -R gnuradio-default

# clean out old apt files
$LXC_ATTACH_CMD apt-get clean

# add an sc2 user and change password to sc2
$LXC_ATTACH_CMD adduser --disabled-password --gecos "" sc2

# this is the output of "mkpasswd -m sha-256" with password sc2 
PASS_HASH='$5$mJaFsBOiPKkWoD0$otbJtAsJI10meMi69HrBIeAyl0HjFutg6xSE7xfvpt5'
$LXC_ATTACH_CMD usermod -p "$PASS_HASH" sc2

# add to sudoers
$LXC_ATTACH_CMD usermod -aG sudo sc2

# clear out build files to shrink image size
$LXC_ATTACH_CMD rm -rf /usr/local/src/gnuradio/build
$LXC_ATTACH_CMD rm -rf /usr/local/src/uhd/host/build


# clone hurdle repository into container
$LXC_ATTACH_CMD git clone "$REPOSITORY_URL" /home/sc2/phase1-hurdles

# build hurdle 1 support code
$LXC_ATTACH_CMD bash -c 'mkdir /home/sc2/phase1-hurdles/hurdle1/gr-hurdle1/build && cd /home/sc2/phase1-hurdles/hurdle1/gr-hurdle1/build && cmake ../ && make && make install'
$LXC_ATTACH_CMD ldconfig

# change owner to sc2 user
$LXC_ATTACH_CMD chown -R sc2 /home/sc2/phase1-hurdles
$LXC_ATTACH_CMD chgrp -R sc2 /home/sc2/phase1-hurdles


# make clone for example solution
lxc-stop -P "$LXC_PREFIX" -n $LXC_NAME
lxc-copy -P "$LXC_PREFIX" -n $LXC_NAME -N $SOLUTION_NAME

# make metadata.yaml file for example solution
creation_date=`date +%s`

cat >"$LXC_PREFIX"/metadata.yaml <<EOL
architecture: "amd64"
creation_date: ${creation_date}
EOL
