# Code Header Annotator - 优化说明

## 问题背景

在使用 AI 工具（如 LLM）批量处理代码文件时，可能会遇到以下极端情况：

1. **工具崩溃**：处理过程中 AI 工具崩溃，导致部分文件的某些字段未被填充
2. **网络中断**：远程 API 调用中断
3. **Token 限制**：处理超时或达到 token 限制

在这些情况下，头注释可能已经插入到文件中，但某些自动填充的字段（Key funcs、Entrypoints）仍然是 "TODO"，需要重新处理。

## 解决方案

采用**方案2：全文件校验**，通过脚本自动检测不完整的头注释。

### 新增功能

1. **验证脚本** (`check_incomplete_headers.py`)
   - 扫描所有带 `@codex-header: v1` 标记的文件
   - 智能分析文件内容，检查自动填充字段是否完整
   - 输出不完整的文件列表和具体问题

2. **自动验证选项** (`--verify`)
   - 在 `annotate_code_headers.py` 中添加 `--verify` 选项
   - 处理完成后自动运行验证脚本

### 智能检测逻辑

验证脚本不仅仅是检查字段是否为 "TODO"，而是会：

1. 扫描文件内容，检测是否真的有函数定义
2. 检查文件是否真的有入口点（如 `if __name__ == "__main__"`）
3. 只有当文件有相关内容但头注释对应字段仍为 "TODO" 时，才报告为不完整

**注意**：
- `Key types` 和 `Index` 是可选的，即使保持 "TODO" 也是正常的
- 只有 `Key funcs` 和 `Entrypoints` 是必须自动填充的

## 使用方式

### 方式1：手动验证

```bash
# 1. 添加/更新头注释
python scripts/annotate_code_headers.py src/ --root . --resolve-parents

# 2. 手动验证
python scripts/check_incomplete_headers.py src/ --root .

# 3. 如果发现不完整文件，重新处理
python scripts/annotate_code_headers.py path/to/incomplete_file.py --root .

# 4. 再次验证，直到所有文件都完整
python scripts/check_incomplete_headers.py src/ --root .
```

### 方式2：自动验证

```bash
# 使用 --verify 选项自动进行验证
python scripts/annotate_code_headers.py src/ --root . --resolve-parents --verify
```

## 文件结构

```
scripts/
├── annotate_code_headers.py      # 主脚本（已更新，添加 --verify 选项）
└── check_incomplete_headers.py   # 验证脚本（新增）

USAGE.md                          # 详细使用指南
```

## 优势

相比"建立索引"方案，全文件校验方案有以下优势：

1. **无需额外存储**：基于实际文件状态，不需要维护索引文件
2. **简单直接**：实现简单，易于理解和维护
3. **准确可靠**：直接扫描文件内容，避免索引不同步的问题
4. **智能检测**：分析实际内容，区分正常 TODO 和异常 TODO

## 示例

### 场景1：正常文件

文件内容：
```python
def process_data(data):
    return data.upper()
```

头注释：
```
Key funcs: process_data@L25
```

验证结果：✅ 完整

### 场景2：无函数的文件

文件内容：
```python
# 只有一些常量定义
MAX_SIZE = 100
```

头注释：
```
Key funcs: TODO
```

验证结果：✅ 完整（因为文件确实没有函数定义）

### 场景3：处理中断的文件

文件内容：
```python
def process_data(data):
    return data.upper()
```

头注释：
```
Key funcs: TODO
```

验证结果：❌ 不完整（文件有函数，但头注释未填充）

修复方式：
```bash
python scripts/annotate_code_headers.py incomplete_file.py --root .
```

## 技术细节

### 支持的语言

验证脚本支持以下语言的函数和入口点检测：

- Python (.py, .pyi)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- Go (.go)
- Rust (.rs)
- Java (.java)
- Kotlin (.kt)
- C# (.cs)

### 检测模式

- **Python**: `def function_name(...)`
- **JavaScript**: `function name(...)`, `export function name(...)`, `const name = (...)`
- **Go**: `func name(...)`
- **Rust**: `fn name(...)`, `pub fn name(...)`
- **Java**: 方法定义（简单模式）
- **Kotlin**: 方法定义（简单模式）

### 入口点检测

- **Python**: `if __name__ == "__main__"`
- **JavaScript/TypeScript**: `export default`, `export {`
- **Go**: `func main()`
- **Rust**: `fn main()`

## 总结

通过引入验证脚本和智能检测逻辑，Code Header Annotator 技能现在可以：

1. 自动检测因工具崩溃等原因导致的不完整头注释
2. 提供清晰的修复建议
3. 通过 `--verify` 选项简化工作流程

这确保了批处理任务的可靠性，特别是在使用 AI 工具时。
