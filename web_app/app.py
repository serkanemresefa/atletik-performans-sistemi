from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import os
import json
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(32)

DATABASE = 'atletik_performans.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
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
                    print("Database already exists and has users. Skipping initialization.")
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
            activity_type TEXT NOT NULL CHECK (activity_type IN ('training', 'match')),
            duration_minutes INTEGER, total_distance_m INTEGER,
            high_speed_16kmh_m INTEGER, high_speed_18kmh_m INTEGER,
            high_speed_20kmh_m INTEGER, sprint_24kmh_m INTEGER,
            acc_decc_count INTEGER, high_acc_decc_count INTEGER,
            high_metabolic_power_m INTEGER, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
        ''')
        # Demo kullanıcı oluştur
        demo_password = hash_password('demo123')
        try:
            cursor = conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                                ('demo', 'demo@example.com', demo_password))
            demo_user_id = cursor.lastrowid
            
            cursor = conn.execute("INSERT INTO teams (name, user_id) VALUES (?, ?)", ('U17 Milli Takım', demo_user_id))
            team_id = cursor.lastrowid
            sample_players = [
                ('Aleyna', 'Can', '2005-03-15', 'Türkiye', 'ST', 'RW,CAM', 'Sağ', 10, 165, 58.5, 'Fenerbahçe U19', 'Fenerbahçe U16, Fenerbahçe U19', '2024-01-01', '2026-12-31', 'A+', '', 'Sağlam', '0555-123-4567', 'aleyna.can@example.com', 'Anne: 0555-987-6543', 'Hızlı ve teknikli forvet', team_id),
                ('Berra', 'Pekgöz', '2004-07-22', 'Türkiye', 'CM', 'CDM,CAM', 'Sol', 8, 168, 61.0, 'Galatasaray U19', 'Galatasaray U16, Galatasaray U19', '2024-01-01', '2026-12-31', 'O-', '', 'Sağlam', '0555-234-5678', 'berra.pekgoz@example.com', 'Baba: 0555-876-5432', 'Orta saha organizatörü', team_id),
                ('Ecemnur', 'Öztürk', '2005-11-08', 'Türkiye', 'CB', 'LB,RB', 'Sağ', 4, 172, 64.5, 'Beşiktaş U19', 'Beşiktaş U16, Beşiktaş U19', '2024-01-01', '2026-12-31', 'B+', 'Diz sakatlığı - 2023 (2 ay)', 'Sağlam', '0555-345-6789', 'ecemnur.ozturk@example.com', 'Anne: 0555-765-4321', 'Güçlü ve hava toplarında iyi', team_id)
            ]
            conn.executemany("INSERT INTO players (first_name, last_name, birth_date, nationality, primary_position, secondary_positions, preferred_foot, jersey_number, height_cm, weight_kg, previous_club, club_history, contract_start, contract_end, blood_type, injury_history, current_injury_status, phone, email, emergency_contact, notes, team_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_players)
            conn.commit()
            print("Database initialized and demo user created.")
        except sqlite3.IntegrityError:
            print("Demo user already exists.")

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

@app.route('/api/players/<int:player_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_player(player_id):
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Check if player belongs to user's team
    player = conn.execute('''
        SELECT p.* FROM players p 
        JOIN teams t ON p.team_id = t.id 
        WHERE p.id = ? AND t.user_id = ?
    ''', (player_id, user_id)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'error': 'Oyuncu bulunamadı veya yetkiniz yok'}), 404
    
    if request.method == 'PUT':
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not first_name or not last_name:
            conn.close()
            return jsonify({'error': 'Ad ve soyad gerekli'}), 400
        
        # Update player with all fields
        conn.execute('''
            UPDATE players SET first_name = ?, last_name = ?, birth_date = ?, nationality = ?,
                             primary_position = ?, secondary_positions = ?, preferred_foot = ?,
                             jersey_number = ?, height_cm = ?, weight_kg = ?, previous_club = ?,
                             club_history = ?, contract_start = ?, contract_end = ?, blood_type = ?,
                             injury_history = ?, current_injury_status = ?, phone = ?, email = ?,
                             emergency_contact = ?, notes = ?
            WHERE id = ?
        ''', (
            first_name, last_name, data.get('birth_date'), data.get('nationality'),
            data.get('primary_position'), data.get('secondary_positions'), data.get('preferred_foot'),
            data.get('jersey_number'), data.get('height_cm'), data.get('weight_kg'),
            data.get('previous_club'), data.get('club_history'), data.get('contract_start'),
            data.get('contract_end'), data.get('blood_type'), data.get('injury_history'),
            data.get('current_injury_status'), data.get('phone'), data.get('email'),
            data.get('emergency_contact'), data.get('notes'), player_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Oyuncu bilgileri güncellendi'})
    
    if request.method == 'DELETE':
        # Get activity count before deletion
        activity_count = conn.execute('SELECT COUNT(*) FROM activities WHERE player_id = ?', (player_id,)).fetchone()[0]
        
        # Delete player and their activities
        conn.execute('DELETE FROM activities WHERE player_id = ?', (player_id,))
        conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Oyuncu silindi: {activity_count} aktivite verisi kaldırıldı'
        })

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
    
    conn.execute('''
    INSERT INTO activities (player_id, date, activity_type, duration_minutes, total_distance_m, high_speed_16kmh_m, high_speed_18kmh_m, high_speed_20kmh_m, sprint_24kmh_m, acc_decc_count, high_acc_decc_count, high_metabolic_power_m, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['player_id'], data['date'], data['activity_type'],
        data.get('duration_minutes'), data.get('total_distance_m'),
        data.get('high_speed_16kmh_m'), data.get('high_speed_18kmh_m'),
        data.get('high_speed_20kmh_m'), data.get('sprint_24kmh_m'),
        data.get('acc_decc_count'), data.get('high_acc_decc_count'),
        data.get('high_metabolic_power_m'), data.get('notes')
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

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
        SELECT a.date, p.name as player_name, a.activity_type, a.total_distance_m, a.duration_minutes
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

    Expects JSON body with:
        player_ids: list of player IDs to analyse
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)

    Returns JSON with per‐player averages for training and match activities and
    percentage ratios (training ÷ match × 100). A team summary aggregated over
    selected players is also included.
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
        player_row = conn.execute('SELECT name FROM players WHERE id = ?', (pid,)).fetchone()
        if not player_row:
            # Skip unknown players
            continue
        player_name = player_row['name']

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

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True)