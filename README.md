# pcolor

智能彩色打印库（纯标准库，**零第三方依赖**）。256 色 ANSI（低饱和护眼色，Gruvbox/Solarized 风格），VS Code / Windows Terminal 支持。

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Coverage](https://img.shields.io/badge/Types_covered-100%25-orange)
![Deps](https://img.shields.io/badge/Zero_dependencies-yellowgreen)
![CI](https://github.com/drowsy111/pcolor/actions/workflows/ci.yml/badge.svg)

## 🖼 效果预览

<!--
  把终端彩色输出截图保存为 docs/demo.png 后，取消下面这行注释即可显示效果图
-->

<!-- ![demo](docs/demo.png) -->

```text
运行 demo：
  python tests/test_check.py      # 66 checks, PASS 66, FAIL 0
  import pcolor; print(t, t.shape, t.dtype)   # 一行导入，全部自动上色
```


> 名称含义：**p**rint + **color** = 彩色打印。
>
> ⚠️ 注意：`pcolor` 在 PyPI 上已被他人占用，所以**暂时不能发布到 PyPI**（`pip install pcolor` 会装到别人的包）；本地安装 / 发 wheel 文件不受影响。

## ✨ 功能一览

- **导入即生效**：`import pcolor` 一行，之后所有 `print()` 自动按类型/模式上色。
- **100% 覆盖**：内置 60+ AI 大模型生态关键词（peft/vllm/deepspeed/tokenizers/pydantic/langchain/faiss/paddle…）；未识别的第三方/自定义对象**也有兜底色**，绝无色盲区；还有 `pcolor.register()` 运行时扩展。
- **智能识别**：字符串内部也能识别 `torch.Size(...)`、`torch.float32`、`tensor(...)`（含跨行）、`True/False`、`None`、数字。
- **全类型覆盖**：torch / numpy / pandas / sklearn + Python 所有基础类型（数字、容器、None 等），各配专属护眼色。
- **字体格式**：加粗、斜体、下划线、变淡、反色、删除线……可与颜色任意组合。
- **可扩展**：给某类型默认加字体属性、轻松添加新类型/新颜色。
- 只在终端输出上色，写文件/log 不受影响。

## 📥 安装

```bash
# 从包目录安装（推荐）
pip install C:\Users\Desktop\pcolor

# 升级到最新版
pip install --upgrade --force-reinstall C:\Users\Desktop\pcolor
```

> 如果你之前装过旧版 `pcol`，建议卸载以免互相干扰：
> ```bash
> pip uninstall pcol
> ```

## 🚀 快速开始

```python
import pcolor               # ← 只这一行，自动生效！

import torch
t1 = torch.tensor([[1., 2.], [3., 4.]])

print(f"t1.shape: {t1.shape}, t1.dtype: {t1.dtype}, t1: {t1}")
# torch.Size([2, 3]) = 柔和青，torch.float32 = 柔和黄，tensor(...) = 柔和粉，其余文字 = 柔橙
```

不需要 `pcolor.enable()`——**导入即自动接管 `print`**。想恢复原生 `print`：`pcolor.disable()`。

## 📖 使用方式

### 1. 自动接管 print（推荐）

```python
import pcolor

t1 = torch.tensor([[1., 2.], [3., 4.]])
print(t1, t1.shape, t1.dtype)              # 对象按类型上色
print(f"shape={t1.shape}, dtype={t1.dtype}")  # 字符串内部也识别上色
```

### 2. 显式调用

```python
from pcolor import pp, p, sho, c

pp(t1.shape, t1.dtype, t1, "hello", 3.14)  # 智能打印：每个参数按自身类型上色
p  == pp                                   # p 是 pp 的别名
sho(t1)                                    # 张量三属性分行打印
c("hello", "green")                        # 手动染一色（返回带颜色的字符串）
```

### 3. 字体格式（与颜色组合）

```python
from pcolor import c, set_style_attr, clear_style_attr

c("注意", "bold underline cyan")     # 加粗 + 下划线 + 青色
c("xx",  "dim strike red")           # 变淡 + 删除线 + 红色
c("标题", "bold yellow")             # 加粗 + 黄色

set_style_attr("tensor", "bold")     # 让 tensor 类型默认加粗（全局生效）
clear_style_attr("tensor")           # 清除某类型的字体属性
clear_style_attr()                   # 清除全部
```

可用属性：`bold` 加粗、`dim` 变淡、`italic` 斜体、`underline` 下划线、`reverse` 反色、`strike` 删除线、`blink` 闪烁、`hidden` 隐藏。

## 🎨 颜色规则（低饱和护眼色）

| 值类型 | 颜色（护眼柔和） | 例子 |
|---|---|---|
| `torch.Tensor` / `Parameter` | 柔和粉 | `tensor([1., 2.])` |
| `torch.Size` | 柔和青 | `torch.Size([2, 3])` |
| `torch.dtype` | 土黄 | `torch.float32` |
| 其它 torch（device / nn.Module…） | 浅蓝 | `cpu`、`Linear(...)` |
| `numpy.ndarray` | 深蓝 | `[1 2 3]` |
| numpy 标量 | 黄绿 | `np.float32(2.5)` |
| tensorflow / keras | 天蓝 | - |
| jax / onnx / scipy / transformers / datasets / PIL / cv2… | 灰紫 | - |
| pandas（DataFrame / Series） | 丁香紫 | - |
| sklearn（模型） | 淡薰衣草 | - |
| `int` | 柔绿 | `42` |
| `float` | 浅绿 | `3.14` |
| `complex` | 紫 | `(2+3j)` |
| `bool` | 暗青 | `True` |
| `None` | 灰 | `None` |
| `str`（无关字符串，统一） | **柔橙** | `"hello"` |
| `bytes` / `memoryview` | 茶色 | `b'bytes'` |
| `list` | 梅紫 | `[1, 2, 3]` |
| `tuple` | 暗梅紫 | `(1, 2)` |
| `dict` | 紫红 | `{'a': 1}` |
| `set` / `frozenset` | 深玫瑰 | `{1, 2}` |
| `range` | 橄榄 | `range(5)` |
| `Decimal` / `Fraction` | 浅绿 | - |
| `datetime` | 棕 | - |
| `Enum` | 灰紫 | - |
| `deque` / `Counter` 等容器 | 同 list / dict | - |
| 其它 torch | 浅蓝 | - |
| 其它对象（任意未识别模块/自定义类） | **默认灰（兜底，100% 覆盖）** | - |

字符串**内部识别**（f-string 打印场景）：`torch.Size(...)`、`torch.float32`、`tensor(...)`（含跨行）、`dtype=...`、`True/False`、`None`、**科学计数法（1e-5）**、**十六进制（0xFF）**、**nan / inf**、独立数字（含负数）；其余文字统一柔橙。

## 🔧 API 参考

| 函数 | 说明 |
|---|---|
| `pcolor.enable()` | 手动接管 `print`（导入时已自动调用，一般无需使用） |
| `pcolor.disable()` | 恢复原生 `print` |
| `pcolor.pp(*args)` / `pcolor.p(*args)` | 智能打印，每个参数按类型/模式上色 |
| `pcolor.sho(t, name="t")` | 张量三属性（shape/dtype/值）分行彩色打印 |
| `pcolor.c(text, style)` | 染字，返回带 ANSI 码的字符串；style 支持颜色+属性组合 |
| `pcolor.set_style_attr(name, *attrs)` | 给某类型默认加字体属性 |
| `pcolor.clear_style_attr(name=None)` | 清除字体属性设置 |
| `pcolor.register(模块关键词, style)` | 运行时注册新库：把含该关键词模块的对象染成指定颜色 |
| `pcolor.unregister(模块关键词=None)` | 取消注册 |

## 🛠 自定义与扩展

- **改颜色**：编辑 `pcolor/_STYLES`（`\033[38;5;Nm` 256 色码），或直接改某个类型的色号。
- **加新类型**：在 `pcolor/_style_for()` 里加一个 `isinstance` / 模块判断即可。
- **加字符串识别模式**：在 `pcolor/_PATTERNS` 里加一条 `(正则, 颜色名)`。

## ❓ 常见问题

- **重定向/写文件没有颜色？** 正常——只在终端（TTY）输出上色，写文件是纯文本。
- **`print` 行为被改变？** `import pcolor` 会接管 `print`（只对终端输出上色，其余行为与原版一致）；用 `pcolor.disable()` 可恢复。
- **与其它"接管 print"的库（如 icecream / sitecustomize）冲突？** 是——两套方案只能留一个，建议只留 pcolor。
- **终端显示不出颜色？** 需支持 256 色 ANSI（VS Code 集成终端、Windows Terminal 均支持）。
- **PyPI 上搜不到 pcolor？** 名字被他人占用，暂不上传；本地安装 / 发 `.whl` 文件不受影响。
