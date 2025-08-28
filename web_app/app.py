from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Veritabanı yapılandırması
DATABASE = 'atletik_performans.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    
    # Teams tablosu
    conn.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Players tablosu
    conn.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT,
        birth_date DATE,
        team_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES teams (id)
    )
    ''')
    
    # Activities tablosu
    conn.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        date DATE NOT NULL,
        activity_type TEXT NOT NULL CHECK (activity_type IN ('training', 'match')),
        duration_minutes INTEGER,
        total_distance_m INTEGER,
        high_speed_16kmh_m INTEGER,
        high_speed_18kmh_m INTEGER,
        high_speed_20kmh_m INTEGER,
        sprint_24kmh_m INTEGER,
        acc_decc_count INTEGER,
        high_acc_decc_count INTEGER,
        high_metabolic_power_m INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players (id)
    )
    ''')
    
    # Örnek veri ekle (eğer yoksa)
    existing_teams = conn.execute("SELECT COUNT(*) as count FROM teams").fetchone()['count']
    if existing_teams == 0:
        cursor = conn.execute("INSERT INTO teams (name) VALUES (?)", ('U17 Milli Takım',))
        team_id = cursor.lastrowid
        
        sample_players = [
            ('Aleyna Can', 'Forward'),
            ('Berra Pekgöz', 'Midfielder'),
            ('Ecemnur Öztürk', 'Defender'),
            ('Ela Geçer', 'Forward'),
            ('Elif Ceren Mutlu', 'Midfielder')
        ]
        for name, position in sample_players:
            conn.execute("INSERT INTO players (name, position, team_id) VALUES (?, ?, ?)", (name, position, team_id))

    conn.commit()
    conn.close()

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints

