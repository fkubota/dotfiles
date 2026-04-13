"""
aurelius dashboard generator — Timeline style
Markdownファイルをパースして進捗ダッシュボードHTMLを生成する
"""

import argparse
import re
from datetime import date, datetime, timedelta
from pathlib import Path

GANTT_COLORS = ["c0", "c1", "c2", "c3"]


def parse_plan(plan_path: Path) -> dict:
    """PLAN.mdをパースしてpj情報を取得"""
    text = plan_path.read_text(encoding="utf-8")
    plan = {"name": "", "goal": "", "deadline": None, "easy_deadline": None, "start": None, "cycles": []}

    m = re.search(r"^# (.+)$", text, re.MULTILINE)
    if m:
        plan["name"] = m.group(1).strip()

    m = re.search(r"## ゴール\n(.+?)(?:\n##|\Z)", text, re.DOTALL)
    if m:
        plan["goal"] = m.group(1).strip()

    for line in text.splitlines():
        if "最終期限" in line:
            d = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if d:
                plan["deadline"] = datetime.strptime(d.group(1), "%Y-%m-%d").date()
        if "楽勝スケジュール" in line or "余裕ライン" in line:
            d = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if d:
                plan["easy_deadline"] = datetime.strptime(d.group(1), "%Y-%m-%d").date()

    in_table = False
    for line in text.splitlines():
        if "PDCAサイクル" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line and "サイクル" not in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3:
                plan["cycles"].append({
                    "name": cols[0],
                    "period": cols[1],
                    "goal": cols[2],
                })
        elif in_table and not line.startswith("|") and line.strip():
            in_table = False

    return plan


def parse_tasks(tasks_path: Path) -> dict:
    text = tasks_path.read_text(encoding="utf-8")
    tasks = {"cycle_name": "", "cycle_goal": "", "items": [], "all_items": [], "backlog": []}

    m = re.search(r"## 現在のサイクル[:：]\s*(.+)", text)
    if m:
        tasks["cycle_name"] = m.group(1).strip()

    m = re.search(r"\*\*ゴール\w?\*?\*?[:：]\s*(.+)", text)
    if m:
        tasks["cycle_goal"] = m.group(1).strip()

    in_table = False
    is_first_table = True
    for line in text.splitlines():
        if re.match(r"\|\s*日付\s*\|", line):
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3:
                item = {
                    "date": cols[0],
                    "task": cols[1],
                    "done": "✅" in cols[2],
                }
                tasks["all_items"].append(item)
                if is_first_table:
                    tasks["items"].append(item)
        elif in_table and not line.startswith("|"):
            in_table = False
            if is_first_table:
                is_first_table = False

    in_backlog = False
    for line in text.splitlines():
        if "バックログ" in line:
            in_backlog = True
            continue
        if in_backlog and line.startswith("- ["):
            done = line.startswith("- [x]")
            item = re.sub(r"^- \[.\]\s*", "", line)
            tasks["backlog"].append({"task": item, "done": done})
        elif in_backlog and line.startswith("##"):
            in_backlog = False

    return tasks


def parse_daily(daily_path: Path) -> list:
    text = daily_path.read_text(encoding="utf-8")
    entries = []
    current = None

    for line in text.splitlines():
        m = re.match(r"^## (\d{4}-\d{2}-\d{2})\s*(.*)", line)
        if m:
            if current:
                entries.append(current)
            current = {"date": m.group(1), "label": m.group(2).strip("() "), "goal": "", "achieved": "", "done": "", "tomorrow": ""}
            continue
        if current:
            if line.startswith("**今日のAゴール**"):
                current["goal"] = re.sub(r"^\*\*今日のAゴール\*\*[:：]\s*", "", line)
            elif line.startswith("**達成**"):
                current["achieved"] = re.sub(r"^\*\*達成\*\*[:：]\s*", "", line)
            elif line.startswith("**やったこと**"):
                current["done"] = re.sub(r"^\*\*やったこと\*\*[:：]\s*", "", line)
            elif line.startswith("**明日のAゴール**"):
                current["tomorrow"] = re.sub(r"^\*\*明日のAゴール\*\*[:：]\s*", "", line)

    if current:
        entries.append(current)
    return entries


def parse_cycle_dates(period_str: str, ref_year: int) -> tuple:
    """サイクルの期間文字列 '3/26〜4/3' をdate型に変換"""
    parts = re.findall(r"(\d{1,2})/(\d{1,2})", period_str)
    if len(parts) >= 2:
        start = date(ref_year, int(parts[0][0]), int(parts[0][1]))
        end = date(ref_year, int(parts[1][0]), int(parts[1][1]))
        return start, end
    elif len(parts) == 1:
        d = date(ref_year, int(parts[0][0]), int(parts[0][1]))
        return d, d
    return None, None


