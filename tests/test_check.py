r"""pcolor 自动化检查器：逐项断言颜色，有 bug 直接报 FAIL，不用肉眼。

运行：
    & C:\Users\87936\.conda\envs\PYTHON_DL\python.exe C:\Users\87936\Desktop\dl_case\pcolor_check.py
结果看最后一行：ALL PASS (N 项)  /  has FAIL (M 项)
"""
import builtins
import io
import sys
from collections import Counter, deque
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from fractions import Fraction

import numpy as np
import torch

sys.path.insert(0, r"C:\Users\87936\Desktop\dl_case\pcolor")   # 确保用本地源码 v0.3.0
import pcolor
from pcolor import _highlight_str, _render, _style_for, c, clear_style_attr, set_style_attr

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def has(code, s):
    return f"\x1b[{code}m" in s


# 期望的颜色码（256 色号）
C = {
    "tensor": "38;5;175", "size": "38;5;73", "dtype": "38;5;178", "torch_other": "38;5;110",
    "ndarray": "38;5;67", "np_scalar": "38;5;150", "tf": "38;5;75", "ml_other": "38;5;102",
    "pandas": "38;5;140", "sklearn": "38;5;146", "int": "38;5;71", "float": "38;5;151",
    "complex": "38;5;62", "bool": "38;5;66", "none": "38;5;245", "str": "38;5;173",
    "bytes": "38;5;180", "list": "38;5;139", "tuple": "38;5;95", "dict": "38;5;133",
    "set": "38;5;131", "range": "38;5;108", "datetime": "38;5;137", "enum": "38;5;102",
    "default": "38;5;145",
    "cyan": "38;5;73", "red": "38;5;167", "green": "38;5;71", "yellow": "38;5;178",
    "blue": "38;5;67", "magenta": "38;5;175", "white": "38;5;252", "grey": "38;5;245",
}


class Color(Enum):
    RED = auto()
    BLUE = auto()


t0 = torch.tensor(5.0)
t1 = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
m = torch.nn.Linear(2, 3)


# ---------- A. 类型 -> 样式键 ----------
for obj, key, label in [
    (t1, "tensor", "Tensor"), (t1.shape, "size", "Size"), (t1.dtype, "dtype", "dtype"),
    (t1.device, "torch_other", "device"), (m, "torch_other", "Linear"),
    (torch.nn.Parameter(torch.zeros(1)), "tensor", "Parameter"),
    (np.array([1, 2]), "ndarray", "ndarray"), (np.float32(1.5), "np_scalar", "np标量"),
    (42, "int", "int"), (3.14, "float", "float"), (2 + 3j, "complex", "complex"),
    (True, "bool", "bool"), (None, "none", "None"), ("hi", "str", "str"),
    (b"b", "bytes", "bytes"), ([1], "list", "list"), ((1,), "tuple", "tuple"),
    ({"a": 1}, "dict", "dict"), ({1}, "set", "set"), (range(3), "range", "range"),
    (Decimal("1.5"), "float", "Decimal"), (Fraction(1, 3), "float", "Fraction"),
    (datetime(2025, 1, 1), "datetime", "datetime"), (Color.RED, "enum", "Enum"),
    (deque([1]), "list", "deque"), (Counter("aa"), "dict", "Counter"),
]:
    got = _style_for(obj)
    check(f"A {label} -> {key}", got == key, f"got={got!r}")


# ---------- B. 渲染含正确 ANSI 码 ----------
r = _render(t1, t1.shape, t1.dtype, m, 42, 3.14, True, None, "hi", [1], (1,), {"a": 1}, {1})
expects = [("tensor", "tensor"), ("size", "size"), ("dtype", "dtype"), ("torch_other", "torch_other"),
           ("int", "int"), ("float", "float"), ("bool", "bool"), ("none", "none"),
           ("str", "str"), ("list", "list"), ("tuple", "tuple"), ("dict", "dict"), ("set", "set")]
for key, label in expects:
    check(f"B render 含{label}色", has(C[key], r))

# ---------- C. 字符串内部识别 ----------
s = "sc={1e-5}, hex={0xFF}, nan={nan}, inf={inf}, neg={-42}, b={True}, n={None}, " \
    "d={torch.float32}, sz={torch.Size([2, 3])}, t={tensor([1., 2.])}, a={array([[1,2]])}"
h = _highlight_str(s)
for key, label in [
    ("int", "科学计数/hex/负数"), ("float", "nan/inf"), ("bool", "True/False"),
    ("none", "None"), ("dtype", "torch.float32"), ("size", "torch.Size"),
    ("tensor", "tensor("), ("ndarray", "array("), ("str", "底色文字"),
]:
    check(f"C 字符串识别[{label}]", has(C[key], h))

