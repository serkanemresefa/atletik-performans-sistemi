from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import os
import json
import hashlib
import secrets
import bcrypt
from functools import wraps

app = Flask(__name__)
# Restrict CORS to localhost and only API routes
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:8081", "http://127.0.0.1:8081"]}
})

# Session configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-' + secrets.token_hex(16))
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SECURE'] = True  # Enable in production with HTTPS

DATABASE = 'atletik_performans.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password with backward compatibility for SHA-256 hashes"""
    # Check if it's a bcrypt hash (starts with $2a$, $2b$, $2x$, or $2y$)
    if password_hash.startswith('$2'):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    # Fallback to SHA-256 for existing users
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def init_database():
    # Veritabanı zaten varsa ve içinde kullanıcılar varsa işlem yapma
    if os.path.exists(DATABASE):
        conn_check = get_db_connection()
        try:
            users_count = conn_check.execute('SELECT COUNT(id) FROM users').fetchone()[0]
            
            if users_count > 0:
                # Check if teams table needs migration
                try:
                    conn_check.execute('SELECT league FROM teams LIMIT 1')
                    
                    # Check if activities table needs time column
                    try:
                        conn_check.execute('SELECT activity_time FROM activities LIMIT 1')
                        print("Database already exists and has users. Skipping initialization.")
                    except sqlite3.OperationalError:
                        # Activities table needs time column migration
                        print("Migrating activities table to add time column...")
                        try:
                            conn_check.execute('ALTER TABLE activities ADD COLUMN activity_time TIME')
                            conn_check.commit()
                            print("Activities table migrated successfully - added activity_time column.")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" in str(e).lower():
                                print("Activities time column already exists.")
                            else:
                                raise e
                    
                    conn_check.close()
                    return
                except sqlite3.OperationalError:
                    # Teams table needs migration
                    print("Migrating teams table...")
                    try:
                        conn_check.execute('ALTER TABLE teams ADD COLUMN league TEXT')
                        conn_check.execute('ALTER TABLE teams ADD COLUMN season TEXT') 
                        conn_check.execute('ALTER TABLE teams ADD COLUMN coach_name TEXT')
                        conn_check.execute('ALTER TABLE teams ADD COLUMN description TEXT')
                        conn_check.commit()
                        print("Teams table migrated successfully.")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            print("Teams table columns already exist.")
                        else:
                            raise e
                    
                    # After teams migration, check for activities time column
                    try:
                        conn_check.execute('SELECT activity_time FROM activities LIMIT 1')
                    except sqlite3.OperationalError:
                        # Activities table needs time column migration
                        print("Migrating activities table to add time column...")
                        try:
                            conn_check.execute('ALTER TABLE activities ADD COLUMN activity_time TIME')
                            conn_check.commit()
                            print("Activities table migrated successfully - added activity_time column.")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" in str(e).lower():
                                print("Activities time column already exists.")
                            else:
                                raise e
                    
                    conn_check.close()
                    return
                    
        except sqlite3.OperationalError:
            # Henüz users tablosu yok, init devam etsin
            pass
        conn_check.close()

    conn = get_db_connection()
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            league TEXT,
            season TEXT,
            coach_name TEXT,
            description TEXT,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(name, user_id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date DATE,
            nationality TEXT,
            primary_position TEXT,
            secondary_positions TEXT,
            preferred_foot TEXT,
            jersey_number INTEGER,
            height_cm INTEGER,
            weight_kg REAL,
            previous_club TEXT,
            club_history TEXT,
            contract_start DATE,
            contract_end DATE,
            blood_type TEXT,
            injury_history TEXT,
            current_injury_status TEXT,
            phone TEXT,
            email TEXT,
            emergency_contact TEXT,
            notes TEXT,
            team_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            date DATE NOT NULL,
            activity_time TIME,
            activity_type TEXT NOT NULL CHECK (activity_type IN ('training', 'match')),
            duration_minutes INTEGER, total_distance_m INTEGER,
            high_speed_16kmh_m INTEGER, high_speed_18kmh_m INTEGER,
            high_speed_20kmh_m INTEGER, sprint_24kmh_m INTEGER,
            acc_decc_count INTEGER, high_acc_decc_count INTEGER,
            high_metabolic_power_m INTEGER, 
            max_speed_kmh REAL,
            sprint_count_16plus INTEGER,
            sprint_count_18plus INTEGER,
            sprint_count_20plus INTEGER,
            sprint_count_24plus INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS weight_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            weight_kg REAL NOT NULL,
            measurement_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS injury_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            injury_date DATE NOT NULL,
            injury_type TEXT NOT NULL,
            description TEXT,
            recovery_date DATE,
            status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'recovered')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS match_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            period_type TEXT NOT NULL CHECK (period_type IN ('1st_half', '2nd_half', 'extra_time')),
            start_minute INTEGER NOT NULL DEFAULT 0,
            end_minute INTEGER NOT NULL DEFAULT 45,
            duration_minutes INTEGER,
            total_distance_m INTEGER,
            high_speed_16kmh_m INTEGER,
            high_speed_18kmh_m INTEGER,
            high_speed_20kmh_m INTEGER,
            sprint_24kmh_m INTEGER,
            acc_decc_count INTEGER,
            high_acc_decc_count INTEGER,
            high_metabolic_power_m INTEGER,
            max_speed_kmh REAL,
            sprint_count_16plus INTEGER,
            sprint_count_18plus INTEGER,
            sprint_count_20plus INTEGER,
            sprint_count_24plus INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        )
        ''')
        # Demo kullanıcı oluştur
        demo_password = hash_password('demo123')
        try:
            cursor = conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                                ('demo', 'demo@example.com', demo_password))
            demo_user_id = cursor.lastrowid
            
            # Create demo teams with full details
            team1_cursor = conn.execute("INSERT INTO teams (name, league, season, coach_name, description, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                                      ('Fenerbahçe U19', 'U19 Elit Ligi', '2024-25', 'Emre Belözoğlu', 'Fenerbahçe altyapı takımı - gelecek vadeden oyuncular', demo_user_id))
            team1_id = team1_cursor.lastrowid
            
            team2_cursor = conn.execute("INSERT INTO teams (name, league, season, coach_name, description, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                                      ('Galatasaray A2', 'Süper Lig', '2024-25', 'Okan Buruk', 'Galatasaray 2. takım - genç yetenek geliştirme', demo_user_id))
            team2_id = team2_cursor.lastrowid
            
            # Fenerbahçe U19 Full Squad (18 players)
            fenerbahce_players = [
                # Kaleciler
                ('Arda', 'Güvenç', '2005-01-15', 'Türkiye', 'GK', '', 'Sağ', 1, 188, 78.0, 'Fenerbahçe U17', 'Fenerbahçe U15, U16, U17', '2024-01-01', '2025-06-30', 'A+', '', 'Sağlam', '0555-101-0001', 'arda.guvenc@fb.org.tr', 'Anne: 0555-201-0001', 'Refleksleri güçlü genç kaleci', team1_id),
                ('Mehmet', 'Akgün', '2006-03-22', 'Türkiye', 'GK', '', 'Sağ', 12, 185, 76.5, 'Fenerbahçe U16', 'Fenerbahçe U14, U15, U16', '2024-01-01', '2025-06-30', 'O+', '', 'Sağlam', '0555-101-0002', 'mehmet.akgun@fb.org.tr', 'Baba: 0555-201-0002', 'Yetenekli 2. kaleci', team1_id),
                
                # Defanslar
                ('Can', 'Uzun', '2005-04-10', 'Türkiye', 'CB', 'RB', 'Sağ', 2, 185, 79.0, 'Fenerbahçe U17', 'Fenerbahçe U15, U16, U17', '2024-01-01', '2026-06-30', 'A-', '', 'Sağlam', '0555-101-0003', 'can.uzun@fb.org.tr', 'Anne: 0555-201-0003', 'Liderlik özelliği olan stoper', team1_id),
                ('Emir', 'Ortakaya', '2006-02-18', 'Türkiye', 'CB', 'LB', 'Sol', 4, 182, 75.0, 'Fenerbahçe U16', 'Fenerbahçe U14, U15, U16', '2024-01-01', '2025-06-30', 'B+', '', 'Sağlam', '0555-101-0004', 'emir.ortakaya@fb.org.tr', 'Baba: 0555-201-0004', 'Hızlı ve çıkış yapabilen stoper', team1_id),
                ('Kerem', 'Kesgin', '2005-07-05', 'Türkiye', 'LB', 'LM', 'Sol', 3, 176, 68.0, 'Galatasaray U17', 'Galatasaray U15, U16, U17', '2024-07-01', '2026-06-30', 'O-', '', 'Sağlam', '0555-101-0005', 'kerem.kesgin@fb.org.tr', 'Anne: 0555-201-0005', 'Hücuma destek veren sol bek', team1_id),
                ('Burak', 'Özdemir', '2005-09-12', 'Türkiye', 'RB', 'RM', 'Sağ', 20, 179, 71.5, 'Beşiktaş U17', 'Beşiktaş U15, U16, U17', '2024-07-01', '2026-06-30', 'A+', '', 'Sağlam', '0555-101-0006', 'burak.ozdemir@fb.org.tr', 'Baba: 0555-201-0006', 'Dayanıklı ve disiplinli sağ bek', team1_id),
                
                # Orta sahalar
                ('Enes', 'Ünal', '2005-05-20', 'Türkiye', 'CDM', 'CM', 'Sağ', 6, 180, 72.0, 'Trabzonspor U17', 'Trabzonspor U15, U16, U17', '2024-01-01', '2026-06-30', 'B-', '', 'Sağlam', '0555-101-0007', 'enes.unal@fb.org.tr', 'Anne: 0555-201-0007', 'Defansif orta saha, top kırma uzmanı', team1_id),
                ('Mert', 'Hakan', '2005-08-08', 'Türkiye', 'CM', 'CAM,CDM', 'Her ikisi', 8, 177, 69.0, 'Fenerbahçe U17', 'Fenerbahçe U15, U16, U17', '2024-01-01', '2026-06-30', 'AB+', '', 'Sağlam', '0555-101-0008', 'mert.hakan@fb.org.tr', 'Baba: 0555-201-0008', 'Box-to-box oyuncu, her pozisyonda oynayabilir', team1_id),
                ('Yusuf', 'Yazıcı', '2006-01-30', 'Türkiye', 'CAM', 'CM,LM', 'Sol', 10, 174, 66.5, 'Lille U17', 'Lille U15, U16, U17', '2024-07-01', '2027-06-30', 'A+', '', 'Sağlam', '0555-101-0009', 'yusuf.yazici@fb.org.tr', 'Anne: 0555-201-0009', 'Kreativ oyuncu, pas ve şut kalitesi yüksek', team1_id),
                ('Ali', 'Koç', '2005-11-25', 'Türkiye', 'RM', 'RW,CAM', 'Sağ', 11, 172, 65.0, 'Fenerbahçe U17', 'Fenerbahçe U15, U16, U17', '2024-01-01', '2025-06-30', 'O+', '', 'Sağlam', '0555-101-0010', 'ali.koc@fb.org.tr', 'Baba: 0555-201-0010', 'Hızlı kanat oyuncusu, 1v1 iyi', team1_id),
                ('Emre', 'Mor', '2005-12-03', 'Türkiye', 'LM', 'LW,CAM', 'Sol', 7, 170, 63.0, 'Celta Vigo U17', 'Celta Vigo U15, U16, U17', '2024-07-01', '2027-06-30', 'B+', '', 'Sağlam', '0555-101-0011', 'emre.mor@fb.org.tr', 'Anne: 0555-201-0011', 'Teknikli sol kanat, dribling ustası', team1_id),
                
                # Forvetler  
                ('Arda', 'Güler', '2005-02-25', 'Türkiye', 'RW', 'CAM,ST', 'Sol', 21, 175, 68.0, 'Real Madrid Castilla', 'Real Madrid U16, U17, Castilla', '2024-07-01', '2027-06-30', 'A-', '', 'Sağlam', '0555-101-0012', 'arda.guler@fb.org.tr', 'Baba: 0555-201-0012', 'Genç yıldız, şut ve pas kalitesi mükemmel', team1_id),
                ('Cenk', 'Tosun', '2005-06-18', 'Türkiye', 'ST', 'CAM', 'Sağ', 9, 183, 76.0, 'Everton U18', 'Everton U16, U17, U18', '2024-07-01', '2026-06-30', 'O-', '', 'Sağlam', '0555-101-0013', 'cenk.tosun@fb.org.tr', 'Anne: 0555-201-0013', 'Güçlü santrafor, hava toplarında etkili', team1_id),
                ('Barış', 'Alper', '2006-04-14', 'Türkiye', 'LW', 'ST,CAM', 'Sol', 17, 173, 64.5, 'Fenerbahçe U16', 'Fenerbahçe U14, U15, U16', '2024-01-01', '2025-06-30', 'AB-', '', 'Sağlam', '0555-101-0014', 'baris.alper@fb.org.tr', 'Baba: 0555-201-0014', 'Hızlı sol kanat, finiş kalitesi iyi', team1_id),
                
                # Yedekler
                ('Umut', 'Bozok', '2005-10-07', 'Türkiye', 'ST', 'CAM', 'Sağ', 19, 181, 73.0, 'Nürnberg U17', 'Nürnberg U15, U16, U17', '2024-07-01', '2026-06-30', 'A+', '', 'Sağlam', '0555-101-0015', 'umut.bozok@fb.org.tr', 'Anne: 0555-201-0015', 'Alternatif forvet, pozisyon alması iyi', team1_id),
                ('Dorukhan', 'Toköz', '2005-03-28', 'Türkiye', 'CM', 'CDM,RB', 'Sağ', 15, 178, 70.0, 'Fenerbahçe U17', 'Fenerbahçe U15, U16, U17', '2024-01-01', '2025-06-30', 'B+', 'Ayak bileği burkulması - 2024 (3 hafta)', 'İyileşme aşamasında', '0555-101-0016', 'dorukhan.tokoz@fb.org.tr', 'Baba: 0555-201-0016', 'Çok fonksiyonlu oyuncu, takım oyunu güçlü', team1_id),
                ('İrfan Can', 'Kahveci', '2005-07-15', 'Türkiye', 'CAM', 'CM,RW', 'Sol', 14, 176, 67.0, 'Medipol Başakşehir U17', 'Başakşehir U15, U16, U17', '2024-07-01', '2026-06-30', 'O+', '', 'Sağlam', '0555-101-0017', 'irfancan.kahveci@fb.org.tr', 'Anne: 0555-201-0017', 'Çok yetenekli ofansif oyuncu, set piece uzmanı', team1_id),
                ('Oğuzhan', 'Özyakup', '2005-09-23', 'Türkiye', 'CM', 'CAM,CDM', 'Sağ', 16, 175, 68.5, 'Feyenoord U17', 'Feyenoord U15, U16, U17', '2024-07-01', '2027-06-30', 'A-', '', 'Sağlam', '0555-101-0018', 'oguzhan.ozyakup@fb.org.tr', 'Baba: 0555-201-0018', 'Pas dağıtımı mükemmel, oyun kurma yetisi var', team1_id)
            ]
            
            # Galatasaray A2 Squad (10 players - smaller squad)
            galatasaray_players = [
                # Kaleci
                ('Berke', 'Özer', '2004-05-10', 'Türkiye', 'GK', '', 'Sağ', 1, 190, 82.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2026-06-30', 'A+', '', 'Sağlam', '0555-201-0001', 'berke.ozer@gala.org', 'Baba: 0555-301-0001', 'Yetenekli genç kaleci, A takım yedeklerinde', team2_id),
                
                # Defanslar
                ('Kaan', 'Ayhan', '2004-08-15', 'Türkiye', 'CB', 'CDM', 'Sağ', 4, 186, 78.0, 'Fortuna Düsseldorf', 'Fortuna Düsseldorf U19, U21', '2024-07-01', '2026-06-30', 'O+', '', 'Sağlam', '0555-201-0002', 'kaan.ayhan@gala.org', 'Anne: 0555-301-0002', 'Güçlü stoper, liderlik vasfı var', team2_id),
                ('Alpaslan', 'Öztürk', '2004-11-22', 'Türkiye', 'LB', 'LM', 'Sol', 3, 177, 70.0, 'Fenerbahçe U19', 'Fenerbahçe U17, U18, U19', '2024-07-01', '2027-06-30', 'B-', '', 'Sağlam', '0555-201-0003', 'alpaslan.ozturk@gala.org', 'Baba: 0555-301-0003', 'Hızlı sol bek, hücuma katılır', team2_id),
                ('Abdurrahim', 'Dursun', '2004-02-28', 'Türkiye', 'RB', 'CB', 'Sağ', 2, 181, 74.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2025-06-30', 'A-', '', 'Sağlam', '0555-201-0004', 'abdurrahim.dursun@gala.org', 'Anne: 0555-301-0004', 'Versatil defans oyuncusu', team2_id),
                
                # Orta sahalar
                ('Kerem', 'Aktürkoğlu', '2004-10-21', 'Türkiye', 'LW', 'LM,CAM', 'Sol', 7, 174, 67.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2026-06-30', 'O-', '', 'Sağlam', '0555-201-0005', 'kerem.akturkoglu@gala.org', 'Baba: 0555-301-0005', 'Hızlı sol kanat, dribling ve finiş iyi', team2_id),
                ('Taylan', 'Antalyalı', '2004-06-05', 'Türkiye', 'CDM', 'CM', 'Sağ', 6, 175, 68.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2026-06-30', 'AB+', '', 'Sağlam', '0555-201-0006', 'taylan.antalyali@gala.org', 'Anne: 0555-301-0006', 'Defansif orta saha, pas dağıtımı güçlü', team2_id),
                ('Yunus', 'Akgün', '2004-07-07', 'Türkiye', 'CAM', 'CM,RW', 'Her ikisi', 10, 176, 69.0, 'Leicester City U21', 'Leicester U18, U19, U21', '2024-07-01', '2026-06-30', 'A+', '', 'Sağlam', '0555-201-0007', 'yunus.akgun@gala.org', 'Baba: 0555-301-0007', 'Teknikli 10 numara, şut kalitesi yüksek', team2_id),
                
                # Forvetler
                ('Halil', 'Dervişoğlu', '2004-12-08', 'Türkiye', 'ST', 'RW', 'Sağ', 9, 185, 77.0, 'Brentford U21', 'Brentford U18, U19, U21', '2024-07-01', '2026-06-30', 'B+', '', 'Sağlam', '0555-201-0008', 'halil.dervisoglu@gala.org', 'Anne: 0555-301-0008', 'Güçlü santrafor, hava topu ve bitiricilik iyi', team2_id),
                ('Berkan', 'Kutlu', '2004-09-18', 'Türkiye', 'RW', 'CAM,ST', 'Sol', 11, 172, 65.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2025-06-30', 'O+', 'Hamstring - 2024 (2 hafta)', 'Sağlam', '0555-201-0009', 'berkan.kutlu@gala.org', 'Baba: 0555-301-0009', 'Çok yönlü ofansif oyuncu, çalışkan', team2_id),
                ('Atalay', 'Babacan', '2004-04-30', 'Türkiye', 'ST', 'CAM', 'Sağ', 19, 180, 72.0, 'Galatasaray U19', 'Galatasaray U17, U18, U19', '2024-01-01', '2025-06-30', 'A-', '', 'Sağlam', '0555-201-0010', 'atalay.babacan@gala.org', 'Anne: 0555-301-0010', 'Genç forvet, gelişim aşamasında', team2_id)
            ]
            
            # Insert both teams' players
            conn.executemany("INSERT INTO players (first_name, last_name, birth_date, nationality, primary_position, secondary_positions, preferred_foot, jersey_number, height_cm, weight_kg, previous_club, club_history, contract_start, contract_end, blood_type, injury_history, current_injury_status, phone, email, emergency_contact, notes, team_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fenerbahce_players)
            conn.executemany("INSERT INTO players (first_name, last_name, birth_date, nationality, primary_position, secondary_positions, preferred_foot, jersey_number, height_cm, weight_kg, previous_club, club_history, contract_start, contract_end, blood_type, injury_history, current_injury_status, phone, email, emergency_contact, notes, team_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", galatasaray_players)
            
            # Get all inserted players for activity data
            all_players = conn.execute('SELECT id, primary_position FROM players').fetchall()
            
            # Generate sample activity data
            import random
            from datetime import datetime, timedelta
            
            sample_activities = []
            base_date = datetime.now() - timedelta(days=30)
            
            for player in all_players:
                player_id = player[0]
                position = player[1]
                
                # Generate 18 activities per player over 30 days
                for i in range(18):
                    # Random date within last 30 days
                    days_ago = random.randint(1, 30)
                    activity_date = (base_date + timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    
                    # 70% training, 30% match
                    activity_type = 'training' if random.random() < 0.7 else 'match'
                    
                    # Position-based performance values
                    if position == 'GK':  # Goalkeepers
                        duration = random.randint(80, 95)
                        total_distance = random.randint(4000, 6000)
                        hs16 = random.randint(200, 800)
                        hs18 = random.randint(100, 400)
                        hs20 = random.randint(50, 200)
                        sprint = random.randint(20, 100)
                        acc_decc = random.randint(180, 250)
                        high_acc = random.randint(15, 35)
                        metabolic = random.randint(800, 1200)
                    elif position in ['CB', 'LB', 'RB']:  # Defenders
                        duration = random.randint(85, 95)
                        total_distance = random.randint(8000, 11000)
                        hs16 = random.randint(800, 1500)
                        hs18 = random.randint(400, 800)
                        hs20 = random.randint(200, 500)
                        sprint = random.randint(100, 300)
                        acc_decc = random.randint(220, 280)
                        high_acc = random.randint(25, 45)
                        metabolic = random.randint(1200, 1800)
                    elif position in ['CDM', 'CM', 'CAM', 'LM', 'RM']:  # Midfielders
                        duration = random.randint(80, 95)
                        total_distance = random.randint(10000, 13000)
                        hs16 = random.randint(1200, 2000)
                        hs18 = random.randint(600, 1200)
                        hs20 = random.randint(300, 700)
                        sprint = random.randint(150, 400)
                        acc_decc = random.randint(250, 320)
                        high_acc = random.randint(30, 55)
                        metabolic = random.randint(1400, 2000)
                    else:  # Forwards (LW, RW, ST)
                        duration = random.randint(75, 90)
                        total_distance = random.randint(9000, 12000)
                        hs16 = random.randint(1500, 2500)
                        hs18 = random.randint(800, 1500)
                        hs20 = random.randint(400, 900)
                        sprint = random.randint(200, 600)
                        acc_decc = random.randint(200, 300)
                        high_acc = random.randint(25, 50)
                        metabolic = random.randint(1300, 1900)
                    
                    # Match vs Training variations
                    if activity_type == 'match':
                        # Matches are typically more intense
                        total_distance = int(total_distance * random.uniform(1.1, 1.3))
                        hs16 = int(hs16 * random.uniform(1.2, 1.5))
                        hs18 = int(hs18 * random.uniform(1.3, 1.6))
                        hs20 = int(hs20 * random.uniform(1.4, 1.7))
                        sprint = int(sprint * random.uniform(1.5, 2.0))
                        acc_decc = int(acc_decc * random.uniform(1.2, 1.4))
                        high_acc = int(high_acc * random.uniform(1.3, 1.6))
                        metabolic = int(metabolic * random.uniform(1.2, 1.5))
                        duration = 90  # Standard match duration
                        notes_options = [
                            'İyi performans, takım oyunu güçlü',
                            'Hızlı başlangıç, ikinci yarıda düştü',
                            'Defansif görevi iyi yerine getirdi',
                            'Hücumda etkili, pozisyon aldı',
                            'Fiziksel olarak iyiydi',
                            'Pas kalitesi yüksekti',
                            'Baskı altında sakin kaldı'
                        ]
                    else:
                        # Training variations
                        variation = random.uniform(0.8, 1.2)
                        total_distance = int(total_distance * variation)
                        hs16 = int(hs16 * variation)
                        hs18 = int(hs18 * variation)
                        hs20 = int(hs20 * variation)
                        sprint = int(sprint * variation)
                        acc_decc = int(acc_decc * variation)
                        high_acc = int(high_acc * variation)
                        metabolic = int(metabolic * variation)
                        notes_options = [
                            'Teknik antrenman, pas çalışması',
                            'Dayanıklılık odaklı antrenman',
                            'Hız ve çeviklik çalışması',
                            'Taktikal antrenman, pozisyonel',
                            'Kondisyon antrenmanı',
                            'Top ile çalışma ağırlıklı',
                            'Fiziksel hazırlık antrenmanı'
                        ]
                    
                    notes = random.choice(notes_options) if random.random() < 0.6 else ''
                    
                    sample_activities.append((
                        player_id, activity_date, activity_type, duration,
                        total_distance, hs16, hs18, hs20, sprint,
                        acc_decc, high_acc, metabolic, notes
                    ))
            
            # Insert all activity data
            conn.executemany("""
                INSERT INTO activities (
                    player_id, date, activity_type, duration_minutes,
                    total_distance_m, high_speed_16kmh_m, high_speed_18kmh_m,
                    high_speed_20kmh_m, sprint_24kmh_m, acc_decc_count,
                    high_acc_decc_count, high_metabolic_power_m, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_activities)
            
            conn.commit()
            print(f"Database initialized with demo user, {len(all_players)} players, and {len(sample_activities)} activities.")
        except sqlite3.IntegrityError:
            print("Demo user already exists.")
    
    # Create performance indexes (idempotent)
    conn = get_db_connection()
    try:
        # Index for frequent player queries by team
        conn.execute('CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)')
        
        # Index for activity queries by player and date
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_player_date ON activities(player_id, date)')
        
        # Index for weight measurements by player
        conn.execute('CREATE INDEX IF NOT EXISTS idx_weight_player_id ON weight_measurements(player_id)')
        
        # Index for injury records by player
        conn.execute('CREATE INDEX IF NOT EXISTS idx_injury_player_id ON injury_records(player_id)')
        
        conn.commit()
        conn.close()
        print("Database indexes created successfully.")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        conn.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli'}), 400
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and verify_password(password, user['password_hash']):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'message': 'Giriş başarılı'})
    else:
        return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Tüm alanlar zorunlu'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Şifre en az 6 karakter olmalı'}), 400
    
    conn = get_db_connection()
    try:
        password_hash = hash_password(password)
        cursor = conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                            (username, email, password_hash))
        user_id = cursor.lastrowid
        conn.commit()
        
        session['user_id'] = user_id
        session['username'] = username
        
        conn.close()
        return jsonify({'success': True, 'message': 'Kayıt başarılı'}), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'username' in str(e):
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 409
        elif 'email' in str(e):
            return jsonify({'error': 'Bu email adresi zaten kullanılıyor'}), 409
        return jsonify({'error': 'Kayıt hatası'}), 409

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@login_required
def user_profile():
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        user = conn.execute('SELECT id, username, email, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Get user stats
        team_count = conn.execute('SELECT COUNT(*) FROM teams WHERE user_id = ?', (user_id,)).fetchone()[0]
        player_count = conn.execute('''
            SELECT COUNT(*) FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE t.user_id = ?
        ''', (user_id,)).fetchone()[0]
        activity_count = conn.execute('''
            SELECT COUNT(*) FROM activities a 
            JOIN players p ON a.player_id = p.id 
            JOIN teams t ON p.team_id = t.id 
            WHERE t.user_id = ?
        ''', (user_id,)).fetchone()[0]
        
        conn.close()
        return jsonify({
            'user': dict(user),
            'stats': {
                'team_count': team_count,
                'player_count': player_count,
                'activity_count': activity_count
            }
        })
    
    if request.method == 'PUT':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            conn.close()
            return jsonify({'error': 'Kullanıcı adı ve email gerekli'}), 400
        
        try:
            conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (username, email, user_id))
            conn.commit()
            session['username'] = username
            conn.close()
            return jsonify({'success': True, 'message': 'Profil güncellendi'})
        except sqlite3.IntegrityError as e:
            conn.close()
            if 'username' in str(e):
                return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 409
            elif 'email' in str(e):
                return jsonify({'error': 'Bu email adresi zaten kullanılıyor'}), 409
            return jsonify({'error': 'Güncelleme hatası'}), 409

@app.route('/api/user/password', methods=['PUT'])
@login_required
def change_password():
    user_id = session['user_id']
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Mevcut ve yeni şifre gerekli'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Yeni şifre en az 6 karakter olmalı'}), 400
    
    conn = get_db_connection()
    user = conn.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or not verify_password(current_password, user['password_hash']):
        conn.close()
        return jsonify({'error': 'Mevcut şifre yanlış'}), 400
    
    new_password_hash = hash_password(new_password)
    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Şifre güncellendi'})

@app.route('/api/teams', methods=['GET', 'POST'])
@login_required
def handle_teams():
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        teams = conn.execute('SELECT * FROM teams WHERE user_id = ? ORDER BY name', (user_id,)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in teams])
    
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        league = data.get('league', '')
        season = data.get('season', '')
        coach_name = data.get('coach_name', '')
        description = data.get('description', '')
        
        if not name:
            conn.close()
            return jsonify({'error': 'Takım adı gerekli'}), 400
        try:
            cursor = conn.execute('INSERT INTO teams (name, league, season, coach_name, description, user_id) VALUES (?, ?, ?, ?, ?, ?)', 
                                (name, league, season, coach_name, description, user_id))
            conn.commit()
            team_id = cursor.lastrowid
            conn.close()
            return jsonify({'id': team_id, 'name': name}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Bu takım adı zaten var'}), 409

@app.route('/api/teams/<int:team_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_team(team_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Check if team belongs to user
    team = conn.execute('SELECT * FROM teams WHERE id = ? AND user_id = ?', (team_id, user_id)).fetchone()
    if not team:
        conn.close()
        return jsonify({'error': 'Takım bulunamadı veya yetkiniz yok'}), 404
    
    if request.method == 'PUT':
        data = request.json
        new_name = data.get('name')
        if not new_name:
            conn.close()
            return jsonify({'error': 'Takım adı gerekli'}), 400
        try:
            conn.execute('UPDATE teams SET name = ? WHERE id = ?', (new_name, team_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Takım adı güncellendi'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Bu takım adı zaten kullanılıyor'}), 409
    
    if request.method == 'DELETE':
        # Get stats before deletion
        player_count = conn.execute('SELECT COUNT(*) FROM players WHERE team_id = ?', (team_id,)).fetchone()[0]
        activity_count = conn.execute('''
            SELECT COUNT(*) FROM activities a 
            JOIN players p ON a.player_id = p.id 
            WHERE p.team_id = ?
        ''', (team_id,)).fetchone()[0]
        
        # Delete team (cascading will handle players and activities via foreign keys)
        # First delete activities, then players, then team
        conn.execute('''
            DELETE FROM activities WHERE player_id IN 
            (SELECT id FROM players WHERE team_id = ?)
        ''', (team_id,))
        conn.execute('DELETE FROM players WHERE team_id = ?', (team_id,))
        conn.execute('DELETE FROM teams WHERE id = ?', (team_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Takım silindi: {player_count} oyuncu, {activity_count} aktivite verisi kaldırıldı'
        })

@app.route('/api/players', methods=['GET', 'POST'])
@login_required
def handle_players():
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        team_id = request.args.get('team_id')
        if not team_id:
            conn.close()
            return jsonify({'error': 'team_id gerekli'}), 400
        
        # Takımın kullanıcıya ait olduğunu kontrol et
        team_check = conn.execute('SELECT id FROM teams WHERE id = ? AND user_id = ?', (team_id, user_id)).fetchone()
        if not team_check:
            conn.close()
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        players = conn.execute('SELECT * FROM players WHERE team_id = ? ORDER BY first_name, last_name', (team_id,)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in players])

    if request.method == 'POST':
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        team_id = data.get('team_id')
        
        if not all([first_name, last_name, team_id]):
            conn.close()
            return jsonify({'error': 'Ad, soyad ve takım bilgisi gerekli'}), 400
        
        # Takımın kullanıcıya ait olduğunu kontrol et
        team_check = conn.execute('SELECT id FROM teams WHERE id = ? AND user_id = ?', (team_id, user_id)).fetchone()
        if not team_check:
            conn.close()
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        # Insert player with all fields
        cursor = conn.execute('''
            INSERT INTO players (first_name, last_name, birth_date, nationality, primary_position, 
                               secondary_positions, preferred_foot, jersey_number, height_cm, weight_kg,
                               previous_club, club_history, contract_start, contract_end, blood_type,
                               injury_history, current_injury_status, phone, email, emergency_contact, notes, team_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            first_name, last_name, data.get('birth_date'), data.get('nationality'),
            data.get('primary_position'), data.get('secondary_positions'), data.get('preferred_foot'),
            data.get('jersey_number'), data.get('height_cm'), data.get('weight_kg'),
            data.get('previous_club'), data.get('club_history'), data.get('contract_start'),
            data.get('contract_end'), data.get('blood_type'), data.get('injury_history'),
            data.get('current_injury_status'), data.get('phone'), data.get('email'),
            data.get('emergency_contact'), data.get('notes'), team_id
        ))
        conn.commit()
        player_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': player_id, 'name': f'{first_name} {last_name}'}), 201


