"""pcolor —— 智能彩色打印库（可 pip 安装，零第三方依赖）。

用法（一行即可）：
    import pcolor                     # 导入即自动生效！之后所有 print() 自动上色
    print(f"t1.shape: {t1.shape}")    # 字符串里的 torch.Size 也会被识别上色

    # 显式使用 / 手动：
    from pcolor import pp, sho, c
    pp(t1.shape, t1.dtype, t1, "hello", 3.14)
    sho(t1)
    c("hello", "str")

    # 运行时扩展（可选）：把新库的对象也染成指定颜色
    pcolor.register("peft", "ml_other")
    pcolor.unregister("peft")

字体属性（可跟颜色组合）：
    bold(加粗) dim(变淡) italic(斜体) underline(下划线)
    reverse(反色) strike(删除线) blink(闪烁) hidden(隐藏)
    例：c("hi", "bold underline cyan")
    给某类型默认加属性：set_style_attr("tensor", "bold", "underline")

颜色规则（低饱和护眼色，256 色，VS Code 终端支持）：
    torch.Tensor/Parameter=粉   torch.Size=青   torch.dtype=土黄   其它torch=浅蓝
    numpy数组=深蓝  numpy标量=黄绿  tensorflow/keras=天蓝  其它ML库=灰紫
    pandas=丁香紫   sklearn=淡薰衣草
    int=绿  float=浅绿  complex=紫  bool=暗青  None=灰   range=橄榄
    bytes=茶色  list=梅紫  tuple=暗梅紫  dict=紫红  set=深玫瑰
    datetime=棕   enum=灰紫  无关字符串=柔橙(统一)  其它对象=默认
"""

import builtins
import re
import sys
from enum import Enum as _Enum

__all__ = ["c", "clear_style_attr", "disable", "enable", "p", "pp",
           "register", "set_style_attr", "sho", "unregister"]

# 256 色 ANSI 码（\033[38;5;Nm），VS Code / Windows Terminal 均支持
# 护眼基调：低饱和柔和色；色相尽量拉开，相近类型可区分（* 为高频相邻出现的组合刻意错开）
_STYLES = {
    # ---- torch 深度学习 ----
    "tensor": "\033[38;5;175m",      # 柔和粉
    "size": "\033[38;5;73m",         # 柔和青
    "dtype": "\033[38;5;178m",       # 土黄
    "torch_other": "\033[38;5;110m",  # 浅蓝 (device / nn.Module 等)
    # ---- numpy ----
    "ndarray": "\033[38;5;67m",      # 深蓝
    "np_scalar": "\033[38;5;150m",   # 黄绿（与 int/float 拉开）
    # ---- 其它 ML 库 ----
    "tf": "\033[38;5;75m",           # 天蓝 (tensorflow/keras)
    "ml_other": "\033[38;5;102m",    # 灰紫 (jax/onnx/scipy/transformers/PIL 等)
    "pandas": "\033[38;5;140m",      # 丁香紫
    "sklearn": "\033[38;5;146m",     # 淡薰衣草
    # ---- python 基础类型 ----
    "int": "\033[38;5;71m",          # 绿
    "float": "\033[38;5;151m",       # 浅绿
    "complex": "\033[38;5;62m",      # 紫
    "bool": "\033[38;5;66m",         # 暗青（与 torch.Size 青拉开）
    "none": "\033[38;5;245m",        # 灰
    "str": "\033[38;5;173m",         # 柔橙 —— 无关字符串的统一颜色
    "bytes": "\033[38;5;180m",       # 茶色
    "list": "\033[38;5;139m",        # 梅紫
    "tuple": "\033[38;5;95m",        # 暗梅紫
    "dict": "\033[38;5;133m",        # 紫红（与 tensor 粉拉开）
    "set": "\033[38;5;131m",         # 深玫瑰
    "range": "\033[38;5;108m",       # 橄榄
    "datetime": "\033[38;5;137m",    # 棕
    "enum": "\033[38;5;102m",        # 灰紫
    "default": "\033[38;5;145m",     # 默认灰 —— 兜底：任何未识别对象也有颜色（100% 覆盖）
    # 经典颜色名（兼容 c(text, "red") 等写法，同样为柔和色）
    "red": "\033[38;5;167m",
    "green": "\033[38;5;71m",
    "yellow": "\033[38;5;178m",
    "blue": "\033[38;5;67m",
    "magenta": "\033[38;5;175m",
    "cyan": "\033[38;5;73m",
    "white": "\033[38;5;252m",
    "grey": "\033[38;5;245m",
}
_RESET = "\033[0m"

