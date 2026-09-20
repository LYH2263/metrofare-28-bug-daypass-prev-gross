import os
import sqlite3
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="metrofare-test-")

from app import seed  # noqa: E402
from app.modules import day_pass  # noqa: E402
from app.services.metro_service import MetroService  # noqa: E402

TODAY = day_pass.today_str()


def mem_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(day_pass.DDL)
    return conn


# --- engine:纯函数判定 ---

def test_not_requested_matches_legacy():
    out = day_pass.apply_day_pass(4.0, {"day": TODAY, "cap": 3.5, "enabled": True}, False, TODAY)
    assert out["payable"] == 4.0 and out["day_pass"] is None


def test_capped_when_fare_above_cap():
    out = day_pass.apply_day_pass(4.0, {"day": TODAY, "cap": 3.5, "enabled": True}, True, TODAY)
    assert out["payable"] == 3.5
    assert out["day_pass"]["capped"] is True
    assert out["day_pass"]["original_fare"] == 4.0
    assert out["day_pass"]["cap"] == 3.5


def test_not_capped_when_fare_below_cap():
    out = day_pass.apply_day_pass(3.0, {"day": TODAY, "cap": 3.5, "enabled": True}, True, TODAY)
    assert out["payable"] == 3.0 and out["day_pass"]["capped"] is False


def test_disabled_or_other_day_not_applied():
    cfg = {"day": TODAY, "cap": 3.5, "enabled": False}
    out = day_pass.apply_day_pass(4.0, cfg, True, TODAY)
    assert out["payable"] == 4.0 and out["day_pass"]["applied"] is False
    out2 = day_pass.apply_day_pass(4.0, {"day": "2000-01-01", "cap": 3.5, "enabled": True}, True, TODAY)
    assert out2["payable"] == 4.0 and out2["day_pass"]["applied"] is False


def test_each_quote_independent_no_accumulation():
    cfg = {"day": TODAY, "cap": 3.5, "enabled": True}
    first = day_pass.apply_day_pass(3.0, cfg, True, TODAY)
    second = day_pass.apply_day_pass(3.0, cfg, True, TODAY)
    assert first["day_pass"]["capped"] is False
    assert second["payable"] == 3.0 and second["day_pass"]["capped"] is False


# --- repository:落库与校验 ---

def test_repository_roundtrip():
    conn = mem_conn()
    assert day_pass.get_config(conn) is None
    saved = day_pass.save_config(conn, TODAY, 3.5, True)
    assert saved == {"day": TODAY, "cap": 3.5, "enabled": True}
    again = day_pass.save_config(conn, TODAY, 4.5, False)
    assert again["cap"] == 4.5 and again["enabled"] is False


def test_repository_rejects_non_positive_cap():
    conn = mem_conn()
    for bad in (0, -1.5):
        try:
            day_pass.save_config(conn, TODAY, bad, True)
        except ValueError:
            pass
        else:
            raise AssertionError("cap <= 0 must be rejected")
    assert day_pass.get_config(conn) is None


# --- service:询价链路 ---

def setup_service():
    seed.init_db()
    return MetroService()


def test_quote_without_day_pass_unchanged():
    with setup_service() as s:
        q = s.quote("A1", "B2", persist=False, use_day_pass=False)
        assert q["fare"] == 4.0 and q["payable"] == 4.0 and q["day_pass"] is None
        assert q["hops"] == 3 and q["run_id"] is None


def test_quote_with_day_pass_capped():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        q = s.quote("A1", "B2", persist=False, use_day_pass=True)
        assert q["fare"] == 4.0 and q["payable"] == 3.5
        assert q["day_pass"]["capped"] is True and q["day_pass"]["cap"] == 3.5
        assert q["hops"] == 3


def test_trial_quote_does_not_persist():
    with setup_service() as s:
        before = len(s.history())
        s.quote("A1", "B2", persist=False, use_day_pass=True)
        assert len(s.history()) == before


def test_two_trial_quotes_keep_record_count():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        before = len(s.history())
        s.quote("A1", "B2", persist=False, use_day_pass=True)
        s.quote("A1", "B2", persist=False, use_day_pass=True)
        assert len(s.history()) == before


def test_persisted_payable_matches_trial():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        trial = s.quote("A1", "B2", persist=False, use_day_pass=True)
        written = s.quote("A1", "B2", persist=True, use_day_pass=True)
        assert written["run_id"] is not None
        assert written["payable"] == trial["payable"] == 3.5
        assert written["day_pass"]["capped"] == trial["day_pass"]["capped"] is True
        import json
        rows = {r["id"]: r for r in s.history()}
        stored = json.loads(rows[written["run_id"]]["result_json"])
        assert stored["payable"] == 3.5 and stored["day_pass"]["capped"] is True


def test_persisted_without_day_pass_pays_uncapped_original():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        q = s.quote("A1", "B2", persist=True, use_day_pass=False)
        assert q["run_id"] is not None
        assert q["fare"] == 4.0 and q["payable"] == 4.0 and q["day_pass"] is None


def test_second_quote_without_day_pass_no_accumulation():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        s.quote("A1", "B2", persist=True, use_day_pass=True)   # 原价 4.0,触顶 3.5
        second = s.quote("A1", "B2", persist=True, use_day_pass=False)
        # 前一笔原价不得加进本单;未勾选一日通,应付 == 本单原价
        assert second["fare"] == 4.0 and second["payable"] == 4.0
        assert second["day_pass"] is None


def test_same_day_two_quotes_no_accumulation():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        q1 = s.quote("A1", "A3", persist=True, use_day_pass=True)
        q2 = s.quote("A1", "A3", persist=True, use_day_pass=True)
        # 两次分段原价都是 3.0 < 3.5,后一次不得把前一次累加进封顶比较
        assert q1["payable"] == 3.0 and q1["day_pass"]["capped"] is False
        assert q2["payable"] == 3.0 and q2["day_pass"]["capped"] is False


def test_new_cap_applies_and_history_snapshot_kept():
    with setup_service() as s:
        s.save_day_pass(TODAY, 3.5, True)
        q1 = s.quote("A1", "B2", persist=True, use_day_pass=True)
        assert q1["payable"] == 3.5 and q1["day_pass"]["capped"] is True
        # 改封顶后,新试算跟新封顶
        s.save_day_pass(TODAY, 5.0, True)
        q2 = s.quote("A1", "B2", persist=True, use_day_pass=True)
        assert q2["payable"] == 4.0 and q2["day_pass"]["capped"] is False
        # 已写入记录保留当时触顶与应付,不被改写
        import json
        rows = {r["id"]: r for r in s.history()}
        r1 = json.loads(rows[q1["run_id"]]["result_json"])
        assert r1["payable"] == 3.5 and r1["day_pass"]["capped"] is True
