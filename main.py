from flask import Flask, render_template, request, session, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-random-key'

ITEMS = [
    {'name': 'Coffee',   'price': 2.50},
    {'name': 'Tea',      'price': 2.00},
    {'name': 'Sandwich', 'price': 5.00},
    {'name': 'Cake',     'price': 3.00},
    {'name': 'Juice',    'price': 2.80},
    {'name': 'Salad',    'price': 4.50},
    {'name': 'Water',    'price': 1.00},
    {'name': 'Cookie',   'price': 1.50},
    {'name': 'Smoothie', 'price': 4.00},
]

# Receipt overall width and column splits
WIDTH = 29
COL1_W, COL2_W, COL3_W, COL4_W = 2, 10, 6, 6

def _init_order():
    session.setdefault('order_items', [])
    session.setdefault('total', 0.0)

@app.route('/')
def index():
    _init_order()
    return render_template('index.html', items=ITEMS)

@app.route('/add_item', methods=['POST'])
def add_item():
    _init_order()
    data = request.json
    session['order_items'].append({
        'name': data['name'],
        'price': float(data['price'])
    })
    session['total'] += float(data['price'])
    session.modified = True
    return jsonify(order=session['order_items'], total=session['total'])

@app.route('/clear_order', methods=['POST'])
def clear_order():
    session['order_items'] = []
    session['total'] = 0.0
    session.modified = True
    return jsonify(order=[], total=0.0)

@app.route('/finish_order', methods=['POST'])
def finish_order():
    _init_order()

    # ASCII‑hyphen separator
    sep    = "-" * WIDTH
    title  = "Lemonado".center(WIDTH)
    fiscal = "PARAGON FISKALNY".center(WIDTH)
    now    = datetime.now().strftime("%H-%M %d-%m-%Y")

    # Build each line with a sequential index
    item_lines = []
    for idx, it in enumerate(session['order_items'], start=1):
        num  = str(idx).center(COL1_W)
        desc = it['name'][:COL2_W].ljust(COL2_W)
        unit = f"€{it['price']:.2f}".rjust(COL3_W)
        tot  = f"€{it['price']:.2f}".rjust(COL4_W)
        item_lines.append(f"|{num}|{desc}|{unit}|{tot}|")

    # Blank row before summary
    blank_row = "|" + " " * COL1_W + "|"

    # Summary row with "Suma:" label
    suma_str          = f"Suma: €{session['total']:.2f}"
    space_for_summary = WIDTH - len(blank_row)
    summary           = blank_row + suma_str.rjust(space_for_summary)

    # Thank‑you lines
    ty1 = "Dziękujemy za zamówienie".center(WIDTH)
    ty2 = "Wesołych wakacji".center(WIDTH)

    # Assemble receipt with 3 trailing blank lines
    lines = [
        sep,
        title,
        sep,
        "",            # blank
        fiscal,
        "",            # blank
        sep,
        f"Data: {now}",
        sep,
        *item_lines,
        blank_row,
        summary,
        sep,
        ty1,
        ty2,
        sep,
        "", "", ""     # three extra blank lines
    ]
    receipt = "\n".join(lines)

    # Encode for RawBT intent
    payload    = receipt.replace("\n", "%0A").replace(" ", "%20")
    intent_uri = f"intent:{payload}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"

    print("🔔 RawBT Intent URI:", intent_uri)

    # Clear session
    session['order_items'] = []
    session['total']       = 0.0
    session.modified       = True

    return jsonify(order=[], total=0.0, intent_uri=intent_uri)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
