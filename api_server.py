from flask import Flask, request, jsonify
import joblib, numpy as np, time, logging
from prometheus_client import Counter, Histogram, generate_latest

app = Flask(__name__)
PREDICTION_COUNT = Counter('ml_predictions_total', 'Total predictions made')
PREDICTION_DURATION = Histogram('ml_prediction_duration_seconds', 'Prediction duration')
ERROR_COUNT = Counter('ml_errors_total', 'Total errors', ['error_type'])

class ModelServer:
    def __init__(self):
        self.model = None
        self.model_version = None
        self.load_model()
    def load_model(self):
        try:
            self.model = joblib.load('models/production_model.pkl')
            with open('models/model_version.txt') as f:
                self.model_version = f.read().strip()
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            ERROR_COUNT.labels(error_type='model_loading').inc()

model_server = ModelServer()

@app.route('/predict', methods=['POST'])
def predict():
    start_time = time.time()
    try:
        data = request.get_json()
        if not data or 'features' not in data:
            ERROR_COUNT.labels(error_type='invalid_input').inc()
            return jsonify({'error': 'Invalid input format'}), 400
        features = np.array(data['features']).reshape(1, -1)
        prediction = model_server.model.predict(features)[0]
        probability = model_server.model.predict_proba(features)[0].max()
        PREDICTION_COUNT.inc()
        PREDICTION_DURATION.observe(time.time() - start_time)
        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'model_version': model_server.model_version,
            'timestamp': time.time()
        })
    except Exception as e:
        ERROR_COUNT.labels(error_type='prediction_error').inc()
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/metrics')
def metrics():
    return generate_latest()

@app.route('/health')
def health():
    if model_server.model is None:
        return jsonify({'status': 'unhealthy'}), 503
    return jsonify({'status': 'healthy', 'model_version': model_server.model_version})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)