"""UnitRegistry — the blueprint domain's single entry (unit-model.md §2).

The only kernel module that scans ``configs/`` and reads unit manifests.
Adding a unit = adding a directory (plus an optional ``manifest.toml``) —
zero kernel code change. TOML parsing is delegated to
``nyxuri.deploy.manifest`` (pure stdlib); state.json is never touched
here — that is ledger's monopoly.
"""

from pathlib import Path

from nyxuri.core import get_env
from nyxuri.deploy.manifest import ModuleManifest, load_manifest

_METADATA_NAMES = frozenset({"__pycache__", ".optional-apps.toml"})


def unit_ids() -> list[str]:
    """Sorted ids of every directory unit under the source blueprint.

    A unit is a directory: ``configs/<unit>/``. Metadata entries are not
    units; the single-file degenerate (``starship.toml`` + sidecar) dies
    at KM1 and is not scanned here.
    """
    src = get_env().configs_src
    if not src.is_dir():
        return []
    return sorted(
        p.name for p in src.iterdir() if p.is_dir() and p.name not in _METADATA_NAMES
    )


def unit_dir(unit_id: str) -> Path | None:
    """On-disk blueprint directory for a unit, or None if it does not exist."""
    src = get_env().configs_src / unit_id
    return src if src.is_dir() else None


def load_unit(unit_id: str) -> ModuleManifest:
    """Load one unit's resolved manifest; zero-config defaults applied."""
    src = unit_dir(unit_id)
    if src is None:
        raise KeyError(f"unknown unit: {unit_id}")
    return load_manifest(src)


def dependency_graph() -> dict[str, list[str]]:
    """``{unit id: declared unit dependencies}`` for the whole blueprint.

    Feed this straight into ``nyxuri.resolver.resolve_order``; the two
    modules never import each other — the caller composes them.
    """
    return {uid: load_unit(uid).dependencies for uid in unit_ids()}
