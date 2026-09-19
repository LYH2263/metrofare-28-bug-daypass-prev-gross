"""一日通封顶模块:维护自然日、封顶金额、是否启用,并在询价时按 min(分段票价, 封顶) 计算应付。"""
from app.modules.day_pass.engine import apply_day_pass, today_str
from app.modules.day_pass.repository import DDL, get_config, save_config

__all__ = ["apply_day_pass", "today_str", "get_config", "save_config", "DDL"]
