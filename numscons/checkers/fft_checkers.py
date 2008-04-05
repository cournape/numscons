#! /usr/bin/env python
# Last Change: Fri Mar 07 09:00 PM 2008 J

"""Module for fft checkers."""
from numscons.checkers.checker_factory import CheckerFactory

__all__ = ['CheckFFT']

FFT_PERFLIBS = {
        'default': ('MKL', 'FFTW3', 'FFTW2')}

def _fft_test_src(context):
    return 'int main() {return 0;}', 0

# Checkers
CheckFFT = CheckerFactory(FFT_PERFLIBS, 'fft', 'fft', 'FFT',
                          _fft_test_src)
