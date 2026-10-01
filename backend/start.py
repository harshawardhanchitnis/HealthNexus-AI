"""Portable local/container entrypoint; Cloud Run supplies PORT."""
import os
# Set native thread/allocator bounds before NumPy/scikit-learn imports. Model
# parameters, prediction arithmetic and 500-path risk sampling are unchanged.
if os.getenv('HEALTHNEXUS_LOW_MEMORY', 'false').lower() == 'true':
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
import uvicorn

if __name__ == '__main__':
    uvicorn.run('app.main:app',host='0.0.0.0',port=int(os.getenv('PORT','8000')),workers=1)