# 字体属性（ANSI SGR）：可与颜色组合使用
_ATTRS = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "blink": "\033[5m",
    "reverse": "\033[7m",
    "hidden": "\033[8m",
    "strike": "\033[9m",
}
# 某个语义样式默认附加的字体属性（如让 tensor 默认加粗）
_STYLE_ATTRS = {}

# 性能：样式名 -> 已拼接好的 ANSI 码（c() 高频调用走缓存）
_CODES_CACHE = {}


def _codes_for(style):
    cached = _CODES_CACHE.get(style)
    if cached is not None:
        return cached
    codes = []
    for token in style.split():
        if token in _STYLE_ATTRS:
            codes.extend(_ATTRS[a] for a in _STYLE_ATTRS[token])
        if token in _ATTRS:
            codes.append(_ATTRS[token])
        elif token in _STYLES:
            codes.append(_STYLES[token])
    _CODES_CACHE[style] = codes
    return codes


def c(text, style="cyan"):
    """染字：颜色名/字体属性可任意组合，如 c("hi", "bold underline cyan")。"""
    codes = _codes_for(style)
    if not codes:
        return str(text)
    return "".join(codes) + str(text) + _RESET


def set_style_attr(name, *attrs):
    """让某类型默认带字体属性，如 set_style_attr("tensor", "bold", "underline")。"""
    if name not in _STYLES:
        raise ValueError(f"未知样式名: {name}")
    lst = _STYLE_ATTRS.setdefault(name, [])
    for a in attrs:
        if a not in _ATTRS:
            raise ValueError(f"未知字体属性: {a}")
        if a not in lst:
            lst.append(a)
    _CODES_CACHE.clear()


def clear_style_attr(name=None):
    """清除字体属性设置（name=None 时全部清除）。"""
    if name is None:
        _STYLE_ATTRS.clear()
    else:
        _STYLE_ATTRS.pop(name, None)
    _CODES_CACHE.clear()


# ---------------- 字符串内部模式识别（f-string 打印时也能上色，支持跨行 tensor） ----------------
_PATTERNS = [
    (r"torch\.Size\([\s\S]*?\)", "size"),                                  # torch.Size([..])
    (r"tensor\([\s\S]*?\)", "tensor"),                                     # tensor(..) 含多行
    (r"torch\.(?:float|int|uint|bool|complex|long|short)[a-z0-9]*", "dtype"),  # torch.float32 等
    (r"\btorch\.\w+", "torch_other"),                                      # 其它 torch.xxx
    (r"\b(?:cpu|cuda:\d+)\b", "torch_other"),                              # torch.device 值
    (r"\bdtype\s*=\s*[\w.]+\b", "dtype"),                                  # dtype=float64 / dtype=torch.float32
    (r"np\.(?:float|int|complex|bool)[a-z0-9]*", "np_scalar"),             # numpy 标量
    (r"\barray\([\s\S]*?\)", "ndarray"),                                   # numpy 数组 [含 dtype=...]
    (r"\b(?:True|False)\b", "bool"),                                       # bool
    (r"\bNone\b", "none"),                                                 # None
    (r"\b0[xX][0-9a-fA-F]+\b", "int"),                                     # 十六进制
    (r"(?<![\w.])[-+]?(?:\d+\.?\d*|\.\d+)[eE][-+]?\d+(?![\w.])", "int"),   # 科学计数 1e-5
    (r"\b(?:nan|inf|infinity)\b", "float"),                                # nan / inf
    (r"(?<![\w.])[-+]?\d+\.?\d*(?![\w.])", "int"),                         # 独立数字(含负数)
]
_COMBINED = re.compile("|".join(f"(?P<g{i}>{p})" for i, (p, _) in enumerate(_PATTERNS)),
                       re.IGNORECASE)
_COLORS = [color for _, color in _PATTERNS]


