from pulp import *
import json

def optimize_plan(data):
    """
    Proje verilerini girdi olarak alır, kaynak seviyelendirme optimizasyonunu çalıştırır
    ve sonuçları bir dictionary olarak döndürür.

    Args:
        data (dict): Proje, aktivite, kaynak ve kısıtları içeren veri.

    Returns:
        dict: Optimizasyon sonuçlarını içeren dictionary.
    """

    # 1. Adım: Gelen veriden parametreleri ayıklama
    J = data["projects"]
    I = data["activities"]
    T_horizon = data["time_periods"]
    K = data["resources"]
    # JSON anahtarları string olduğu için tuple'a çeviriyoruz
    E = {j: [tuple(p) for p in preds] for j, preds in data["precedences"].items()}
    r = {tuple(k.split(',')): v for k, v in data["resource_requirements"].items()}
    w = data["resource_weights"]
    t0 = data["earliest_start_times"]
    PD = data["project_deadlines"]
    max_res_capacity = data["max_resource_capacity"]
    TF = {tuple(k.split(',')): v for k, v in data["target_finish_times"].items()}
    P = {tuple(k.split(',')): v for k, v in data["lateness_penalties"].items()}
    min_dur = {tuple(k.split(',')): v for k, v in data["min_durations"].items()}
    max_dur = {tuple(k.split(',')): v for k, v in data["max_durations"].items()}
    cost_per_day = data["cost_per_day"]

    # Diğer parametreler
    all_activities = [(i, j) for j in J for i in I[j]]
    T = range(1, T_horizon + 1)
    H = len(T)
    M = H + 100

    # 2. Adım: Optimizasyon Modelini Kurma
    prob = LpProblem("Multi-Project_Resource_Leveling", LpMinimize)

    # Karar Değişkenleri
    D = LpVariable.dicts("D", ((i, j, t) for j in J for i in I[j] for t in T), 0, 1, LpBinary)
    ActualDur = LpVariable.dicts("ActualDur", ((i, j) for j in J for i in I[j]), lowBound=1, cat=LpInteger)
    S = LpVariable.dicts("S", ((i, j) for j in J for i in I[j]), lowBound=1, cat=LpInteger)
    F = LpVariable.dicts("F", ((i, j) for j in J for i in I[j]), lowBound=1, cat=LpInteger)
    R = LpVariable.dicts("R", (k for k in K), lowBound=0, cat=LpContinuous)
    Late = LpVariable.dicts("Late", ((i, j) for j in J for i in I[j]), lowBound=0, cat=LpContinuous)

    # Amaç Fonksiyonu
    prob += lpSum(w[k] * R[k] for k in K) + \
            lpSum(P[(i,j)] * Late[(i,j)] for i,j in all_activities) + \
            lpSum(cost_per_day * ActualDur[(i,j)] for i,j in all_activities), \
            "Weighted_Peak_Resource_Usage_Minimization"

    # Kısıtlar
    # Öncüllük Kısıtları
    for j in J:
        if j in E:
            for p, i in E[j]:
                prob += S[(i, j)] >= F[(p, j)] + 1, f"Precedence_{p}_{i}_{j}"

    # Zaman ve Başlangıç/Bitiş Bağlantıları
    for i, j in all_activities:
        for t in T:
            prob += S[(i, j)] <= t * D[(i, j, t)] + M * (1 - D[(i, j, t)]), f"StartLinkage1_{i}_{j}_{t}"
            prob += F[(i, j)] >= t * D[(i, j, t)] - M * (1 - D[(i, j, t)]), f"FinishLinkage1_{i}_{j}_{t}"

    # Proje Zaman Penceresi
    for i, j in all_activities:
        prob += S[(i, j)] >= t0[j], f"ProjectWindow_Start_{i}_{j}"
        prob += F[(i, j)] <= PD[j], f"ProjectWindow_Finish_{i}_{j}"

    # Süre Kısıtları
    for i, j in all_activities:
        prob += lpSum(D[(i, j, t)] for t in T) == ActualDur[(i, j)], f"Duration2_{i}_{j}"
        prob += F[(i, j)] == S[(i, j)] + ActualDur[(i, j)] - 1, f"FinishDurationLink_{i}_{j}"
        prob += ActualDur[(i, j)] >= min_dur[(i, j)], f"MinDuration_{i}_{j}"
        prob += ActualDur[(i, j)] <= max_dur[(i, j)], f"MaxDuration_{i}_{j}"

    # Zirve Kaynak Kullanımı
    for k in K:
        for t in T:
            prob += lpSum(r.get((i, j, k), 0) * D[(i, j, t)] for i, j in all_activities) <= R[k], f"PeakResource_{k}_{t}"

    # Maksimum Kaynak Kapasitesi
    for k in K:
        prob += R[k] <= max_res_capacity[k], f"MaxResourceCapacity_{k}"

    # Gecikme Tanımlaması
    for i, j in all_activities:
        prob += Late[(i, j)] >= F[(i, j)] - TF[(i, j)], f"LatenessDefinition_{i}_{j}"

    # 3. Adım: Modeli Çözme
    prob.solve()

    # 4. Adım: Sonuçları Yapılandırılmış Bir Formatta Döndürme
    if LpStatus[prob.status] == "Optimal":
        results = {
            "status": LpStatus[prob.status],
            "objective_value": value(prob.objective),
            "schedule": [],
            "peak_resource_usage": {},
            "lateness": [],
            "daily_usage": {}
        }

        for i, j in all_activities:
            results["schedule"].append({
                "activity": i,
                "project": j,
                "start": value(S[(i, j)]),
                "finish": value(F[(i, j)]),
                "duration": value(ActualDur[(i, j)])
            })
            if value(Late[(i, j)]) > 0.01:
                results["lateness"].append({
                    "activity": i,
                    "project": j,
                    "days_late": round(value(Late[(i, j)]), 2)
                })

        for k in K:
            results["peak_resource_usage"][k] = value(R[k])
        
        for t in T:
            daily_res = {k: 0 for k in K}
            for k in K:
                daily_res[k] = sum(r.get((i, j, k), 0) * value(D[(i, j, t)]) for i,j in all_activities)
            if any(val > 0 for val in daily_res.values()):
                 results["daily_usage"][t] = daily_res

        return results
    else:
        return {"status": LpStatus[prob.status], "error": "Optimizasyon başarısız oldu. Kısıtlar sağlanamıyor olabilir."}