def calc_progress(plan: dict, today: date) -> dict:
    result = {"overall": 0, "easy": 0, "days_left": 0, "easy_days_left": 0, "start": None}

    if not plan.get("deadline"):
        return result

    deadline = plan["deadline"]
    easy_deadline = plan.get("easy_deadline") or deadline

    start = None
    if plan["cycles"]:
        s, _ = parse_cycle_dates(plan["cycles"][0]["period"], today.year)
        start = s

    if not start:
        start = deadline - timedelta(days=30)

    result["start"] = start

    total = (deadline - start).days or 1
    elapsed = (today - start).days
    result["overall"] = min(100, max(0, int(elapsed / total * 100)))
    result["days_left"] = (deadline - today).days

    easy_total = (easy_deadline - start).days or 1
    result["easy"] = min(100, max(0, int(elapsed / easy_total * 100)))
    result["easy_days_left"] = (easy_deadline - today).days

    return result


def calc_task_progress(tasks: dict) -> dict:
    items = tasks["items"]
    if not items:
        return {"done": 0, "total": 0, "percent": 0}
    done = sum(1 for t in items if t["done"])
    total = len(items)
    return {"done": done, "total": total, "percent": int(done / total * 100)}


WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def fmt_date_short(d: date) -> str:
    return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"


