from numscons.checkers.new.perflib_checkers import \
        _check_perflib
from numscons.checkers.new.common import \
        get_perflib_names, get_initialized_perflib_config, \
        save_and_set, restore, set_checker_result
from numscons.checkers.fortran import CheckF77Mangling

__all__ = ['CheckF77Lapack', 'CheckF77Blas', 'CheckCblas']

# Test for sgesv
_LAPACK_TEST_CODE = r"""\
int %(func)s(int *n, int *nrhs, float a[], int *lda, int ipiv[], 
                  float b[], int *ldb, int *info);

int compare(float A[], float B[], int sz)
{
        int i;

        for(i = 0; i < sz; ++i) {
                if ( (A[i] - B[i] > 0.01) || (A[i] - B[i] < -0.01)) {
                        return -1;
                }
        }
        return 0;
}

int main(void)
{
    int n = 2;
    int nrhs = 2;
    int lda = 2;
    float A[] = { 1, 3, 2, 4};

    int ldb = 2;
    float B[] = { 1, 0, 0, 1};
    float X[] = { -2, 1.5, 1, -0.5};

    int ipov[] = {0, 0};
    int info;

    /* Compute X in A * X = B */
    %(func)s(&n, &nrhs, A, &lda, ipov, B, &ldb, &info);

    return compare(B, X, 4);
}
"""

# Test for sgemm
_BLAS_TEST_CODE = r"""\
#include <stdio.h>

int
main (void)
{
    char transa = 'N', transb = 'N';
    int lda = 2;
    int ldb = 3;
    int n = 2, m = 2, k = 3;
    float alpha = 1.0, beta = 0.0;

    float A[] = {1, 4,
		 2, 5,
		 3, 6};

    float B[] = {1, 3, 5,
	         2, 4, 6}; 
    int ldc = 2;
    float C[] = { 0.00, 0.00,
                 0.00, 0.00 };

    /* Compute C = A B */
    %(func)s(&transa, &transb, &n, &m, &k,
          &alpha, A, &lda, B, &ldb, &beta, C, &ldc);

    printf("C = {%%f, %%f; %%f, %%f}\n", C[0], C[2], C[1], C[3]);
    return 0;  
}
"""

# Test for CBLAS
_CBLAS_TEST_CODE = r"""\
enum CBLAS_ORDER {CblasRowMajor=101, CblasColMajor=102};
enum CBLAS_TRANSPOSE {CblasNoTrans=111, CblasTrans=112, CblasConjTrans=113};

void cblas_sgemm(const enum CBLAS_ORDER Order, const enum CBLAS_TRANSPOSE TransA,
                 const enum CBLAS_TRANSPOSE TransB, const int M, const int N,
                 const int K, const float alpha, const float *A,
                 const int lda, const float *B, const int ldb,
                 const float beta, float *C, const int ldc);
int
main (void)
{
    int lda = 3;
    float A[] = {1, 2, 3,
                 4, 5, 6};

    int ldb = 2;
    float B[] = {1, 2, 
	         3, 4,
		 5, 6};

    int ldc = 2;
    float C[] = { 0.00, 0.00,
                 0.00, 0.00 };

    /* Compute C = A B */
    cblas_sgemm (CblasRowMajor, 
                CblasNoTrans, CblasNoTrans, 2, 2, 3,
                1.0, A, lda, B, ldb, 0.0, C, ldc);

    return 0;  
}
"""

def _check_fortran(context, name, autoadd, test_code_tpl, func):
    # Generate test code using name mangler
    try:
        mangler = context.env['F77_NAME_MANGLER']
    except KeyError:
        if not CheckF77Mangling(context):
            return 0
        mangler = context.env['F77_NAME_MANGLER']
    test_code = test_code_tpl % {'func': mangler(func)}

    # Detect which performance library to use
    info = None
    for perflib in get_perflib_names(context.env):
        _info = get_initialized_perflib_config(context.env, perflib)
        if  name in _info.interfaces() and _check_perflib(context, 0, _info):
            info = _info
            break

    context.Message("Checking for F77 %s ... " % name)

    if info is None:
        context.Result('no')
        return 0

    if not name in info.interfaces():
        raise RuntimeError("%s does not support %s interface" % \
                (info.__class__, name))

    saved = save_and_set(context.env, info._interfaces[name],
                info._interfaces[name].keys())
    ret = context.TryLink(test_code, extension='.c')
    if not ret or not autoadd:
        restore(context.env, saved)
    if not ret:
        context.Result('no')
    context.Result('yes - %s' % info.name)
    set_checker_result(context.env, name, info)
    return ret

def _check_c(context, name, autoadd, test_code):
    # Detect which performance library to use
    info = None
    for perflib in get_perflib_names(context.env):
        _info = get_initialized_perflib_config(context.env, perflib)
        if  name in _info.interfaces() and _check_perflib(context, 0, _info):
            info = _info
            break

    context.Message("Checking for %s ... " % name.upper())

    if info is None:
        context.Result('no')
        return 0

    if not name in info.interfaces():
        raise RuntimeError("%s does not support %s interface" % \
                (info.__class__, name.upper()))

    saved = save_and_set(context.env, info._interfaces[name],
                info._interfaces[name].keys())
    ret = context.TryLink(test_code, extension='.c')
    if not ret or not autoadd:
        restore(context.env, saved)
    if not ret:
        context.Result('no')
    context.Result('yes - %s' % info.name)
    return ret

def CheckF77Lapack(context, autoadd=1, check_version=0):
    return _check_fortran(context, 'LAPACK', autoadd, _LAPACK_TEST_CODE,
            'sgesv')

def CheckF77Blas(context, autoadd=1, check_version=0):
    return _check_fortran(context, 'BLAS', autoadd, _BLAS_TEST_CODE, 'sgemm')

def CheckCblas(context, autoadd=1, check_version=0):
    return _check_c(context, 'CBLAS', autoadd, _CBLAS_TEST_CODE)
