from celery import Celery
import time
# Projenin çekirdek optimizasyon mantığını import ediyoruz
from optimization_core import optimize_plan
import traceback

# Celery uygulamasını yapılandırıyoruz
# Broker: Görevlerin bırakıldığı yer (bizim durumumuzda bir dosya)
# Backend: Sonuçların saklandığı yer (yine aynı dosya)
celery_app = Celery(
    'tasks',
    broker='sqla+sqlite:///celerydb.sqlite3',
    backend='db+sqlite:///celerydb.sqlite3'
)

@celery_app.task(name='optimize_plan_task')
def optimize_plan_task(data):
    """Arka planda optimizasyon modelini çalıştıran Celery görevi."""
    # HATA AYIKLAMA: Görevin başladığını terminale yazdırıyoruz.
    print(f"\n--- [CELERY WORKER]: optimize_plan_task GÖREVİ BAŞLADI ---")
    try:
        # HATA AYIKLAMA: Fonksiyonu çağırmadan hemen önce bir mesaj yazdırıyoruz.
        print(f"--- [CELERY WORKER]: optimize_plan fonksiyonu çağrılıyor... ---")
        results = optimize_plan(data)
        # HATA AYIKLAMA: Fonksiyon başarılı olursa bir mesaj yazdırıyoruz.
        print(f"--- [CELERY WORKER]: optimize_plan başarıyla tamamlandı. ---")
        return results
    except Exception as e:
        # HATA AYIKLAMA: Herhangi bir hata olursa, hatayı terminale yazdırıyoruz.
        print(f"!!! [CELERY WORKER]: GÖREV İÇİNDE BİR HATA YAKALANDI !!!")
        # Hatanın tam traceback dökümünü yazdırır
        traceback.print_exc()
        # Celery'nin görevi "FAILURE" olarak işaretlemesi için hatayı yeniden fırlatıyoruz
        raise e

@celery_app.task(name='add_task')
def add_task(x, y):
    """İki sayıyı toplayan basit bir test görevi."""
    time.sleep(1) # 1 saniye bekletiyoruz
    return x + y

