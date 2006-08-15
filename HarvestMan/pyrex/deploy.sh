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
      fname=`froot $i`
      source=$src/$fname$extn
      echo "Backing up $source..."
      mv $source $src/$fname$extn$old
      rm -rf $src$extn*
    done
}

function copy_extensions()
{
    for i in *.pyx
    do
      fname=`froot $i`
      sofile=$fname$soextn
      echo "Copying extension $sofile..."
      cp $sofile $src
    done
}

function remove_extensions()
{
   for i in *.pyx
    do
      fname=`froot $i`
      sofile=$fname$soextn
      if [ -f $src/$sofile ]; 
          then
          echo "Removing extension $src/$sofile..."
          rm -rf $src/$sofile
          fi
          
    done

}

function restore_py_files()
{
    for i in *.pyx
      do
      fname=`froot $i`
      oldpy=$src/$fname$extn$old
      if [ -f $oldpy ]
          then
          echo "Restoring file $src/$fname$extn..."
          cp $oldpy $src/$fname$extn
          rm -rf $oldpy
          fi
      done
}

function clean_up()
{
    echo "Cleaning up cwd..."
    rm -rf *.so
    rm -rf *.c
}

function deploy()
{    
    build
    backup_py_files
    copy_extensions
    echo "Done."
}

function undeploy()
{
    remove_extensions
    restore_py_files
    clean_up
    echo "Done."
}

function usage()
{
    echo "Usage: $0 options"
    echo
    echo "[options]"
    echo "    --deploy      Build and deploy Pyrex extensions"
    echo "    --undeploy    Remove and undeploy Pyrex extensions"
}

function dowork()
{
    case $1 in
        "--deploy") deploy;;
        "--undeploy") undeploy;;
    esac
}

case $# in
0) usage; exit 2;;
1) dowork $1;;
esac

