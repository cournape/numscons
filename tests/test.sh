PREFIX=$PWD
rm -rf $PREFIX/build
rm -rf $PREFIX/tmp
python setup.py scons install --prefix=$PREFIX/tmp
(cd $PREFIX/tmp && PYTHONPATH=$PREFIX/tmp/lib/python2.5/site-packages:$PYTHONPATH nosetests $PREFIX)
