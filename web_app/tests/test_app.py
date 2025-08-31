"""
Test suite for Atletik Performans Sistemi

Basic integration tests for main API endpoints and authentication flow.
"""
import pytest
import sqlite3
import tempfile
import os
from flask import session
from app import app, init_database


@pytest.fixture
def client():
    """Create a test client with temporary database"""
    # Create temporary database
    db_fd, temp_db = tempfile.mkstemp()
    
    # Update DATABASE constant for tests
    import app
    original_db = app.DATABASE
    app.DATABASE = temp_db
    
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app.test_client() as client:
        with app.app.app_context():
            # Initialize test database
            init_database()
        yield client
    
    # Restore original database path
    app.DATABASE = original_db
    os.close(db_fd)
    os.unlink(temp_db)


@pytest.fixture
def auth_client(client):
    """Client with logged in demo user"""
    # Login with demo credentials
    response = client.post('/login', json={
        'username': 'demo',
        'password': 'demo123'
    })
    assert response.status_code == 200
    return client


def test_login_success(client):
    """Test successful login with demo credentials"""
    response = client.post('/login', json={
        'username': 'demo', 
        'password': 'demo123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_login_failure(client):
    """Test failed login with wrong credentials"""
    response = client.post('/login', json={
        'username': 'demo',
        'password': 'wrong'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_teams_requires_auth(client):
    """Test that teams endpoint requires authentication"""
    response = client.get('/api/teams')
    assert response.status_code == 401


def test_teams_list_after_login(auth_client):
    """Test teams list returns data after login"""
    response = auth_client.get('/api/teams')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2  # Demo has 2 teams


def test_players_list(auth_client):
    """Test players list for first team"""
    # Get teams first
    teams_response = auth_client.get('/api/teams')
    teams = teams_response.get_json()
    team_id = teams[0]['id']
    
    # Get players for first team
    response = auth_client.get(f'/api/players?team_id={team_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_team_stats(auth_client):
    """Test team statistics endpoint"""
    # Get teams first
    teams_response = auth_client.get('/api/teams')
    teams = teams_response.get_json()
    team_id = teams[0]['id']
    
    # Get team stats
    response = auth_client.get(f'/api/dashboard-stats?team_id={team_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'players_count' in data
    assert 'activities_count' in data


def test_analysis_with_players(auth_client):
    """Test analysis endpoint with demo data"""
    # Get teams and players first
    teams_response = auth_client.get('/api/teams')
    teams = teams_response.get_json()
    team_id = teams[0]['id']
    
    players_response = auth_client.get(f'/api/players?team_id={team_id}')
    players = players_response.get_json()
    
    if len(players) > 0:
        player_ids = [players[0]['id']]
        
        # Run analysis
        response = auth_client.post('/api/analysis', json={
            'player_ids': player_ids,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'players' in data
        assert 'summary' in data


def test_register_new_user(client):
    """Test user registration"""
    response = client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True


def test_password_change(auth_client):
    """Test password change functionality"""
    response = auth_client.put('/api/user/password', json={
        'current_password': 'demo123',
        'new_password': 'newpassword123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])