"""一日通封顶:按自然日生效的票价上限,纯函数,不碰数据库。"""
from datetime import date


def today_str() -> str:
    """服务器本地自然日,YYYY-MM-DD。"""
    return date.today().isoformat()


def apply_day_pass(original_fare: float, config: dict | None, requested: bool, day: str) -> dict:
    """把一日通规则作用到一次询价的分段原价上。

    requested=False 时等价于改造前:应付 == 分段原价,day_pass 为 None。
    requested=True 且配置启用、配置自然日等于当日时才生效(applied);
    生效后应付 = min(分段原价, 封顶),capped 表示封顶真正压低了票价(触顶)。
    每次调用独立判定,不读取也不累计历史询价。
    """
    if not requested:
        return {"payable": original_fare, "day_pass": None}
    enabled = bool(config and config.get("enabled"))
    cap = float(config["cap"]) if config and config.get("cap") is not None else None
    cfg_day = config.get("day") if config else None
    applied = bool(enabled and cap is not None and cfg_day == day)
    capped = bool(applied and original_fare > cap)
    payable = round(min(original_fare, cap), 2) if applied else original_fare
    return {
        "payable": payable,
        "day_pass": {
            "day": cfg_day,
            "cap": cap,
            "enabled": enabled,
            "applied": applied,
            "capped": capped,
            "original_fare": original_fare,
            "payable": payable,
        },
    }
