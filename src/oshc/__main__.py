"""支持 ``python -m oshc`` 调用。"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
