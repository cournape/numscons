PREFIX=$PWD
VERSION=`python -c "import sys; print '.'.join([str(i) for i in sys.version_info[:2]])"`
TESTINSTALL=$PREFIX/tmp/lib/python$VERSION/site-packages
rm -rf $PREFIX/build
rm -rf $PREFIX/tmp
PYTHONPATH=$HOME/local/lib/python$VERSION/site-packages python setup.py scons install --prefix=$PREFIX/tmp
echo "====== TESTING BUILT EXTENSIONS .... ========"
(cd $PREFIX/tmp && nosetests -w $TESTINSTALL -v numsconstests)
