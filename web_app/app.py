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
    
    # Players tablosu
    conn.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT,
        birth_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    existing_players = conn.execute("SELECT COUNT(*) as count FROM players").fetchone()
    if existing_players['count'] == 0:
        sample_players = [
            ('Aleyna Can', 'Forward'),
            ('Berra Pekgöz', 'Midfielder'),
            ('Ecemnur Öztürk', 'Defender'),
            ('Ela Geçer', 'Forward'),
            ('Elif Ceren Mutlu', 'Midfielder')
        ]
        for name, position in sample_players:
            conn.execute("INSERT INTO players (name, position) VALUES (?, ?)", (name, position))
    
    conn.commit()
    conn.close()

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints

@app.route('/api/players', methods=['GET'])
def get_players():
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in players])

@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.json
    name = data.get('name')
    position = data.get('position', '')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO players (name, position) VALUES (?, ?)', (name, position))
    player_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': player_id, 'name': name, 'position': position})

@app.route('/api/activities', methods=['GET'])
def get_activities():
    player_id = request.args.get('player_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    
    query = '''
    SELECT a.*, p.name as player_name 
    FROM activities a 
    JOIN players p ON a.player_id = p.id 
    WHERE 1=1
    '''
    params = []
    
    if player_id:
        query += ' AND a.player_id = ?'
        params.append(player_id)
    if start_date:
        query += ' AND a.date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND a.date <= ?'
        params.append(end_date)
        
    query += ' ORDER BY a.date DESC'
    
    activities = conn.execute(query, params).fetchall()
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
    
    for player_id in player_ids:
        # Oyuncu bilgisini al
        player = conn.execute('SELECT name FROM players WHERE id = ?', (player_id,)).fetchone()
        if not player:
            continue
            
        # Aktivite verilerini al
        query = '''
        SELECT * FROM activities 
        WHERE player_id = ? AND date >= ? AND date <= ?
        '''
        activities = conn.execute(query, (player_id, start_date, end_date)).fetchall()
        
        if not activities:
            continue
            
        # Antrenman ve maç verilerini ayır
        training_data = [a for a in activities if a['activity_type'] == 'training']
        match_data = [a for a in activities if a['activity_type'] == 'match']
        
        if not training_data or not match_data:
            continue
            
        # Ortalamalar hesapla
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
        
        # Yüzde hesapla
        distance_ratio = (training_avg_distance / match_avg_distance * 100) if match_avg_distance > 0 else 0
        hs16_ratio = (training_avg_hs16 / match_avg_hs16 * 100) if match_avg_hs16 > 0 else 0
        hs20_ratio = (training_avg_hs20 / match_avg_hs20 * 100) if match_avg_hs20 > 0 else 0
        sprint_ratio = (training_avg_sprint / match_avg_sprint * 100) if match_avg_sprint > 0 else 0
        
        analysis_data.append({
            'player_id': player_id,
            'player_name': player['name'],
            'training_count': len(training_data),
            'match_count': len(match_data),
            'distance_ratio': round(distance_ratio, 1),
            'hs16_ratio': round(hs16_ratio, 1),
            'hs20_ratio': round(hs20_ratio, 1),
            'sprint_ratio': round(sprint_ratio, 1),
            'avg_training_distance': round(training_avg_distance, 0),
            'avg_match_distance': round(match_avg_distance, 0)
        })
    
    conn.close()
    return jsonify(analysis_data)

@app.route('/api/dashboard-stats')
def dashboard_stats():
    conn = get_db_connection()
    
    # Temel istatistikler
    players_count = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
    activities_count = conn.execute('SELECT COUNT(*) as count FROM activities').fetchone()['count']
    training_count = conn.execute('SELECT COUNT(*) as count FROM activities WHERE activity_type = "training"').fetchone()['count']
    match_count = conn.execute('SELECT COUNT(*) as count FROM activities WHERE activity_type = "match"').fetchone()['count']
    
    # Son aktiviteler
    recent_activities = conn.execute('''
    SELECT a.date, p.name as player_name, a.activity_type, a.total_distance_m, a.duration_minutes
    FROM activities a 
    JOIN players p ON a.player_id = p.id 
    ORDER BY a.created_at DESC 
    LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'players_count': players_count,
        'activities_count': activities_count,
        'training_count': training_count,
        'match_count': match_count,
        'recent_activities': [dict(row) for row in recent_activities]
    })

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)