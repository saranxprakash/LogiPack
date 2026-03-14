from flask import Flask, request, jsonify, render_template
import csv
import io
from box import Box
from multi_container import pack_multi_container

app = Flask(__name__)


def parse_csv(file_content):
    """Parse CSV text into list of Box objects."""
    boxes  = []
    reader = csv.DictReader(io.StringIO(file_content))
    for i, row in enumerate(reader):
        w       = int(row['width'])
        h       = int(row['height'])
        label   = row.get('label',   f'box_{i+1}').strip()
        weight  = float(row.get('weight',  0) or 0)
        fragile = row.get('fragile', 'False').strip().lower() == 'true'
        boxes.append(Box(w, h, label, weight, fragile))
    return boxes


def containers_to_json(containers, unplaceable, W, H, max_weight):
    """Convert packing result into JSON-serialisable dict."""
    total_placed = sum(len(c['placed']) for c in containers)
    total_failed = len(unplaceable)
    total_boxes  = total_placed + total_failed
    total_area   = W * H * len(containers)
    used_area    = sum(r.w * r.h
                       for c in containers for r in c['placed'])
    total_weight = sum(c['total_weight'] for c in containers)

    space_eff = round((used_area / total_area) * 100, 1) if total_area else 0
    box_eff   = round((total_placed / total_boxes) * 100, 1) if total_boxes else 0
    combined  = round(0.6 * space_eff + 0.4 * box_eff, 1)

    return {
        'summary': {
            'containers'      : len(containers),
            'total_boxes'     : total_boxes,
            'placed'          : total_placed,
            'unplaceable'     : total_failed,
            'total_weight'    : round(total_weight, 1),
            'space_efficiency': space_eff,
            'box_efficiency'  : box_eff,
            'combined_score'  : combined,
            'W': W, 'H': H,
            'max_weight': max_weight if max_weight != float('inf') else None
        },
        'containers': [
            {
                'id'          : c['id'],
                'type'        : c.get('type', 'standard'),
                'total_weight': round(c['total_weight'], 1),
                'weight_limit': max_weight if max_weight != float('inf') else None,
                'boxes': [
                    {
                        'x'      : r.x,
                        'y'      : r.y,
                        'w'      : r.w,
                        'h'      : r.h,
                        'label'  : r.label,
                        'weight' : r.weight,
                        'fragile': r.fragile
                    }
                    for r in c['placed']
                ]
            }
            for c in containers
        ],
        'unplaceable': [
            {'label': b.label, 'w': b.w, 'h': b.h,
             'weight': b.weight, 'fragile': b.fragile}
            for b in unplaceable
        ]
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pack', methods=['POST'])
def pack():
    try:
        W          = int(request.form.get('width',      20))
        H          = int(request.form.get('height',     20))
        max_weight = request.form.get('max_weight', '').strip()
        max_weight = float(max_weight) if max_weight else float('inf')

        file = request.files.get('csv_file')
        if not file:
            return jsonify({'error': 'No CSV file uploaded'}), 400

        content = file.read().decode('utf-8')
        boxes   = parse_csv(content)

        if not boxes:
            return jsonify({'error': 'No boxes found in CSV'}), 400

        containers, unplaceable = pack_multi_container(
            boxes, W, H, max_weight=max_weight
        )

        result = containers_to_json(containers, unplaceable, W, H, max_weight)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)