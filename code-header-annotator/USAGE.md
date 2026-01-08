# Code Header Annotator - 使用指南

## 概述

Code Header Annotator 是一个为代码文件添加固定 20 行头注释的工具，该头注释包含文件摘要和关键类/函数的索引（带行号）。

## 工作流程

### 1. 添加/更新头注释

使用 `annotate_code_headers.py` 脚本：

```bash
python scripts/annotate_code_headers.py <files-or-dirs> --root <repo-root> --resolve-parents
```

参数说明：
- `<files-or-dirs>`: 要处理的文件或目录
- `--root`: 仓库根目录（用于计算相对路径）
- `--resolve-parents`: 尝试解析外部父类为跨文件引用（如 `Base@path/to/file.py#L42`）
- `--purpose`: 覆盖 Purpose 行（否则从现有文档字符串中提取）
- `--index-hint`: 覆盖 Index 行
- `--refresh`: 强制从零重建头注释（可能把已填写的手工字段重置为 TODO）
- `--max-width`: 截断每行头注释到此宽度（默认 120）
- `--dry-run`: 仅打印操作，不实际写入
- `--verify`: 处理完成后自动运行验证

### 2. 验证完整性（必需）

在处理完所有文件后，**必须运行验证步骤**以确保所有自动填充的字段已完成：

```bash
python scripts/check_incomplete_headers.py <files-or-dirs> --root <repo-root>
```

此脚本检查以下自动填充字段中是否有未完成的 TODO：
- `Key funcs`: 函数定义
- `Entrypoints`: 入口点（如 `if __name__ == "__main__"`）

**重要**：脚本会智能地分析文件内容，只有当文件确实包含函数定义或入口点，但头注释中的对应字段仍为 "TODO" 时，才会报告为不完整。

### 3. 处理不完整的文件

如果验证脚本发现了不完整的文件，重新处理它们：

```bash
python scripts/annotate_code_headers.py <incomplete-files> --root <repo-root>
```

然后重新运行验证，直到所有头注释都完整。

## 为什么需要验证步骤？

当使用 AI 工具（如 LLM）进行批量处理时，可能会遇到以下情况：

1. **工具崩溃**：处理过程中 AI 工具崩溃，导致部分文件的某些字段未被填充
2. **网络中断**：远程 API 调用中断
3. **Token 限制**：处理超时或达到 token 限制

在这些情况下，头注释可能已经插入到文件中，但某些自动填充的字段（Key funcs、Entrypoints）仍然是 "TODO"。

验证步骤通过扫描文件内容并对比头注释，可以准确地识别出这些不完整的文件。

## 头注释格式

每个文件的头注释固定为 20 行，包含以下字段：

```
1. Marker/version + invariants: @codex-header: v1 | 20 lines | keep updated
2. Path: 相对路径
3. Purpose: 一句话描述
4. Key types: 类型定义（可选，无类型时为 TODO）
5. Inheritance: 继承关系
6. Key funcs: 函数定义（自动填充）
7. Entrypoints: 入口点（自动填充）
8. Public API: 公共 API（需手动填充）
9. Inputs/Outputs: 输入/输出（需手动填充）
10. Core flow: 核心流程（需手动填充）
11. Dependencies: 依赖项（需手动填充）
12. Error handling: 错误处理（需手动填充）
13. Config/env: 配置/环境（需手动填充）
14. Side effects: 副作用（需手动填充）
15. Performance: 性能（需手动填充）
16. Security: 安全（需手动填充）
17. Tests: 测试（需手动填充）
18. Known issues: 已知问题（需手动填充）
19. Index: 章节索引（可选）
20. Last update: 最后更新日期
```

## 使用头注释进行导航

当探索大型代码库时，**优先阅读头注释**，只有当头注释表明相关性时才打开完整文件。

### 查找已注释的文件
```bash
rg "@codex-header: v1"
```

### 从头注释中快速定位
- `Purpose` 是否匹配当前任务？
- `Key types` / `Key funcs` 是否包含你需要的符号？
- `Inheritance` 是否显示了所需的父类/基类？
- `Index` 是否给出了跳转到的章节锚点？

### 作为可导航图使用
- 使用 `Key types` / `Key funcs` 定位具体符号
- 使用 `Inheritance` "向上"跳转（基类/接口/mixins）和"横向"跳转（共享同一基类的兄弟类）
- 如果 `Inheritance` 边指向另一个文件（如 `Base@pkg/base.py#L42`），打开该文件的头注释并重复此过程

## 完整工作流示例

```bash
# 1. 添加/更新头注释
python scripts/annotate_code_headers.py src/ --root . --resolve-parents

# 2. 验证完整性
python scripts/check_incomplete_headers.py src/ --root .

# 3. 如果发现不完整文件，重新处理
python scripts/annotate_code_headers.py path/to/incomplete_file.py --root .

# 4. 再次验证，直到所有文件都完整
python scripts/check_incomplete_headers.py src/ --root .
```

或者使用 `--verify` 选项自动进行验证：

```bash
python scripts/annotate_code_headers.py src/ --root . --resolve-parents --verify
```

## 注意事项

- 验证脚本会跳过没有头注释的文件
- `Key types` 和 `Index` 是可选的，即使文件中没有类型定义或明显的章节结构，它们保持 "TODO" 也是正常的
- 只有 `Key funcs` 和 `Entrypoints` 是必须自动填充的
- 如果文件有函数定义但 `Key funcs` 是 "TODO"，则认为该文件不完整
- 如果文件有入口点但 `Entrypoints` 是 "TODO"，则认为该文件不完整
