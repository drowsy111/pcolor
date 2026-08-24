r"""
pcolor 完整演示脚本（12 个场景，覆盖全部功能）

运行（clone 后免安装直接跑）：
    python examples/demo.py

说明：请在支持 256 色 ANSI 的终端（VS Code 集成终端 / Windows Terminal）里运行，
     逐节目测颜色；期望颜色见各节注释。数字/True/None 等字符串内也会被识别上色。
"""
import os
import sys
import time
from collections import Counter, deque
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from fractions import Fraction

import numpy as np
import torch

# 让 clone 后无需安装也能直接演示
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

import pcolor  # noqa: E402  # 导入即自动生效（位于 sys.path 引导之后）


class Color(Enum):
    RED = auto()
    GREEN = auto()


def sec(title):
    print("-" * 70)
    print(f"[{title}]")
    print("-" * 70)


# ========== 1. 基础：张量三属性（最常用场景） ==========
sec("1. 基础 f-string：tensor / Size / dtype")
print()
t0 = torch.tensor(5.0)                                  # 0 维
t1 = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])
t2 = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
for t in (t0, t1, t2):
    print(f"shape: {t.shape}, dtype: {t.dtype}, value: {t}")
# 期望：torch.Size 青、torch.float32 土黄、tensor(...) 粉（跨行也整块粉）、其余文字柔橙

# ========== 2. 字符串内部识别增强 ==========
sec("2. 字符串内部识别：科学计数/十六进制/nan/inf/dtype=/负数")
print()
print(f"科学计数: {1e-5} | 十六进制: {0xFF} | 负数: {-42} | 小数: {3.14}")
print(f"nan:{float('nan')} inf:{float('inf')} inf:{float('-inf')}")
print(f"bool:{True} / {False} | None:{None} | dtype={torch.float64}")
print(f"tensor: {torch.tensor([0.1, 0.2])}")
# 期望：1e-05 / 0xFF / -42 / 3.14 绿；nan / inf 浅绿；True/False 暗青；None 灰；dtype=.. 土黄

# ========== 3. Python 基础类型全覆盖 ==========
sec("3. Python 基础类型：int/float/complex/bool/str/bytes/list/tuple/dict/set/range")
print()
print(42, 3.14, 2 + 3j, True, "hello, py", b"bytes", [1, 2, 3], (1, 2), {"a": 1}, {1, 2}, range(5))
print("memoryview:", memoryview(b"abc"), "| frozenset:", frozenset([1, 2]))
# 期望：42 绿 / 3.14 浅绿 / (2+3j) 紫 / True 暗青 / "hello, py" 柔橙 / b'bytes' 茶色
#       [1,2,3] 梅紫 / (1,2) 暗梅紫 / {'a':1} 紫红 / {1,2} 深玫瑰 / range(5) 橄榄

# ========== 4. 扩充类型 ==========
sec("4. 扩充类型：Decimal/Fraction/datetime/Enum/deque/Counter")
print()
print(Decimal("3.14"), Fraction(1, 3), datetime(2025, 6, 1, 12, 30), Color.RED, deque([1, 2]), Counter("aabbcc"))  # noqa: DTZ001
# 期望：Decimal/Fraction 浅绿、datetime 棕、Color.RED 灰紫、deque 梅紫、Counter 紫红

# ========== 5. torch 深度学习对象全景 ==========
sec("5. torch 对象：Module/Parameter/device/梯度张量/切片")
print()
model = torch.nn.Linear(2, 3)
seq = torch.nn.Sequential(torch.nn.Linear(2, 4), torch.nn.ReLU(), torch.nn.Linear(4, 1))
param = torch.nn.Parameter(torch.zeros(2))
x = torch.randn(1, 2)
y = model(x)
loss = y.sum()
loss.requires_grad_(True)
print("model:", model, "\nseq:", seq)
print("param:", param, "| param.shape:", param.shape, "| param.dtype:", param.dtype, "| param.requires_grad:", param.requires_grad)
print("device:", x.device, "| grad_fn:", loss.grad_fn, "| is_cuda:", x.is_cuda)
print("tensor 切片:", torch.arange(12).reshape(3, 4)[:2, 1:3])
# 期望：model/seq 浅蓝、param 粉、Size 青、dtype 土黄、device/布尔 各自颜色

# ========== 6. numpy 对象 ==========
sec("6. numpy：ndarray / 标量 / bool_ / 带 dtype 的数组")
print()
print(np.array([[1, 2, 3], [4, 5, 6]]), np.float32(2.5), np.int64(7), np.bool_(True))
print(np.array([1.5, 2.5], dtype=np.float16), np.zeros((2, 2)))
print("np dtype in str:", f"arr={np.array([1, 2])} | 标量={np.float32(9.9)}")
# 期望：ndarray 深蓝、np 标量 黄绿、bool_ 暗青、array(...) 深蓝（含 dtype 整块）

# ========== 7. 混合大杂烩（一个 print 塞满） ==========
sec("7. 混合打印：不同类型混在一个 print / f-string")
print()
print(f"t={t2} shape={t2.shape} np={np.float32(1.1)} num={3.14} str={'ok'} b={True} none={None} mod={model}")
print(model.weight, model.bias, model.weight.shape, model.weight.dtype)

# ========== 8. 显式 API：pp / p / sho / c ==========
sec("8. 显式 API：pp / p / sho / c")
print()
from pcolor import pp, p, sho, c
pp(t2.shape, t2.dtype, t2, "hello", 3.14)
p(t2.shape, t2.dtype, t2)                              # p 是 pp 别名
sho(t2)                                                # 三属性分行
print(repr(c("手动染色", "bold underline cyan")))       # 返回带 ANSI 的字符串（repr 可见码）

# ========== 9. 字体属性 ==========
sec("9. 字体属性：组合 + set_style_attr")
print()
print(c("加粗+下划线+青色", "bold underline cyan"))
print(c("变淡+删除线+红色", "dim strike red"))
print(c("斜体+土黄", "italic yellow"))
pcolor.set_style_attr("tensor", "bold")
print(f"tensor 加了 bold: {t0}")                        # tensor(5.) 应为粉+加粗
pcolor.clear_style_attr("tensor")
print(f"tensor 恢复: {t0}")

# ========== 10. enable / disable 行为 ==========
sec("10. enable / disable")
print()
pcolor.disable()
print("disable 后: 这行应该没有颜色（纯白）")
pcolor.enable()
print("enable 后: 这行应该恢复柔橙")

# ========== 11. 边界与异常场景 ==========
sec("11. 边界场景：空字符串/None/嵌套/大张量")
print()
print("", None, "", [None, [1, 2], {"k": (3, 4)}], {"t": t1, "model": model})
print(torch.zeros(60))                                  # 多行大张量（观察是否整块上色）
s = "只看模式: tensor(1.2, dtype=torch.float32), numpy: array([1, 2]), 0x1F, 1e3"
print(s)

# ========== 12. 性能冒烟 ==========
sec("12. 性能：1000 次混合打印计时")
print()
start = time.perf_counter()
for _ in range(1000):
    print(f"row: {t1.shape} {t1.dtype} {t1} {np.float64(1.5)}", end="\r")
print("\n1000 次耗时（含终端渲染，仅供参考）:", round(time.perf_counter() - start, 3), "s")
print()
print("==== 全部执行完毕，请逐节检查颜色 ====")
