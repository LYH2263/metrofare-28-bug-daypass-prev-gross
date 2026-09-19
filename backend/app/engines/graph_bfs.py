from collections import defaultdict, deque


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    if start == end:
        return 0
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None
    q = deque([(start, 0)])
    seen = {start}
    while q:
        cur, d = q.popleft()
        for nxt in g[cur]:
            if nxt in seen:
                continue
            if nxt == end:
                return d + 1
            seen.add(nxt)
            q.append((nxt, d + 1))
    return None
