#! /bin/bash

# Build script for building Pyrex extensions and copying
# it to HarvestMan source folder.

src="../HarvestMan"
extn=".py"
old=".old"
soextn=".so"

function lastindex()
{
myidx=0
str=$1
idx=1
while [ $idx != "0" ]
do
  l=`expr length $str`
  idx=`expr index $str $2`
  myidx=`expr $myidx + $idx`
  str=`expr substr $str $[$idx+1] $l`
done
echo $myidx
}

function froot()
{
# Return the root filename (filename minus extension)
idx=`lastindex $1 .`
root=`expr substr $1 1 $[$idx-1]`
echo $root
}

function build()
{
    for i in *.pyx
    do
      export MODULE=`froot $i`
      ./setup.sh
    done
}

function backup_py_files()
{
    for i in *.pyx
    do
      fname = `froot $i`
      mv $src/$fname$extn $src/$fname$extn$old
      rm -rf $src$extn*
    done
}

function copy_extensions()
{
    for i in *.pyx
    do
      fname=`froot $i`
      sofile=$fname$soextn
      cp $sofile $src
    done
}
    
build
backup_py_files
copy_extensions
echo "Done."

