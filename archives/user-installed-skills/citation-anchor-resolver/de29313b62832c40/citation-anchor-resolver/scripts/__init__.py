"""citation-anchor-resolver — Cite-or-Block 架构基石 skill.

公开 API 通过 ``resolver`` 模块暴露:

    from resolver import (
        Citation,
        parse_citations_in_text,
        resolve_citation,
        verify_claim_against_source,
    )

P0 守护:本 skill 绝不维护任何已知字典,不 fallback 到内置答案。
"""

try:  # pragma: no cover
    from ._anchor_schema import Citation, parse_anchor, ALLOWED_SOURCE_TYPES
    from .resolver import (
        parse_citations_in_text,
        resolve_citation,
        verify_claim_against_source,
    )
except ImportError:  # pragma: no cover
    from _anchor_schema import Citation, parse_anchor, ALLOWED_SOURCE_TYPES  # type: ignore
    from resolver import (  # type: ignore
        parse_citations_in_text,
        resolve_citation,
        verify_claim_against_source,
    )

__all__ = [
    "Citation",
    "parse_anchor",
    "ALLOWED_SOURCE_TYPES",
    "parse_citations_in_text",
    "resolve_citation",
    "verify_claim_against_source",
]
