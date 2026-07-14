# Gunicorn configuration for LEPS on Render free tier.
#
# Why these settings:
#
# workers=1
#   Render free tier has 512MB RAM. The ML model (RandomForest/XGBoost) is
#   loaded into memory per worker. Multiple workers each load their own copy,
#   exhausting RAM and causing SIGKILL. One worker avoids this.
#
# preload_app is intentionally OFF.
#
# scikit-learn and XGBoost link OpenBLAS/OpenMP, which spin up native thread
# pools the moment the model is loaded via joblib.load(). With preload_app=True,
# that loading happens in the gunicorn master process BEFORE it forks the
# worker. Forking a process that already has live BLAS thread pools is a
# known deadlock hazard: the child worker inherits mutexes with no owning
# thread, and the first threading.Thread() created in that worker can hang
# forever. This was the actual cause of admin status updates hanging.
#
# With preload_app off, the model loads fresh inside the worker AFTER fork,
# so no thread state is inherited and no deadlock risk exists. Since we run
# a single worker anyway, preload_app's copy-on-write memory benefit (which
# only matters with multiple workers) does not apply here — there is no
# downside to leaving it off.
preload_app = False
worker_class = 'sync'
bind = '0.0.0.0:10000'
accesslog = '-'
errorlog = '-'
loglevel = 'info'
