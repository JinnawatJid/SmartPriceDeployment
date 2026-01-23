from config.db_sqlite import get_conn


def match_rule(rule, product):
    pg = rule["Product Group"]
    sg = rule["Product Sub Group"]

    if pg and sg:
        return (
            product["productGroup"] == pg and
            product["productSubGroup"] == sg
        )

    if pg:
        return product["productGroup"] == pg

    if sg:
        return product["productSubGroup"] == sg

    return False


def get_cross_sell(products):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM Rule
        ORDER BY ruleNo, ruleSeq
    """)

    rules = [dict(r) for r in cur.fetchall()]
    conn.close()

    cart_groups = {
        p["productGroup"]
        for p in products
        if p.get("productGroup")
    }

    result = []
    added = set()

    rules_by_no = {}
    for r in rules:
        rules_by_no.setdefault(r["ruleNo"], []).append(r)

    for rule_no in sorted(rules_by_no.keys()):
        block = rules_by_no[rule_no]

        mains = [r for r in block if r["Type"] == "main"]
        subs  = [r for r in block if r["Type"] == "sub"]

        # 1. trigger rule
        triggered = False
        for p in products:
            for m in mains:
                if match_rule(m, p):
                    triggered = True
                    break
            if triggered:
                break

        if not triggered:
            continue

        # 2. หา main ที่ยังไม่มี
        missing_mains = [
            r for r in mains
            if r["Product Group"] not in cart_groups
        ]

        candidates = missing_mains if missing_mains else subs

        for r in candidates:
            name = r["DisplayName"]
            if name in added:
                continue

            result.append({
                "displayName": name,
                "ruleNo": r["ruleNo"],
                "ruleType": r["Type"],
                "ruleGroup": r.get("Group")
            })
            added.add(name)

    return result
