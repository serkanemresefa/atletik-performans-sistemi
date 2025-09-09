        let currentTeamId = null;
        let teams = [];
        let players = [];
        let analysisChart = null;
        let matchPeriodsChart = null;
        let currentUser = null;

        document.addEventListener('DOMContentLoaded', () => {
            checkAuth();
            loadUserProfile();
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('start-date').value = new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0];
            document.getElementById('end-date').value = today;
        });

        async function checkAuth() {
            try {
                const response = await fetch('/api/teams');
                if (response.status === 401) {
                    window.location.href = '/';
                    return;
                }
                loadTeams();
            } catch (error) {
                console.error('Auth check failed:', error);
                window.location.href = '/';
            }
        }

        async function logout() {
            try {
                await fetch('/logout', { method: 'POST' });
                window.location.href = '/';
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/';
            }
        }

        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.currentTarget.classList.add('active');
            if(tabName === 'team-management') {
                loadTeamsTable();
            }
            
            const tabMessages = {
                'team-management': '',
                'players': !currentTeamId ? 'Profil sekmesinden bir takım seçmelisiniz.' : '',
                'analysis': !currentTeamId ? 'Profil sekmesinden bir takım seçmelisiniz.' : (players.length === 0 ? 'Bu takımda oyuncu yok. Analiz için oyuncu gerekli.' : '')
            };
            
            const message = tabMessages[tabName];
            if (message) {
                const alertIds = {
                    'team-management': 'team-alert',
                    'players': 'player-alert', 
                    'analysis': 'analysis-alert'
                };
                setTimeout(() => showAlert(alertIds[tabName] || 'team-alert', 'error', message), 100);
            }
            
            if (tabName === 'user-profile') {
                loadUserProfile();
            }
        }

        function showAlert(containerId, type, message) {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => { container.innerHTML = ''; }, 5000);
        }

        async function loadTeams() {
            try {
                const response = await fetch('/api/teams');
                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = '/';
                        return;
                    }
                    throw new Error('Teams yüklenemedi');
                }
                teams = await response.json();
                const teamSelect = document.getElementById('player-team-select');
                if (teamSelect) {
                    teamSelect.innerHTML = '';
                    
                    if (teams.length > 0) {
                        teamSelect.innerHTML = '<option value="">Takım seçin...</option>';
                        teams.forEach(team => {
                            const option = new Option(team.name, team.id);
                            teamSelect.add(option);
                        });
                        
                        const savedTeamId = localStorage.getItem('selectedTeamId');
                        if (savedTeamId && teams.find(t => t.id == savedTeamId)) {
                            teamSelect.value = savedTeamId;
                            currentTeamId = savedTeamId;
                        }
                    } else {
                        teamSelect.innerHTML = '<option value="">Önce takım oluşturun</option>';
                    }
                    
                    handlePlayerTeamChange();
                }
            } catch (error) {
                console.error('Error loading teams:', error);
                showAlert('team-alert', 'error', 'Takımlar yüklenirken hata oluştu.');
            }
        }

        function handlePlayerTeamChange() {
            const teamSelect = document.getElementById('player-team-select');
            currentTeamId = teamSelect.value;
            
            if (currentTeamId) {
                localStorage.setItem('selectedTeamId', currentTeamId);
                document.getElementById('add-player-section').style.display = 'block';
                loadPlayers();
            } else {
                document.getElementById('add-player-section').style.display = 'none';
                players = [];
                updatePlayerDropdowns();
                loadPlayersTable();
            }
        }

        async function loadUserProfile() {
            try {
                const response = await fetch('/api/user/profile');
                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = '/';
                        return;
                    }
                    throw new Error('Profil verileri yüklenemedi');
                }
                const data = await response.json();
                
                // Update profile display
                document.getElementById('welcome-username').textContent = data.user.username;
                document.getElementById('profile-username-display').textContent = data.user.username;
                document.getElementById('profile-email-display').textContent = data.user.email;
                document.getElementById('profile-created-date').textContent = new Date(data.user.created_at).toLocaleDateString('tr-TR');
                document.getElementById('user-info').textContent = `Hoşgeldin, ${data.user.username}`;
                
                // Update stats
                document.getElementById('user-teams').textContent = data.stats.team_count;
                document.getElementById('user-players').textContent = data.stats.player_count;
                document.getElementById('user-activities').textContent = data.stats.activity_count;
                
                // Calculate account age
                const createdDate = new Date(data.user.created_at);
                const daysSince = Math.floor((new Date() - createdDate) / (1000 * 60 * 60 * 24));
                document.getElementById('user-since').textContent = daysSince;
                
            } catch (error) {
                console.error('Error loading profile:', error);
                showAlert('profile-alert', 'error', 'Profil verileri yüklenirken hata oluştu.');
            }
        }

        async function loadPlayers() {
            if (!currentTeamId) return;
            try {
                const response = await fetch(`/api/players?team_id=${currentTeamId}`);
                players = await response.json();
                loadPlayersTable();
                updatePlayerDropdowns();
            } catch (error) {
                console.error('Error loading players:', error);
            }
        }

        function loadPlayersTable() {
            const tbody = document.getElementById('players-table');
            tbody.innerHTML = '';
            if (players.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="loading">Bu takıma ait oyuncu yok.</td></tr>';
            } else {
                players.forEach(p => {
                    // Handle both new schema (first_name/last_name) and old schema (name)
                    const fullName = p.name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || 'İsimsiz Oyuncu';
                    const position = p.primary_position || p.position || '-';
                    
                    tbody.innerHTML += `<tr><td>${fullName}</td><td>${position}</td><td>${new Date(p.created_at).toLocaleDateString('tr-TR')}</td><td><button class="btn btn-sm" onclick="openPlayerDetailModal(${p.id})" style="margin-right: 5px;">Detay</button><button class="btn btn-sm btn-danger" onclick="deletePlayer(${p.id}, '${fullName}')">Sil</button></td></tr>`;
                });
            }
        }

        function updatePlayerDropdowns() {
            const analysisPlayers = document.getElementById('analysis-players');
            analysisPlayers.innerHTML = '';
            players.forEach(p => {
                const fullName = p.name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || 'İsimsiz Oyuncu';
                analysisPlayers.add(new Option(fullName, p.id));
            });
        }


        document.getElementById('team-form').addEventListener('submit', async e => {
            e.preventDefault();
            const name = document.getElementById('team-name').value;
            const league = document.getElementById('team-league').value;
            const season = document.getElementById('team-season').value;
            const coach_name = document.getElementById('team-coach').value;
            const description = document.getElementById('team-description').value;
            
            try {
                const response = await fetch('/api/teams', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, league, season, coach_name, description })
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert('team-alert', 'success', 'Takım eklendi.');
                    e.target.reset();
                    await loadTeams(); // Wait for teams to load first
                    loadTeamsTable();
                } else {
                    showAlert('team-alert', 'error', data.error);
                }
            } catch (error) {
                console.error('Error adding team:', error);
            }
        });

        async function loadTeamsTable() {
            const tbody = document.getElementById('teams-table');
            tbody.innerHTML = '';
            if(teams.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="loading">Takım yok.</td></tr>';
                return;
            } 
            
            // Build all rows first, then insert at once
            let rowsHTML = '';
            for (const t of teams) {
                // Get player count for each team
                let playerCount = 0;
                try {
                    const response = await fetch(`/api/players?team_id=${t.id}`);
                    if (response.ok) {
                        const players = await response.json();
                        playerCount = players.length;
                    }
                } catch (error) {
                    console.error('Error loading player count:', error);
                }
                
                const league = t.league || '-';
                const season = t.season || '-';
                const coach = t.coach_name || '-';
                
                rowsHTML += `<tr>
                    <td><span id="team-name-${t.id}">${t.name}</span><input type="text" id="team-edit-${t.id}" value="${t.name}" class="form-control" style="display:none;"></td>
                    <td>${league}</td>
                    <td>${season}</td>
                    <td>${coach}</td>
                    <td>${playerCount} oyuncu</td>
                    <td>
                        <button class="btn btn-sm" onclick="editTeam(${t.id})" id="team-edit-btn-${t.id}" style="margin-right: 5px;">Düzenle</button>
                        <button class="btn btn-sm btn-success" onclick="saveTeam(${t.id})" id="team-save-btn-${t.id}" style="display:none; margin-right: 5px;">Kaydet</button>
                        <button class="btn btn-sm" onclick="cancelEditTeam(${t.id})" id="team-cancel-btn-${t.id}" style="display:none; margin-right: 5px;">İptal</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteTeam(${t.id}, '${t.name}')">Sil</button>
                    </td>
                </tr>`;
            }
            tbody.innerHTML = rowsHTML;
        }


        async function runAnalysis() {
            if (!currentTeamId) {
                showAlert('analysis-alert', 'error', 'Önce bir takım seçmelisiniz.');
                return;
            }
            
            const select = document.getElementById('analysis-players');
            const selectedIds = Array.from(select.selectedOptions).map(o => o.value);
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            
            if (selectedIds.length === 0) {
                showAlert('analysis-alert', 'error', 'Lütfen analiz için en az bir oyuncu seçiniz.');
                return;
            }
            if (!start || !end) {
                showAlert('analysis-alert', 'error', 'Lütfen başlangıç ve bitiş tarihlerini seçiniz.');
                return;
            }
            if (new Date(start) > new Date(end)) {
                showAlert('analysis-alert', 'error', 'Başlangıç tarihi bitiş tarihinden sonra olamaz.');
                return;
            }
            try {
                const response = await fetch('/api/analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_ids: selectedIds, start_date: start, end_date: end })
                });
                const result = await response.json();
                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = '/';
                        return;
                    }
                    showAlert('analysis-alert', 'error', result.error || 'Analiz hatası');
                    return;
                }
                
                if (result.players.length === 0) {
                    showAlert('analysis-alert', 'error', 'Seçilen tarih aralığında veri bulunamadı.');
                    return;
                }
                const tbody = document.getElementById('analysis-table');
                tbody.innerHTML = '';
                const labels = [];
                const distanceData = [];
                const hs16Data = [];
                const hs20Data = [];
                const sprintData = [];
                result.players.forEach(item => {
                    labels.push(item.player_name);
                    const tDist = item.training.total_distance;
                    const mDist = item.match.total_distance;
                    const pctDist = item.ratios.distance_pct !== null ? item.ratios.distance_pct.toFixed(0) : '-';
                    const pct16 = item.ratios.hs16_pct !== null ? item.ratios.hs16_pct.toFixed(0) : '-';
                    const pct20 = item.ratios.hs20_pct !== null ? item.ratios.hs20_pct.toFixed(0) : '-';
                    const pctSprint = item.ratios.sprint_pct !== null ? item.ratios.sprint_pct.toFixed(0) : '-';
                    distanceData.push(item.ratios.distance_pct ?? 0);
                    hs16Data.push(item.ratios.hs16_pct ?? 0);
                    hs20Data.push(item.ratios.hs20_pct ?? 0);
                    sprintData.push(item.ratios.sprint_pct ?? 0);
                    const tDistDisplay = tDist !== null && tDist !== undefined ? Number(tDist).toFixed(0) : '-';
                    const mDistDisplay = mDist !== null && mDist !== undefined ? Number(mDist).toFixed(0) : '-';
                    tbody.innerHTML += `<tr><td>${item.player_name}</td><td>${tDistDisplay}</td><td>${mDistDisplay}</td><td>${pctDist}</td><td>${pct16}</td><td>${pct20}</td><td>${pctSprint}</td></tr>`;
                });
                document.getElementById('analysis-results').style.display = 'block';
                
                const ctx = document.getElementById('analysis-chart').getContext('2d');
                if (analysisChart) analysisChart.destroy();
                analysisChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Mesafe %', data: distanceData, backgroundColor: '#0d6efd' },
                            { label: 'HS16 %', data: hs16Data, backgroundColor: '#6c757d' },
                            { label: 'HS20 %', data: hs20Data, backgroundColor: '#198754' },
                            { label: 'Sprint %', data: sprintData, backgroundColor: '#dc3545' }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: '%' }
                            }
                        }
                    }
                });
            } catch (err) {
                console.error('Analysis error:', err);
                showAlert('analysis-alert', 'error', 'Analiz sırasında hata oluştu.');
            }
        }

        async function runMatchPeriodsAnalysis() {
            if (!currentTeamId) {
                showAlert('analysis-alert', 'error', 'Önce bir takım seçmelisiniz.');
                return;
            }

            const selectedPlayers = Array.from(document.getElementById('analysis-players').selectedOptions).map(o => o.value);
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;

            if (selectedPlayers.length === 0 || !startDate || !endDate) {
                showAlert('analysis-alert', 'error', 'Oyuncu, başlangıç ve bitiş tarihi seçmelisiniz.');
                return;
            }

            try {
                // Hide other results
                document.getElementById('analysis-results').style.display = 'none';
                
                const response = await fetch('/api/match-periods-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        player_ids: selectedPlayers.map(id => parseInt(id)),
                        start_date: startDate,
                        end_date: endDate
                    })
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.error);

                // Show results
                document.getElementById('match-periods-results').style.display = 'block';

                // Prepare chart data
                const labels = data.players.map(p => p.player_name);
                const firstHalfDistance = data.players.map(p => p.first_half.distance);
                const secondHalfDistance = data.players.map(p => p.second_half.distance);
                const firstHalfSpeed = data.players.map(p => p.first_half.max_speed);
                const secondHalfSpeed = data.players.map(p => p.second_half.max_speed);

                // Create chart
                const ctx = document.getElementById('match-periods-chart').getContext('2d');
                if (matchPeriodsChart) matchPeriodsChart.destroy();
                matchPeriodsChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { 
                                label: '1. Devre Mesafe (m)', 
                                data: firstHalfDistance, 
                                backgroundColor: '#28a745',
                                yAxisID: 'y'
                            },
                            { 
                                label: '2. Devre Mesafe (m)', 
                                data: secondHalfDistance, 
                                backgroundColor: '#dc3545',
                                yAxisID: 'y'
                            },
                            { 
                                label: '1. Devre Max Hız (km/h)', 
                                data: firstHalfSpeed, 
                                backgroundColor: '#17a2b8',
                                type: 'line',
                                yAxisID: 'y1'
                            },
                            { 
                                label: '2. Devre Max Hız (km/h)', 
                                data: secondHalfSpeed, 
                                backgroundColor: '#ffc107',
                                type: 'line',
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: { display: true, text: 'Mesafe (m)' }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: { display: true, text: 'Hız (km/h)' },
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });

                // Fill table
                const tableBody = document.getElementById('match-periods-table');
                tableBody.innerHTML = data.players.map(player => `
                    <tr>
                        <td>${player.player_name}</td>
                        <td>${player.first_half.distance}m</td>
                        <td>${player.second_half.distance}m</td>
                        <td>${player.first_half.max_speed} km/h</td>
                        <td>${player.second_half.max_speed} km/h</td>
                        <td>${player.first_half.sprint_count}</td>
                        <td>${player.second_half.sprint_count}</td>
                        <td>${player.total.distance}m / ${player.total.max_speed} km/h</td>
                    </tr>
                `).join('');

            } catch (err) {
                console.error('Match periods analysis error:', err);
                showAlert('analysis-alert', 'error', 'Devre analizi sırasında hata oluştu.');
            }
        }

        function openDataEntryModal(playerId, playerName) {
            document.getElementById('modal-player-id').value = playerId;
            document.getElementById('modal-player-name').textContent = `${playerName} - Veri Girişi`;
            document.getElementById('modal-activity-date').value = new Date().toISOString().split('T')[0];
            document.getElementById('data-entry-modal').style.display = 'block';
            document.getElementById('modal-alert').innerHTML = '';
            document.getElementById('modal-activity-form').reset();
            document.getElementById('modal-activity-date').value = new Date().toISOString().split('T')[0];
        }

        function closeDataEntryModal() {
            document.getElementById('data-entry-modal').style.display = 'none';
        }

        document.getElementById('modal-activity-form').addEventListener('submit', async e => {
            e.preventDefault();
            const playerId = document.getElementById('modal-player-id').value;
            const date = document.getElementById('modal-activity-date').value;
            const activityType = document.getElementById('modal-activity-type').value;
            
            if (!playerId || !date || !activityType) {
                showModalAlert('error', 'Lütfen zorunlu alanları doldurun.');
                return;
            }
            
            const toInt = v => {
                const parsed = parseInt(v, 10);
                return isNaN(parsed) ? null : parsed;
            };
            
            const data = {
                player_id: parseInt(playerId, 10),
                date: date,
                activity_type: activityType,
                duration_minutes: toInt(document.getElementById('modal-duration').value),
                total_distance_m: toInt(document.getElementById('modal-distance').value),
                high_speed_16kmh_m: toInt(document.getElementById('modal-hs16').value),
                high_speed_18kmh_m: toInt(document.getElementById('modal-hs18').value),
                high_speed_20kmh_m: toInt(document.getElementById('modal-hs20').value),
                sprint_24kmh_m: toInt(document.getElementById('modal-sprint').value),
                acc_decc_count: toInt(document.getElementById('modal-acc').value),
                high_acc_decc_count: toInt(document.getElementById('modal-high_acc').value),
                high_metabolic_power_m: toInt(document.getElementById('modal-metabolic').value),
                notes: document.getElementById('modal-notes').value || null
            };
            
            try {
                const response = await fetch('/api/activities', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const resData = await response.json();
                if (response.ok) {
                    showModalAlert('success', 'Aktivite kaydedildi.');
                    setTimeout(() => {
                        closeDataEntryModal();
                        loadUserProfile();
                    }, 1500);
                } else {
                    showModalAlert('error', resData.error || 'Hata oluştu');
                }
            } catch (err) {
                console.error('Error adding activity:', err);
                showModalAlert('error', 'Sunucu hatası');
            }
        });

        function showModalAlert(type, message) {
            const container = document.getElementById('modal-alert');
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => {
                if (type !== 'success') container.innerHTML = '';
            }, 5000);
        }

        // Modal dışına tıklayınca kapat
        window.onclick = function(event) {
            const modal = document.getElementById('data-entry-modal');
            if (event.target === modal) {
                closeDataEntryModal();
            }
        }
        
        // Player Detail Modal Data Entry Functions
        function resetPlayerDetailForm() {
            document.getElementById('player-detail-activity-form').reset();
            document.getElementById('player-detail-activity-date').value = new Date().toISOString().split('T')[0];
            document.getElementById('player-detail-modal-alert').style.display = 'none';
            // Clear custom metrics
            document.getElementById('custom-metrics-container').innerHTML = '';
            // Reset match periods
            document.getElementById('match-periods-section').style.display = 'none';
            document.getElementById('period-inputs').style.display = 'none';
            document.getElementById('enable-periods').checked = false;
        }
        
        function toggleMatchPeriods() {
            const activityType = document.getElementById('player-detail-activity-type').value;
            const matchPeriodsSection = document.getElementById('match-periods-section');
            
            if (activityType === 'match') {
                matchPeriodsSection.style.display = 'block';
            } else {
                matchPeriodsSection.style.display = 'none';
                document.getElementById('period-inputs').style.display = 'none';
                document.getElementById('enable-periods').checked = false;
            }
        }
        
        function togglePeriodInputs() {
            const enablePeriods = document.getElementById('enable-periods').checked;
            const periodInputs = document.getElementById('period-inputs');
            
            if (enablePeriods) {
                periodInputs.style.display = 'block';
            } else {
                periodInputs.style.display = 'none';
            }
        }
        
        let customMetricCounter = 0;
        
        function addCustomMetric() {
            customMetricCounter++;
            const container = document.getElementById('custom-metrics-container');
            const metricDiv = document.createElement('div');
            metricDiv.className = 'form-row custom-metric-row';
            metricDiv.style.marginBottom = '10px';
            metricDiv.innerHTML = `
                <div class="form-group" style="flex: 2;">
                    <input type="text" name="custom-metric-name-${customMetricCounter}" 
                           placeholder="Metrik Adı (örn: Kalp Atış Hızı)" class="form-control">
                </div>
                <div class="form-group">
                    <input type="number" name="custom-metric-value-${customMetricCounter}" 
                           placeholder="Değer" class="form-control" step="0.1">
                </div>
                <div class="form-group">
                    <input type="text" name="custom-metric-unit-${customMetricCounter}" 
                           placeholder="Birim (örn: bpm)" class="form-control">
                </div>
                <div class="form-group" style="flex: 0 0 auto;">
                    <button type="button" class="btn" onclick="removeCustomMetric(this)" 
                            style="background: #e74c3c; color: white; padding: 8px 12px;">×</button>
                </div>
            `;
            container.appendChild(metricDiv);
        }
        
        function removeCustomMetric(button) {
            button.closest('.custom-metric-row').remove();
        }
        
        function showPlayerDetailAlert(type, message) {
            const container = document.getElementById('player-detail-modal-alert');
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            container.style.display = 'block';
            setTimeout(() => {
                if (type !== 'success') container.style.display = 'none';
            }, 5000);
        }
        
        // Player Detail Modal Form Handler
        document.getElementById('player-detail-activity-form').addEventListener('submit', async e => {
            e.preventDefault();
            
            if (!currentPlayerData) {
                showPlayerDetailAlert('error', 'Oyuncu bilgisi bulunamadı.');
                return;
            }
            
            const date = document.getElementById('player-detail-activity-date').value;
            const activityType = document.getElementById('player-detail-activity-type').value;
            
            if (!date || !activityType) {
                showPlayerDetailAlert('error', 'Lütfen tarih ve aktivite türünü seçin.');
                return;
            }
            
            const toInt = v => {
                const parsed = parseInt(v, 10);
                return isNaN(parsed) ? null : parsed;
            };
            
            const data = {
                player_id: currentPlayerData.id,
                date: date,
                activity_time: document.getElementById('player-detail-activity-time').value || null,
                activity_type: activityType,
                duration_minutes: toInt(document.getElementById('player-detail-duration').value),
                total_distance_m: toInt(document.getElementById('player-detail-distance').value),
                high_speed_16kmh_m: toInt(document.getElementById('player-detail-hs16').value),
                high_speed_18kmh_m: toInt(document.getElementById('player-detail-hs18').value),
                high_speed_20kmh_m: toInt(document.getElementById('player-detail-hs20').value),
                high_speed_24kmh_m: toInt(document.getElementById('player-detail-hs24').value),
                sprint_count: toInt(document.getElementById('player-detail-sprint-count').value),
                acc_count: toInt(document.getElementById('player-detail-acc-count').value),
                dec_count: toInt(document.getElementById('player-detail-dec-count').value),
                metabolic_power: parseFloat(document.getElementById('player-detail-metabolic-power').value) || null,
                max_speed_kmh: parseFloat(document.getElementById('player-detail-max-speed').value) || null,
                sprint_count_16plus: toInt(document.getElementById('player-detail-sprint-16').value),
                sprint_count_18plus: toInt(document.getElementById('player-detail-sprint-18').value),
                sprint_count_20plus: toInt(document.getElementById('player-detail-sprint-20').value),
                sprint_count_24plus: toInt(document.getElementById('player-detail-sprint-24').value),
                notes: document.getElementById('player-detail-notes').value || null
            };
            
            // Collect custom metrics
            const customMetrics = [];
            const customMetricRows = document.querySelectorAll('.custom-metric-row');
            customMetricRows.forEach(row => {
                const nameInput = row.querySelector('input[name^="custom-metric-name-"]');
                const valueInput = row.querySelector('input[name^="custom-metric-value-"]');
                const unitInput = row.querySelector('input[name^="custom-metric-unit-"]');
                
                const name = nameInput?.value?.trim();
                const value = parseFloat(valueInput?.value);
                const unit = unitInput?.value?.trim();
                
                if (name && !isNaN(value)) {
                    customMetrics.push({
                        metric_name: name,
                        metric_value: value,
                        unit: unit || null
                    });
                }
            });
            
            if (customMetrics.length > 0) {
                data.custom_metrics = customMetrics;
            }
            
            // Collect match periods if enabled
            if (activityType === 'match' && document.getElementById('enable-periods').checked) {
                const matchPeriods = [];
                
                // 1st Half
                const period1Data = {
                    duration_minutes: document.getElementById('period-1-duration').value,
                    total_distance_m: document.getElementById('period-1-distance').value,
                    high_speed_16kmh_m: document.getElementById('period-1-high-speed-16').value,
                    high_speed_18kmh_m: document.getElementById('period-1-high-speed-18').value,
                    high_speed_20kmh_m: document.getElementById('period-1-high-speed-20').value,
                    sprint_24kmh_m: document.getElementById('period-1-sprint-24').value,
                    acc_decc_count: document.getElementById('period-1-acc-decc').value,
                    high_acc_decc_count: document.getElementById('period-1-high-acc-decc').value,
                    high_metabolic_power_m: document.getElementById('period-1-metabolic-power').value,
                    max_speed_kmh: document.getElementById('period-1-max-speed').value,
                    sprint_count_16plus: document.getElementById('period-1-sprint-16').value,
                    sprint_count_18plus: document.getElementById('period-1-sprint-18').value,
                    sprint_count_20plus: document.getElementById('period-1-sprint-20').value,
                    sprint_count_24plus: document.getElementById('period-1-sprint-24-count').value,
                    notes: document.getElementById('period-1-notes').value
                };
                
                // Check if any period 1 data is entered
                const hasP1Data = Object.values(period1Data).some(val => val && val.trim() !== '');
                if (hasP1Data) {
                    matchPeriods.push({
                        period_type: '1st_half',
                        start_minute: 0,
                        end_minute: 45,
                        duration_minutes: period1Data.duration_minutes ? parseInt(period1Data.duration_minutes) : null,
                        total_distance_m: period1Data.total_distance_m ? parseInt(period1Data.total_distance_m) : null,
                        high_speed_16kmh_m: period1Data.high_speed_16kmh_m ? parseInt(period1Data.high_speed_16kmh_m) : null,
                        high_speed_18kmh_m: period1Data.high_speed_18kmh_m ? parseInt(period1Data.high_speed_18kmh_m) : null,
                        high_speed_20kmh_m: period1Data.high_speed_20kmh_m ? parseInt(period1Data.high_speed_20kmh_m) : null,
                        sprint_24kmh_m: period1Data.sprint_24kmh_m ? parseInt(period1Data.sprint_24kmh_m) : null,
                        acc_decc_count: period1Data.acc_decc_count ? parseInt(period1Data.acc_decc_count) : null,
                        high_acc_decc_count: period1Data.high_acc_decc_count ? parseInt(period1Data.high_acc_decc_count) : null,
                        high_metabolic_power_m: period1Data.high_metabolic_power_m ? parseInt(period1Data.high_metabolic_power_m) : null,
                        max_speed_kmh: period1Data.max_speed_kmh ? parseFloat(period1Data.max_speed_kmh) : null,
                        sprint_count_16plus: period1Data.sprint_count_16plus ? parseInt(period1Data.sprint_count_16plus) : null,
                        sprint_count_18plus: period1Data.sprint_count_18plus ? parseInt(period1Data.sprint_count_18plus) : null,
                        sprint_count_20plus: period1Data.sprint_count_20plus ? parseInt(period1Data.sprint_count_20plus) : null,
                        sprint_count_24plus: period1Data.sprint_count_24plus ? parseInt(period1Data.sprint_count_24plus) : null,
                        notes: period1Data.notes || null
                    });
                }
                
                // 2nd Half
                const period2Data = {
                    duration_minutes: document.getElementById('period-2-duration').value,
                    total_distance_m: document.getElementById('period-2-distance').value,
                    high_speed_16kmh_m: document.getElementById('period-2-high-speed-16').value,
                    high_speed_18kmh_m: document.getElementById('period-2-high-speed-18').value,
                    high_speed_20kmh_m: document.getElementById('period-2-high-speed-20').value,
                    sprint_24kmh_m: document.getElementById('period-2-sprint-24').value,
                    acc_decc_count: document.getElementById('period-2-acc-decc').value,
                    high_acc_decc_count: document.getElementById('period-2-high-acc-decc').value,
                    high_metabolic_power_m: document.getElementById('period-2-metabolic-power').value,
                    max_speed_kmh: document.getElementById('period-2-max-speed').value,
                    sprint_count_16plus: document.getElementById('period-2-sprint-16').value,
                    sprint_count_18plus: document.getElementById('period-2-sprint-18').value,
                    sprint_count_20plus: document.getElementById('period-2-sprint-20').value,
                    sprint_count_24plus: document.getElementById('period-2-sprint-24-count').value,
                    notes: document.getElementById('period-2-notes').value
                };
                
                // Check if any period 2 data is entered
                const hasP2Data = Object.values(period2Data).some(val => val && val.trim() !== '');
                if (hasP2Data) {
                    matchPeriods.push({
                        period_type: '2nd_half',
                        start_minute: 45,
                        end_minute: 90,
                        duration_minutes: period2Data.duration_minutes ? parseInt(period2Data.duration_minutes) : null,
                        total_distance_m: period2Data.total_distance_m ? parseInt(period2Data.total_distance_m) : null,
                        high_speed_16kmh_m: period2Data.high_speed_16kmh_m ? parseInt(period2Data.high_speed_16kmh_m) : null,
                        high_speed_18kmh_m: period2Data.high_speed_18kmh_m ? parseInt(period2Data.high_speed_18kmh_m) : null,
                        high_speed_20kmh_m: period2Data.high_speed_20kmh_m ? parseInt(period2Data.high_speed_20kmh_m) : null,
                        sprint_24kmh_m: period2Data.sprint_24kmh_m ? parseInt(period2Data.sprint_24kmh_m) : null,
                        acc_decc_count: period2Data.acc_decc_count ? parseInt(period2Data.acc_decc_count) : null,
                        high_acc_decc_count: period2Data.high_acc_decc_count ? parseInt(period2Data.high_acc_decc_count) : null,
                        high_metabolic_power_m: period2Data.high_metabolic_power_m ? parseInt(period2Data.high_metabolic_power_m) : null,
                        max_speed_kmh: period2Data.max_speed_kmh ? parseFloat(period2Data.max_speed_kmh) : null,
                        sprint_count_16plus: period2Data.sprint_count_16plus ? parseInt(period2Data.sprint_count_16plus) : null,
                        sprint_count_18plus: period2Data.sprint_count_18plus ? parseInt(period2Data.sprint_count_18plus) : null,
                        sprint_count_20plus: period2Data.sprint_count_20plus ? parseInt(period2Data.sprint_count_20plus) : null,
                        sprint_count_24plus: period2Data.sprint_count_24plus ? parseInt(period2Data.sprint_count_24plus) : null,
                        notes: period2Data.notes || null
                    });
                }
                
                if (matchPeriods.length > 0) {
                    data.match_periods = matchPeriods;
                }
            }
            
            try {
                const response = await fetch('/api/activities', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const resData = await response.json();
                if (response.ok) {
                    showPlayerDetailAlert('success', 'Aktivite başarıyla kaydedildi!');
                    resetPlayerDetailForm();
                    // Refresh performance and stats tabs if they are visible
                    if (document.getElementById('tab-performance').classList.contains('active')) {
                        loadPlayerActivities(currentPlayerData.id);
                    }
                    if (document.getElementById('tab-stats').classList.contains('active')) {
                        loadPlayerStats(currentPlayerData.id);
                    }
                    setTimeout(() => {
                        document.getElementById('player-detail-modal-alert').style.display = 'none';
                    }, 3000);
                } else {
                    showPlayerDetailAlert('error', resData.error || 'Aktivite kaydedilirken hata oluştu');
                }
            } catch (err) {
                console.error('Error adding activity:', err);
                showPlayerDetailAlert('error', 'Sunucu hatası oluştu');
            }
        });

        // Team Edit/Delete Functions
        function editTeam(teamId) {
            document.getElementById(`team-name-${teamId}`).style.display = 'none';
            document.getElementById(`team-edit-${teamId}`).style.display = 'block';
            document.getElementById(`team-edit-btn-${teamId}`).style.display = 'none';
            document.getElementById(`team-save-btn-${teamId}`).style.display = 'inline-block';
            document.getElementById(`team-cancel-btn-${teamId}`).style.display = 'inline-block';
        }

        function cancelEditTeam(teamId) {
            document.getElementById(`team-name-${teamId}`).style.display = 'block';
            document.getElementById(`team-edit-${teamId}`).style.display = 'none';
            document.getElementById(`team-edit-btn-${teamId}`).style.display = 'inline-block';
            document.getElementById(`team-save-btn-${teamId}`).style.display = 'none';
            document.getElementById(`team-cancel-btn-${teamId}`).style.display = 'none';
            // Reset input value
            const originalName = document.getElementById(`team-name-${teamId}`).textContent;
            document.getElementById(`team-edit-${teamId}`).value = originalName;
        }

        async function saveTeam(teamId) {
            const newName = document.getElementById(`team-edit-${teamId}`).value.trim();
            if (!newName) {
                showAlert('team-alert', 'error', 'Takım adı boş olamaz');
                return;
            }
            
            try {
                const response = await fetch(`/api/teams/${teamId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert('team-alert', 'success', data.message);
                    document.getElementById(`team-name-${teamId}`).textContent = newName;
                    cancelEditTeam(teamId);
                    loadTeams(); // Refresh team list
                } else {
                    showAlert('team-alert', 'error', data.error);
                }
            } catch (error) {
                console.error('Team update error:', error);
                showAlert('team-alert', 'error', 'Güncelleme hatası');
            }
        }

        async function deleteTeam(teamId, teamName) {
            try {
                // Get delete stats first
                const statsResponse = await fetch(`/api/teams/${teamId}/stats`);
                const stats = await statsResponse.json();
                
                if (!statsResponse.ok) {
                    showAlert('team-alert', 'error', stats.error);
                    return;
                }
                
                const message = `"${teamName}" takımını silmek istediğinizden emin misiniz?\\n\\n${stats.player_count} oyuncu ve ${stats.activity_count} aktivite verisi kalıcı olarak silinecek.`;
                
                if (confirm(message)) {
                    const response = await fetch(`/api/teams/${teamId}`, { method: 'DELETE' });
                    const data = await response.json();
                    
                    if (response.ok) {
                        showAlert('team-alert', 'success', data.message);
                        loadTeams();
                        loadTeamsTable();
                            // Clear current team if deleted
                        if (currentTeamId == teamId) {
                            currentTeamId = null;
                            localStorage.removeItem('selectedTeamId');
                            handlePlayerTeamChange();
                        }
                    } else {
                        showAlert('team-alert', 'error', data.error);
                    }
                }
            } catch (error) {
                console.error('Team delete error:', error);
                showAlert('team-alert', 'error', 'Silme hatası');
            }
        }

        // Player Edit/Delete Functions


        async function deletePlayer(playerId, playerName) {
            try {
                // Get delete stats first
                const statsResponse = await fetch(`/api/players/${playerId}/stats`);
                const stats = await statsResponse.json();
                
                if (!statsResponse.ok) {
                    showAlert('player-alert', 'error', stats.error);
                    return;
                }
                
                const message = `"${playerName}" oyuncusunu silmek istediğinizden emin misiniz?\\n\\n${stats.activity_count} aktivite verisi kalıcı olarak silinecek.`;
                
                if (confirm(message)) {
                    const response = await fetch(`/api/players/${playerId}`, { method: 'DELETE' });
                    const data = await response.json();
                    
                    if (response.ok) {
                        showAlert('player-alert', 'success', data.message);
                        loadPlayers();
                        loadUserProfile();
                    } else {
                        showAlert('player-alert', 'error', data.error);
                    }
                }
            } catch (error) {
                console.error('Player delete error:', error);
                showAlert('player-alert', 'error', 'Silme hatası');
            }
        }




        function calculateAge(birthDate) {
            const today = new Date();
            const birth = new Date(birthDate);
            let age = today.getFullYear() - birth.getFullYear();
            const monthDiff = today.getMonth() - birth.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
                age--;
            }
            return age;
        }

        function viewPlayerDetails(player) {
            alert(`${player.first_name} ${player.last_name} detay sayfası henüz hazır değil.`);
        }

        // Player Modal Functions
        let editingPlayerId = null;

        function openPlayerModal(playerId = null) {
            editingPlayerId = playerId;
            const modal = document.getElementById('player-modal');
            const form = document.getElementById('player-detail-form');
            
            if (playerId) {
                document.getElementById('player-modal-title').textContent = 'Oyuncu Düzenle';
                // Load player data for editing
                loadPlayerForEdit(playerId);
            } else {
                document.getElementById('player-modal-title').textContent = 'Yeni Oyuncu Ekle';
                form.reset();
            }
            
            modal.style.display = 'block';
            document.getElementById('player-modal-alert').innerHTML = '';
        }

        function closePlayerModal() {
            document.getElementById('player-modal').style.display = 'none';
            editingPlayerId = null;
        }

        async function loadPlayerForEdit(playerId) {
            try {
                const response = await fetch(`/api/players?team_id=${selectedTeamForManagement}`);
                const players = await response.json();
                const player = players.find(p => p.id === playerId);
                
                if (player) {
                    document.getElementById('player-first-name').value = player.first_name || '';
                    document.getElementById('player-last-name').value = player.last_name || '';
                    document.getElementById('player-birth-date').value = player.birth_date || '';
                    document.getElementById('player-nationality').value = player.nationality || '';
                    document.getElementById('player-primary-position').value = player.primary_position || '';
                    document.getElementById('player-secondary-positions').value = player.secondary_positions || '';
                    document.getElementById('player-preferred-foot').value = player.preferred_foot || '';
                    document.getElementById('player-jersey-number').value = player.jersey_number || '';
                    document.getElementById('player-height').value = player.height_cm || '';
                    document.getElementById('player-weight').value = player.weight_kg || '';
                    document.getElementById('player-previous-club').value = player.previous_club || '';
                    document.getElementById('player-blood-type').value = player.blood_type || '';
                    document.getElementById('player-phone').value = player.phone || '';
                    document.getElementById('player-email').value = player.email || '';
                    document.getElementById('player-emergency-contact').value = player.emergency_contact || '';
                    document.getElementById('player-notes').value = player.notes || '';
                }
            } catch (error) {
                console.error('Error loading player for edit:', error);
            }
        }

        // Player Form Handler
        document.getElementById('player-detail-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedTeamForManagement) {
                showAlert('team-alert', 'error', 'Önce bir takım seçmelisiniz.');
                return;
            }
            
            const formData = {
                first_name: document.getElementById('player-first-name').value,
                last_name: document.getElementById('player-last-name').value,
                birth_date: document.getElementById('player-birth-date').value,
                nationality: document.getElementById('player-nationality').value,
                primary_position: document.getElementById('player-primary-position').value,
                secondary_positions: document.getElementById('player-secondary-positions').value,
                preferred_foot: document.getElementById('player-preferred-foot').value,
                jersey_number: document.getElementById('player-jersey-number').value || null,
                height_cm: document.getElementById('player-height').value || null,
                weight_kg: document.getElementById('player-weight').value || null,
                previous_club: document.getElementById('player-previous-club').value,
                blood_type: document.getElementById('player-blood-type').value,
                phone: document.getElementById('player-phone').value,
                email: document.getElementById('player-email').value,
                emergency_contact: document.getElementById('player-emergency-contact').value,
                notes: document.getElementById('player-notes').value,
                team_id: selectedTeamForManagement
            };
            
            try {
                let response;
                if (editingPlayerId) {
                    response = await fetch(`/api/players/${editingPlayerId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });
                } else {
                    response = await fetch('/api/players', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });
                }
                
                const data = await response.json();
                if (response.ok) {
                    showModalAlert('player-modal-alert', 'success', editingPlayerId ? 'Oyuncu güncellendi.' : 'Oyuncu eklendi.');
                    setTimeout(() => {
                        closePlayerModal();
                        loadTeamPlayers(selectedTeamForManagement);
                        loadUserProfile();
                        loadTeamsTable();
                    }, 1500);
                } else {
                    showModalAlert('player-modal-alert', 'error', data.error);
                }
            } catch (error) {
                console.error('Error saving player:', error);
                showModalAlert('player-modal-alert', 'error', 'Kaydetme hatası');
            }
        });

        function showModalAlert(containerId, type, message) {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => {
                if (type !== 'success') container.innerHTML = '';
            }, 5000);
        }

        // Profile Edit Functions
        function toggleProfileEdit() {
            const displays = ['profile-username-display', 'profile-email-display'];
            const inputs = ['profile-username-edit', 'profile-email-edit'];
            const isEditing = document.getElementById('profile-username-edit').style.display !== 'none';
            
            if (isEditing) {
                // Cancel edit
                displays.forEach(id => document.getElementById(id).style.display = 'inline');
                inputs.forEach(id => document.getElementById(id).style.display = 'none');
                document.getElementById('profile-edit-buttons').style.display = 'none';
                document.getElementById('profile-edit-toggle').textContent = 'Düzenle';
            } else {
                // Start edit
                displays.forEach(id => document.getElementById(id).style.display = 'none');
                inputs.forEach(id => document.getElementById(id).style.display = 'block');
                document.getElementById('profile-edit-buttons').style.display = 'block';
                document.getElementById('profile-edit-toggle').textContent = 'İptal';
                
                // Fill edit fields with current values
                document.getElementById('profile-username-edit').value = document.getElementById('profile-username-display').textContent;
                document.getElementById('profile-email-edit').value = document.getElementById('profile-email-display').textContent;
            }
        }

        function cancelProfileEdit() {
            toggleProfileEdit();
        }

        async function saveProfile() {
            const username = document.getElementById('profile-username-edit').value;
            const email = document.getElementById('profile-email-edit').value;
            
            try {
                const response = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email })
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert('profile-alert', 'success', data.message);
                    document.getElementById('profile-username-display').textContent = username;
                    document.getElementById('profile-email-display').textContent = email;
                    document.getElementById('user-info').textContent = `Hoşgeldin, ${username}`;
                    document.getElementById('welcome-username').textContent = username;
                    toggleProfileEdit();
                } else {
                    showAlert('profile-alert', 'error', data.error);
                }
            } catch (error) {
                console.error('Profile update error:', error);
                showAlert('profile-alert', 'error', 'Profil güncelleme hatası');
            }
        }

        function togglePasswordEdit() {
            const form = document.getElementById('password-edit-form');
            const isVisible = form.style.display !== 'none';
            
            if (isVisible) {
                form.style.display = 'none';
                document.getElementById('password-edit-toggle').textContent = 'Şifre Değiştir';
                form.querySelectorAll('input').forEach(input => input.value = '');
            } else {
                form.style.display = 'block';
                document.getElementById('password-edit-toggle').textContent = 'İptal';
            }
        }

        function cancelPasswordEdit() {
            togglePasswordEdit();
        }

        async function savePassword() {
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (newPassword !== confirmPassword) {
                showAlert('profile-alert', 'error', 'Yeni şifreler eşleşmiyor');
                return;
            }
            
            try {
                const response = await fetch('/api/user/password', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert('profile-alert', 'success', data.message);
                    togglePasswordEdit();
                } else {
                    showAlert('profile-alert', 'error', data.error);
                }
            } catch (error) {
                console.error('Password change error:', error);
                showAlert('profile-alert', 'error', 'Şifre değiştirme hatası');
            }
        }

        
        // Player Detail Modal Functions
        let currentPlayerData = null;
        let isEditMode = false;
        
        async function openPlayerDetailModal(playerId) {
            try {
                const response = await fetch(`/api/players/${playerId}`);
                const player = await response.json();
                if (response.ok) {
                    currentPlayerData = player;
                    populatePlayerDetailModal(player);
                    document.getElementById('player-detail-modal').style.display = 'block';
                    showDetailTab('personal');
                } else {
                    showAlert('player-alert', 'error', 'Oyuncu bilgileri yüklenemedi');
                }
            } catch (error) {
                console.error('Error loading player details:', error);
                showAlert('player-alert', 'error', 'Oyuncu bilgileri yüklenirken hata');
            }
        }
        
        function populatePlayerDetailModal(player) {
            // Summary card
            const fullName = `${player.first_name || ''} ${player.last_name || ''}`.trim() || 'İsimsiz Oyuncu';
            document.getElementById('detail-player-name').textContent = fullName;
            document.getElementById('detail-position').textContent = player.primary_position || '-';
            document.getElementById('detail-age').textContent = player.birth_date ? calculateAge(player.birth_date) : '-';
            document.getElementById('detail-jersey').textContent = player.jersey_number || '-';
            document.getElementById('detail-height').textContent = player.height_cm || '-';
            document.getElementById('detail-weight').textContent = player.weight_kg || '-';
            document.getElementById('detail-updated').textContent = new Date(player.created_at).toLocaleDateString('tr-TR');
            document.getElementById('player-detail-title').textContent = `${fullName} - Detayları`;
            
            // Personal info
            document.getElementById('view-first-name').textContent = player.first_name || '-';
            document.getElementById('view-last-name').textContent = player.last_name || '-';
            document.getElementById('view-birth-date').textContent = player.birth_date ? new Date(player.birth_date).toLocaleDateString('tr-TR') : '-';
            document.getElementById('view-nationality').textContent = player.nationality || '-';
            document.getElementById('view-primary-position').textContent = player.primary_position || '-';
            document.getElementById('view-secondary-positions').textContent = player.secondary_positions || '-';
            document.getElementById('view-preferred-foot').textContent = player.preferred_foot || '-';
            document.getElementById('view-jersey-number').textContent = player.jersey_number || '-';
            document.getElementById('view-height-cm').textContent = player.height_cm ? `${player.height_cm} cm` : '-';
            document.getElementById('view-weight-kg').textContent = player.weight_kg ? `${player.weight_kg} kg` : '-';
            document.getElementById('view-blood-type').textContent = player.blood_type || '-';
            document.getElementById('view-current-injury-status').textContent = player.current_injury_status || '-';
            document.getElementById('view-phone').textContent = player.phone || '-';
            document.getElementById('view-email').textContent = player.email || '-';
            document.getElementById('view-emergency-contact').textContent = player.emergency_contact || '-';
            document.getElementById('view-previous-club').textContent = player.previous_club || '-';
            document.getElementById('view-contract-start').textContent = player.contract_start ? new Date(player.contract_start).toLocaleDateString('tr-TR') : '-';
            document.getElementById('view-contract-end').textContent = player.contract_end ? new Date(player.contract_end).toLocaleDateString('tr-TR') : '-';
            document.getElementById('view-club-history').textContent = player.club_history || '-';
            // Injury status will be loaded dynamically when injury modal is opened
            document.getElementById('view-notes').textContent = player.notes || '-';
            
            // Populate edit fields
            document.getElementById('edit-first-name').value = player.first_name || '';
            document.getElementById('edit-last-name').value = player.last_name || '';
            document.getElementById('edit-birth-date').value = player.birth_date || '';
            document.getElementById('edit-nationality').value = player.nationality || '';
            document.getElementById('edit-primary-position').value = player.primary_position || '';
            document.getElementById('edit-secondary-positions').value = player.secondary_positions || '';
            document.getElementById('edit-preferred-foot').value = player.preferred_foot || '';
            document.getElementById('edit-jersey-number').value = player.jersey_number || '';
            document.getElementById('edit-height-cm').value = player.height_cm || '';
            // Weight is managed through separate weight history system
            document.getElementById('edit-blood-type').value = player.blood_type || '';
            document.getElementById('edit-current-injury-status').value = player.current_injury_status || '';
            document.getElementById('edit-phone').value = player.phone || '';
            document.getElementById('edit-email').value = player.email || '';
            document.getElementById('edit-emergency-contact').value = player.emergency_contact || '';
            document.getElementById('edit-previous-club').value = player.previous_club || '';
            document.getElementById('edit-contract-start').value = player.contract_start || '';
            document.getElementById('edit-contract-end').value = player.contract_end || '';
            document.getElementById('edit-club-history').value = player.club_history || '';
            // Injury history is now managed separately
            document.getElementById('edit-notes').value = player.notes || '';
        }
        
        function closePlayerDetailModal() {
            document.getElementById('player-detail-modal').style.display = 'none';
            if (isEditMode) {
                cancelPlayerEdit();
            }
            currentPlayerData = null;
        }
        
        function showDetailTab(tabName) {
            // Hide all tabs and contents
            document.querySelectorAll('.detail-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.detail-tab-content').forEach(content => content.style.display = 'none');
            
            // Show selected tab and content
            document.getElementById(`tab-${tabName}`).classList.add('active');
            document.getElementById(`detail-content-${tabName}`).style.display = 'block';
            
            // Load content based on tab
            if (tabName === 'performance' && currentPlayerData) {
                loadPlayerActivities(currentPlayerData.id);
            } else if (tabName === 'stats' && currentPlayerData) {
                loadPlayerStats(currentPlayerData.id);
            } else if (tabName === 'data-entry' && currentPlayerData) {
                // Initialize data entry form
                resetPlayerDetailForm();
            }
        }
        
        function togglePlayerEdit() {
            if (isEditMode) {
                cancelPlayerEdit();
            } else {
                enterEditMode();
            }
        }
        
        function enterEditMode() {
            isEditMode = true;
            document.querySelectorAll('.view-mode').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'block');
            document.getElementById('edit-toggle-btn').textContent = 'İptal';
        }
        
        function cancelPlayerEdit() {
            isEditMode = false;
            document.querySelectorAll('.view-mode').forEach(el => el.style.display = 'block');
            document.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'none');
            document.getElementById('edit-toggle-btn').textContent = 'Düzenle';
            
            // Restore original values
            if (currentPlayerData) {
                populatePlayerDetailModal(currentPlayerData);
            }
        }
        
        async function savePlayerDetails() {
            try {
                const updatedPlayer = {
                    first_name: document.getElementById('edit-first-name').value,
                    last_name: document.getElementById('edit-last-name').value,
                    birth_date: document.getElementById('edit-birth-date').value,
                    nationality: document.getElementById('edit-nationality').value,
                    primary_position: document.getElementById('edit-primary-position').value,
                    secondary_positions: document.getElementById('edit-secondary-positions').value,
                    preferred_foot: document.getElementById('edit-preferred-foot').value,
                    jersey_number: parseInt(document.getElementById('edit-jersey-number').value) || null,
                    height_cm: parseInt(document.getElementById('edit-height-cm').value) || null,
                    // weight_kg: managed through weight history system,
                    blood_type: document.getElementById('edit-blood-type').value,
                    current_injury_status: document.getElementById('edit-current-injury-status').value,
                    phone: document.getElementById('edit-phone').value,
                    email: document.getElementById('edit-email').value,
                    emergency_contact: document.getElementById('edit-emergency-contact').value,
                    previous_club: document.getElementById('edit-previous-club').value,
                    contract_start: document.getElementById('edit-contract-start').value,
                    contract_end: document.getElementById('edit-contract-end').value,
                    club_history: document.getElementById('edit-club-history').value,
                    // injury_history managed separately,
                    notes: document.getElementById('edit-notes').value
                };
                
                const response = await fetch(`/api/players/${currentPlayerData.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedPlayer)
                });
                
                const result = await response.json();
                if (response.ok) {
                    currentPlayerData = { ...currentPlayerData, ...updatedPlayer };
                    populatePlayerDetailModal(currentPlayerData);
                    cancelPlayerEdit();
                    loadPlayers(); // Refresh player list
                    showAlert('player-alert', 'success', 'Oyuncu bilgileri güncellendi');
                } else {
                    showAlert('player-alert', 'error', result.error || 'Güncelleme hatası');
                }
            } catch (error) {
                console.error('Error saving player details:', error);
                showAlert('player-alert', 'error', 'Kaydetme hatası');
            }
        }
        
        async function loadPlayerActivities(playerId) {
            try {
                const response = await fetch(`/api/activities?player_id=${playerId}`);
                const activities = await response.json();
                const container = document.getElementById('player-activities-list');
                
                if (response.ok && activities.length > 0) {
                    container.innerHTML = activities.map(activity => `
                        <div style="border: 1px solid #e9ecef; padding: 20px; margin-bottom: 15px; border-radius: 8px; background: ${activity.activity_type === 'match' ? 'linear-gradient(135deg, #ff6b6b, #ffa726)' : 'linear-gradient(135deg, #4ecdc4, #44a08d)'}; color: white; position: relative;">
                            <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 5px; opacity: 0.9;">
                                <button onclick="editActivity(${activity.id})" style="background: #007bff; border: none; color: white; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold;" title="Düzenle">Düzenle</button>
                                <button onclick="deleteActivity(${activity.id})" style="background: #dc3545; border: none; color: white; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold;" title="Sil">Sil</button>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-right: 110px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                                        ${activity.activity_type === 'training' ? 'ANTRENMAN' : 'MAÇ'}
                                    </span>
                                    <span style="font-weight: bold; font-size: 16px;">
                                        ${new Date(activity.date).toLocaleDateString('tr-TR')}
                                        ${activity.activity_time ? ` - ${activity.activity_time}` : ''}
                                    </span>
                                </div>
                                ${activity.duration_minutes ? `<span style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; font-size: 12px;">${activity.duration_minutes} dk</span>` : ''}
                            </div>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 10px;">
                                ${activity.total_distance_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Toplam Mesafe</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.total_distance_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.high_speed_16kmh_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Hız 16+ km/h</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.high_speed_16kmh_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.high_speed_18kmh_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Hız 18+ km/h</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.high_speed_18kmh_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.high_speed_20kmh_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Hız 20+ km/h</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.high_speed_20kmh_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.sprint_24kmh_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Sprint 24+ km/h</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.sprint_24kmh_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.acc_decc_count ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">AccDecc Sayısı</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.acc_decc_count}</div>
                                    </div>
                                ` : ''}
                                ${activity.high_metabolic_power_m ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Metabolik Güç</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.high_metabolic_power_m} m</div>
                                    </div>
                                ` : ''}
                                ${activity.max_speed_kmh ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Max Sürat</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.max_speed_kmh} km/h</div>
                                    </div>
                                ` : ''}
                                ${activity.sprint_count_16plus ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Sprint 16+ Sayısı</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.sprint_count_16plus}</div>
                                    </div>
                                ` : ''}
                                ${activity.sprint_count_18plus ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Sprint 18+ Sayısı</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.sprint_count_18plus}</div>
                                    </div>
                                ` : ''}
                                ${activity.sprint_count_20plus ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Sprint 20+ Sayısı</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.sprint_count_20plus}</div>
                                    </div>
                                ` : ''}
                                ${activity.sprint_count_24plus ? `
                                    <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                        <div style="font-size: 11px; opacity: 0.9;">Sprint 24+ Sayısı</div>
                                        <div style="font-weight: bold; font-size: 14px;">${activity.sprint_count_24plus}</div>
                                    </div>
                                ` : ''}
                            </div>
                            
                            ${activity.custom_metrics && activity.custom_metrics.length > 0 ? `
                                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                                    <div style="font-size: 12px; margin-bottom: 10px; opacity: 0.9; font-weight: bold;">Özel Metrikler:</div>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">
                                        ${activity.custom_metrics.map(metric => `
                                            <div style="background: rgba(255,255,255,0.15); padding: 8px; border-radius: 6px; text-align: center;">
                                                <div style="font-size: 10px; opacity: 0.9;">${metric.metric_name}</div>
                                                <div style="font-weight: bold; font-size: 13px;">${metric.metric_value}${metric.unit ? ' ' + metric.unit : ''}</div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            </div>
                            
                            ${activity.notes ? `<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; font-style: italic; margin-top: 10px; font-size: 13px;">"${activity.notes}"</div>` : ''}
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="loading">Bu oyuncu için henüz aktivite verisi yok.</div>';
                }
            } catch (error) {
                document.getElementById('player-activities-list').innerHTML = '<div class="loading">Aktiviteler yüklenemedi.</div>';
            }
        }
        
        async function loadPlayerStats(playerId) {
            try {
                const response = await fetch(`/api/players/${playerId}/statistics`);
                const stats = await response.json();
                const container = document.getElementById('player-stats-summary');
                
                if (response.ok && stats) {
                    container.innerHTML = `
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px;">
                                <h5 style="margin: 0 0 15px 0; font-size: 16px;">Genel İstatistikler</h5>
                                <div style="font-size: 14px; line-height: 1.6;">
                                    <div><strong>Toplam Aktivite:</strong> ${stats.general_stats.total_activities}</div>
                                    <div><strong>Antrenman:</strong> ${stats.general_stats.training_count}</div>
                                    <div><strong>Maç:</strong> ${stats.general_stats.match_count}</div>
                                    <div><strong>Son Aktivite:</strong> ${stats.general_stats.last_activity_date ? new Date(stats.general_stats.last_activity_date).toLocaleDateString('tr-TR') : 'Yok'}</div>
                                </div>
                            </div>
                            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px;">
                                <h5 style="margin: 0 0 15px 0; font-size: 16px;">Ortalama Performans</h5>
                                <div style="font-size: 14px; line-height: 1.6;">
                                    <div><strong>Süre:</strong> ${stats.averages.duration_minutes} dk</div>
                                    <div><strong>Mesafe:</strong> ${stats.averages.total_distance_m} m</div>
                                    <div><strong>Yüksek Hız 20+:</strong> ${stats.averages.high_speed_20kmh_m} m</div>
                                    <div><strong>Sprint 24+:</strong> ${stats.averages.sprint_24kmh_m} m</div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px;">
                            <h5 style="margin: 0 0 20px 0; color: #333;">Antrenman vs Maç Karşılaştırması</h5>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; text-align: center;">
                                <div>
                                    <div style="font-weight: bold; color: #666; margin-bottom: 8px;">Süre (dk)</div>
                                    <div style="background: #4CAF50; color: white; padding: 8px; border-radius: 4px; margin-bottom: 5px;">
                                        <div style="font-size: 12px;">Antrenman</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.training.duration}</div>
                                    </div>
                                    <div style="background: #FF5722; color: white; padding: 8px; border-radius: 4px;">
                                        <div style="font-size: 12px;">Maç</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.match.duration}</div>
                                    </div>
                                </div>
                                <div>
                                    <div style="font-weight: bold; color: #666; margin-bottom: 8px;">Mesafe (m)</div>
                                    <div style="background: #4CAF50; color: white; padding: 8px; border-radius: 4px; margin-bottom: 5px;">
                                        <div style="font-size: 12px;">Antrenman</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.training.distance}</div>
                                    </div>
                                    <div style="background: #FF5722; color: white; padding: 8px; border-radius: 4px;">
                                        <div style="font-size: 12px;">Maç</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.match.distance}</div>
                                    </div>
                                </div>
                                <div>
                                    <div style="font-weight: bold; color: #666; margin-bottom: 8px;">Yüksek Hız (m)</div>
                                    <div style="background: #4CAF50; color: white; padding: 8px; border-radius: 4px; margin-bottom: 5px;">
                                        <div style="font-size: 12px;">Antrenman</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.training.high_speed}</div>
                                    </div>
                                    <div style="background: #FF5722; color: white; padding: 8px; border-radius: 4px;">
                                        <div style="font-size: 12px;">Maç</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.match.high_speed}</div>
                                    </div>
                                </div>
                                <div>
                                    <div style="font-weight: bold; color: #666; margin-bottom: 8px;">Sprint (m)</div>
                                    <div style="background: #4CAF50; color: white; padding: 8px; border-radius: 4px; margin-bottom: 5px;">
                                        <div style="font-size: 12px;">Antrenman</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.training.sprint}</div>
                                    </div>
                                    <div style="background: #FF5722; color: white; padding: 8px; border-radius: 4px;">
                                        <div style="font-size: 12px;">Maç</div>
                                        <div style="font-weight: bold;">${stats.training_vs_match.match.sprint}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 15px;">
                            <h6 style="margin: 0 0 10px 0; color: #333;">Detaylı Ortalamalar</h6>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 13px;">
                                <div><strong>16 km/h+:</strong> ${stats.averages.high_speed_16kmh_m} m</div>
                                <div><strong>18 km/h+:</strong> ${stats.averages.high_speed_18kmh_m} m</div>
                                <div><strong>AccDecc:</strong> ${stats.averages.acc_decc_count}</div>
                                <div><strong>Metabolik Güç:</strong> ${stats.averages.metabolic_power_m} m</div>
                            </div>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="loading">İstatistik verileri yüklenemedi.</div>';
                }
            } catch (error) {
                document.getElementById('player-stats-summary').innerHTML = '<div class="loading">İstatistikler yüklenemedi.</div>';
            }
        }
        
        // Weight History Modal Functions
        function showWeightHistoryModal() {
            if (!currentPlayerData) return;
            
            const fullName = `${currentPlayerData.first_name || ''} ${currentPlayerData.last_name || ''}`.trim();
            document.getElementById('weight-history-title').textContent = `${fullName} - Kilo Geçmişi`;
            document.getElementById('weight-date').value = new Date().toISOString().split('T')[0];
            document.getElementById('weight-history-modal').style.display = 'block';
            loadWeightHistory();
        }
        
        function closeWeightHistoryModal() {
            document.getElementById('weight-history-modal').style.display = 'none';
        }
        
        async function loadWeightHistory() {
            if (!currentPlayerData) return;
            
            try {
                const response = await fetch(`/api/players/${currentPlayerData.id}/weight-measurements`);
                const weights = await response.json();
                
                const container = document.getElementById('weight-history-table');
                
                if (weights.length > 0) {
                    let html = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Tarih</th>
                                    <th>Kilo (kg)</th>
                                    <th>Notlar</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    weights.forEach(weight => {
                        html += `
                            <tr>
                                <td>${new Date(weight.measurement_date).toLocaleDateString('tr-TR')}</td>
                                <td style="font-weight: bold; color: #007bff;">${weight.weight_kg} kg</td>
                                <td>${weight.notes || '-'}</td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">Henüz kilo ölçümü kaydedilmemiş.</div>';
                }
            } catch (error) {
                console.error('Error loading weight history:', error);
                document.getElementById('weight-history-table').innerHTML = '<div style="color: red;">Kilo geçmişi yüklenemedi.</div>';
            }
        }
        
        // Weight Form Handler
        document.getElementById('weight-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentPlayerData) return;
            
            const data = {
                weight_kg: parseFloat(document.getElementById('weight-value').value),
                measurement_date: document.getElementById('weight-date').value,
                notes: document.getElementById('weight-notes').value || ''
            };
            
            try {
                const response = await fetch(`/api/players/${currentPlayerData.id}/weight-measurements`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showWeightAlert('success', 'Kilo ölçümü başarıyla kaydedildi!');
                    document.getElementById('weight-form').reset();
                    document.getElementById('weight-date').value = new Date().toISOString().split('T')[0];
                    loadWeightHistory();
                    
                    // Update current weight display
                    document.getElementById('detail-weight').textContent = data.weight_kg;
                    document.getElementById('view-weight-kg').textContent = data.weight_kg;
                } else {
                    showWeightAlert('error', result.error || 'Kilo ölçümü kaydedilemedi');
                }
            } catch (error) {
                console.error('Error adding weight measurement:', error);
                showWeightAlert('error', 'Sunucu hatası oluştu');
            }
        });
        
        function showWeightAlert(type, message) {
            const container = document.getElementById('weight-modal-alert');
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            container.style.display = 'block';
            setTimeout(() => {
                if (type !== 'success') container.style.display = 'none';
            }, 5000);
        }
        
        // Injury History Modal Functions
        function showInjuryHistoryModal() {
            if (!currentPlayerData) return;
            
            const fullName = `${currentPlayerData.first_name || ''} ${currentPlayerData.last_name || ''}`.trim();
            document.getElementById('injury-history-title').textContent = `${fullName} - Sakatlık Geçmişi`;
            document.getElementById('injury-date').value = new Date().toISOString().split('T')[0];
            document.getElementById('injury-history-modal').style.display = 'block';
            loadInjuryHistory();
        }
        
        function closeInjuryHistoryModal() {
            document.getElementById('injury-history-modal').style.display = 'none';
        }
        
        async function loadInjuryHistory() {
            if (!currentPlayerData) return;
            
            try {
                const response = await fetch(`/api/players/${currentPlayerData.id}/injury-records`);
                const injuries = await response.json();
                
                const container = document.getElementById('injury-history-table');
                
                if (injuries.length > 0) {
                    let activeInjuries = injuries.filter(i => i.status === 'active');
                    
                    // Update injury status display
                    if (activeInjuries.length > 0) {
                        document.getElementById('view-injury-status').textContent = 
                            `${activeInjuries.length} aktif sakatlık: ${activeInjuries.map(i => i.injury_type).join(', ')}`;
                    } else {
                        document.getElementById('view-injury-status').textContent = 'Aktif sakatlık bulunmuyor';
                    }
                    
                    let html = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Tarih</th>
                                    <th>Tür</th>
                                    <th>Durum</th>
                                    <th>İyileşme</th>
                                    <th>Açıklama</th>
                                    <th>İşlem</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    injuries.forEach(injury => {
                        const statusClass = injury.status === 'active' ? 'color: red; font-weight: bold;' : 'color: green;';
                        const recoveryDate = injury.recovery_date ? new Date(injury.recovery_date).toLocaleDateString('tr-TR') : '-';
                        
                        html += `
                            <tr>
                                <td>${new Date(injury.injury_date).toLocaleDateString('tr-TR')}</td>
                                <td style="font-weight: bold;">${injury.injury_type}</td>
                                <td style="${statusClass}">${injury.status === 'active' ? 'Aktif' : 'İyileşmiş'}</td>
                                <td>${recoveryDate}</td>
                                <td>${injury.description || '-'}</td>
                                <td>
                                    ${injury.status === 'active' ? 
                                        `<button class="btn btn-sm" onclick="markInjuryRecovered(${injury.id})" style="background: #28a745; color: white;">İyileşti</button>` 
                                        : '-'
                                    }
                                </td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">Henüz sakatlık kaydı bulunmuyor.</div>';
                    document.getElementById('view-injury-status').textContent = 'Aktif sakatlık bulunmuyor';
                }
            } catch (error) {
                console.error('Error loading injury history:', error);
                document.getElementById('injury-history-table').innerHTML = '<div style="color: red;">Sakatlık geçmişi yüklenemedi.</div>';
            }
        }
        
        // Injury Form Handler
        document.getElementById('injury-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentPlayerData) return;
            
            const data = {
                injury_date: document.getElementById('injury-date').value,
                injury_type: document.getElementById('injury-type').value,
                description: document.getElementById('injury-description').value || '',
                recovery_date: document.getElementById('injury-recovery-date').value || null,
                status: document.getElementById('injury-status').value
            };
            
            try {
                const response = await fetch(`/api/players/${currentPlayerData.id}/injury-records`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showInjuryAlert('success', 'Sakatlık kaydı başarıyla eklendi!');
                    document.getElementById('injury-form').reset();
                    document.getElementById('injury-date').value = new Date().toISOString().split('T')[0];
                    document.getElementById('injury-status').value = 'active';
                    loadInjuryHistory();
                } else {
                    showInjuryAlert('error', result.error || 'Sakatlık kaydedilemedi');
                }
            } catch (error) {
                console.error('Error adding injury record:', error);
                showInjuryAlert('error', 'Sunucu hatası oluştu');
            }
        });
        
        async function markInjuryRecovered(injuryId) {
            if (!currentPlayerData) return;
            
            const recoveryDate = prompt('İyileşme tarihi (YYYY-MM-DD formatında):');
            if (!recoveryDate) return;
            
            try {
                const response = await fetch(`/api/players/${currentPlayerData.id}/injury-records/${injuryId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        status: 'recovered',
                        recovery_date: recoveryDate
                    })
                });
                
                if (response.ok) {
                    loadInjuryHistory();
                } else {
                    alert('Sakatlık durumu güncellenemedi');
                }
            } catch (error) {
                console.error('Error updating injury:', error);
                alert('Sunucu hatası oluştu');
            }
        }
        
        function showInjuryAlert(type, message) {
            const container = document.getElementById('injury-modal-alert');
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            container.style.display = 'block';
            setTimeout(() => {
                if (type !== 'success') container.style.display = 'none';
            }, 5000);
        }
        
        // Activity Edit/Delete Functions
        let currentEditingActivity = null;
        
        async function editActivity(activityId) {
            try {
                // Get current activities from the loaded data
                const response = await fetch(`/api/activities?player_id=${currentPlayerData.id}`);
                const activities = await response.json();
                
                const activity = activities.find(a => a.id === activityId);
                if (!activity) {
                    alert('Aktivite bulunamadı');
                    return;
                }
                
                currentEditingActivity = activity;
                
                // Populate edit form
                document.getElementById('edit-activity-id').value = activity.id;
                document.getElementById('edit-activity-date').value = activity.date;
                document.getElementById('edit-activity-time').value = activity.activity_time || '';
                document.getElementById('edit-activity-type').value = activity.activity_type;
                document.getElementById('edit-duration').value = activity.duration_minutes || '';
                document.getElementById('edit-distance').value = activity.total_distance_m || '';
                document.getElementById('edit-hs16').value = activity.high_speed_16kmh_m || '';
                document.getElementById('edit-hs18').value = activity.high_speed_18kmh_m || '';
                document.getElementById('edit-hs20').value = activity.high_speed_20kmh_m || '';
                document.getElementById('edit-hs24').value = activity.sprint_24kmh_m || '';
                document.getElementById('edit-sprint-count').value = activity.sprint_count || '';
                document.getElementById('edit-acc-count').value = activity.acc_count || '';
                document.getElementById('edit-dec-count').value = activity.dec_count || '';
                document.getElementById('edit-metabolic-power').value = activity.metabolic_power || '';
                document.getElementById('edit-activity-notes').value = activity.notes || '';
                
                // Show modal
                document.getElementById('activity-edit-title').textContent = 
                    `${activity.activity_type === 'training' ? 'Antrenman' : 'Maç'} Düzenle - ${new Date(activity.date).toLocaleDateString('tr-TR')}`;
                document.getElementById('activity-edit-modal').style.display = 'block';
                
            } catch (error) {
                console.error('Error loading activity for edit:', error);
                alert('Aktivite yüklenirken hata oluştu');
            }
        }
        
        async function deleteActivity(activityId) {
            if (!confirm('Bu aktiviteyi silmek istediğinizden emin misiniz?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/activities/${activityId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    // Refresh activities list
                    loadPlayerActivities(currentPlayerData.id);
                    // Refresh stats if visible
                    if (document.getElementById('tab-stats').classList.contains('active')) {
                        loadPlayerStats(currentPlayerData.id);
                    }
                } else {
                    const error = await response.json();
                    alert(error.error || 'Aktivite silinirken hata oluştu');
                }
            } catch (error) {
                console.error('Error deleting activity:', error);
                alert('Sunucu hatası oluştu');
            }
        }
        
        function closeActivityEditModal() {
            document.getElementById('activity-edit-modal').style.display = 'none';
            document.getElementById('activity-edit-modal-alert').style.display = 'none';
            currentEditingActivity = null;
        }
        
        function showActivityEditAlert(type, message) {
            const container = document.getElementById('activity-edit-modal-alert');
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            container.style.display = 'block';
            setTimeout(() => {
                if (type !== 'success') container.style.display = 'none';
            }, 5000);
        }
        
        // Activity Edit Form Handler
        document.getElementById('activity-edit-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentEditingActivity) {
                showActivityEditAlert('error', 'Düzenlenecek aktivite bulunamadı');
                return;
            }
            
            const toInt = v => {
                const parsed = parseInt(v, 10);
                return isNaN(parsed) ? null : parsed;
            };
            
            const data = {
                date: document.getElementById('edit-activity-date').value,
                activity_time: document.getElementById('edit-activity-time').value || null,
                activity_type: document.getElementById('edit-activity-type').value,
                duration_minutes: toInt(document.getElementById('edit-duration').value),
                total_distance_m: toInt(document.getElementById('edit-distance').value),
                high_speed_16kmh_m: toInt(document.getElementById('edit-hs16').value),
                high_speed_18kmh_m: toInt(document.getElementById('edit-hs18').value),
                high_speed_20kmh_m: toInt(document.getElementById('edit-hs20').value),
                sprint_24kmh_m: toInt(document.getElementById('edit-hs24').value),
                sprint_count: toInt(document.getElementById('edit-sprint-count').value),
                acc_count: toInt(document.getElementById('edit-acc-count').value),
                dec_count: toInt(document.getElementById('edit-dec-count').value),
                metabolic_power: parseFloat(document.getElementById('edit-metabolic-power').value) || null,
                notes: document.getElementById('edit-activity-notes').value || null
            };
            
            try {
                const response = await fetch(`/api/activities/${currentEditingActivity.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showActivityEditAlert('success', 'Aktivite başarıyla güncellendi!');
                    setTimeout(() => {
                        closeActivityEditModal();
                        // Refresh activities and stats
                        loadPlayerActivities(currentPlayerData.id);
                        if (document.getElementById('tab-stats').classList.contains('active')) {
                            loadPlayerStats(currentPlayerData.id);
                        }
                    }, 1500);
                } else {
                    showActivityEditAlert('error', result.error || 'Aktivite güncellenirken hata oluştu');
                }
            } catch (error) {
                console.error('Error updating activity:', error);
                showActivityEditAlert('error', 'Sunucu hatası oluştu');
            }
        });
        