@app.route('/api/teams/<int:team_id>/stats', methods=['GET'])
@login_required
def get_team_delete_stats(team_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Verify team ownership
    team = conn.execute('SELECT * FROM teams WHERE id = ? AND user_id = ?', (team_id, user_id)).fetchone()
    if not team:
        conn.close()
        return jsonify({'error': 'Takım bulunamadı'}), 404
    
    player_count = conn.execute('SELECT COUNT(*) FROM players WHERE team_id = ?', (team_id,)).fetchone()[0]
    activity_count = conn.execute('''
        SELECT COUNT(*) FROM activities a 
        JOIN players p ON a.player_id = p.id 
        WHERE p.team_id = ?
    ''', (team_id,)).fetchone()[0]
    
    conn.close()
    return jsonify({
        'team_name': team['name'],
        'player_count': player_count,
        'activity_count': activity_count
    })

@app.route('/api/players/<int:player_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_single_player(player_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        # Get single player details
        player = conn.execute('''
            SELECT p.* FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE p.id = ? AND t.user_id = ?
        ''', (player_id, user_id)).fetchone()
        
        conn.close()
        if player:
            return jsonify(dict(player))
        else:
            return jsonify({'error': 'Oyuncu bulunamadı'}), 404
    
    elif request.method == 'PUT':
        # Update player details
        data = request.json
        
        # Verify player ownership first
        player_check = conn.execute('''
            SELECT 1 FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE p.id = ? AND t.user_id = ?
        ''', (player_id, user_id)).fetchone()
        
        if not player_check:
            conn.close()
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        # Update player
        conn.execute('''
            UPDATE players SET 
                first_name=?, last_name=?, birth_date=?, nationality=?, 
                primary_position=?, secondary_positions=?, preferred_foot=?, jersey_number=?,
                height_cm=?, weight_kg=?, previous_club=?, club_history=?,
                contract_start=?, contract_end=?, blood_type=?, injury_history=?,
                current_injury_status=?, phone=?, email=?, emergency_contact=?, notes=?
            WHERE id=?
        ''', (
            data.get('first_name'), data.get('last_name'), data.get('birth_date'), 
            data.get('nationality'), data.get('primary_position'), data.get('secondary_positions'),
            data.get('preferred_foot'), data.get('jersey_number'), data.get('height_cm'), 
            data.get('weight_kg'), data.get('previous_club'), data.get('club_history'),
            data.get('contract_start'), data.get('contract_end'), data.get('blood_type'),
            data.get('injury_history'), data.get('current_injury_status'), data.get('phone'),
            data.get('email'), data.get('emergency_contact'), data.get('notes'), player_id
        ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Oyuncu güncellendi'})
    
    elif request.method == 'DELETE':
        # Delete player logic (existing)
        # Verify player ownership
        player_check = conn.execute('''
            SELECT 1 FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE p.id = ? AND t.user_id = ?
        ''', (player_id, user_id)).fetchone()
        
        if not player_check:
            conn.close()
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        # Delete associated activities first
        conn.execute('DELETE FROM activities WHERE player_id = ?', (player_id,))
        # Delete player
        conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Oyuncu silindi'})

@app.route('/api/players/<int:player_id>/statistics', methods=['GET'])
@login_required
def get_player_statistics(player_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Oyuncunun kullanıcının takımına ait olduğunu kontrol et
    player_check = conn.execute('''
        SELECT p.id, p.first_name, p.last_name, p.primary_position FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player_check:
        conn.close()
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    # Genel istatistikler
    total_activities = conn.execute('SELECT COUNT(*) FROM activities WHERE player_id = ?', (player_id,)).fetchone()[0]
    training_count = conn.execute("SELECT COUNT(*) FROM activities WHERE player_id = ? AND activity_type = 'training'", (player_id,)).fetchone()[0]
    match_count = conn.execute("SELECT COUNT(*) FROM activities WHERE player_id = ? AND activity_type = 'match'", (player_id,)).fetchone()[0]
    
    # Ortalama performans metrikleri
    avg_stats = conn.execute('''
        SELECT 
            AVG(duration_minutes) as avg_duration,
            AVG(total_distance_m) as avg_distance,
            AVG(high_speed_16kmh_m) as avg_hs16,
            AVG(high_speed_18kmh_m) as avg_hs18,
            AVG(high_speed_20kmh_m) as avg_hs20,
            AVG(sprint_24kmh_m) as avg_sprint,
            AVG(acc_decc_count) as avg_acc_decc,
            AVG(high_metabolic_power_m) as avg_metabolic
        FROM activities WHERE player_id = ?
    ''', (player_id,)).fetchone()
    
    # Antrenman vs maç karşılaştırması
    training_avg = conn.execute('''
        SELECT 
            AVG(duration_minutes) as avg_duration,
            AVG(total_distance_m) as avg_distance,
            AVG(high_speed_20kmh_m) as avg_hs20,
            AVG(sprint_24kmh_m) as avg_sprint
        FROM activities WHERE player_id = ? AND activity_type = 'training'
    ''', (player_id,)).fetchone()
    
    match_avg = conn.execute('''
        SELECT 
            AVG(duration_minutes) as avg_duration,
            AVG(total_distance_m) as avg_distance,
            AVG(high_speed_20kmh_m) as avg_hs20,
            AVG(sprint_24kmh_m) as avg_sprint
        FROM activities WHERE player_id = ? AND activity_type = 'match'
    ''', (player_id,)).fetchone()
    
    # En son aktivite tarihi
    last_activity = conn.execute('SELECT MAX(date) FROM activities WHERE player_id = ?', (player_id,)).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'player_name': f"{player_check['first_name']} {player_check['last_name']}",
        'position': player_check['primary_position'],
        'general_stats': {
            'total_activities': total_activities,
            'training_count': training_count,
            'match_count': match_count,
            'last_activity_date': last_activity
        },
        'averages': {
            'duration_minutes': round(avg_stats['avg_duration'] or 0, 1),
            'total_distance_m': round(avg_stats['avg_distance'] or 0, 0),
            'high_speed_16kmh_m': round(avg_stats['avg_hs16'] or 0, 0),
            'high_speed_18kmh_m': round(avg_stats['avg_hs18'] or 0, 0),
            'high_speed_20kmh_m': round(avg_stats['avg_hs20'] or 0, 0),
            'sprint_24kmh_m': round(avg_stats['avg_sprint'] or 0, 0),
            'acc_decc_count': round(avg_stats['avg_acc_decc'] or 0, 0),
            'metabolic_power_m': round(avg_stats['avg_metabolic'] or 0, 0)
        },
        'training_vs_match': {
            'training': {
                'duration': round(training_avg['avg_duration'] or 0, 1),
                'distance': round(training_avg['avg_distance'] or 0, 0),
                'high_speed': round(training_avg['avg_hs20'] or 0, 0),
                'sprint': round(training_avg['avg_sprint'] or 0, 0)
            },
            'match': {
                'duration': round(match_avg['avg_duration'] or 0, 1),
                'distance': round(match_avg['avg_distance'] or 0, 0),
                'high_speed': round(match_avg['avg_hs20'] or 0, 0),
                'sprint': round(match_avg['avg_sprint'] or 0, 0)
            }
        }
    })

@app.route('/api/players/<int:player_id>/stats', methods=['GET'])
@login_required
def get_player_delete_stats(player_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Verify player ownership
    player = conn.execute('''
        SELECT p.first_name, p.last_name FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Oyuncu bulunamadı'}), 404
    
    activity_count = conn.execute('SELECT COUNT(*) FROM activities WHERE player_id = ?', (player_id,)).fetchone()[0]
    
    conn.close()
    return jsonify({
        'player_name': f"{player['first_name']} {player['last_name']}",
        'activity_count': activity_count
    })

@app.route('/api/activities', methods=['POST'])
@login_required
def add_activity():
    user_id = session['user_id']
    data = request.json
    
    if not data.get('player_id') or not data.get('date') or not data.get('activity_type'):
        return jsonify({'error': 'Zorunlu alanlar eksik'}), 400
    
    conn = get_db_connection()
    
    # Oyuncunun kullanıcının takımına ait olduğunu kontrol et
    player_check = conn.execute('''
        SELECT p.id FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id = ? AND t.user_id = ?
    ''', (data['player_id'], user_id)).fetchone()
    
    if not player_check:
        conn.close()
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    # Insert activity with new metrics
    cursor = conn.execute('''
    INSERT INTO activities (player_id, date, activity_time, activity_type, duration_minutes, total_distance_m, 
                          high_speed_16kmh_m, high_speed_18kmh_m, high_speed_20kmh_m, sprint_24kmh_m, 
                          acc_decc_count, high_acc_decc_count, high_metabolic_power_m, 
                          max_speed_kmh, sprint_count_16plus, sprint_count_18plus, sprint_count_20plus, sprint_count_24plus, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['player_id'], data['date'], data.get('activity_time'),
        data['activity_type'], data.get('duration_minutes'), data.get('total_distance_m'),
        data.get('high_speed_16kmh_m'), data.get('high_speed_18kmh_m'),
        data.get('high_speed_20kmh_m'), data.get('sprint_24kmh_m'),
        data.get('acc_decc_count'), data.get('high_acc_decc_count'),
        data.get('high_metabolic_power_m'), data.get('max_speed_kmh'),
        data.get('sprint_count_16plus'), data.get('sprint_count_18plus'),
        data.get('sprint_count_20plus'), data.get('sprint_count_24plus'),
        data.get('notes')
    ))
    
    activity_id = cursor.lastrowid
    
    # Insert custom metrics if any
    if 'custom_metrics' in data and data['custom_metrics']:
        for metric in data['custom_metrics']:
            conn.execute('''
            INSERT INTO custom_metrics (activity_id, metric_name, metric_value, unit)
            VALUES (?, ?, ?, ?)
            ''', (activity_id, metric['metric_name'], metric['metric_value'], metric.get('unit')))
    
    # Insert match periods if any
    if 'match_periods' in data and data['match_periods']:
        for period in data['match_periods']:
            conn.execute('''
            INSERT INTO match_periods (activity_id, period_type, start_minute, end_minute, 
                                     duration_minutes, total_distance_m, high_speed_16kmh_m, 
                                     high_speed_18kmh_m, high_speed_20kmh_m, sprint_24kmh_m,
                                     acc_decc_count, high_acc_decc_count, high_metabolic_power_m,
                                     max_speed_kmh, sprint_count_16plus, sprint_count_18plus,
                                     sprint_count_20plus, sprint_count_24plus, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (activity_id, period['period_type'], period['start_minute'], period['end_minute'],
                  period.get('duration_minutes'), period.get('total_distance_m'), period.get('high_speed_16kmh_m'),
                  period.get('high_speed_18kmh_m'), period.get('high_speed_20kmh_m'), period.get('sprint_24kmh_m'),
                  period.get('acc_decc_count'), period.get('high_acc_decc_count'), period.get('high_metabolic_power_m'),
                  period.get('max_speed_kmh'), period.get('sprint_count_16plus'), period.get('sprint_count_18plus'),
                  period.get('sprint_count_20plus'), period.get('sprint_count_24plus'), period.get('notes')))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/activities', methods=['GET'])
@login_required
def get_activities():
    user_id = session['user_id']
    player_id = request.args.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'player_id gerekli'}), 400
    
    conn = get_db_connection()
    
    # Oyuncunun kullanıcının takımına ait olduğunu kontrol et
    player_check = conn.execute('''
        SELECT p.id FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player_check:
        conn.close()
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    # Oyuncunun aktivitelerini getir
    activities = conn.execute('''
        SELECT * FROM activities 
        WHERE player_id = ? 
        ORDER BY date DESC, activity_time DESC, created_at DESC
    ''', (player_id,)).fetchall()
    
    # Her aktivite için custom metrics'i getir
    result = []
    for activity in activities:
        activity_dict = dict(activity)
        
        # Custom metrics'i getir
        custom_metrics = conn.execute('''
            SELECT metric_name, metric_value, unit FROM custom_metrics 
            WHERE activity_id = ?
            ORDER BY metric_name
        ''', (activity['id'],)).fetchall()
        
        activity_dict['custom_metrics'] = [dict(metric) for metric in custom_metrics]
        result.append(activity_dict)
    
    conn.close()
    return jsonify(result)

@app.route('/api/activities/<int:activity_id>', methods=['PUT', 'DELETE'])
@login_required
def handle_activity(activity_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Verify activity belongs to user's team
    activity_check = conn.execute('''
        SELECT a.*, p.id as player_id FROM activities a
        JOIN players p ON a.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        WHERE a.id = ? AND t.user_id = ?
    ''', (activity_id, user_id)).fetchone()
    
    if not activity_check:
        conn.close()
        return jsonify({'error': 'Activity not found or unauthorized'}), 404
    
    if request.method == 'DELETE':
        # Delete activity
        conn.execute('DELETE FROM activities WHERE id = ?', (activity_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Activity deleted successfully'})
    
    elif request.method == 'PUT':
        # Update activity
        data = request.json or {}
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if 'date' in data:
            update_fields.append('date = ?')
            params.append(data['date'])
        
        if 'activity_time' in data:
            update_fields.append('activity_time = ?')
            params.append(data['activity_time'])
            
        if 'activity_type' in data:
            if data['activity_type'] not in ['training', 'match']:
                conn.close()
                return jsonify({'error': 'Invalid activity type'}), 400
            update_fields.append('activity_type = ?')
            params.append(data['activity_type'])
        
        # Add all other numeric fields
        numeric_fields = [
            'duration_minutes', 'total_distance_m', 'high_speed_16kmh_m', 
            'high_speed_18kmh_m', 'high_speed_20kmh_m', 'sprint_24kmh_m',
            'acc_decc_count', 'high_acc_decc_count', 'high_metabolic_power_m'
        ]
        
        for field in numeric_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                params.append(data[field])
        
        if 'notes' in data:
            update_fields.append('notes = ?')
            params.append(data['notes'])
        
        if not update_fields:
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(activity_id)
        query = f'UPDATE activities SET {", ".join(update_fields)} WHERE id = ?'
        
        try:
            conn.execute(query, params)
            conn.commit()
            conn.close()
            return jsonify({'message': 'Activity updated successfully'})
        except Exception as e:
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    user_id = session['user_id']
    team_id = request.args.get('team_id')
    
    if not team_id:
        return jsonify({'error': 'team_id gerekli'}), 400
    
    conn = get_db_connection()
    
    # Takımın kullanıcıya ait olduğunu kontrol et
    team_check = conn.execute('SELECT id FROM teams WHERE id = ? AND user_id = ?', (team_id, user_id)).fetchone()
    if not team_check:
        conn.close()
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    players_count = conn.execute('SELECT COUNT(*) FROM players WHERE team_id = ?', (team_id,)).fetchone()[0]
    query_counts = '''
        SELECT COUNT(a.id), SUM(CASE WHEN a.activity_type = 'training' THEN 1 ELSE 0 END), SUM(CASE WHEN a.activity_type = 'match' THEN 1 ELSE 0 END)
        FROM activities a JOIN players p ON a.player_id = p.id
        WHERE p.team_id = ?
    '''
    counts = conn.execute(query_counts, (team_id,)).fetchone()
    recent_activities = conn.execute('''
        SELECT a.date, (p.first_name || ' ' || p.last_name) as player_name, a.activity_type, a.total_distance_m, a.duration_minutes
        FROM activities a JOIN players p ON a.player_id = p.id 
        WHERE p.team_id = ? ORDER BY a.created_at DESC LIMIT 10
    ''', (team_id,)).fetchall()
    conn.close()
    return jsonify({
        'players_count': players_count,
        'activities_count': counts[0] or 0,
        'training_count': counts[1] or 0,
        'match_count': counts[2] or 0,
        'recent_activities': [dict(row) for row in recent_activities]
    })

@app.route('/api/analysis', methods=['POST'])
@login_required
def get_analysis():
    """
    Compute training vs match load metrics for one or more players over a date range.

    Request JSON body:
        player_ids: list of player IDs to analyse
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)

    Response JSON:
        players: array of player analysis objects with training/match stats and ratios
        summary: aggregated team summary with training, match, and ratios objects
    """
    user_id = session['user_id']
    data = request.json or {}
    player_ids = data.get('player_ids', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not player_ids or not start_date or not end_date:
        return jsonify({'error': 'player_ids, start_date ve end_date gerekli'}), 400

    conn = get_db_connection()
    
    # Seçilen oyuncuların kullanıcının takımlarına ait olduğunu kontrol et
    placeholders = ','.join(['?' for _ in player_ids])
    player_check = conn.execute(f'''
        SELECT COUNT(*) FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id IN ({placeholders}) AND t.user_id = ?
    ''', player_ids + [user_id]).fetchone()[0]
    
    if player_check != len(player_ids):
        conn.close()
        return jsonify({'error': 'Yetkisiz oyuncu erişimi'}), 403
    results = []
    # Containers to aggregate team averages across players
    agg_training = {'total_distance': 0.0, 'hs16': 0.0, 'hs20': 0.0, 'sprint': 0.0}
    agg_match = {'total_distance': 0.0, 'hs16': 0.0, 'hs20': 0.0, 'sprint': 0.0}
    agg_counts_training = {'total_distance': 0, 'hs16': 0, 'hs20': 0, 'sprint': 0}
    agg_counts_match = {'total_distance': 0, 'hs16': 0, 'hs20': 0, 'sprint': 0}

    for pid in player_ids:
        # Fetch player name
        player_row = conn.execute('SELECT first_name, last_name FROM players WHERE id = ?', (pid,)).fetchone()
        if not player_row:
            # Skip unknown players
            continue
        player_name = f"{player_row['first_name']} {player_row['last_name']}"

        # Compute averages for training activities
        training_stats = conn.execute(
            '''SELECT
                   AVG(total_distance_m) AS dist_avg,
                   AVG(high_speed_16kmh_m) AS hs16_avg,
                   AVG(high_speed_20kmh_m) AS hs20_avg,
                   AVG(sprint_24kmh_m) AS sprint_avg
               FROM activities
               WHERE player_id = ? AND activity_type = 'training'
                 AND date BETWEEN ? AND ?''',
            (pid, start_date, end_date)
        ).fetchone()
        # Compute averages for match activities
        match_stats = conn.execute(
            '''SELECT
                   AVG(total_distance_m) AS dist_avg,
                   AVG(high_speed_16kmh_m) AS hs16_avg,
                   AVG(high_speed_20kmh_m) AS hs20_avg,
                   AVG(sprint_24kmh_m) AS sprint_avg
               FROM activities
               WHERE player_id = ? AND activity_type = 'match'
                 AND date BETWEEN ? AND ?''',
            (pid, start_date, end_date)
        ).fetchone()

        # Extract numeric values or None
        t_dist = training_stats['dist_avg'] if training_stats and training_stats['dist_avg'] is not None else None
        t_hs16 = training_stats['hs16_avg'] if training_stats and training_stats['hs16_avg'] is not None else None
        t_hs20 = training_stats['hs20_avg'] if training_stats and training_stats['hs20_avg'] is not None else None
        t_sprint = training_stats['sprint_avg'] if training_stats and training_stats['sprint_avg'] is not None else None

        m_dist = match_stats['dist_avg'] if match_stats and match_stats['dist_avg'] is not None else None
        m_hs16 = match_stats['hs16_avg'] if match_stats and match_stats['hs16_avg'] is not None else None
        m_hs20 = match_stats['hs20_avg'] if match_stats and match_stats['hs20_avg'] is not None else None
        m_sprint = match_stats['sprint_avg'] if match_stats and match_stats['sprint_avg'] is not None else None

        # Ratios: training ÷ match × 100
        def compute_pct(train_val, match_val):
            if match_val and match_val != 0:
                return (train_val / match_val) * 100 if train_val is not None else 0.0
            return None

        pct_dist = compute_pct(t_dist, m_dist)
        pct_hs16 = compute_pct(t_hs16, m_hs16)
        pct_hs20 = compute_pct(t_hs20, m_hs20)
        pct_sprint = compute_pct(t_sprint, m_sprint)

        results.append({
            'player_id': pid,
            'player_name': player_name,
            'training': {
                'total_distance': t_dist,
                'hs16': t_hs16,
                'hs20': t_hs20,
                'sprint': t_sprint
            },
            'match': {
                'total_distance': m_dist,
                'hs16': m_hs16,
                'hs20': m_hs20,
                'sprint': m_sprint
            },
            'ratios': {
                'distance_pct': pct_dist,
                'hs16_pct': pct_hs16,
                'hs20_pct': pct_hs20,
                'sprint_pct': pct_sprint
            }
        })

        # Accumulate for team summary averages
        for metric_key, val in [('total_distance', t_dist), ('hs16', t_hs16), ('hs20', t_hs20), ('sprint', t_sprint)]:
            if val is not None:
                agg_training[metric_key] += val
                agg_counts_training[metric_key] += 1
        for metric_key, val in [('total_distance', m_dist), ('hs16', m_hs16), ('hs20', m_hs20), ('sprint', m_sprint)]:
            if val is not None:
                agg_match[metric_key] += val
                agg_counts_match[metric_key] += 1

    # Compute team-level averages and ratios
    summary_training = {}
    summary_match = {}
    summary_ratios = {}
    for metric in ['total_distance', 'hs16', 'hs20', 'sprint']:
        avg_train = None
        if agg_counts_training[metric] > 0:
            avg_train = agg_training[metric] / agg_counts_training[metric]
        avg_match = None
        if agg_counts_match[metric] > 0:
            avg_match = agg_match[metric] / agg_counts_match[metric]
        summary_training[metric] = avg_train
        summary_match[metric] = avg_match
        # ratio
        if avg_match and avg_match != 0:
            summary_ratios[f'{metric}_pct'] = (avg_train / avg_match) * 100 if avg_train is not None else 0.0
        else:
            summary_ratios[f'{metric}_pct'] = None

    conn.close()
    return jsonify({'players': results, 'summary': {
        'training': summary_training,
        'match': summary_match,
        'ratios': summary_ratios
    }})

@app.route('/api/match-periods-analysis', methods=['POST'])
@login_required
def get_match_periods_analysis():
    """
    Analyze match performance by periods (1st half vs 2nd half).
    """
    user_id = session['user_id']
    data = request.json or {}
    player_ids = data.get('player_ids', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not player_ids or not start_date or not end_date:
        return jsonify({'error': 'player_ids, start_date ve end_date gerekli'}), 400

    conn = get_db_connection()
    
    # Security check
    placeholders = ','.join(['?' for _ in player_ids])
    player_check = conn.execute(f'''
        SELECT COUNT(*) FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id IN ({placeholders}) AND t.user_id = ?
    ''', player_ids + [user_id]).fetchone()[0]
    
    if player_check != len(player_ids):
        conn.close()
        return jsonify({'error': 'Yetkisiz oyuncu erişimi'}), 403
        
    results = []
    
    for pid in player_ids:
        # Get player name
        player_row = conn.execute('SELECT first_name, last_name FROM players WHERE id = ?', (pid,)).fetchone()
        if not player_row:
            continue
        player_name = f"{player_row['first_name']} {player_row['last_name']}"

        # Get match periods data
        periods_data = conn.execute('''
            SELECT mp.period_type, 
                   AVG(mp.duration_minutes) as avg_duration,
                   AVG(mp.total_distance_m) as avg_distance,
                   AVG(mp.high_speed_16kmh_m) as avg_high_speed_16,
                   AVG(mp.high_speed_18kmh_m) as avg_high_speed_18,
                   AVG(mp.high_speed_20kmh_m) as avg_high_speed_20,
                   AVG(mp.sprint_24kmh_m) as avg_sprint_24,
                   AVG(mp.acc_decc_count) as avg_acc_decc,
                   AVG(mp.high_acc_decc_count) as avg_high_acc_decc,
                   AVG(mp.high_metabolic_power_m) as avg_metabolic_power,
                   AVG(mp.max_speed_kmh) as avg_max_speed,
                   AVG(mp.sprint_count_16plus) as avg_sprint_16plus,
                   AVG(mp.sprint_count_18plus) as avg_sprint_18plus,
                   AVG(mp.sprint_count_20plus) as avg_sprint_20plus,
                   AVG(mp.sprint_count_24plus) as avg_sprint_24plus
            FROM match_periods mp
            JOIN activities a ON mp.activity_id = a.id
            WHERE a.player_id = ? AND a.activity_type = 'match'
              AND a.date BETWEEN ? AND ?
            GROUP BY mp.period_type
        ''', (pid, start_date, end_date)).fetchall()
        
        # Organize data by period
        first_half = {'distance': 0, 'max_speed': 0, 'sprint_count': 0}
        second_half = {'distance': 0, 'max_speed': 0, 'sprint_count': 0}
        
        for period in periods_data:
            period_data = {
                'distance': round(period['avg_distance'] or 0, 0),
                'max_speed': round(period['avg_max_speed'] or 0, 1),
                'sprint_count': round(period['avg_sprint_count'] or 0, 0)
            }
            
            if period['period_type'] == '1st_half':
                first_half = period_data
            elif period['period_type'] == '2nd_half':
                second_half = period_data
        
        # Calculate totals and differences
        total = {
            'distance': first_half['distance'] + second_half['distance'],
            'max_speed': max(first_half['max_speed'], second_half['max_speed']),
            'sprint_count': first_half['sprint_count'] + second_half['sprint_count']
        }
        
        results.append({
            'player_id': pid,
            'player_name': player_name,
            'first_half': first_half,
            'second_half': second_half,
            'total': total
        })
    
    conn.close()
    return jsonify({'players': results})

# Weight Measurements API
@app.route('/api/players/<int:player_id>/weight-measurements', methods=['GET'])
@login_required
def get_weight_measurements(player_id):
    """Get weight measurement history for a player"""
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Verify player belongs to user's team
    player = conn.execute('''
        SELECT p.id FROM players p
        JOIN teams t ON p.team_id = t.id
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Player not found'}), 404
    
    measurements = conn.execute('''
        SELECT id, weight_kg, measurement_date, notes, created_at
        FROM weight_measurements
        WHERE player_id = ?
        ORDER BY measurement_date DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in measurements])

@app.route('/api/players/<int:player_id>/weight-measurements', methods=['POST'])
@login_required
def add_weight_measurement(player_id):
    """Add a new weight measurement for a player"""
    user_id = session['user_id']
    data = request.json or {}
    
    weight_kg = data.get('weight_kg')
    measurement_date = data.get('measurement_date')
    notes = data.get('notes', '')
    
    if not weight_kg or not measurement_date:
        return jsonify({'error': 'Weight and measurement date are required'}), 400
    
    conn = get_db_connection()
    
    # Verify player belongs to user's team
    player = conn.execute('''
        SELECT p.id FROM players p
        JOIN teams t ON p.team_id = t.id
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        cursor = conn.execute('''
            INSERT INTO weight_measurements (player_id, weight_kg, measurement_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (player_id, weight_kg, measurement_date, notes))
        
        measurement_id = cursor.lastrowid
        
        # Update player's current weight
        conn.execute('''
            UPDATE players SET weight_kg = ? WHERE id = ?
        ''', (weight_kg, player_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'id': measurement_id, 'message': 'Weight measurement added successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Injury Records API
@app.route('/api/players/<int:player_id>/injury-records', methods=['GET'])
@login_required
def get_injury_records(player_id):
    """Get injury records for a player"""
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Verify player belongs to user's team
    player = conn.execute('''
        SELECT p.id FROM players p
        JOIN teams t ON p.team_id = t.id
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Player not found'}), 404
    
    injuries = conn.execute('''
        SELECT id, injury_date, injury_type, description, recovery_date, status, created_at
        FROM injury_records
        WHERE player_id = ?
        ORDER BY injury_date DESC
    ''', (player_id,)).fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in injuries])

@app.route('/api/players/<int:player_id>/injury-records', methods=['POST'])
@login_required
def add_injury_record(player_id):
    """Add a new injury record for a player"""
    user_id = session['user_id']
    data = request.json or {}
    
    injury_date = data.get('injury_date')
    injury_type = data.get('injury_type')
    description = data.get('description', '')
    recovery_date = data.get('recovery_date')
    status = data.get('status', 'active')
    
    if not injury_date or not injury_type:
        return jsonify({'error': 'Injury date and type are required'}), 400
    
    if status not in ['active', 'recovered']:
        return jsonify({'error': 'Status must be active or recovered'}), 400
    
    conn = get_db_connection()
    
    # Verify player belongs to user's team
    player = conn.execute('''
        SELECT p.id FROM players p
        JOIN teams t ON p.team_id = t.id
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        cursor = conn.execute('''
            INSERT INTO injury_records (player_id, injury_date, injury_type, description, recovery_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_id, injury_date, injury_type, description, recovery_date, status))
        
        injury_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': injury_id, 'message': 'Injury record added successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<int:player_id>/injury-records/<int:injury_id>', methods=['PUT'])
@login_required
def update_injury_record(player_id, injury_id):
    """Update an injury record (e.g., mark as recovered)"""
    user_id = session['user_id']
    data = request.json or {}
    
    conn = get_db_connection()
    
    # Verify player belongs to user's team and injury exists
    injury = conn.execute('''
        SELECT ir.id FROM injury_records ir
        JOIN players p ON ir.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        WHERE ir.id = ? AND p.id = ? AND t.user_id = ?
    ''', (injury_id, player_id, user_id)).fetchone()
    
    if not injury:
        conn.close()
        return jsonify({'error': 'Injury record not found'}), 404
    
    # Update fields
    recovery_date = data.get('recovery_date')
    status = data.get('status')
    description = data.get('description')
    
    try:
        # Build dynamic update query
        update_fields = []
        params = []
        
        if recovery_date is not None:
            update_fields.append('recovery_date = ?')
            params.append(recovery_date)
            
        if status is not None:
            if status not in ['active', 'recovered']:
                conn.close()
                return jsonify({'error': 'Status must be active or recovered'}), 400
            update_fields.append('status = ?')
            params.append(status)
            
        if description is not None:
            update_fields.append('description = ?')
            params.append(description)
        
        if update_fields:
            params.append(injury_id)
            query = f'UPDATE injury_records SET {", ".join(update_fields)} WHERE id = ?'
            conn.execute(query, params)
            conn.commit()
        
        conn.close()
        return jsonify({'message': 'Injury record updated successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True)