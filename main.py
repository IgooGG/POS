import os
from datetime import datetime
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

load_dotenv()  # take environment variables from .env.


app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24)


# Receipt layout constants
WIDTH = 29
COL1_W, COL2_W, COL3_W, COL4_W = 2, 10, 6, 6

# Menu items
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


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _init_order():
    """Ensure session has order_items list and total set."""
    session.setdefault('order_items', [])
    session.setdefault('total', 0.0)



# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route('/')
def index():
    """Render the main ordering page."""
    _init_order()
    return render_template('index.html', items=ITEMS)



@app.route('/add_item', methods=['POST'])
def add_item():
    """Add one item to the session order."""
    _init_order()
    data = request.get_json()
    name = data.get('name')
    price = float(data.get('price', 0))
    session['order_items'].append({'name': name, 'price': price})
    session['total'] += price
    session.modified = True
    return jsonify(order=session['order_items'], total=session['total'])



@app.route('/clear_order', methods=['POST'])
def clear_order():
    """Clear the current order."""
    session['order_items'] = []
    session['total'] = 0.0
    session.modified = True
    return jsonify(order=[], total=0.0)



@app.route('/finish_order', methods=['POST'])
def finish_order():
    """Generate a formatted receipt and return a RawBT intent URI."""
    _init_order()

    sep    = "-" * WIDTH
    title  = "Lemonado".center(WIDTH)
    fiscal = "PARAGON FISKALNY".center(WIDTH)
    now    = datetime.now().strftime("%H-%M %d-%m-%Y")

    # Line items
    item_lines = []
    for idx, it in enumerate(session['order_items'], start=1):
        num  = str(idx).center(COL1_W)
        desc = it['name'][:COL2_W].ljust(COL2_W)
        unit = f"€{it['price']:.2f}".rjust(COL3_W)
        tot  = f"€{it['price']:.2f}".rjust(COL4_W)
        item_lines.append(f"|{num}|{desc}|{unit}|{tot}|")

    # Summary
    blank_row         = "|" + " " * COL1_W + "|"
    suma_str          = f"Suma: €{session['total']:.2f}"
    space_for_summary = WIDTH - len(blank_row)
    summary           = blank_row + suma_str.rjust(space_for_summary)

    # Thank‑you notes
    ty1 = "Dziękujemy za zamówienie".center(WIDTH)
    ty2 = "Wesołych wakacji".center(WIDTH)

    lines = [
        sep,
        title,
        sep,
        "",
        fiscal,
        "",
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
        "", "", ""
    ]
    receipt = "\n".join(lines)

    # Encode for RawBT intent
    payload    = receipt.replace("\n", "%0A").replace(" ", "%20")
    intent_uri = (
        f"intent:{payload}"
        "#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    )

    # Reset order
    session['order_items'] = []
    session['total']       = 0.0
    session.modified       = True

    return jsonify(order=[], total=0.0, intent_uri=intent_uri)



# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # In production, use a WSGI server instead of Flask's built‐in
    app.run(host='0.0.0.0', port=5000, debug=True)
