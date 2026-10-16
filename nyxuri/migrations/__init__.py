"""Linear, idempotent cleanup migrations for managed user state."""

from nyxuri.core import get_env
from nyxuri.ledger import read_ledger, update_ledger

MIGRATION_LEVEL = 2
# Deprecated paths cleaned during linear migration.
TOMBSTONES: tuple[str, ...] = (
    ".config/fish/completions/nyxniri.fish",
    ".config/fish/conf.d/nyxniri-path.fish",
    ".config/noctalia/templates/nyxniri-palette.toml",
)

def run() -> bool:
    env = get_env()
    try:
        level = int(read_ledger().get("migration_level", 0) or 0)
    except (ValueError, TypeError):
        level = 0
    if level >= MIGRATION_LEVEL:
        return True
    for relative in TOMBSTONES:
        target = env.home / relative
        try:
            target.parent.resolve().relative_to(env.home.resolve())
        except ValueError:
            return False
        try:
            if target.is_symlink() or target.is_file():
                target.unlink()
        except OSError:
            return False
    try:
        update_ledger(migration_level=MIGRATION_LEVEL)
    except OSError:
        return False
    return True
