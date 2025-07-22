from ortools.sat.python import cp_model
import pandas as pd
from datetime import date, timedelta
import jpholiday

def is_holiday(d: date) -> bool:
    """土日 or 日本の祝日を True"""
    return d.weekday() >= 5 or jpholiday.is_holiday(d)

def build_schedule(start: date,
                   end: date,
                   doctors_df: pd.DataFrame,
                   off_requests_df: pd.DataFrame):
    """
    必要人数: 平日1, 土日祝2
    医師ごとの曜日NG/特定日希望休（ハード）/連続禁止
    公平性: max_cnt - min_cnt 最小化
    戻り値: (schedule_df, counts_dict)
    doctors_df columns: doctor_id(int), name(str), cannot_mon..cannot_sun (0/1)
    off_requests_df columns: doctor_id(int), date(str)
    """

    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    need = {d: 2 if is_holiday(d) else 1 for d in days}

    dow_cols = ["mon","tue","wed","thu","fri","sat","sun"]
    cannot = {
        int(row.doctor_id): {i: bool(row[f"cannot_{dow_cols[i]}"]) for i in range(7)}
        for _, row in doctors_df.iterrows()
    }

    # 特定日希望休（ハード）
    off_requests = {(int(r.doctor_id), pd.to_datetime(r.date).date())
                    for _, r in off_requests_df.iterrows()} if len(off_requests_df)>0 else set()

    model = cp_model.CpModel()

    slots = [0, 1]  # 最大2枠
    doctor_ids = doctors_df.doctor_id.astype(int).tolist()
    x = {}
    for d in doctor_ids:
        for day in days:
            for s in slots:
                x[d, day, s] = model.NewBoolVar(f"x_{d}_{day}_{s}")

    # 必要人数充足 & 余分枠0
    for day in days:
        model.Add(sum(x[d, day, s] for d in doctor_ids for s in slots) == need[day])
        for s in slots[need[day]:]:
            for d in doctor_ids:
                model.Add(x[d, day, s] == 0)

    # 同一日1枠まで
    for d in doctor_ids:
        for day in days:
            model.Add(sum(x[d, day, s] for s in slots) <= 1)

    # 曜日NG
    for d in doctor_ids:
        for day in days:
            if cannot[d][day.weekday()]:
                for s in slots:
                    model.Add(x[d, day, s] == 0)

    # 特定日希望休（ハード）
    for d in doctor_ids:
        for day in days:
            if (d, day) in off_requests:
                for s in slots:
                    model.Add(x[d, day, s] == 0)

    # 連続当直禁止
    for d in doctor_ids:
        for i in range(len(days) - 1):
            d0, d1 = days[i], days[i + 1]
            model.Add(sum(x[d, d0, s] for s in slots) +
                      sum(x[d, d1, s] for s in slots) <= 1)

    # 公平性
    counts = {d: model.NewIntVar(0, len(days)*2, f"cnt_{d}") for d in doctor_ids}
    for d in doctor_ids:
        model.Add(counts[d] == sum(x[d, day, s] for day in days for s in slots))

    max_cnt = model.NewIntVar(0, len(days)*2, "max_cnt")
    min_cnt = model.NewIntVar(0, len(days)*2, "min_cnt")
    model.AddMaxEquality(max_cnt, list(counts.values()))
    model.AddMinEquality(min_cnt, list(counts.values()))

    model.Minimize(max_cnt - min_cnt)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("解が見つかりませんでした。制約を確認してください。" )

    # 出力整形
    id_to_name = dict(zip(doctors_df.doctor_id.astype(int), doctors_df.name))
    rows = []
    for day in days:
        assigned = ["", ""]
        for s in slots[:need[day]]:
            for d in doctor_ids:
                if solver.Value(x[d, day, s]):
                    assigned[s] = id_to_name[d]
        rows.append({
            "date": day,
            "weekday": "月火水木金土日"[day.weekday()],
            "slot1": assigned[0],
            "slot2": assigned[1] if need[day] == 2 else ""
        })

    schedule_df = pd.DataFrame(rows)
    counts_dict = {d: int(solver.Value(counts[d])) for d in doctor_ids}
    return schedule_df, counts_dict
