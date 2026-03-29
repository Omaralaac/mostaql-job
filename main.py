import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import threading
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

# ==============================
# ⚙️ M-SNIPER: الإعدادات الأساسية
# ==============================
SYSTEM_NAME = "M-Sniper"
TOKEN = "8546208480:AAF9601HRW7SXOqYc5vwb99s7r85aFInAMo"
BOT_USERNAME = "mostaqljonbot"
ADMIN_EMAIL = "omaralaaadmin@omar.com"
ADMIN_PASS = "1292002"
ADMIN_TELEGRAM_ID = "1130472857" # معرف الأدمن اللي حددته
DB_NAME = "database.db"

app = Flask(SYSTEM_NAME)
app.secret_key = "M_SNIPER_SUPER_SECRET_2026"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# التأكد من وجود مجلد الرفع
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# التصنيفات الرسمية لـ "مستقل" - محدثة وشاملة
KEYWORDS_LIST = [
    "أعمال وخدمات استشارية",
    "برمجة، تطوير المواقع والتطبيقات",
    "ذكاء اصطناعي وتعلم الآلة",
    "هندسة، عمارة وتصميم داخلي",
    "تصميم، فيديو وصوتيات",
    "تسويق إلكتروني ومبيعات",
    "كتابة، تحرير، ترجمة ولغات",
    "دعم، مساعدة وإدخال بيانات",
    "تدريب وتعليم عن بعد"
]

# ==============================
# ✨ M-SNIPER UI: لمسات الأنيميشن والاحترافية
# ==============================
# ده الجزء اللي هيخلي الموقع "حيوي" (Glow & Glass Effect)
SNIPER_STYLE = """
<style>
    :root {
        --primary-glow: #3498db;
        --secondary-glow: #2ecc71;
        --glass-bg: rgba(255, 255, 255, 0.85);
    }
    
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #fdfdfd;
        /* تأثير الـ Glow الهادئ في الخلفية */
        background-image: 
            radial-gradient(at 0% 0%, rgba(52, 152, 219, 0.1) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(46, 204, 113, 0.08) 0px, transparent 50%);
        min-height: 100vh;
        color: #2c3e50;
    }

    /* أنيميشن الدخول الناعم للعناصر */
    .fade-in {
        animation: fadeIn 0.8s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* تأثير الـ Glassmorphism للكروت */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: 0.3s all ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        border: 1px solid var(--primary-glow);
    }

    /* زرار الـ Sniper القناص */
    .btn-sniper {
        background: linear-gradient(45deg, #2c3e50, #3498db);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 30px;
        font-weight: bold;
        transition: 0.4s;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
    }
    
    .btn-sniper:hover {
        letter-spacing: 1px;
        box-shadow: 0 6px 20px rgba(52, 152, 219, 0.5);
        color: white;
        transform: scale(1.02);
    }
</style>
"""
# ==============================
# 🗄️ M-SNIPER: قاعدة البيانات الذكية
# ==============================

def get_db():
    # استخدام check_same_thread=False ضروري لأن السكرابر يعمل في Thread منفصل
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    تهيئة قاعدة البيانات بالتصميم المطور لنظام M-Sniper.
    تم إضافة قيود الفرادة (UNIQUE) لضمان عدم تكرار الحسابات.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. جدول المستخدمين (نواة نظام M-Sniper)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        phone TEXT UNIQUE,
        gender TEXT, 
        birthdate TEXT, 
        password TEXT NOT NULL,
        is_active INTEGER DEFAULT 0,         -- 0: غير نشط، 1: مشترك مفعل
        payment_status TEXT DEFAULT 'none',   -- none, pending, verified
        payment_image TEXT,                  -- اسم ملف إثبات الدفع
        keywords TEXT,                       -- المجالات المختارة (مفصولة بفاصلة)
        temp_token TEXT UNIQUE,              -- كود الربط المؤقت مع تليجرام
        telegram_id TEXT UNIQUE,             -- معرف الشات (الهدف الأساسي للقنص)
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 2. جدول المشاريع المرصودة (ذاكرة القناص)
    # تم إضافة UNIQUE للرابط لضمان عدم إرسال نفس المشروع مرتين مهما حدث
    cursor.execute('CREATE TABLE IF NOT EXISTS seen_projects (
        link TEXT UNIQUE,
        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )')
    
    conn.commit()
    conn.close()
    print(f"✅ تم تهيئة قاعدة بيانات {SYSTEM_NAME} بنجاح.")

# تشغيل التأسيس
init_db()

# ==============================
# 🗄️ M-SNIPER: قاعدة البيانات الذكية
# ==============================

