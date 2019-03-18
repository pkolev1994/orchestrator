#!/bin/bash
dir=`pwd`
component='ocorchestrator'
version=$(grep "Version:" $component.spec | cut -d ':' -f 2 | tr -d ' ' | uniq)
gitcommit=`git show --summary | grep commit`

sed -i -e "s/^GIT commit/GIT $gitcommit/" $component.spec

mkdir /tmp/$component-$version
( cat $component.spec | grep -B 10000  ^%changelog; /usr/bin/perl changelog.pl) > $component.spec.tmp
mv -f $component.spec.tmp $component.spec
cp -fr * /tmp/$component-$version/
tar -C /tmp --exclude='.svn' --exclude='.git*' --exclude=$component-$version.tar.gz --exclude='changelog.pl' --exclude='gen_tarball.sh' --exclude=$component.spec -zcvf $component-$version.tar.gz $component-$version/
rm -rf /tmp/$component-$version