def _highlight_str(s):
    """字符串内识别 DL 类型/数字/bool/None 等并上色，其余文字统一柔橙。"""
    parts = []
    pos = 0
    for m in _COMBINED.finditer(s):
        if m.start() > pos:
            parts.append(c(s[pos:m.start()], "str"))
        parts.append(c(m.group(), _COLORS[m.lastindex - 1]))
        pos = m.end()
    if pos < len(s):
        parts.append(c(s[pos:], "str"))
    return "".join(parts) if parts else c(s, "str")


# ---------------- 类型 -> 颜色（带缓存，性能优化） ----------------
_TYPE_STYLE_CACHE = {}

# AI 大模型开发生态关键词（子串匹配模块名）。命中 -> ml_other 灰紫
_AI_MODULES = (
    # 深度学习框架
    "tensorflow", "keras", "jax", "flax", "onnx", "paddle", "mindspore", "jittor",
    "tvm", "triton", "xformers", "flash_attn", "bitsandbytes", "megatron",
    "deepspeed", "horovod", "ray", "dask",
    # 训练/推理/模型库
    "accelerate", "lightning", "vllm", "sglang", "generation", "optimum", "peft",
    "trl", "unsloth", "transformers", "diffusers", "sentence_transformers",
    "datasets", "evaluate", "tokenizers", "tiktoken", "sentencepiece",
    "timm", "monai", "kornia", "albumentations", "decord", "open3d", "pytorchvideo",
    # 机器学习库
    "sklearn", "imblearn", "catboost", "lightgbm", "xgboost", "statsmodels",
    "gensim", "nltk", "spacy", "jieba", "hanlp", "lightfm", "optuna",
    "fasttext", "fastText",
    # 数据
    "polars", "xarray", "zarr", "h5py", "tables",
    # 视觉/音频
    "cv2", "PIL", "imageio", "skimage", "librosa", "soundfile", "einops",
    # 大模型应用/智能体/向量库
    "langchain", "langgraph", "llama_index", "crewai", "autogen", "openai",
    "anthropic", "huggingface", "faiss", "chromadb", "weaviate", "qdrant",
    # 工具/实验跟踪/配置
    "pydantic", "wandb", "mlflow", "tensorboard", "omegaconf", "hydra",
    # 科学计算
    "sympy",
)

# 用户运行时注册的模块关键词（优先级最高）
_EXTRA_MODULES = {}


def register(module_keyword, style="ml_other"):
    """运行时注册：把包含该关键词的模块对象染成指定颜色。
    例：pcolor.register("peft", "dtype")  /  pcolor.register("myagent", "tf")
    未识别的对象也会兜底为默认灰，本函数用于给特定库定制颜色。
    """
    if style not in _STYLES:
        raise ValueError(f"未知样式名: {style}")
    _EXTRA_MODULES[module_keyword] = style
    _TYPE_STYLE_CACHE.clear()


def unregister(module_keyword=None):
    """取消注册（module_keyword=None 时清空全部）。"""
    if module_keyword is None:
        _EXTRA_MODULES.clear()
    else:
        _EXTRA_MODULES.pop(module_keyword, None)
    _TYPE_STYLE_CACHE.clear()


def _compute_style(t, module, name):
    """只依赖类型信息计算样式。"""
    module = module or ""
    # 1) 用户运行时注册（优先级最高）
    for kw, style in _EXTRA_MODULES.items():
        if kw in module:
            return style
    # 2) 主要深度学习/数据框架（独立颜色）
    if "torch" in module or "pytorch" in module:
        if name in ("Tensor", "Parameter"):
            return "tensor"
        if name == "Size":
            return "size"
        if name == "dtype":
            return "dtype"
        return "torch_other"
    if "numpy" in module:
        if name in ("ndarray", "matrix"):
            return "ndarray"
        if name in ("bool_", "bool"):
            return "bool"
        return "np_scalar"
    if "pandas" in module:
        return "pandas"
    if "sklearn" in module:
        return "sklearn"
    if "tensorflow" in module or "keras" in module:
        return "tf"
    # 2.4) 继承自 torch 的自定义类（如 class Model(nn.Module)，定义在 __main__/自己模块里）
    #      查类型祖先链(MRO)即可识别，无需 import torch，保持零依赖
    #      （放在主框架分支之后：直接 torch/numpy 类型先被名字精准识别）
    for base in getattr(t, "__mro__", ())[1:]:
        if "torch" in (getattr(base, "__module__", "") or ""):
            return "torch_other"
    # 2.5) 标准库其它容器/数值/时间
    if module.startswith("collections"):
        if name in ("Counter", "OrderedDict", "defaultdict", "ChainMap"):
            return "dict"
        return "list"
    if module in ("decimal", "fractions"):
        return "float"
    if module.startswith("datetime"):
        return "datetime"
    # 3) AI 大模型生态关键词 -> 灰紫
    if any(k in module for k in _AI_MODULES):
        return "ml_other"
    # 4) 兜底：任何第三方/自定义模块对象 -> 默认灰（保证 100% 都有颜色）
    if module and module != "builtins":
        return "default"
    return None