# 跨行 tensor 整体上色（不因换行中断）
h2 = _highlight_str(f"t={torch.tensor([[1., 2., 3.], [4., 5., 6.]])}")
check("C 跨行 tensor 整块色", has(C["tensor"], h2) and h2.count(f"\x1b[{C['tensor']}m") == 1)


# ---------- D. 端到端：接管后的 print（模拟 TTY） ----------
class TTY(io.StringIO):
    def isatty(self):
        return True


def capture_tty(fn):
    old, fake = sys.stdout, TTY()
    sys.stdout = fake
    try:
        fn()
    finally:
        sys.stdout = old
    return fake.getvalue()


check("D 导入即接管", builtins.print.__module__ == "pcolor")

out = capture_tty(lambda: builtins.print(f"a {t1.shape} {t1.dtype} {t1}"))
check("D print 自动上色", has(C["size"], out) and has(C["dtype"], out) and has(C["tensor"], out))

pcolor.disable()
out2 = capture_tty(lambda: builtins.print("plain text"))
check("D disable 后无色", "\x1b[" not in out2)
pcolor.enable()
out3 = capture_tty(lambda: builtins.print("again"))
check("D enable 后恢复色", has(C["str"], out3))

# 非 TTY（管道/重定向）应走原生 print、无色不报错
buf = io.StringIO()
old = sys.stdout
sys.stdout = buf
try:
    builtins.print(t1)
finally:
    sys.stdout = old
check("D 非TTY 无色不报错", "\x1b[" not in buf.getvalue() and "tensor" in buf.getvalue())

buf2 = io.StringIO()
builtins.print(t1, file=buf2)          # file= 路径不应报错
check("D file= 写入正常", "tensor" in buf2.getvalue())


# ---------- E. 字体属性 ----------
sx = c("x", "bold underline cyan")
check("E bold+underline+cyan", has("1", sx) and has("4", sx) and has(C["cyan"], sx))
set_style_attr("tensor", "bold")
r_bold = _render(t1)
check("E set_style_attr 生效", has("1", r_bold))
clear_style_attr("tensor")
r_clear = _render(t1)
check("E clear_style_attr 恢复", not has("1", r_clear))


# ---------- F. 100% 覆盖：任何对象都有颜色 ----------
class MyDataclass:
    def __init__(self, x=1):
        self.x = x


class FakePeft:
    pass


FakePeft.__module__ = "peft.models"          # 模拟 peft 库对象
FakeVllm = type("FakeVllm", (), {}); FakeVllm.__module__ = "vllm.engine"


class FakeUnknownLib:
    pass


FakeUnknownLib.__module__ = "requests"        # 非 AI 库（如 requests）

check("F 自定义 dataclass 兜底色", _style_for(MyDataclass()) == "default")
check("F peft 命中 ml_other", _style_for(FakePeft()) == "ml_other")
check("F vllm 命中 ml_other", _style_for(FakeVllm()) == "ml_other")
check("F 非AI库也有颜色(requests)", _style_for(FakeUnknownLib()) == "default")
check("F 100% 无无色对象", has(C["default"], _render(MyDataclass(), FakeUnknownLib())))

# ---------- G. register / unregister 运行时扩展 ----------
pcolor.register("requests", "dtype")          # 注册：请求对象→土黄
check("G register 生效", _style_for(FakeUnknownLib()) == "dtype")
pcolor.unregister("requests")
check("G unregister 恢复", _style_for(FakeUnknownLib()) == "default")
try:
    pcolor.register("x", "not_a_style")
    check("G 非法样式名报错", False)
except ValueError:
    check("G 非法样式名报错", True)


# ---------- H. 自定义 torch 子类（如 class Model(nn.Module) 定义在 __main__） ----------
class MyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = torch.nn.Linear(2, 2)


class NotTorchClass:
    pass


check("H 自定义 nn.Module 子类 -> torch_other", _style_for(MyModel()) == "torch_other")
check("H 普通自定义类 -> 兜底 default", _style_for(NotTorchClass()) == "default")

# ---------- I. 常见 ML 库关键词（fasttext 等） ----------
FakeFastText = type("FakeFastText", (), {})
FakeFastText.__module__ = "fasttext.FastText"
check("I fasttext.FastText -> ml_other", _style_for(FakeFastText()) == "ml_other")
FakeFastText2 = type("FakeFastText2", (), {})
FakeFastText2.__module__ = "fasttext"
check("I fasttext -> ml_other", _style_for(FakeFastText2()) == "ml_other")


# ---------- 汇总 ----------
fails = [x for x in RESULTS if not x[1]]
print(f"\n===== pcolor automated check: {len(RESULTS)} checks, PASS {len(RESULTS) - len(fails)}, FAIL {len(fails)} =====")
for name, ok, detail in RESULTS:
    print(f"  [{'OK  ' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
sys.exit(0 if not fails else 1)
