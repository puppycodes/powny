import sys
if not hasattr(sys, "exc_clear"):
    sys.exc_clear = (lambda: None)  # FIXME: Workaround for broken flask-0.11