def _style_for(obj):
    """根据对象类型决定颜色（对象本身就是值的情况）。"""
    t = type(obj)
    style = _TYPE_STYLE_CACHE.get(t)
    if style is not None:
        return style
    module = getattr(t, "__module__", "") or ""
    name = getattr(t, "__name__", "") or ""

    # 0) enum 优先（枚举模块通常是用户代码，不能被兜底抢走）
    if isinstance(obj, _Enum):
        style = "enum"
    else:
        # 1) ML/数据分析库按模块判定（必须在 isinstance 之前：如 torch.Size 是 tuple 子类）
        style = _compute_style(t, module, name)
        if style is None:
            # 2) python 基础类型
            if isinstance(obj, bool):
                style = "bool"
            elif isinstance(obj, int):
                style = "int"
            elif isinstance(obj, float):
                style = "float"
            elif isinstance(obj, complex):
                style = "complex"
            elif isinstance(obj, str):
                style = "str"
            elif isinstance(obj, (bytes, memoryview)):
                style = "bytes"
            elif isinstance(obj, list):
                style = "list"
            elif isinstance(obj, tuple):
                style = "tuple"
            elif isinstance(obj, dict):
                style = "dict"
            elif isinstance(obj, (set, frozenset)):
                style = "set"
            elif isinstance(obj, range):
                style = "range"
            elif type(None) is t:
                style = "none"
            else:
                style = "default"      # 兜底：任何未识别对象也有颜色（100% 覆盖）
    _TYPE_STYLE_CACHE[t] = style
    return style


def _render(*args, sep=" "):
    """统一渲染：字符串做内部识别，非字符串按类型上色。"""
    parts = []
    for a in args:
        if isinstance(a, str):
            parts.append(_highlight_str(a))
        else:
            parts.append(c(str(a), _style_for(a)))
    return sep.join(parts)


def pp(*args, sep=" ", end="\n", file=None):
    """智能打印：字符串内部识别 + 对象按类型上色。"""
    text = _render(*args, sep=sep) + end
    if file is None:
        sys.stdout.write(text)
    else:
        file.write(text)


# p 与 pp 同为智能打印
p = pp


def sho(t, name="t"):
    """张量三属性分行打印，按类型上色。"""
    pp(f"{name}.shape", t.shape)
    pp(f"{name}.dtype", t.dtype)
    pp(f"{name}", t)


# ---------------- 自动接管 print ----------------
_ORIGINAL_PRINT = builtins.print
_enabled = False


def _should_color(file):
    return file is None and sys.stdout.isatty()


def _patched_print(*args, sep=" ", end="\n", file=None, flush=False):
    if _should_color(file):
        sys.stdout.write(_render(*args, sep=sep) + end)
        if flush:
            sys.stdout.flush()
    else:
        _ORIGINAL_PRINT(*args, sep=sep, end=end, file=file, flush=flush)


def enable():
    """让普通 print() 自动按类型/模式上色（仅终端输出，写文件不受影响）。"""
    global _enabled
    if not _enabled:
        builtins.print = _patched_print
        _enabled = True


def disable():
    """撤销 enable()，恢复原生 print。"""
    global _enabled
    if _enabled:
        builtins.print = _ORIGINAL_PRINT
        _enabled = False


# ------------- 导入即自动启用：只需一行 import pcolor -------------
enable()
