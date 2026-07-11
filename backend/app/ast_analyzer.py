from __future__ import annotations

import re

from tree_sitter import Language, Node, Parser
import tree_sitter_cpp
import tree_sitter_python

from .models import CodeAnalysis

_LANGUAGES: dict[str, Language] = {
    "python": Language(tree_sitter_python.language()),
    "cpp": Language(tree_sitter_cpp.language()),
}

_LOOP_NODES = {
    "for_statement",
    "while_statement",
    "do_statement",
    "for_range_loop",
    "for_in_clause",
}

_FUNCTION_NODES = {"function_definition", "function_declarator", "lambda"}


# cpp vs python heuristic
def detect_language(code: str) -> str:
    cpp_signals = ("#include", "std::", "int main", "->", ";\n", "vector<")
    py_signals = ("def ", "import ", "print(", "elif ", "self.")
    cpp_score = sum(code.count(s) for s in cpp_signals)
    py_score = sum(code.count(s) for s in py_signals)
    return "cpp" if cpp_score > py_score else "python"


# walk ast
def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


# max loop nesting
def _loop_nesting(node: Node, depth: int = 0) -> int:
    best = depth
    for child in node.children:
        d = depth + 1 if child.type in _LOOP_NODES else depth
        best = max(best, _loop_nesting(child, d))
    return best


# node source text
def _text(node: Node, code: bytes) -> str:
    return code[node.start_byte : node.end_byte].decode("utf8", errors="replace")


# parse user code
def analyze_code(code: str, language: str | None = None) -> CodeAnalysis:
    if not code.strip():
        return CodeAnalysis()

    lang = language or detect_language(code)
    parser = Parser(_LANGUAGES[lang])
    raw = code.encode("utf8")
    tree = parser.parse(raw)
    root = tree.root_node

    functions: list[str] = []
    variables: set[str] = set()
    loop_count = 0

    for node in _walk(root):
        if node.type in _LOOP_NODES:
            loop_count += 1
        elif node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node is None:
                decl = node.child_by_field_name("declarator")
                while decl is not None and decl.type != "identifier":
                    decl = decl.child_by_field_name("declarator") or (
                        decl.children[0] if decl.children else None
                    )
                name_node = decl
            if name_node is not None:
                functions.append(_text(name_node, raw))
        elif node.type == "assignment" and lang == "python":
            left = node.child_by_field_name("left")
            if left is not None and left.type == "identifier":
                variables.add(_text(left, raw))
        elif node.type == "init_declarator" and lang == "cpp":
            decl = node.child_by_field_name("declarator")
            if decl is not None and decl.type == "identifier":
                variables.add(_text(decl, raw))

    nesting = _loop_nesting(root)
    recursion = any(
        re.search(rf"\b{re.escape(fn)}\s*\(", _strip_definition_line(code, fn))
        for fn in functions
    )

    warnings: list[str] = []
    if lang == "cpp" and re.search(r"\bint\b", code) and re.search(r"\*", code):
        warnings.append(
            "Kod używa typu int i mnożenia — możliwe przepełnienie zakresu (rozważ long long)."
        )
    if lang == "python" and "input()" in code and "sys.stdin" not in code:
        warnings.append(
            "input() bywa wolne przy dużym wejściu — sys.stdin może uratować przed TLE."
        )
    if re.search(r"<=\s*len\(|<=\s*n\b", code):
        warnings.append("Warunek z '<=' przy granicy rozmiaru — sprawdź off-by-one.")

    complexity = _estimate_complexity(nesting, recursion, code)

    return CodeAnalysis(
        language=lang,
        functions=functions[:20],
        variables=sorted(variables)[:30],
        max_loop_nesting=nesting,
        loop_count=loop_count,
        recursion=recursion,
        estimated_complexity=complexity,
        warnings=warnings,
    )


# remove fn defs for recursion check
def _strip_definition_line(code: str, fn_name: str) -> str:
    pattern = re.compile(rf"^.*(def\s+{re.escape(fn_name)}|\b{re.escape(fn_name)}\s*\([^)]*\)\s*\{{?\s*$).*$", re.M)
    return pattern.sub("", code)


# estimate big-O
def _estimate_complexity(nesting: int, recursion: bool, code: str) -> str:
    has_sort = bool(re.search(r"\bsort(ed)?\s*\(|\.sort\s*\(", code))
    if recursion and nesting == 0:
        return "prawdopodobnie rekurencyjna — zależna od głębokości rekursji (możliwa wykładnicza bez memoizacji)"
    if nesting >= 3:
        return "O(N^3) lub gorzej (potrójnie zagnieżdżone pętle)"
    if nesting == 2:
        return "O(N^2) (podwójnie zagnieżdżone pętle)"
    if nesting == 1:
        return "O(N log N)" if has_sort else "O(N)"
    return "O(N log N) — dominuje sortowanie" if has_sort else "O(1)/O(N) — brak pętli w AST"


# structural text for embeddings
def code_to_search_text(analysis: CodeAnalysis, code: str) -> str:
    parts = [
        f"language: {analysis.language}",
        f"functions: {', '.join(analysis.functions) or 'none'}",
        f"loop nesting depth: {analysis.max_loop_nesting}",
        f"recursion: {analysis.recursion}",
        f"estimated complexity: {analysis.estimated_complexity}",
    ]
    identifiers = " ".join(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", code))[:500]
    parts.append(f"identifiers: {identifiers}")
    return "\n".join(parts)
