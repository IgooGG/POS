import os
from datetime import datetime
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24)

# Receipt overall width and column splits
WIDTH = 29
COL1_W, COL2_W, COL3_W, COL4_W = 2, 10, 6, 6

ITEMS = [
    {'name': 'Lemoniada', 'price': 2.00},
    {'name': 'Slime',     'price': 5.00},
    {'name': 'Woda gaz',    'price': 5.00},
    {'name': 'NIE-MA',    'price': 0.00},
    {'name': 'NIE-MA',    'price': 0.00},
    {'name': 'NIE-MA',    'price': 0.00},
    {'name': 'NIE-MA',    'price': 0.00},
    {'name': 'NIE-MA',    'price': 0.00},
    {'name': 'NIE-MA',    'price': 0.00},
]

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
    data = request.get_json()
    name  = data.get('name')
    price = float(data.get('price', 0))
    session['order_items'].append({'name': name, 'price': price})
    session['total'] += price
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

    sep    = '-' * WIDTH
    title  = 'Lemonado'.center(WIDTH)
    fiscal = 'PARAGON FISKALNY'.center(WIDTH)
    now    = datetime.now().strftime('%H-%M %d-%m-%Y')

    # Build each line with sequential index
    item_lines = []
    for idx, it in enumerate(session['order_items'], start=1):
        num  = str(idx).center(COL1_W)
        desc = it['name'][:COL2_W].ljust(COL2_W)
        unit = f'{it["price"]:.2f}zł'.rjust(COL3_W)
        tot  = f'{it["price"]:.2f}zł'.rjust(COL4_W)
        item_lines.append(f'|{num}|{desc}|{unit}|{tot}|')

    blank_row = '|' + ' ' * COL1_W + '|'

    # Summary row with "Suma:" and zł at end
    suma_str          = f'Suma: {session["total"]:.2f}zł'
    space_for_summary = WIDTH - len(blank_row)
    summary           = blank_row + suma_str.rjust(space_for_summary)

    ty1 = 'Dziękujemy za zamówienie'.center(WIDTH)
    ty2 = 'Wesołych wakacji'.center(WIDTH)

    lines = [
        sep,
        title,
        sep,
        '',
        fiscal,
        '',
        sep,
        f'Data: {now}',
        sep,
        *item_lines,
        blank_row,
        summary,
        sep,
        ty1,
        ty2,
        sep,
        '', '', ''  # three extra blank lines
    ]
    receipt = '\n'.join(lines)

    # Encode for RawBT intent
    payload    = receipt.replace('\n', '%0A').replace(' ', '%20')
    intent_uri = (
        f'intent:{payload}'
        '#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end'
    )

    # Clear session
    session['order_items'] = []
    session['total']       = 0.0
    session.modified       = True

    return jsonify(order=[], total=0.0, intent_uri=intent_uri)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )
