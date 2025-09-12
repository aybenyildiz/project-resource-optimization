from flask import Flask, request, jsonify
from flask_cors import CORS
from celery.result import AsyncResult
from celery_worker import celery_app, optimize_plan_task
import pandas as pd
import numpy as np
import io

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/api/optimize', methods=['POST'])
def start_optimization():
    if not request.json:
        return jsonify({"error": "Geçersiz istek: JSON verisi bulunamadı"}), 400
    
    data = request.get_json()
    task = optimize_plan_task.delay(data)
    return jsonify({"task_id": task.id}), 202

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task_result = AsyncResult(task_id, app=celery_app)
    
    result_data = None
    if task_result.successful():
        result_data = task_result.get()
    elif task_result.failed():
        result_data = str(task_result.info)

    return jsonify({
        "task_id": task_id,
        "status": task_result.status,
        "result": result_data
    })

@app.route('/api/import_excel', methods=['POST'])
def import_excel():
    """Excel dosyasını alır, işler ve ön yüze uygun JSON formatında döndürür."""
    if 'file' not in request.files:
        return jsonify({"error": "İstekte dosya bulunamadı."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Dosya seçilmedi."}), 400

    try:
        # Dosyayı bayt olarak oku
        file_bytes = file.read()
        xls = pd.ExcelFile(io.BytesIO(file_bytes))

        required_sheets = ['Activities', 'Resources', 'Precedences', 'Settings']
        for sheet in required_sheets:
            if sheet not in xls.sheet_names:
                return jsonify({"error": f"Excel dosyasında '{sheet}' sayfası bulunamadı."}), 400
        
        # Sayfaları DataFrame olarak oku
        df_activities = pd.read_excel(xls, 'Activities')
        df_resources = pd.read_excel(xls, 'Resources')
        df_precedences = pd.read_excel(xls, 'Precedences')
        df_settings = pd.read_excel(xls, 'Settings')

        # Veriyi JSON formatına dönüştür
        data = {
            "projects": df_activities['Project'].unique().tolist(),
            "activities": df_activities.groupby('Project')['Activity'].apply(list).to_dict(),
            "resources": df_resources['Resource'].tolist(),
            "precedences": {},
            "resource_requirements": {},
            "resource_weights": df_resources.set_index('Resource')['Weight'].to_dict(),
            "earliest_start_times": {}, "project_deadlines": {},
            "max_resource_capacity": df_resources.set_index('Resource')['Capacity'].to_dict(),
            "target_finish_times": {}, "lateness_penalties": {},
            "min_durations": {}, "max_durations": {},
            "time_periods": int(df_settings[df_settings['Setting'] == 'Planning Horizon (Days)']['Value'].iloc[0]),
            "cost_per_day": float(df_settings[df_settings['Setting'] == 'Daily Activity Cost']['Value'].iloc[0])
        }

        # Öncüllükleri işle
        for proj in df_precedences['Project'].unique():
            if pd.notna(proj):
                preds = df_precedences[df_precedences['Project'] == proj][['Predecessor', 'Successor']].values.tolist()
                data['precedences'][proj] = [p for p in preds if pd.notna(p[0]) and pd.notna(p[1])]

        # Aktivite detaylarını ve kaynak gereksinimlerini işle
        resource_cols = [col for col in df_activities.columns if col.startswith('Req ')]
        for _, row in df_activities.iterrows():
            proj, act = row['Project'], row['Activity']
            key = f"{act},{proj}"
            data['min_durations'][key] = int(row['Min Duration'])
            data['max_durations'][key] = int(row['Max Duration'])
            data['target_finish_times'][key] = int(row['Target Finish'])
            data['lateness_penalties'][key] = int(row['Penalty'])
            for res_col in resource_cols:
                res_name = res_col.replace('Req ', '')
                if res_name in data['resources'] and pd.notna(row[res_col]) and int(row[res_col]) > 0:
                    data['resource_requirements'][f"{key},{res_name}"] = int(row[res_col])
        
        # Projeler için varsayılan başlangıç ve bitiş tarihlerini ayarla
        for proj in data['projects']:
            data['earliest_start_times'][proj] = 1
            data['project_deadlines'][proj] = data['time_periods'] * 2

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": f"Dosya işlenirken bir hata oluştu: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)