def generate_gantt_dates(start: date, end: date) -> str:
    """ガントチャートのヘッダー日付ラベルを生成（絶対位置配置）"""
    total = (end - start).days or 1
    step = max(1, total // 14)
    dates = []
    d = start
    while d <= end:
        dates.append(d)
        d += timedelta(days=step)
    if dates[-1] != end:
        dates.append(end)
    html = ""
    for d in dates:
        pct = (d - start).days / total * 100
        html += f'<span style="position:absolute;left:{pct:.1f}%;transform:translateX(-50%);">{fmt_date_short(d)}</span>'
    return html


def generate_weekend_bands(start: date, end: date) -> str:
    """土日の縦帯HTMLを生成（土=青、日=赤）"""
    total_days = (end - start).days or 1
    bands = ""
    d = start
    while d <= end:
        wd = d.weekday()
        if wd in (5, 6):
            left_pct = (d - start).days / total_days * 100
            width_pct = 1 / total_days * 100
            color = "rgba(74,144,217,0.10)" if wd == 5 else "rgba(228,68,68,0.10)"
            bands += f'<div style="position:absolute;top:0;bottom:0;left:{left_pct:.2f}%;width:{width_pct:.2f}%;background:{color};pointer-events:none;"></div>\n'
        d += timedelta(days=1)
    return bands


def parse_task_date(date_str: str, ref_year: int) -> date | None:
    """タスクの日付文字列 '3/31(火)' をdate型に変換"""
    m = re.search(r"(\d{1,2})/(\d{1,2})", date_str)
    if m:
        return date(ref_year, int(m.group(1)), int(m.group(2)))
    return None


def generate_card_html(pj: dict, today: date) -> str:
    plan = pj["plan"]
    tasks = pj["tasks"]
    daily = pj["daily"]
    progress = pj["progress"]
    task_progress = pj["task_progress"]

    start = progress["start"]
    deadline = plan["deadline"]
    easy_deadline = plan.get("easy_deadline") or deadline

    if not start or not deadline:
        return f'<div class="project-card"><div class="pj-header"><div class="pj-title">{plan["name"] or pj["dir_name"]}</div></div><p>期限が設定されていません</p></div>'

    total_days = (deadline - start).days or 1

    # --- Progress bars ---
    start_label = fmt_date_short(start)
    today_label = fmt_date_short(today)
    deadline_label = fmt_date_short(deadline)
    easy_label = fmt_date_short(easy_deadline)

    overall_pct = progress["overall"]
    easy_pct = progress["easy"]
    overall_color = "#e44" if progress["days_left"] < 0 else "#333"
    easy_color = "#e44" if progress["easy_days_left"] < 0 else "#52b788"

    days_left = progress["days_left"]
    easy_days_left = progress["easy_days_left"]
    overall_note = f'{overall_pct}%' if days_left >= 0 else f'<span class="pbar-pct overdue">{abs(days_left)}日超過</span>'
    easy_note = f'{easy_pct}%' if easy_days_left >= 0 else f'<span class="pbar-pct overdue">{abs(easy_days_left)}日超過</span>'

    easy_today_label = f"今日 {today_label} ＝ 余裕〆" if easy_days_left == 0 else f"今日 {today_label}"
    easy_right = "" if easy_days_left <= 0 else f"<span>{easy_label} 余裕〆</span>"

    # 余裕バーのトラック幅を全体に対する比率で計算
    easy_track_pct = min(100, max(10, (easy_deadline - start).days / total_days * 100))

    progress_html = f"""
    <div class="progress-section">
      <div class="progress-block">
        <div class="progress-block-label">全体進捗 <span class="pbar-pct">{overall_note}</span></div>
        <div class="pbar-track"><div class="pbar-fill" style="width:{overall_pct}%; background:{overall_color};"></div></div>
        <div class="pbar-dates">
          <span>{start_label} 開始</span>
          <span class="now">今日 {today_label}</span>
          <span>{deadline_label} 締切</span>
        </div>
      </div>
      <div class="progress-block">
        <div class="progress-block-label">余裕スケジュール <span class="pbar-pct">{easy_note}</span></div>
        <div class="pbar-track" style="width:{easy_track_pct:.1f}%;"><div class="pbar-fill" style="width:{min(easy_pct, 100)}%; background:{easy_color};"></div></div>
        <div class="pbar-dates" style="width:{easy_track_pct:.1f}%;">
          <span>{start_label} 開始</span>
          <span class="now">{easy_today_label}</span>
          {easy_right}
        </div>
      </div>
    </div>
    """

    # --- Gantt chart ---
    gantt_date_labels = generate_gantt_dates(start, deadline)

    today_pct = min(100, max(0, (today - start).days / total_days * 100))
    weekend_bands = generate_weekend_bands(start, deadline)

    # サイクルごとの日付範囲を先に計算
    cycle_ranges = []
    for i, cycle in enumerate(plan["cycles"]):
        cs, ce = parse_cycle_dates(cycle["period"], today.year)
        cycle_ranges.append((cs, ce, i, cycle))

    # サイクルバー行 + そのサイクルに属するタスクバー
    gantt_rows = ""
    for cs, ce, i, cycle in cycle_ranges:
        if not cs or not ce:
            continue
        left_pct = max(0, (cs - start).days / total_days * 100)
        width_pct = max(1, ((ce - cs).days + 1) / total_days * 100)
        is_buffer = "バッファ" in cycle["name"].lower() or "buffer" in cycle["name"].lower()
        color_class = "buffer" if is_buffer else GANTT_COLORS[i % len(GANTT_COLORS)]
        label_style = ' style="color:#aaa;"' if is_buffer else ""
        bar_label = f'{fmt_date_short(cs)} — {fmt_date_short(ce)}'

        gantt_rows += f"""
        <div class="gantt-row">
          <div class="gantt-row-label"{label_style}>{cycle["name"]}</div>
          <div class="gantt-row-bar-area">
            <div class="gantt-bar {color_class}" style="left:{left_pct:.1f}%; width:{width_pct:.1f}%;">{bar_label}</div>
          </div>
        </div>
        """

        # このサイクルに属するタスクを追加（全サイクル分）
        for t in tasks["all_items"]:
            td = parse_task_date(t["date"], today.year)
            if not td:
                continue
            if td < cs or td > ce:
                continue
            t_left = max(0, (td - start).days / total_days * 100)
            t_width = max(0.5, 1 / total_days * 100)
            bar_bg = "#52b788" if t["done"] else "#ddd"
            icon = "✅ " if t["done"] else "⬜ "
            gantt_rows += f"""
        <div class="gantt-row gantt-row-task">
          <div class="gantt-row-label gantt-task-label">{icon}{t["task"][:24]}</div>
          <div class="gantt-row-bar-area">
            <div class="gantt-bar-task" style="left:{t_left:.1f}%; width:{t_width:.1f}%; background:{bar_bg};" title="{t["date"]} {t["task"]}"></div>
          </div>
        </div>
            """

    gantt_html = f"""
    <div class="gantt">
      <div class="gantt-header">
        <div class="gantt-label-col">CYCLE</div>
        <div class="gantt-chart-col">
          <div class="gantt-today-flag" style="left:{today_pct:.1f}%;">{today_label} TODAY</div>
          <div class="gantt-dates">{gantt_date_labels}</div>
        </div>
      </div>
      <div style="position:relative;">
        <div style="position:absolute; top:0; bottom:0; left:160px; right:0; pointer-events:none;">
          {weekend_bands}
          <div class="gantt-today-line" style="left:{today_pct:.1f}%;"></div>
        </div>
        {gantt_rows}
      </div>
    </div>
    """

    # --- Today's goal ---
    today_str = today.isoformat()
    today_entry = next((e for e in daily if e["date"] == today_str), None)
    today_goal = today_entry["goal"] if today_entry else "未設定"

    today_html = f"""
    <div class="today-section">
      <div class="today-label">TODAY'S A-GOAL</div>
      <div class="today-goal">{today_goal}</div>
    </div>
    """

    # --- Tasks table ---
    cycle_info = tasks["cycle_name"] if tasks["cycle_name"] else "未設定"
    task_rows = ""
    for t in tasks["items"]:
        icon_class = "dot-done" if t["done"] else "dot-todo"
        icon = "✅" if t["done"] else "⬜"
        task_rows += f'<tr><td>{t["date"]}</td><td>{t["task"]}</td><td class="{icon_class}">{icon}</td></tr>\n'

    # --- Daily table (今日のタスクのみ、「+」区切りで分解) ---
    current_cycle_label = ""
    if plan["cycles"]:
        for cyc in plan["cycles"]:
            if cyc["name"] in tasks.get("cycle_name", ""):
                current_cycle_label = cyc["name"]
                break
        if not current_cycle_label and plan["cycles"]:
            current_cycle_label = plan["cycles"][0]["name"]

    today_str = today.isoformat()
    today_daily = next((e for e in daily if e["date"] == today_str), None)

    daily_rows = ""
    if today_daily:
        short_date = fmt_date_short(today)
        # Aゴールを「+」で分解して個別行にする
        sub_tasks = [s.strip() for s in re.split(r'\s*\+\s*', today_daily["goal"]) if s.strip()]
        if not sub_tasks:
            sub_tasks = [today_daily["goal"]]
        overall_icon = "✅" if "✅" in today_daily["achieved"] else "⬜" if today_daily["achieved"] else "—"
        for i, st in enumerate(sub_tasks):
            date_cell = short_date if i == 0 else ""
            daily_rows += f'<tr><td>{date_cell}</td><td>{st}</td><td class="dot-done">{overall_icon}</td></tr>\n'

    tables_html = f"""
    <div class="two-col">
      <div>
        <div class="section-title">Cycle Tasks — {cycle_info} ({task_progress["done"]}/{task_progress["total"]})</div>
        <table>
          <thead><tr><th>日付</th><th>タスク</th><th></th></tr></thead>
          <tbody>{task_rows}</tbody>
        </table>
      </div>
      <div>
        <div class="section-title">Today's Tasks (PDCA {current_cycle_label})</div>
        <table>
          <thead><tr><th>日付</th><th>タスク</th><th></th></tr></thead>
          <tbody>{daily_rows}</tbody>
        </table>
      </div>
    </div>
    """

    return f"""
    <div class="project-card">
      <div class="pj-header">
        <div class="pj-title">{plan["name"] or pj["dir_name"]}</div>
        <div class="pj-goal">{plan["goal"]}</div>
      </div>
      <div class="section-title">Overall Progress</div>
      {progress_html}
      <div class="section-title">Gantt Chart</div>
      {gantt_html}
      {today_html}
      {tables_html}
    </div>
    """


def generate_html(projects: list, today: date) -> str:
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    template = template_path.read_text(encoding="utf-8")

    cards_html = ""
    for pj in projects:
        cards_html += generate_card_html(pj, today)

    html = template.replace("{{DATE}}", today.isoformat())
    html = html.replace("{{PROJECT_COUNT}}", str(len(projects)))
    html = html.replace("{{CARDS}}", cards_html)
    return html


def main():
    parser = argparse.ArgumentParser(description="aurelius dashboard generator")
    parser.add_argument("--data-dir", required=True, help="projects directory path")
    parser.add_argument("--output", required=True, help="output HTML path")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_path = Path(args.output)
    today = date.today()

    projects = []

    if not data_dir.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = generate_html([], today)
        output_path.write_text(html, encoding="utf-8")
        print(f"Empty dashboard generated: {output_path}")
        return

    for pj_dir in sorted(data_dir.iterdir()):
        if not pj_dir.is_dir():
            continue

        plan_path = pj_dir / "PLAN.md"
        tasks_path = pj_dir / "TASKS.md"
        daily_path = pj_dir / "DAILY.md"

        plan = parse_plan(plan_path) if plan_path.exists() else {"name": "", "goal": "", "deadline": None, "easy_deadline": None, "start": None, "cycles": []}
        tasks = parse_tasks(tasks_path) if tasks_path.exists() else {"cycle_name": "", "cycle_goal": "", "items": [], "all_items": [], "backlog": []}
        daily = parse_daily(daily_path) if daily_path.exists() else []
        progress = calc_progress(plan, today)
        task_progress = calc_task_progress(tasks)

        projects.append({
            "dir_name": pj_dir.name,
            "plan": plan,
            "tasks": tasks,
            "daily": daily,
            "progress": progress,
            "task_progress": task_progress,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = generate_html(projects, today)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {output_path} ({len(projects)} projects)")


if __name__ == "__main__":
    main()