def get_db():
    # استخدام check_same_thread=False ضروري لأن السكرابر يعمل في Thread منفصل
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    تهيئة قاعدة البيانات بالتصميم المطور لنظام M-Sniper.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. جدول المستخدمين (نواة نظام M-Sniper)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        phone TEXT UNIQUE,
        gender TEXT, 
        birthdate TEXT, 
        password TEXT NOT NULL,
        is_active INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'none',
        payment_image TEXT,
        keywords TEXT,
        temp_token TEXT UNIQUE,
        telegram_id TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 2. جدول المشاريع المرصودة (ذاكرة القناص)
    # تم تصحيح الـ Syntax هنا لضمان عدم وجود أخطاء في التنفيذ
    cursor.execute('''CREATE TABLE IF NOT EXISTS seen_projects (
        link TEXT UNIQUE,
        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print(f"✅ تم تهيئة قاعدة بيانات {SYSTEM_NAME} بنجاح.")

# تنفيذ التأسيس
try:
    init_db()
except Exception as e:
    print(f"❌ حدث خطأ أثناء تهيئة القاعدة: {e}")
    print("💡 نصيحة: امسح ملف database.db وشغل الكود مرة أخرى.")


# ==============================
# 🎯 M-SNIPER: محرك القنص الذكي (Scraper)
# ==============================

def scraper_worker():
    print(f"🚀 {SYSTEM_NAME} Sniper is now patrolling...")
    while True:
        try:
            conn = get_db()
            # جلب المشاريع من مستقل مع Header احترافي لتجنب الحظر
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            res = requests.get("https://mostaql.com/projects", headers=headers, timeout=20)
            
            if res.status_code != 200:
                print(f"⚠️ {SYSTEM_NAME}: Connection issue (Status: {res.status_code})")
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            
            # جلب المشتركين المفعلين فقط والذين لديهم Telegram ID
            active_users = conn.execute("""
                SELECT * FROM users 
                WHERE is_active=1 
                AND payment_status='verified' 
                AND telegram_id IS NOT NULL
            """).fetchall()
            
            # البحث عن عناوين المشاريع والروابط
            for project_card in soup.select("h2 a"):
                link = project_card["href"]
                if not link.startswith("http"):
                    link = "https://mostaql.com" + link
                
                title = project_card.text.strip()
                
                # التأكد من أن المشروع لم يتم "قنصه" من قبل
                if not conn.execute("SELECT link FROM seen_projects WHERE link=?", (link,)).fetchone():
                    
                    # عملية الفلترة الذكية لكل مستخدم
                    for user in active_users:
                        if user['keywords']:
                            # تحويل الكلمات المفتاحية لقائمة
                            user_kws = [k.strip().lower() for k in user['keywords'].split(',')]
                            
                            # الفلترة: هل عنوان المشروع يحتوي على أي من مهارات المستخدم؟
                            if any(kw in title.lower() for kw in user_kws):
                                
                                # تصميم رسالة "M-Sniper" الاحترافية
                                msg = (
                                    f"🎯 <b>M-Sniper: هدف جديد تم رصده!</b>\n"
                                    f"━━━━━━━━━━━━━━━━━━\n"
                                    f"📌 <b>المشروع:</b> {title}\n"
                                    f"✅ يطابق مهاراتك المختارة\n"
                                    f"━━━━━━━━━━━━━━━━━━\n"
                                    f"⚡ <i>كن أول من يقدم عرضاً!</i>"
                                )
                                
                                # زر تفاعلي لفتح المشروع
                                kb = {
                                    "inline_keyboard": [[
                                        {"text": "🚀 اقتنص الفرصة الآن", "url": link}
                                    ]]
                                }
                                
                                # إرسال التنبيه الفوري
                                requests.post(
                                    f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                    json={
                                        "chat_id": user['telegram_id'], 
                                        "text": msg, 
                                        "parse_mode": "HTML", 
                                        "reply_markup": kb
                                    },
                                    timeout=10
                                )
                    
                    # تسجيل المشروع في "ذاكرة القناص" حتى لا يتكرر
                    conn.execute("INSERT INTO seen_projects (link) VALUES (?)", (link,))
                    conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ {SYSTEM_NAME} Scraper Error: {e}")
            
        # القناص يأخذ استراحة محارب (دقيقتين) قبل الجولة التالية
        time.sleep(120)


# ==============================
# 🌐 M-SNIPER UI: القالب الرئيسي (BASE_HTML)
# ==============================

BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M-Sniper | نظام القنص الذكي للمشاريع</title>
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        :root {
            --sniper-blue: #3498db;
            --sniper-dark: #2c3e50;
            --glow-color: rgba(52, 152, 219, 0.15);
        }

        body { 
            background: #ffffff; 
            font-family: 'Noto Kufi Arabic', sans-serif;
            color: #2c3e50;
            min-height: 100vh;
            /* تأثير الـ Glow المستوحى من الفيديو */
            background-image: 
                radial-gradient(circle at 10% 20%, var(--glow-color) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(46, 204, 113, 0.1) 0%, transparent 40%);
            background-attachment: fixed;
        }

        /* ناف بار زجاجي (Glassmorphism) */
        .navbar-sniper {
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.4s ease;
        }

        .navbar-brand {
            font-weight: 800;
            font-size: 1.5rem;
            letter-spacing: -1px;
            color: var(--sniper-dark) !important;
        }

        .navbar-brand span { color: var(--sniper-blue); }

        /* تأثيرات الأزرار والكروت */
        .glass-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 0 15px 35px rgba(0,0,0,0.05);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: fadeInUp 0.8s ease-out;
        }

        .glass-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 45px rgba(0,0,0,0.1);
            border-color: var(--sniper-blue);
        }

        .btn-sniper {
            background: linear-gradient(135deg, var(--sniper-dark), var(--sniper-blue));
            color: white !important;
            border-radius: 50px;
            padding: 10px 25px;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
            transition: 0.3s;
        }

        .btn-sniper:hover {
            transform: scale(1.05) rotate(-1deg);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.5);
        }

        /* أنيميشن الدخول */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stat-card {
            background: linear-gradient(135deg, #3498db, #2980b9);
            padding: 25px;
            border-radius: 18px;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .stat-card::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            transform: rotate(45deg);
        }

        .nav-link { 
            color: #555 !important; 
            font-weight: 500; 
            margin: 0 5px;
        }
        .nav-link:hover { color: var(--sniper-blue) !important; }

    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-sniper sticky-top py-3">
        <div class="container">
            <a class="navbar-brand" href="/">🎯 M-<span>SNIPER</span></a>
            <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item"><a class="nav-link" href="/">الرئيسية</a></li>
                    {% if session.get('user_id') %}
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fa-solid fa-gauge-high"></i> لوحة التحكم</a></li>
                        <li class="nav-item"><a class="nav-link text-danger fw-bold" href="/logout"><i class="fa-solid fa-right-from-bracket"></i> خروج</a></li>
                    {% elif session.get('admin') %}
                        <li class="nav-item"><a class="nav-link text-info fw-bold" href="/admin"><i class="fa-solid fa-user-shield"></i> الإدارة</a></li>
                        <li class="nav-item"><a class="nav-link text-danger fw-bold" href="/logout">خروج</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="/login">تسجيل دخول</a></li>
                        <li class="nav-item ms-lg-3"><a class="btn btn-sniper" href="/signup">ابدأ القنص الآن</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <script>
                Swal.fire({ 
                    icon: '{{ "error" if category == "error" else "success" }}', 
                    title: '{{ message }}', 
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdrop: `rgba(52, 152, 219, 0.1)`,
                    timer: 3000, 
                    showConfirmButton: false,
                    customClass: { popup: 'glass-card' }
                });
              </script>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        <div class="fade-in">
            {% block content %}{% endblock %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ==============================
# 🛣️ M-SNIPER: المسارات الرئيسية (Routes)
# ==============================

@app.route('/')
def home():
    # محتوى الصفحة الرئيسية بتصميم "M-Sniper" المطور
    home_content = """
    <div class="glass-card p-5 text-center mb-5 mt-4 overflow-hidden position-relative" style="border: none; background: linear-gradient(135deg, rgba(44, 62, 80, 0.95), rgba(52, 152, 219, 0.9)); color: white;">
        <div class="position-relative z-index-1">
            <div class="badge bg-primary mb-3 px-3 py-2 rounded-pill shadow-sm fade-in" style="font-size: 0.9rem;">
                🚀 أسرع نظام تنبيهات لمشاريع مستقل في الوطن العربي
            </div>
            <h1 class="display-3 fw-bold mb-3 fade-in" style="letter-spacing: -2px;">اقتنص مشاريعك <span style="color: #44fbff;">بذكاء</span> 🎯</h1>
            <p class="lead mb-4 opacity-75 fade-in" style="max-width: 700px; margin: 0 auto;">
                لا تضيع وقتك في البحث اليدوي.. <b>M-Sniper</b> يراقب منصة مستقل على مدار الساعة ويرسل لك المشاريع التي تناسب مهاراتك فوراً على تليجرام.
            </p>
            <div class="mt-4 d-flex justify-content-center gap-3 fade-in">
                <a href="/signup" class="btn btn-light btn-lg px-5 fw-bold shadow-lg" style="border-radius: 50px; color: #2c3e50;">ابدأ القنص الآن</a>
                <a href="/login" class="btn btn-outline-light btn-lg px-5 fw-bold" style="border-radius: 50px; backdrop-filter: blur(5px);">دخول الأعضاء</a>
            </div>
        </div>
        
        <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%; filter: blur(50px);"></div>
    </div>

    <div class="row text-center mt-5">
        <div class="col-md-4 mb-4">
            <div class="glass-card p-4 h-100">
                <div class="icon-box mb-3" style="font-size: 3rem; color: #3498db;">
                    <i class="fa-solid fa-bolt-lightning"></i>
                </div>
                <h4 class="fw-bold">سرعة البرق ⚡</h4>
                <p class="text-muted small">نحن لا ننتظر.. فور نشر المشروع على مستقل، يكون التنبيه في جيبك خلال ثوانٍ معدودة.</p>
            </div>
        </div>
        
        <div class="col-md-4 mb-4">
            <div class="glass-card p-4 h-100" style="border-bottom: 3px solid #3498db;">
                <div class="icon-box mb-3" style="font-size: 3rem; color: #3498db;">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <h4 class="fw-bold">فلترة ذكية 🤖</h4>
                <p class="text-muted small">انسَ الإزعاج؛ محرك <b>M-Sniper</b> يقوم بتحليل عنوان المشروع ويرسل لك ما يطابق تخصصك فقط.</p>
            </div>
        </div>
        
        <div class="col-md-4 mb-4">
            <div class="glass-card p-4 h-100">
                <div class="icon-box mb-3" style="font-size: 3rem; color: #3498db;">
                    <i class="fa-solid fa-bullseye"></i>
                </div>
                <h4 class="fw-bold">الأولوية لك 📈</h4>
                <p class="text-muted small">كن أول من يقدم عرضاً احترافياً وارفع فرص اختيارك للمشروع بنسبة تصل إلى 80%.</p>
            </div>
        </div>
    </div>

    <div class="text-center mt-5 mb-5 fade-in">
        <p class="text-muted">انضم إلى مئات المحترفين الذين يعتمدون على <b>M-Sniper</b> يومياً.</p>
        <div class="d-flex justify-content-center gap-4 opacity-50">
            <i class="fa-brands fa-python fa-2x"></i>
            <i class="fa-brands fa-node-js fa-2x"></i>
            <i class="fa-brands fa-react fa-2x"></i>
            <i class="fa-brands fa-php fa-2x"></i>
            <i class="fa-brands fa-wordpress fa-2x"></i>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', home_content))

# ==============================
# 📝 M-SNIPER: مسار التسجيل (Signup)
# ==============================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        bdate = request.form['bdate']
        password = request.form['password']
        
        # توليد توكن فريد لربط تليجرام لاحقاً
        token = str(uuid.uuid4())[:8]
        
        conn = get_db()
        try:
            # التأكد من عدم تكرار البيانات (Email or Phone)
            check = conn.execute("SELECT * FROM users WHERE email=? OR phone=?", (email, phone)).fetchone()
            if check:
                flash("عذراً، البريد الإلكتروني أو رقم الهاتف مسجل بالفعل!", "error")
                return redirect('/signup')
            
            # إدخال البيانات في قاعدة البيانات
            conn.execute("""
                INSERT INTO users (name, email, phone, gender, birthdate, password, temp_token) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, phone, gender, bdate, password, token))
            conn.commit()
            
            # 🚀 تنبيه الأدمن (أنت) بتليجرام فوراً
            admin_msg = f"🔔 <b>مشترك جديد انضم لـ M-Sniper!</b>\n\n👤 الاسم: {name}\n📧 الإيميل: {email}\n📱 الهاتف: {phone}"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": ADMIN_TELEGRAM_ID, "text": admin_msg, "parse_mode": "HTML"})
            
            flash("أهلاً بك في M-Sniper! تم إنشاء حسابك بنجاح.", "success")
            return redirect('/login')
            
        except Exception as e:
            flash(f"حدث خطأ غير متوقع: {e}", "error")
        finally:
            conn.close()
    
    # واجهة التسجيل الاحترافية (Glass Design)
    signup_content = """
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
            <div class="glass-card p-5 mt-4 mb-5 fade-in">
                <div class="text-center mb-4">
                    <div class="display-6 mb-2">🎯</div>
                    <h2 class="fw-bold text-dark">انضم للقناصين</h2>
                    <p class="text-muted small">ابدأ برصد مشاريعك المفضلة في ثوانٍ</p>
                </div>
                
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-bold">الاسم الكامل</label>
                        <input type="text" name="name" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" placeholder="عمر علاء" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label small fw-bold">البريد الإلكتروني</label>
                        <input type="email" name="email" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" placeholder="name@example.com" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label small fw-bold">رقم الهاتف (تليجرام)</label>
                        <input type="text" name="phone" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" placeholder="01xxxxxxxxx" required>
                    </div>

                    <div class="row mb-3">
                        <div class="col-6">
                            <label class="form-label small fw-bold">الجنس</label>
                            <select name="gender" class="form-select rounded-pill border-0 shadow-sm px-4 py-2">
                                <option value="ذكر">ذكر</option>
                                <option value="أنثى">أنثى</option>
                            </select>
                        </div>
                        <div class="col-6">
                            <label class="form-label small fw-bold">تاريخ الميلاد</label>
                            <input type="date" name="bdate" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" required>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label class="form-label small fw-bold">كلمة السر</label>
                        <input type="password" name="password" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" placeholder="••••••••" required>
                    </div>
                    
                    <button class="btn btn-sniper w-100 py-3 mb-3 shadow">إنشاء حسابي الآن 🚀</button>
                </form>
                
                <div class="text-center">
                    <span class="small text-muted">لديك حساب بالفعل؟</span>
                    <a href="/login" class="small fw-bold text-decoration-none" style="color: var(--sniper-blue);">سجل دخولك</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', signup_content))


# ==============================
# 🔑 M-SNIPER: مسار تسجيل الدخول (Login)
# ==============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # 1. التحقق من دخول الأدمن (عمر)
        if email == ADMIN_EMAIL and password == ADMIN_PASS:
            session.clear() 
            session['admin'] = True
            flash(f"مرحباً بك يا مدير النظام في {SYSTEM_NAME}! 🕵️‍♂️", "success")
            return redirect('/admin')
        
        # 2. التحقق من دخول المشتركين
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        conn.close()
        
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name'] # تخزين الاسم للترحيب الشخصي
            
            flash(f"أهلاً بعودتك يا {user['name']}! جاري فتح الرادار.. 🎯", "success")
            return redirect('/dashboard')
        else:
            flash("بيانات الدخول غير صحيحة، تأكد من الإيميل وكلمة السر.", "error")
            return redirect('/login')
    
    # واجهة تسجيل الدخول بتصميم M-Sniper الاحترافي
    login_content = """
    <div class="row justify-content-center align-items-center" style="min-height: 70vh;">
        <div class="col-md-5 col-lg-4">
            <div class="glass-card p-5 fade-in text-center">
                <div class="mb-4">
                    <div class="display-5 mb-2">🔐</div>
                    <h2 class="fw-bold">تسجيل الدخول</h2>
                    <p class="text-muted small">عد لقنص مشاريعك المفضلة الآن</p>
                </div>
                
                <form method="POST">
                    <div class="mb-3">
                        <div class="input-group">
                            <span class="input-group-text bg-white border-0 ps-3"><i class="fa-solid fa-envelope text-muted"></i></span>
                            <input type="email" name="email" class="form-control border-0 shadow-sm py-2 px-3" placeholder="البريد الإلكتروني" required style="border-radius: 0 50px 50px 0;">
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <div class="input-group">
                            <span class="input-group-text bg-white border-0 ps-3"><i class="fa-solid fa-lock text-muted"></i></span>
                            <input type="password" name="password" class="form-control border-0 shadow-sm py-2 px-3" placeholder="كلمة السر" required style="border-radius: 0 50px 50px 0;">
                        </div>
                    </div>
                    
                    <button class="btn btn-sniper w-100 py-3 shadow mb-3">دخول القناصين 🎯</button>
                </form>
                
                <div class="mt-3">
                    <span class="text-muted small">ليس لديك حساب؟</span>
                    <a href="/signup" class="small fw-bold text-decoration-none" style="color: var(--sniper-blue);">أنشئ حسابك الآن</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', login_content))


# ==============================
# 🚀 M-SNIPER: لوحة تحكم القناص (Dashboard)
# ==============================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: 
        return redirect('/login')
        
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    
    # 1. حالة البداية: إذا لم يختر التخصصات أو يرفع الدفع
    if user['payment_status'] == 'none':
        return redirect('/activation_step')
        
    # 2. حالة "رادار المراجعة": انتظار تأكيد الأدمن
    elif user['payment_status'] == 'pending':
        content = """
        <div class="row justify-content-center mt-5">
            <div class="col-md-7 text-center">
                <div class="glass-card p-5 fade-in">
                    <div class="spinner-grow text-primary mb-4" role="status" style="width: 3rem; height: 3rem;"></div>
                    <h2 class="fw-bold text-dark">جاري فحص الإحداثيات... 📡</h2>
                    <p class="text-muted lead">نحن نراجع إثبات الدفع الخاص بك الآن.<br>بمجرد التأكيد، سينطلق القناص لرصد مشاريعك.</p>
                    <div class="mt-4">
                        <a href="/dashboard" class="btn btn-sniper px-5">تحديث حالة الرادار 🔄</a>
                    </div>
                </div>
            </div>
        </div>
        """
        return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', content))
        
    # 3. حالة "القناص النشط": الحساب مفعل وجاهز للربط
    else:
        # عرض التخصصات بشكل "Chips" احترافية
        kws_list = [k.strip() for k in user['keywords'].split(',')] if user['keywords'] else []
        kws_badges = "".join([f'<span class="badge bg-light text-primary border m-1 px-3 py-2 shadow-sm" style="border-radius:20px;">{k}</span>' for k in kws_list])

        content = f"""
        <div class="row justify-content-center mt-4">
            <div class="col-md-8">
                <div class="glass-card p-5 fade-in shadow-lg position-relative overflow-hidden">
                    <div class="position-absolute top-0 end-0 m-4">
                        <span class="badge bg-success px-3 py-2 rounded-pill shadow-sm">
                            <i class="fa-solid fa-circle-check"></i> الحساب نشط
                        </span>
                    </div>

                    <h2 class="fw-bold mb-1">أهلاً يا {user['name']} 👋</h2>
                    <p class="text-muted mb-4">رادار M-Sniper مضبوط حالياً على الأهداف التالية:</p>
                    
                    <div class="mb-5 text-center">
                        {kws_badges}
                    </div>
                    
                    <hr class="opacity-10 mb-5">
                    
                    <div class="activation-box p-4 rounded-4" style="background: rgba(52, 152, 219, 0.05); border: 2px dashed rgba(52, 152, 219, 0.2);">
                        <div class="row align-items-center text-center text-md-start">
                            <div class="col-md-8">
                                <h5 class="fw-bold mb-2">🚀 الخطوة الأخيرة: تفعيل الإشعارات</h5>
                                <p class="small text-muted mb-0">اضغط على الزر، ثم اختر <b>Start</b> داخل البوت لبدء استقبال المشاريع فوراً.</p>
                            </div>
                            <div class="col-md-4 text-center mt-3 mt-md-0">
                                <a href="https://t.me/{BOT_USERNAME}?start={user['temp_token']}" 
                                   target="_blank"
                                   class="btn btn-sniper btn-lg w-100 shadow" 
                                   style="animation: pulse-light 2s infinite;">
                                   ربط تليجرام الآن
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-5 d-flex justify-content-between align-items-center">
                        <a href="/activation_step" class="text-decoration-none small text-muted hover-blue">
                            <i class="fa-solid fa-sliders"></i> تعديل مهارات القنص
                        </a>
                        <span class="small text-muted">ID: {user['id']}</span>
                    </div>
                </div>
            </div>
        </div>
        """
        return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', content))


# ==============================
# 🎯 M-SNIPER: تخصيص الأهداف (Activation Step)
# ==============================

@app.route('/activation_step', methods=['GET', 'POST'])
def activation_step():
    if 'user_id' not in session: 
        return redirect('/login')
        
    if request.method == 'POST':
        selected_kws = request.form.getlist('kws')
        if not selected_kws:
            flash("يرجى اختيار هدف (مجال) واحد على الأقل للقنص!", "error")
            return redirect('/activation_step')
            
        kws_str = ",".join(selected_kws)
        conn = get_db()
        conn.execute("UPDATE users SET keywords=? WHERE id=?", (kws_str, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/payment_page')
    
    # محتوى الصفحة بتصميم M-Sniper التفاعلي
    activation_content = """
    <div class="row justify-content-center mt-4">
        <div class="col-md-10 col-lg-8">
            <div class="glass-card p-5 fade-in">
                <div class="text-center mb-5">
                    <div class="display-5 mb-3">🛠️</div>
                    <h2 class="fw-bold">ضبط إعدادات القنص</h2>
                    <p class="text-muted">حدد المجالات التي تتقنها ليقوم <b>M-Sniper</b> بتصفية المشاريع لك:</p>
                </div>
                
                <form method="POST" id="activationForm">
                    <div class="row g-3">
                        {% for kw in kws_list %}
                        <div class="col-md-6">
                            <label class="keyword-card d-flex align-items-center p-3 rounded-4 border shadow-sm position-relative overflow-hidden">
                                <input class="form-check-input d-none" type="checkbox" name="kws" value="{{ kw }}">
                                <div class="check-indicator me-3 d-flex align-items-center justify-content-center">
                                    <i class="fa-solid fa-check text-white"></i>
                                </div>
                                <span class="fw-bold small">{{ kw }}</span>
                            </label>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div class="mt-5 p-4 rounded-4" style="background: rgba(52, 152, 219, 0.05); border-right: 4px solid var(--sniper-blue);">
                        <small class="text-muted">
                            <i class="fa-solid fa-circle-info text-primary me-1"></i>
                            سيقوم البوت بمراقبة جميع المشاريع في المجالات المختارة وإرسال تنبيه فوري لك عند ظهور أي منها.
                        </small>
                    </div>
                    
                    <button class="btn btn-sniper w-100 py-3 mt-4 shadow-lg text-uppercase fw-bold">
                        تأكيد الأهداف والانتقال للدفع 🚀
                    </button>
                </form>
            </div>
        </div>
    </div>

    <style>
        .keyword-card {
            cursor: pointer;
            background: white;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1.5px solid #eee !important;
        }

        .check-indicator {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid #ddd;
            transition: 0.3s;
            flex-shrink: 0;
        }

        /* حالة الاختيار (Checked) */
        .keyword-card:has(input:checked) {
            border-color: var(--sniper-blue) !important;
            background: rgba(52, 152, 219, 0.03);
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.1) !important;
        }

        .keyword-card:has(input:checked) .check-indicator {
            background: var(--sniper-blue);
            border-color: var(--sniper-blue);
        }

        .keyword-card:hover:not(:has(input:checked)) {
            border-color: #3498db66 !important;
            background: #fcfdfe;
        }

        .keyword-card input:checked + .check-indicator + span {
            color: var(--sniper-blue);
        }
    </style>
    """
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', activation_content), 
        kws_list=KEYWORDS_LIST
    )


# ==============================
# 💸 M-SNIPER: بوابة الدفع وتفعيل الاشتراك
# ==============================

@app.route('/payment_page', methods=['GET', 'POST'])
def payment_page():
    if 'user_id' not in session: 
        return redirect('/login')

    if request.method == 'POST':
        if 'screenshot' not in request.files:
            flash("لم يتم اختيار ملف الإثبات!", "error")
            return redirect(request.url)
            
        file = request.files['screenshot']
        
        if file and file.filename != '':
            # توليد اسم فريد للصورة لمنع التكرار
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            filename = f"sniper_pay_{session['user_id']}_{int(time.time())}.{ext}"
            
            # حفظ الملف في مجلد الرفع
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # تحديث حالة المستخدم في قاعدة البيانات إلى "قيد الانتظار"
            conn = get_db()
            conn.execute("""
                UPDATE users 
                SET payment_status='pending', payment_image=? 
                WHERE id=?
            """, (filename, session['user_id']))
            conn.commit()
            
            # 🚀 تنبيه فوري للأدمن (عمر) بوجود عملية دفع تحتاج مراجعة
            admin_alert = (
                f"💰 <b>إثبات دفع جديد في M-Sniper!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 العميل: {session.get('user_name', 'غير معروف')}\n"
                f"🆔 رقم المعرف: {session['user_id']}\n"
                f"📸 يرجى مراجعة لوحة الإدارة لتفعيل الحساب."
            )
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": ADMIN_TELEGRAM_ID, "text": admin_alert, "parse_mode": "HTML"})
            
            conn.close()
            flash("تم رفع الإثبات بنجاح! سيتم تفعيل رادار القنص الخاص بك فور المراجعة.", "success")
            return redirect('/dashboard')
        else:
            flash("يرجى رفع صورة صحيحة لعملية التحويل.", "error")

    # واجهة الدفع الاحترافية بتصميم M-Sniper
    payment_content = """
    <div class="row justify-content-center mt-4">
        <div class="col-md-7 col-lg-6">
            <div class="glass-card p-5 fade-in text-center shadow-lg">
                <div class="mb-4">
                    <div class="display-5 mb-2">💳</div>
                    <h2 class="fw-bold">تفعيل رادار القنص</h2>
                    <p class="text-muted">اشترك الآن لتصلك المشاريع فور صدورها</p>
                </div>
                
                <div class="alert alert-info border-0 shadow-sm py-3 mb-4 rounded-4" style="background: rgba(52, 152, 219, 0.08);">
                    <p class="mb-1 small">قيمة الاشتراك الشهري:</p>
                    <h3 class="fw-bold text-primary mb-0">200 ج.م</h3>
                </div>

                <p class="small text-muted mb-2">حول المبلغ إلى رقم فودافون كاش التالي:</p>
                <div class="p-4 rounded-4 mb-4 position-relative overflow-hidden" 
                     style="background: #f8f9fa; border: 2px dashed #dee2e6;">
                    <h2 class="fw-bold text-dark mb-1" style="letter-spacing: 2px;">01092843642</h2>
                    <span class="badge bg-danger rounded-pill px-3 py-2 mt-2">
                        <i class="fa-solid fa-mobile-screen-button me-1"></i> Vodafone Cash
                    </span>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100%; height: 100%; background: radial-gradient(circle, rgba(231, 76, 60, 0.05) 0%, transparent 70%); pointer-events: none;"></div>
                </div>
                
                <form method="POST" enctype="multipart/form-data" class="text-start">
                    <div class="mb-4">
                        <label class="form-label small fw-bold px-2">📸 ارفع صورة التحويل (Screenshot):</label>
                        <div class="input-group">
                            <input type="file" name="screenshot" class="form-control rounded-pill border-0 shadow-sm px-4 py-2" accept="image/*" required>
                        </div>
                    </div>
                    
                    <div class="p-3 rounded-4 mb-4 small" style="background: rgba(46, 204, 113, 0.05); color: #27ae60; border-right: 4px solid #2ecc71;">
                        <i class="fa-solid fa-clock-rotate-left me-1"></i>
                        سيتم مراجعة الطلب وتفعيل ميزة التنبيهات على تليجرام خلال دقائق قليلة.
                    </div>
                    
                    <button class="btn btn-sniper w-100 py-3 shadow-lg fw-bold">تأكيد الإرسال وتفعيل الرادار 🚀</button>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', payment_content))


# ==============================
# 👑 M-SNIPER: برج مراقبة الإدارة (Admin)
# ==============================

@app.route('/admin')
def admin():
    if not session.get('admin'): 
        return redirect('/login')
        
    conn = get_db()
    # جلب المستخدمين مع ترتيبهم (الأحدث أولاً)
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    
    # حساب الإحصائيات الذكية
    total_users = len(users)
    active_now = len([u for u in users if u['is_active'] == 1])
    pending_pay = len([u for u in users if u['payment_status'] == 'pending'])
    
    # محتوى لوحة الإدارة بتصميم M-Sniper الاحترافي
    admin_content = """
    <div class="d-flex justify-content-between align-items-center mb-5 fade-in">
        <div>
            <h2 class="fw-bold text-dark mb-0">لوحة الإدارة 🕵️‍♂️</h2>
            <p class="text-muted small">مرحباً يا عمر، لديك التحكم الكامل في نظام M-Sniper</p>
        </div>
        <a href="/logout" class="btn btn-outline-danger btn-sm px-3 rounded-pill">
            <i class="fa-solid fa-power-off me-1"></i> خروج
        </a>
    </div>

    <div class="row mb-5 fade-in">
        <div class="col-md-4 mb-3">
            <div class="glass-card p-4 text-center border-0 shadow-lg position-relative overflow-hidden">
                <div class="stat-icon opacity-10 position-absolute" style="font-size: 4rem; right: -10px; bottom: -10px;">
                    <i class="fa-solid fa-users"></i>
                </div>
                <h6 class="text-muted small fw-bold">إجمالي القناصين</h6>
                <h1 class="display-5 fw-bold text-primary mb-0">{{ t }}</h1>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="glass-card p-4 text-center border-0 shadow-lg position-relative overflow-hidden" style="border-bottom: 4px solid #2ecc71 !important;">
                <div class="stat-icon opacity-10 position-absolute" style="font-size: 4rem; right: -10px; bottom: -10px; color: #2ecc71;">
                    <i class="fa-solid fa-circle-check"></i>
                </div>
                <h6 class="text-muted small fw-bold">الرادارات النشطة</h6>
                <h1 class="display-5 fw-bold text-success mb-0">{{ a }}</h1>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="glass-card p-4 text-center border-0 shadow-lg position-relative overflow-hidden" style="border-bottom: 4px solid #f1c40f !important;">
                <div class="stat-icon opacity-10 position-absolute" style="font-size: 4rem; right: -10px; bottom: -10px; color: #f1c40f;">
                    <i class="fa-solid fa-hourglass-half"></i>
                </div>
                <h6 class="text-muted small fw-bold">طلبات بانتظارك</h6>
                <h1 class="display-5 fw-bold text-warning mb-0">{{ p }}</h1>
            </div>
        </div>
    </div>
    
    <div class="glass-card border-0 shadow-lg p-0 fade-in overflow-hidden">
        <div class="p-4 bg-white border-bottom d-flex justify-content-between align-items-center">
            <h5 class="mb-0 fw-bold"><i class="fa-solid fa-list-check me-2 text-primary"></i> إدارة المشتركين والطلبات</h5>
            <span class="badge bg-light text-dark border px-3 py-2 rounded-pill small">قاعدة البيانات: متصلة ✅</span>
        </div>
        
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light">
                    <tr>
                        <th class="ps-4 py-3 text-muted small fw-bold text-start">القناص</th>
                        <th class="py-3 text-muted small fw-bold">تاريخ الانضمام</th>
                        <th class="py-3 text-muted small fw-bold">إثبات الدفع</th>
                        <th class="py-3 text-muted small fw-bold">المجالات</th>
                        <th class="pe-4 py-3 text-muted small fw-bold text-end">الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users_list %}
                    <tr class="border-bottom-0">
                        <td class="ps-4 py-3 text-start">
                            <div class="d-flex align-items-center">
                                <div class="avatar-circle me-3 d-flex align-items-center justify-content-center bg-primary text-white rounded-circle shadow-sm" style="width: 40px; height: 40px;">
                                    {{ u.name[0] | upper }}
                                </div>
                                <div>
                                    <div class="fw-bold text-dark mb-0">{{ u.name }}</div>
                                    <div class="text-muted small" style="font-size: 0.75rem;">{{ u.email }}</div>
                                    <div class="text-primary fw-bold" style="font-size: 0.75rem;"><i class="fa-solid fa-phone me-1"></i> {{ u.phone }}</div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div class="small text-dark">{{ u.created_at }}</div>
                        </td>
                        <td>
                            {% if u.payment_image %}
                            <div class="position-relative d-inline-block">
                                <a href="/static/uploads/{{ u.payment_image }}" target="_blank" class="d-block">
                                    <img src="/static/uploads/{{ u.payment_image }}" 
                                         class="rounded-3 shadow-sm border p-1 bg-white" 
                                         style="width: 45px; height: 45px; object-fit: cover; transition: 0.3s;"
                                         onmouseover="this.style.transform='scale(1.2)'"
                                         onmouseout="this.style.transform='scale(1)'">
                                </a>
                                {% if u.payment_status == 'pending' %}
                                <span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle animate-pulse"></span>
                                {% endif %}
                            </div>
                            {% else %}
                            <span class="badge bg-light text-muted fw-normal">لم يرفع</span>
                            {% endif %}
                        </td>
                        <td>
                            <div style="max-width: 150px;" class="mx-auto">
                                <span class="text-truncate d-block small text-muted" title="{{ u.keywords }}">{{ u.keywords or 'لم يحدد' }}</span>
                            </div>
                        </td>
                        <td class="pe-4 text-end">
                            <div class="d-flex justify-content-end gap-2">
                                {% if u.payment_status == 'pending' %}
                                <a href="/admin/approve/{{ u.id }}" class="btn btn-success btn-sm rounded-pill px-3 shadow-sm">تفعيل ✅</a>
                                {% endif %}
                                <button onclick="confirmDelete({{ u.id }})" class="btn btn-outline-danger btn-sm rounded-pill px-3 border-0">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    function confirmDelete(id) {
        Swal.fire({
            title: 'هل أنت متأكد؟',
            text: "سيتم حذف قناص من النظام نهائياً!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ff4757',
            cancelButtonColor: '#747d8c',
            confirmButtonText: 'نعم، حذف البيانات',
            cancelButtonText: 'تراجع',
            customClass: {
                popup: 'glass-card'
            }
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = '/admin/delete/' + id;
            }
        })
    }
    </script>
    """
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', admin_content), 
        users_list=users, t=total_users, a=active_now, p=pending_pay
    )


# ==============================
# 🛡️ M-SNIPER: إجراءات الإدارة والخروج
# ==============================

@app.route('/admin/approve/<int:uid>')
def approve(uid):
    if not session.get('admin'): 
        return redirect('/login')
    
    conn = get_db()
    # جلب بيانات المستخدم قبل التفعيل لإرسال رسالة ترحيبية
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    
    if user:
        # تفعيل المستخدم وتحديث حالة الدفع
        conn.execute("UPDATE users SET is_active=1, payment_status='verified' WHERE id=?", (uid,))
        conn.commit()
        
        # 🔔 حركة اختيارية: يمكنك إرسال رسالة تليجرام للمستخدم تخبره بتفعيل حسابه إذا كان الـ ID موجود
        if user['telegram_id']:
            welcome_msg = "✅ <b>تم تفعيل حسابك بنجاح!</b>\nرادار M-Sniper بدأ العمل الآن لرصد مشاريعك."
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": user['telegram_id'], "text": welcome_msg, "parse_mode": "HTML"})
        
        flash(f"تم تفعيل رادار {user['name']} بنجاح! 🎯", "success")
    
    conn.close()
    return redirect('/admin')

@app.route('/admin/delete/<int:uid>')
def delete_user(uid):
    if not session.get('admin'): 
        return redirect('/login')
        
    conn = get_db()
    # حذف صورة التحويل من المجلد لتوفير المساحة
    user = conn.execute("SELECT payment_image FROM users WHERE id=?", (uid,)).fetchone()
    if user and user['payment_image']:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], user['payment_image']))
        except:
            pass # لو الصورة مش موجودة كمل عادي
            
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    
    flash("تم حذف القناص وبياناته نهائياً من الرادار. 🗑️", "info")
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    flash("تم تسجيل الخروج بنجاح. نراك في المهمة القادمة! 🫡", "success")
    return redirect('/')

# ==============================
# 🚀 M-SNIPER: التشغيل النهائي للنظام
# ==============================

if __name__ == '__main__':
    # 1. التأكد من هيكلة المجلدات
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"📁 تم إنشاء مجلد الرفع: {UPLOAD_FOLDER}")

    # 2. تشغيل محرك القنص (Scraper) في Thread منفصل
    # تم ضبط daemon=True لضمان إغلاق المحرك فور إغلاق السيرفر
    print("🎯 M-Sniper Engine: جاري تشغيل محرك البحث...")
    scraper_thread = threading.Thread(target=scraper_worker, daemon=True)
    scraper_thread.start()
    
    # 3. انطلاق سيرفر Flask
    print("🌐 M-Sniper Web: السيرفر جاهز على http://localhost:5000")
    # تم وضع debug=False لضمان عدم تشغيل الـ Thread مرتين في الخلفية
    app.run(host='0.0.0.0', port=5000, debug=False)


