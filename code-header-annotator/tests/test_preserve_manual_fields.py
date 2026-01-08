import tempfile
import unittest
from pathlib import Path


class TestAnnotateCodeHeadersPreserveManualFields(unittest.TestCase):
    def _import_module(self):
        import sys

        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = repo_root / "scripts"
        sys.path.insert(0, str(scripts_dir))
        import annotate_code_headers  # type: ignore

        return annotate_code_headers

    def test_preserves_manual_fields_by_default(self):
        ach = self._import_module()
        today = ach._dt.date.today().isoformat()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "AlarmMessageList.tsx"
            path.write_text(
                "\n".join(
                    [
                        "/* @codex-header: v1 | 20 lines | keep updated",
                        " * Path: src/components/AlarmMessageList.tsx",
                        " * Purpose: React 组件模块（默认导出）：AlarmMessageList",
                        " * Key types: TODO",
                        " * Inheritance: TODO",
                        " * Key funcs: TODO",
                        " * Entrypoints: TODO",
                        " * Public API: 已完成",
                        " * Inputs/Outputs: TODO",
                        " * Core flow: TODO",
                        " * Dependencies: TODO",
                        " * Error handling: TODO",
                        " * Config/env: TODO",
                        " * Side effects: TODO",
                        " * Performance: TODO",
                        " * Security: TODO",
                        " * Tests: TODO",
                        " * Known issues: TODO",
                        " * Index: TODO",
                        " * Last update: 2026-01-01 */",
                        "",
                        "export const AlarmMessageList = () => null;",
                        "export default AlarmMessageList;",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            did_change, _ = ach.annotate_file(
                path,
                root=root,
                purpose="",
                index_hint="",
                max_width=120,
                dry_run=False,
                refresh=False,
            )
            self.assertTrue(did_change)

            updated = path.read_text(encoding="utf-8")
            self.assertIn("Purpose: React 组件模块（默认导出）：AlarmMessageList", updated)
            self.assertIn("Public API: 已完成", updated)
            self.assertIn(f"Last update: {today}", updated)

    def test_refresh_resets_manual_fields(self):
        ach = self._import_module()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "file.ts"
            path.write_text(
                "\n".join(
                    [
                        "/* @codex-header: v1 | 20 lines | keep updated",
                        " * Path: file.ts",
                        " * Purpose: KeepMe",
                        " * Key types: TODO",
                        " * Inheritance: TODO",
                        " * Key funcs: TODO",
                        " * Entrypoints: TODO",
                        " * Public API: KeepMe",
                        " * Inputs/Outputs: KeepMe",
                        " * Core flow: KeepMe",
                        " * Dependencies: KeepMe",
                        " * Error handling: KeepMe",
                        " * Config/env: KeepMe",
                        " * Side effects: KeepMe",
                        " * Performance: KeepMe",
                        " * Security: KeepMe",
                        " * Tests: KeepMe",
                        " * Known issues: KeepMe",
                        " * Index: KeepMe",
                        " * Last update: 2026-01-01 */",
                        "",
                        "export const x = 1;",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            did_change, _ = ach.annotate_file(
                path,
                root=root,
                purpose="",
                index_hint="",
                max_width=120,
                dry_run=False,
                refresh=True,
            )
            self.assertTrue(did_change)

            updated = path.read_text(encoding="utf-8")
            self.assertIn("Purpose: TODO", updated)
            self.assertIn("Public API: TODO", updated)
            self.assertIn("Index: TODO", updated)


if __name__ == "__main__":
    unittest.main()