@app.route('/api/teams', methods=['GET'])
def get_teams():
    conn = get_db_connection()
    teams = conn.execute('SELECT * FROM teams ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in teams])

@app.route('/api/teams', methods=['POST'])
def add_team():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Team name is required'}), 400
    
    conn = get_db_connection()
    try:
        cursor = conn.execute('INSERT INTO teams (name) VALUES (?)', (name,))
        team_id = cursor.lastrowid
        conn.commit()
        return jsonify({'id': team_id, 'name': name})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Team name already exists'}), 409
    finally:
        conn.close()

@app.route('/api/players', methods=['GET'])
def get_players():
    team_id = request.args.get('team_id')
    if not team_id:
        return jsonify({'error': 'team_id is required'}), 400
        
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players WHERE team_id = ? ORDER BY name', (team_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in players])

@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.json
    name = data.get('name')
    position = data.get('position', '')
    team_id = data.get('team_id')
    
    if not name or not team_id:
        return jsonify({'error': 'Name and team_id are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO players (name, position, team_id) VALUES (?, ?, ?)', (name, position, team_id))
    player_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': player_id, 'name': name, 'position': position, 'team_id': team_id})

@app.route('/api/activities', methods=['GET'])
def get_activities():
    team_id = request.args.get('team_id')
    # Diğer filtreler (player_id, start_date, end_date) frontend'den yönetilecek
    # Bu endpoint şimdilik genel aktivite çekmek için kullanılabilir veya takım bazlı olabilir
    
    conn = get_db_connection()
    
    query = '''
    SELECT a.*, p.name as player_name 
    FROM activities a 
    JOIN players p ON a.player_id = p.id 
    WHERE p.team_id = ?
    ORDER BY a.date DESC
    '''
    
    if not team_id:
        return jsonify({'error': 'team_id is required'}), 400

    activities = conn.execute(query, (team_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in activities])

@app.route('/api/activities', methods=['POST'])
def add_activity():
    data = request.json
    
    required_fields = ['player_id', 'date', 'activity_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    conn = get_db_connection()
    conn.execute('''
    INSERT INTO activities 
    (player_id, date, activity_type, duration_minutes, total_distance_m, 
     high_speed_16kmh_m, high_speed_18kmh_m, high_speed_20kmh_m, sprint_24kmh_m,
     acc_decc_count, high_acc_decc_count, high_metabolic_power_m, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['player_id'], data['date'], data['activity_type'],
        data.get('duration_minutes', 0), data.get('total_distance_m', 0),
        data.get('high_speed_16kmh_m', 0), data.get('high_speed_18kmh_m', 0),
        data.get('high_speed_20kmh_m', 0), data.get('sprint_24kmh_m', 0),
        data.get('acc_decc_count', 0), data.get('high_acc_decc_count', 0),
        data.get('high_metabolic_power_m', 0), data.get('notes', '')
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/analysis', methods=['POST'])
def get_analysis():
    data = request.json
    player_ids = data.get('player_ids', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not player_ids:
        return jsonify({'error': 'At least one player_id is required'}), 400
    
    conn = get_db_connection()
    analysis_data = []
    
    placeholders = ', '.join('?' for _ in player_ids)
    
    # Oyuncu bilgilerini al
    players_map = {p['id']: p['name'] for p in conn.execute(f'SELECT id, name FROM players WHERE id IN ({placeholders})', player_ids).fetchall()}

    # Aktivite verilerini al
    query = f'''
    SELECT * FROM activities 
    WHERE player_id IN ({placeholders}) AND date >= ? AND date <= ?
    '''
    activities = conn.execute(query, (*player_ids, start_date, end_date)).fetchall()
    
    for player_id in player_ids:
        player_name = players_map.get(player_id)
        if not player_name:
            continue
            
        player_activities = [a for a in activities if a['player_id'] == player_id]
        if not player_activities:
            continue
            
        training_data = [a for a in player_activities if a['activity_type'] == 'training']
        match_data = [a for a in player_activities if a['activity_type'] == 'match']
        
        if not training_data or not match_data:
            continue
            
        def avg_metric(data, metric):
            values = [d[metric] for d in data if d[metric] is not None]
            return sum(values) / len(values) if values else 0
        
        training_avg_distance = avg_metric(training_data, 'total_distance_m')
        match_avg_distance = avg_metric(match_data, 'total_distance_m')
        training_avg_hs16 = avg_metric(training_data, 'high_speed_16kmh_m')
        match_avg_hs16 = avg_metric(match_data, 'high_speed_16kmh_m')
        training_avg_hs20 = avg_metric(training_data, 'high_speed_20kmh_m')
        match_avg_hs20 = avg_metric(match_data, 'high_speed_20kmh_m')
        training_avg_sprint = avg_metric(training_data, 'sprint_24kmh_m')
        match_avg_sprint = avg_metric(match_data, 'sprint_24kmh_m')
        
        distance_ratio = (training_avg_distance / match_avg_distance * 100) if match_avg_distance > 0 else 0
        hs16_ratio = (training_avg_hs16 / match_avg_hs16 * 100) if match_avg_hs16 > 0 else 0
        hs20_ratio = (training_avg_hs20 / match_avg_hs20 * 100) if match_avg_hs20 > 0 else 0
        sprint_ratio = (training_avg_sprint / match_avg_sprint * 100) if match_avg_sprint > 0 else 0
        
        analysis_data.append({
            'player_id': player_id,
            'player_name': player_name,
            'training_count': len(training_data),
            'match_count': len(match_data),
            'distance_ratio': round(distance_ratio, 1),
            'hs16_ratio': round(hs16_ratio, 1),
            'hs20_ratio': round(hs20_ratio, 1),
            'sprint_ratio': round(sprint_ratio, 1),
        })
    
    conn.close()
    return jsonify(analysis_data)

@app.route('/api/dashboard-stats')
def dashboard_stats():
    team_id = request.args.get('team_id')
    if not team_id:
        return jsonify({'error': 'team_id is required'}), 400

    conn = get_db_connection()
    
    # Takım bazlı istatistikler
    players_count = conn.execute('SELECT COUNT(*) as count FROM players WHERE team_id = ?', (team_id,)).fetchone()['count']
    
    query_counts = '''
    SELECT 
        COUNT(a.id) as total_activities,
        SUM(CASE WHEN a.activity_type = 'training' THEN 1 ELSE 0 END) as training_count,
        SUM(CASE WHEN a.activity_type = 'match' THEN 1 ELSE 0 END) as match_count
    FROM activities a
    JOIN players p ON a.player_id = p.id
    WHERE p.team_id = ?
    '''
    counts = conn.execute(query_counts, (team_id,)).fetchone()
    
    # Son aktiviteler
    recent_activities = conn.execute('''
    SELECT a.date, p.name as player_name, a.activity_type, a.total_distance_m, a.duration_minutes
    FROM activities a 
    JOIN players p ON a.player_id = p.id 
    WHERE p.team_id = ?
    ORDER BY a.created_at DESC 
    LIMIT 10
    ''', (team_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'players_count': players_count,
        'activities_count': counts['total_activities'] or 0,
        'training_count': counts['training_count'] or 0,
        'match_count': counts['match_count'] or 0,
        'recent_activities': [dict(row) for row in recent_activities]
    })

if __name__ == '__main__':
    # Veritabanını yeniden başlatmak için (opsiyonel)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
