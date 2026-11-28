"""L5 optional impure sidecar: the only readers of files in this package.

Readers return values; they never pick paths or walk directories (§7). Nothing in L0-L4 may
import this package (Seam 4)."""