if __name__ == '__main__':
    # Bu blok, fonksiyonun doğrudan çalıştırıldığında test edilmesini sağlar.
    # Orijinal script'teki verilerle bir test senaryosu oluşturulmuştur.
    test_data = {
        "projects": ["J1", "J2", "J3", "J4"],
        "activities": {
            "J1": ["A11", "A12", "A13"],
            "J2": ["A21", "A22"],
            "J3": ["A31", "A32", "A33"],
            "J4": ["A41", "A42"]
        },
        "time_periods": 10,
        "resources": ["K1", "K2"],
        "precedences": {
            "J1": [["A11", "A12"]],
            "J2": [["A21", "A22"]],
            "J3": [["A31", "A32"]],
            "J4": [["A41", "A42"]]
        },
        "resource_requirements": {
            "A11,J1,K1": 2, "A11,J1,K2": 1, "A12,J1,K1": 1, "A12,J1,K2": 3, "A13,J1,K1": 3, "A13,J1,K2": 2,
            "A21,J2,K1": 4, "A21,J2,K2": 2, "A22,J2,K1": 2, "A22,J2,K2": 4,
            "A31,J3,K1": 3, "A31,J3,K2": 1, "A32,J3,K1": 2, "A32,J3,K2": 3, "A33,J3,K1": 1, "A33,J3,K2": 2,
            "A41,J4,K1": 2, "A41,J4,K2": 1, "A42,J4,K1": 3, "A42,J4,K2": 2
        },
        "resource_weights": {"K1": 0.6, "K2": 0.4},
        "earliest_start_times": {"J1": 1, "J2": 1, "J3": 1, "J4": 1},
        "project_deadlines": {"J1": 20, "J2": 20, "J3": 20, "J4": 20},
        "max_resource_capacity": {"K1": 12, "K2": 15},
        "target_finish_times": {
            "A11,J1": 3, "A12,J1": 6, "A13,J1": 7,
            "A21,J2": 5, "A22,J2": 5,
            "A31,J3": 4, "A32,J3": 8, "A33,J3": 10,
            "A41,J4": 5, "A42,J4": 9
        },
        "lateness_penalties": {
            "A11,J1": 10, "A12,J1": 1000, "A13,J1": 2,
            "A21,J2": 8, "A22,J2": 5000,
            "A31,J3": 5, "A32,J3": 50, "A33,J3": 10,
            "A41,J4": 15, "A42,J4": 750
        },
        "min_durations": {
            "A11,J1": 2, "A12,J1": 3, "A13,J1": 1,
            "A21,J2": 3, "A22,J2": 2,
            "A31,J3": 2, "A32,J3": 3, "A33,J3": 1,
            "A41,J4": 2, "A42,J4": 3
        },
        "max_durations": {
            "A11,J1": 5, "A12,J1": 6, "A13,J1": 3,
            "A21,J2": 7, "A22,J2": 4,
            "A31,J3": 4, "A32,J3": 5, "A33,J3": 2,
            "A41,J4": 4, "A42,J4": 5
        },
        "cost_per_day": 0.1
    }

    # Fonksiyonu test verisiyle çalıştır
    results = optimize_plan(test_data)

    # Sonuçları JSON formatında güzel bir şekilde yazdır
    print(json.dumps(results, indent=4))
