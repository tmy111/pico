# 支持通过 python -m pico 启动命令行程序。
from .cli import main


# 把 cli.main() 的返回值作为进程退出码交给系统。
if __name__ == "__main__":
    raise SystemExit(main())
