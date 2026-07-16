# Gunicorn configuration for LEPS on Render free tier.
#
# workers=1
#   Render free tier has 512MB RAM. Each worker loads its own copy of the
#   ML model into memory; more than one worker risks exhausting RAM and
#   triggering a SIGKILL.
#
# preload_app=False
#   scikit-learn and XGBoost link OpenBLAS/OpenMP, which spin up native
#   thread pools when the model loads. Loading the model in the master
#   process before fork (preload_app=True) can leave a forked worker with
#   inherited locks that any later threading.Thread() in that worker can
#   deadlock on. Loading fresh inside the worker after fork avoids this.
#   With a single worker there's no copy-on-write benefit to preloading,
#   so there's no tradeoff in leaving it off.
preload_app = False
worker_class = 'sync'
bind = '0.0.0.0:10000'
accesslog = '-'
errorlog = '-'
loglevel = 'info'
