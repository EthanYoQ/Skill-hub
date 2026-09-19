# cursorMark 分页与流量控制

主 SKILL.md §8 的扩展参考。Europe PMC 大结果集 **必须** 用 `cursorMark` 分页;`page=` 偏移分页在 >1000 条时官方明确不保证一致性。

## cursorMark 流程

```
首次请求:  cursorMark = "*"
响应包含:  nextCursorMark = "AoEpODEyMzQ1Ng=="
下一页:    cursorMark = "AoEpODEyMzQ1Ng=="
循环直到:  nextCursorMark == 当前 cursorMark  (= 已到末页)
```

## 终止条件

| 条件 | 处理 |
|------|------|
| `nextCursorMark` 与本次请求的 `cursorMark` 相同 | 已到末页,正常退出 |
| 累计返回数 ≥ `max_results` | 截断,设 `truncated=True` |
| 累计返回数 ≥ `hitCount` | 数据已取完,正常退出 |
| 连续两次响应 `resultList.result` 为空 | 异常,抛 `EuropePMCPaginationError` |

## 分页参考实现

```python
def _paginate(query: str, max_results: int, page_size: int = 100):
    cursor = "*"
    collected = []
    while len(collected) < max_results:
        resp = self._get("search", {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "cursorMark": cursor,
            "resultType": "core",
        })
        results = resp["resultList"]["result"]
        if not results:
            break
        collected.extend(results)
        next_cursor = resp.get("nextCursorMark")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    return collected[:max_results]
```

## 流量礼貌

| 维度 | 限制 | 备注 |
|------|------|------|
| 单页大小 `pageSize` | ≤ 1000 | 上限 1000 |
| 全局并发 | ≤ 5 | 超过会触发 429 |
| QPS | ≤ 8 | 自动 sleep 间隔 |
| email 标识 | 必传 | 礼貌请求,大流量异常时 EBI 联系你 |

## 退避策略

```python
import random
def _backoff(attempt: int) -> float:
    """指数退避 + 抖动"""
    return (2 ** attempt) + random.uniform(0, 1)

# 调用时:max_retries=3 → 退避 1~3s, 2~5s, 4~9s
```

## 常见坑

1. **cursorMark 含特殊字符必须 URL 编码**:Base64 末尾的 `==` 不编码会被服务端截断
2. **`*` 作为初始游标**:不是字符串 `"asterisk"`,直接传 ASCII `*`
3. **同一 query 不同 sort,cursor 不通用**:换 sort 必须从 `*` 重启
4. **>1000 条仍用 page=**:超过 1000 时返回顺序未定义,可能漏 / 重复 → **不要这样做**
5. **多并发同一 cursor**:cursor 是流式状态,并行重用会拉到同一页;需要并行时按 `pageSize` 分桶用不同 query 切片
