import argparse
import ast
import csv
import json
import os
import re
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch


CORE_IMPORT_PLAN = [
    ("cenro_adminuser.csv", "cenro_adminuser"),
    ("cenro_termsandconditions.csv", "cenro_termsandconditions"),
    ("accounts_barangay.csv", "accounts_barangay"),
    ("accounts_family.csv", "accounts_family"),
    ("accounts_users.csv", "accounts_users"),
    ("accounts_rewardcategory.csv", "accounts_rewardcategory"),
    ("accounts_reward.csv", "accounts_reward"),
    ("accounts_reward_available_barangays.csv", "accounts_reward_available_barangays"),
    ("accounts_wastetype.csv", "accounts_wastetype"),
    ("accounts_garbageschedule.csv", "accounts_garbageschedule"),
    ("accounts_pointstransaction.csv", "accounts_pointstransaction"),
    # Source file name intentionally kept as-is (typo from export)
    ("accounts_redemtion.csv", "accounts_redemption"),
    ("accounts_rewardhistory.csv", "accounts_rewardhistory"),
    ("accounts_notification.csv", "accounts_notification"),
    ("accounts_userconsent.csv", "accounts_userconsent"),
    ("accounts_wastetransaction.csv", "accounts_wastetransaction"),
]


GAME_IMPORT_PLAN = [
    ("game_wastecategory.csv", "game_wastecategory"),
    ("game_wasteitem.csv", "game_wasteitem"),
    ("game_question.csv", "game_question"),
    ("game_choice.csv", "game_choice"),
]


LEARN_IMPORT_PLAN = [
    ("learn_quizquestion.csv", "learn_quizquestion"),
    ("learn_quizresult.csv", "learn_quizresult"),
    ("learn_quizanswer.csv", "learn_quizanswer"),
]


PLAN_GROUPS = {
    "core": CORE_IMPORT_PLAN,
    "game": GAME_IMPORT_PLAN,
    "learn": LEARN_IMPORT_PLAN,
    "all": CORE_IMPORT_PLAN + GAME_IMPORT_PLAN + LEARN_IMPORT_PLAN,
}


