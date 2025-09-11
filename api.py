from flask import Flask, request, jsonify
from flask_cors import CORS  # YENİ import
from celery.result import AsyncResult
from celery_worker import celery_app, optimize_plan_task

app = Flask(__name__)
# YENİ: Tarayıcıdan gelen isteklere izin vermek için CORS'u etkinleştiriyoruz
CORS(app)

# YENİ: Frontend'in API'nin çalışıp çalışmadığını kontrol etmesi için basit bir rota
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/api/optimize', methods=['POST'])
def start_optimization():
    """Optimizasyon görevini başlatır ve görev ID'sini döndürür."""
    if not request.json:
        return jsonify({"error": "Geçersiz istek: JSON verisi bulunamadı"}), 400
    
    data = request.get_json()
    task = optimize_plan_task.delay(data)
    return jsonify({"task_id": task.id}), 202

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Verilen görev ID'sinin durumunu ve sonucunu (varsa) döndürür."""
    # Celery'nin hangi backend'i kullanacağını bilmesi için app context'ini kullanıyoruz
    task_result = AsyncResult(task_id, app=celery_app)
    
    result = None
    if task_result.successful():
        result = task_result.get()
    elif task_result.failed():
        # Hatanın nedenini daha detaylı almak için
        result = str(task_result.info)

    return jsonify({
        "task_id": task_id,
        "status": task_result.status,
        "result": result
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

