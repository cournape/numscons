PREFIX=$PWD
TESTINSTALL=$PREFIX/tmp/lib/python2.5/site-packages
rm -rf $PREFIX/build
rm -rf $PREFIX/tmp
PYTHONPATH=$HOME/local/lib/python2.5/site-packages python setup.py scons install --prefix=$PREFIX/tmp
echo "====== TESTING BUILT EXTENSIONS .... ========"
(cd $PREFIX/tmp && nosetests -w $TESTINSTALL -v numsconstests)