def get_connection():
    required = ["RW_DB_HOST", "RW_DB_PORT", "RW_DB_NAME", "RW_DB_USER", "RW_DB_PASS"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    return psycopg2.connect(
        host=os.environ["RW_DB_HOST"],
        port=os.environ["RW_DB_PORT"],
        dbname=os.environ["RW_DB_NAME"],
        user=os.environ["RW_DB_USER"],
        password=os.environ["RW_DB_PASS"],
        sslmode="require",
        connect_timeout=10,
    )


def fetch_columns(cur, table_name):
    cur.execute(
        """
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError(f"Table not found or has no columns: {table_name}")
    columns = [r[0] for r in rows]
    nullable = {r[0]: (r[1] == "YES") for r in rows}
    return columns, nullable


def fetch_primary_key_columns(cur, table_name):
    cur.execute(
        """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_class t ON t.oid = i.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
        WHERE n.nspname = 'public'
          AND t.relname = %s
          AND i.indisprimary
        ORDER BY array_position(i.indkey, a.attnum)
        """,
        (table_name,),
    )
    return [r[0] for r in cur.fetchall()]


def _convert_cells(row, nullable_map, columns):
    converted = []
    for idx, raw in enumerate(row):
        col = columns[idx]
        if raw == "" and nullable_map[col]:
            converted.append(None)
        else:
            converted.append(raw)
    return converted


def read_csv_rows(file_path, expected_col_count, nullable_map, columns):
    """
    Read CSV with auto header detection.
    Some legacy exports include a header row; others are data-only.
    """
    parsed = []
    with file_path.open("r", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]

    if not rows:
        return parsed

    first = [c.strip().lower() for c in rows[0]]
    expected = [c.strip().lower() for c in columns]
    has_header = len(rows[0]) == expected_col_count and first == expected

    data_rows = rows[1:] if has_header else rows
    start_line = 2 if has_header else 1

    for offset, row in enumerate(data_rows, start=0):
        line_no = start_line + offset
        if len(row) != expected_col_count:
            raise ValueError(
                f"{file_path.name}:{line_no} has {len(row)} columns; expected {expected_col_count}"
            )
        parsed.append(_convert_cells(row, nullable_map, columns))

    return parsed


def read_notification_rows(file_path, expected_col_count, nullable_map, columns):
    """
    Handle legacy rows where message text contains unescaped commas/quotes.
    Expected shape is 11 columns:
    id, type, message, points, reward_name, video_title, game_score,
    is_read, viewed_at, created_at, user_id
    """
    parsed = []
    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line_no, row in enumerate(reader, start=1):
            if not row:
                continue

            if len(row) < expected_col_count:
                raise ValueError(
                    f"{file_path.name}:{line_no} has {len(row)} columns; expected at least {expected_col_count}"
                )

            if len(row) == expected_col_count:
                normalized = row
            else:
                # Preserve first 2 columns and last 8 fixed columns; merge middle as message.
                fixed_tail = row[-8:]
                merged_message = ",".join(row[2:-8]).strip()
                normalized = [row[0], row[1], merged_message, *fixed_tail]

            parsed.append(_convert_cells(normalized, nullable_map, columns))
    return parsed


def read_terms_rows(file_path, expected_col_count, nullable_map, columns):
    """
    Recover legacy terms export with multiline content that may contain
    unescaped quotes and commas.
    """
    uuid_start = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12},")

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    records = []
    buf = []
    for line in lines:
        if uuid_start.match(line):
            if buf:
                records.append("\n".join(buf))
            buf = [line]
        else:
            if buf:
                buf.append(line)
    if buf:
        records.append("\n".join(buf))

    parsed = []
    for i, rec in enumerate(records, start=1):
        head = rec.split(",", 4)
        if len(head) != 5:
            raise ValueError(f"{file_path.name}:record {i} invalid header shape")

        id_val, lang, title, version, remainder = head

        # RSplit from right for fixed tail: file, is_active, created_at,
        # updated_at, created_by_id, updated_by_id
        tail = remainder.rsplit(",", 6)
        if len(tail) != 7:
            raise ValueError(f"{file_path.name}:record {i} invalid tail shape")

        content, file_col, is_active, created_at, updated_at, created_by, updated_by = tail
        content = content.strip()
        if content.startswith('"') and content.endswith('"') and len(content) >= 2:
            content = content[1:-1]

        row = [
            id_val,
            lang,
            title,
            version,
            content,
            file_col,
            is_active,
            created_at,
            updated_at,
            created_by,
            updated_by,
        ]

        if len(row) != expected_col_count:
            raise ValueError(
                f"{file_path.name}:record {i} has {len(row)} columns; expected {expected_col_count}"
            )

        normalized_row = [r.strip() if isinstance(r, str) else r for r in row]
        parsed.append(_convert_cells(normalized_row, nullable_map, columns))

    return parsed


def _normalize_json_array(raw_value):
    if raw_value is None:
        return None

    s = raw_value.strip()
    if not s:
        return "[]"

    # Try strict JSON first.
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return json.dumps(parsed)
    except Exception:
        pass

    # Try Python-literal style list strings.
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, (list, tuple)):
            return json.dumps(list(parsed))
    except Exception:
        pass

    # Last-resort extraction for malformed legacy strings.
    tokens = [t.strip() for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9 .-]*", s) if t.strip()]
    return json.dumps(tokens if tokens else [])


def read_garbageschedule_rows(file_path, expected_col_count, nullable_map, columns):
    parsed = read_csv_rows(file_path, expected_col_count, nullable_map, columns)

    try:
        idx = columns.index("waste_types")
    except ValueError:
        return parsed

    for row in parsed:
        row[idx] = _normalize_json_array(row[idx])

    return parsed


def build_upsert_sql(table_name, columns, pk_columns):
    table_ident = sql.Identifier(table_name)
    col_idents = [sql.Identifier(c) for c in columns]
    placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in columns])

    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        table_ident,
        sql.SQL(", ").join(col_idents),
        placeholders,
    )

    if not pk_columns:
        return insert_sql

    update_cols = [c for c in columns if c not in pk_columns]
    if not update_cols:
        return insert_sql

    set_expr = sql.SQL(", ").join(
        [
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
            for c in update_cols
        ]
    )

    upsert_sql = sql.SQL("{} ON CONFLICT ({}) DO UPDATE SET {}").format(
        insert_sql,
        sql.SQL(", ").join([sql.Identifier(c) for c in pk_columns]),
        set_expr,
    )
    return upsert_sql


def sync_serial_sequence(cur, table_name):
    cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (f"public.{table_name}",))
    seq = cur.fetchone()[0]
    if not seq:
        return

    cur.execute(
        sql.SQL(
            "SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {}), 1), true)"
        ).format(sql.Identifier(table_name)),
        (seq,),
    )


def build_import_plan(selected_groups):
    seen = set()
    plan = []
    for group in selected_groups:
        for item in PLAN_GROUPS[group]:
            if item not in seen:
                seen.add(item)
                plan.append(item)
    return plan


def _extract_int(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return int(s)


def ensure_learningvideo_refs_exist(cur, table_name, rows, columns):
    if table_name not in {"learn_quizquestion", "learn_quizresult"}:
        return

    video_idx = columns.index("video_id")
    referenced = sorted({_extract_int(r[video_idx]) for r in rows if r[video_idx] is not None})
    if not referenced:
        return

    cur.execute("SELECT id FROM learn_learningvideo WHERE id = ANY(%s)", (referenced,))
    existing = {int(r[0]) for r in cur.fetchall()}
    missing = [str(v) for v in referenced if v not in existing]
    if missing:
        raise RuntimeError(
            "Missing required learn_learningvideo rows for "
            f"{table_name}: {', '.join(missing)}. "
            "Import video base data first."
        )


def main():
    parser = argparse.ArgumentParser(description="Import EKOLEK CSV data into PostgreSQL safely")
    parser.add_argument(
        "--data-dir",
        default="EKOLEK DATA",
        help="Directory containing CSV exports (default: EKOLEK DATA)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV structure and schema mapping without writing data",
    )
    parser.add_argument(
        "--group",
        action="append",
        choices=sorted(PLAN_GROUPS.keys()),
        help="Import group(s): core, game, learn, all (default: core)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists() or not data_dir.is_dir():
        raise RuntimeError(f"Data directory not found: {data_dir}")

    selected_groups = args.group or ["core"]
    import_plan = build_import_plan(selected_groups)

    with get_connection() as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            imported_counts = {}

            for file_name, table_name in import_plan:
                csv_path = data_dir / file_name
                if not csv_path.exists():
                    raise RuntimeError(f"Missing CSV file: {csv_path}")

                columns, nullable_map = fetch_columns(cur, table_name)
                pk_columns = fetch_primary_key_columns(cur, table_name)

                if file_name == "cenro_termsandconditions.csv":
                    rows = read_terms_rows(csv_path, len(columns), nullable_map, columns)
                elif file_name == "accounts_notification.csv":
                    rows = read_notification_rows(csv_path, len(columns), nullable_map, columns)
                elif file_name == "accounts_garbageschedule.csv":
                    rows = read_garbageschedule_rows(csv_path, len(columns), nullable_map, columns)
                else:
                    rows = read_csv_rows(csv_path, len(columns), nullable_map, columns)

                ensure_learningvideo_refs_exist(cur, table_name, rows, columns)

                print(f"VALIDATED {file_name} -> {table_name} ({len(rows)} rows)")

                if not args.dry_run and rows:
                    stmt = build_upsert_sql(table_name, columns, pk_columns)
                    execute_batch(cur, stmt, rows, page_size=500)
                    sync_serial_sequence(cur, table_name)

                imported_counts[table_name] = len(rows)

            if args.dry_run:
                conn.rollback()
                print("DRY_RUN_OK: no changes written")
            else:
                conn.commit()
                print("IMPORT_OK")

            print("SUMMARY")
            for t, count in imported_counts.items():
                print(f"- {t}: {count}")


if __name__ == "__main__":
    main()
