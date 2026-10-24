#!/usr/bin/env python3
"""按 .pr-exclude 筛选已提交改动，在独立 worktree 中准备 PR；默认只预览。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


class PreparationError(Exception):
    """表示输入或 Git 操作无法安全继续，交给命令入口输出简短错误。"""


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    """在指定仓库执行 Git，返回原始字节，避免路径中的空格和换行被拆分。"""
    # 外部终端可能残留其他仓库的索引或工作目录设置，不能让它们重定向操作。
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "-C", str(repo), *args], input=data,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip()
        raise PreparationError(detail or f"Git exited with status {result.returncode}.")
    return result.stdout


def read_exclusions(path: Path) -> list[str]:
    """读取根目录相对路径；空行和整行注释忽略，目录覆盖全部子路径。"""
    exclusions = []
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        # 这里只承诺明确的文件/目录路径，拒绝把通配符、否定规则等当成字面路径。
        # 首尾各一个斜线可省略；大小写遵循 Git 路径，不能跳到仓库外部。
        entry = entry.removeprefix("/").removesuffix("/")
        if (not entry or any(part in ("", ".", "..") for part in entry.split("/"))
                or entry.startswith("!") or any(char in entry for char in "*?[]\\\x00")):
            raise PreparationError(
                f"{path}:{number}: expected a repository-relative file or directory; "
                "globs, negation, escapes and parent traversal are not supported."
            )
        if entry not in exclusions:
            exclusions.append(entry)
    return exclusions


def resolve_commit(repo: Path, ref: str) -> str:
    """将用户指定的引用固定为提交 ID，后续操作不受引用移动影响。"""
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()


def changed_paths(repo: Path, start: str, end: str, paths: list[str]) -> list[str]:
    """列出指定范围的路径；关闭重命名检测，使两个端点分别接受排除规则。"""
    output = git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                 "--name-only", "-z", start, end, "--", *paths)
    return [os.fsdecode(item) for item in output.split(b"\x00") if item]


def prepare(args: argparse.Namespace) -> None:
    """先展示来源和筛选结果，显式创建时再生成分支、暂存补丁并留下审阅入口。"""
    # 1. 始终操作脚本所在的仓库；清单取当前工作目录版本，代码只取已提交版本。
    location = Path(__file__).resolve().parent.parent
    repo = Path(os.fsdecode(git(location, "rev-parse", "--show-toplevel")).rstrip("\n"))
    exclude_file = repo / args.exclude_file
    exclusions = read_exclusions(exclude_file)
    source = resolve_commit(repo, args.source)
    base = resolve_commit(repo, args.base)
    ancestors = git(repo, "merge-base", "--all", base, source).decode().splitlines()
    if len(ancestors) != 1:
        raise PreparationError("Expected exactly one merge base; reconcile the histories first.")
    ancestor = ancestors[0]

    # 2. 只提取来源分支自共同祖先以来的净改动，避免把上游新增内容误当成删除。
    # literal + top 禁用路径模式解释；目录名也会匹配其子路径。
    paths = [".", *(f":(top,literal,exclude){entry}" for entry in exclusions)]
    all_changed = changed_paths(repo, ancestor, source, ["."])
    included = changed_paths(repo, ancestor, source, paths)
    included_set = set(included)
    excluded = [name for name in all_changed if name not in included_set]
    print(f"Repository: {repo}")
    print(f"Source: {args.source} ({source})")
    print(f"Base: {args.base} ({base})")
    print(f"Merge base: {ancestor}")
    print(f"Exclusions: {exclude_file} ({len(exclusions)} rules)")
    if not exclusions:
        print("The exclusion list is empty; no paths are filtered.")
    for title, names in (("Included", included), ("Excluded", excluded)):
        print(f"{title}: {len(names)} path(s)")
        for name in names:
            print(f"  {name!r}")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=normal"):
        print("Working-tree changes and untracked files are not exported; "
              "only the exclusion file is read from the working tree.")

    if not args.create:
        print("Preview only. No branch, worktree, commit or push was created.")
        return
    if not included:
        print("No included changes; no branch or worktree was created.")
        return

    # 3. 只接受不存在的分支和工作目录，不切换来源工作区，也不覆盖旧 PR 分支。
    git(repo, "check-ref-format", "--branch", args.branch)
    existing = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads/").decode().splitlines()
    if f"refs/heads/{args.branch}" in existing:
        raise PreparationError(f"Branch already exists: {args.branch}")
    worktree = Path(args.worktree).expanduser().absolute()
    if os.path.lexists(worktree):
        raise PreparationError(f"Worktree destination already exists: {worktree}")
    worktree = worktree.resolve()
    if worktree.is_relative_to(repo):
        raise PreparationError("The PR worktree must be outside the source working tree.")

    # 二进制、权限位与符号链接均交给 Git patch 格式处理，不自行复制文件内容。
    patch = git(repo, "diff", "--binary", "--full-index", "--no-renames",
                "--no-ext-diff", "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/",
                ancestor, source, "--", *paths)
    print(f"Creating branch {args.branch!r} at {base} in {str(worktree)!r}.", flush=True)
    # 显式关闭跟踪与 checkout hook，避免新分支误跟踪上游或运行个人自动提交 hook。
    git(repo, "-c", f"core.hooksPath={os.devnull}", "worktree", "add", "--no-track",
        "-b", args.branch, str(worktree), base)
    try:
        # 4. 新 worktree 以目标上游为底，三方应用尽量保留上游后续变化。
        # 冲突时保留现场和非零退出码，由用户检查解决，不自动选 ours/theirs。
        git(worktree, "apply", "--index", "--3way", "--whitespace=nowarn", data=patch)
    except PreparationError as error:
        raise PreparationError(
            f"Patch application failed. Branch {args.branch!r} and worktree {str(worktree)!r} "
            f"were retained for inspection; no commit or push was made.\n{error}"
        ) from error
    print(git(worktree, "diff", "--cached", "--stat").decode(errors="replace"), end="")
    print("Prepared changes are staged in the PR worktree. Review them before committing.")
    print("The source branch and working tree were not changed. No commit or push was made.")


def main() -> int:
    """解析预览/创建选项；创建操作必须由用户同时指定分支名和独立目录。"""
    parser = argparse.ArgumentParser(
        description="Prepare a filtered PR branch from committed source changes; preview by default.",
        epilog="Uses local refs without fetching. Run git fetch upstream first when needed. "
               "Exclusions are root-relative literal file/directory paths, not gitignore patterns.",
    )
    parser.add_argument("--source", default="ubuntu", help="source ref (default: ubuntu)")
    parser.add_argument("--base", default="upstream/main", help="target ref (default: upstream/main)")
    parser.add_argument("--exclude-file", default=".pr-exclude",
                        help="exclusion file, relative to the repository root by default")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="preview only (the default)")
    mode.add_argument("--create", action="store_true", help="create a branch and stage its filtered patch")
    parser.add_argument("--branch", help="new PR branch name; required with --create")
    parser.add_argument("--worktree", help="new directory outside the source tree; required with --create")
    args = parser.parse_args()
    if args.create and (not args.branch or not args.worktree):
        parser.error("--create requires --branch and --worktree")
    try:
        prepare(args)
    except (PreparationError, OSError, UnicodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
