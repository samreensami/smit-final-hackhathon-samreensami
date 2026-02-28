from flask import Blueprint, render_template, request, jsonify
from analyzer import ReceiptAnalyzer

# Using a Blueprint for cleaner modularity
main_routes = Blueprint('main', __name__)
analyzer = ReceiptAnalyzer()

@main_routes.route('/')
def index():
    """Main dashboard route."""
    return render_template('index.html')

@main_routes.route('/upload', methods=['POST'])
def upload():
    """Endpoint for AJAX image upload and analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read file as bytes to pass to analyzer
        img_bytes = file.read()
        analysis_result = analyzer.analyze(img_bytes)
        
        if "error" in analysis_result:
            return jsonify(analysis_result), 500
            
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500