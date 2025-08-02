// Parlay Optimizer Pro - Frontend JavaScript
const API_BASE_URL = 'http://localhost:8002';

// Global state
let currentParlay = null;
let stats = {
    totalParlays: 0,
    avgConfidence: 0,
    bestPayout: 0
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Parlay Optimizer Pro - Frontend Loaded');
    checkHealth();
    updateStats();
});

// Health check
async function checkHealth() {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok && data.status === 'healthy') {
            statusIndicator.innerHTML = '<div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>';
            statusText.textContent = 'Connected';
            showToast('System Status', 'API connection healthy', 'success');
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        statusIndicator.innerHTML = '<div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>';
        statusText.textContent = 'Disconnected';
        showToast('Connection Error', 'Unable to connect to API', 'error');
    }
}

// Generate tier-based parlay
async function generateTierParlay() {
    const amount = document.getElementById('tier-amount').value;
    const sport = document.getElementById('tier-sport').value;
    
    if (!amount || amount < 1) {
        showToast('Invalid Input', 'Please enter a valid bet amount', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate/tier`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bet_amount: parseFloat(amount),
                sport: sport
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayParlay(data, 'tier');
        updateStatsAfterParlay(data);
        showToast('Success', `Generated ${data.legs?.length || 0}-leg parlay!`, 'success');
        
    } catch (error) {
        console.error('Error generating tier parlay:', error);
        showToast('Generation Error', 'Failed to generate tier parlay', 'error');
    } finally {
        showLoading(false);
    }
}

// Generate custom parlay
async function generateCustomParlay() {
    const targetOdds = document.getElementById('custom-odds').value;
    const sport = document.getElementById('custom-sport').value;
    const riskTolerance = document.getElementById('custom-risk').value;
    
    if (!targetOdds) {
        showToast('Invalid Input', 'Please enter target odds', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate/custom`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                target_odds: targetOdds,
                sport: sport,
                risk_tolerance: riskTolerance
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayParlay(data, 'custom');
        updateStatsAfterParlay(data);
        showToast('Success', `Generated custom parlay matching ${targetOdds}!`, 'success');
        
    } catch (error) {
        console.error('Error generating custom parlay:', error);
        showToast('Generation Error', 'Failed to generate custom parlay', 'error');
    } finally {
        showLoading(false);
    }
}

// Quick parlay generation
async function generateQuickParlay(sport, amount) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate/tier`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bet_amount: amount,
                sport: sport
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayParlay(data, 'quick');
        updateStatsAfterParlay(data);
        showToast('Quick Parlay', `Generated ${sport} parlay for $${amount}!`, 'success');
        
    } catch (error) {
        console.error('Error generating quick parlay:', error);
        showToast('Generation Error', 'Failed to generate quick parlay', 'error');
    } finally {
        showLoading(false);
    }
}

// Display parlay results
function displayParlay(data, type) {
    currentParlay = data;
    const resultsSection = document.getElementById('results-section');
    const parlaySummary = document.getElementById('parlay-summary');
    const parlayLegs = document.getElementById('parlay-legs');
    
    // Show results section
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Get confidence level class
    const confidence = data.confidence_score || 0;
    let confidenceClass = 'low-confidence';
    let confidenceText = 'Low';
    let confidenceColor = 'text-red-600';
    
    if (confidence >= 75) {
        confidenceClass = 'high-confidence';
        confidenceText = 'High';
        confidenceColor = 'text-green-600';
    } else if (confidence >= 50) {
        confidenceClass = 'medium-confidence';
        confidenceText = 'Medium';
        confidenceColor = 'text-yellow-600';
    }
    
    // Display summary
    parlaySummary.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="text-center">
                <p class="text-2xl font-bold text-blue-600">${data.legs?.length || 0}</p>
                <p class="text-sm text-gray-600">Legs</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold text-purple-600">${data.total_odds || 'N/A'}</p>
                <p class="text-sm text-gray-600">Total Odds</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold ${confidenceColor}">${Math.round(confidence)}%</p>
                <p class="text-sm text-gray-600">Confidence</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold text-green-600">$${data.potential_payout?.toFixed(2) || '0.00'}</p>
                <p class="text-sm text-gray-600">Potential Payout</p>
            </div>
        </div>
        
        <div class="mt-4 p-4 bg-blue-50 rounded-lg">
            <h4 class="font-semibold text-blue-800 mb-2">Recommendation</h4>
            <p class="text-blue-700">${data.recommendation || 'No recommendation available'}</p>
        </div>
    `;
    
    // Display legs
    if (data.legs && data.legs.length > 0) {
        parlayLegs.innerHTML = data.legs.map((leg, index) => `
            <div class="prop-card ${confidenceClass} bg-white p-4 rounded-lg shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-gray-800">
                        <span class="bg-blue-500 text-white text-xs px-2 py-1 rounded-full mr-2">${index + 1}</span>
                        ${leg.player_name || 'Unknown Player'}
                    </h4>
                    <span class="text-sm font-medium text-gray-600">${leg.team || ''}</span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-3">
                    <div>
                        <p class="text-sm text-gray-600">Prop</p>
                        <p class="font-medium">${leg.prop_type || 'Unknown'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Line</p>
                        <p class="font-medium">${leg.line || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Odds</p>
                        <p class="font-medium text-blue-600">${leg.odds || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Hit Rate</p>
                        <p class="font-medium ${leg.hit_rate >= 0.7 ? 'text-green-600' : leg.hit_rate >= 0.5 ? 'text-yellow-600' : 'text-red-600'}">
                            ${Math.round((leg.hit_rate || 0) * 100)}%
                        </p>
                    </div>
                </div>
                
                ${leg.recent_form ? `
                    <div class="mb-2">
                        <p class="text-sm text-gray-600 mb-1">Recent Form (Last 10)</p>
                        <div class="flex space-x-1">
                            ${leg.recent_form.slice(-10).map(hit => `
                                <div class="w-3 h-3 rounded-full ${hit ? 'bg-green-500' : 'bg-red-500'}"></div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="text-xs text-gray-500">
                    ${leg.position || ''} • ${leg.game_date || 'Today'}
                </div>
            </div>
        `).join('');
    } else {
        parlayLegs.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-exclamation-triangle text-3xl mb-2"></i>
                <p>No parlay legs available</p>
            </div>
        `;
    }
}

// Update stats after generating parlay
function updateStatsAfterParlay(data) {
    stats.totalParlays += 1;
    
    const confidence = data.confidence_score || 0;
    stats.avgConfidence = ((stats.avgConfidence * (stats.totalParlays - 1)) + confidence) / stats.totalParlays;
    
    const payout = parseOdds(data.total_odds || '+0');
    if (payout > stats.bestPayout) {
        stats.bestPayout = payout;
    }
    
    updateStats();
}

// Update statistics display
function updateStats() {
    document.getElementById('total-parlays').textContent = stats.totalParlays;
    document.getElementById('avg-confidence').textContent = `${Math.round(stats.avgConfidence)}%`;
    document.getElementById('best-payout').textContent = `+${stats.bestPayout}`;
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

// Utility function to parse odds
function parseOdds(oddsString) {
    if (typeof oddsString === 'string' && oddsString.startsWith('+')) {
        return parseInt(oddsString.substring(1));
    }
    return 0;
}

// Copy parlay to clipboard
async function copyParlay() {
    if (!currentParlay) {
        showToast('No Parlay', 'No parlay to copy', 'error');
        return;
    }
    
    try {
        const parlayText = formatParlayForCopy(currentParlay);
        await navigator.clipboard.writeText(parlayText);
        showToast('Copied', 'Parlay copied to clipboard', 'success');
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('Copy Failed', 'Unable to copy to clipboard', 'error');
    }
}

// Format parlay for copying
function formatParlayForCopy(parlay) {
    let text = `🎯 PARLAY OPTIMIZER PRO\n\n`;
    text += `📊 ${parlay.legs?.length || 0} Legs | ${parlay.total_odds || 'N/A'} Odds | ${Math.round(parlay.confidence_score || 0)}% Confidence\n`;
    text += `💰 Potential Payout: $${parlay.potential_payout?.toFixed(2) || '0.00'}\n\n`;
    
    if (parlay.legs) {
        parlay.legs.forEach((leg, index) => {
            text += `${index + 1}. ${leg.player_name || 'Unknown'} (${leg.team || 'N/A'})\n`;
            text += `   ${leg.prop_type || 'Unknown'} ${leg.line || ''} (${leg.odds || 'N/A'})\n`;
            text += `   Hit Rate: ${Math.round((leg.hit_rate || 0) * 100)}%\n\n`;
        });
    }
    
    text += `🎲 Recommendation: ${parlay.recommendation || 'No recommendation'}\n`;
    text += `⏰ Generated: ${new Date().toLocaleString()}`;
    
    return text;
}

// Export parlay
function exportParlay() {
    if (!currentParlay) {
        showToast('No Parlay', 'No parlay to export', 'error');
        return;
    }
    
    const dataStr = JSON.stringify(currentParlay, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `parlay_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showToast('Exported', 'Parlay exported successfully', 'success');
}

// Clear results
function clearResults() {
    currentParlay = null;
    document.getElementById('results-section').classList.add('hidden');
    showToast('Cleared', 'Results cleared', 'info');
}

// Show/hide loading
function showLoading(show) {
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    
    if (show) {
        loading.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

// Toast notifications
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    // Set icon and colors based on type
    let iconClass = 'fas fa-info-circle text-blue-500';
    let bgClass = 'bg-white border-blue-200';
    
    switch (type) {
        case 'success':
            iconClass = 'fas fa-check-circle text-green-500';
            bgClass = 'bg-green-50 border-green-200';
            break;
        case 'error':
            iconClass = 'fas fa-exclamation-circle text-red-500';
            bgClass = 'bg-red-50 border-red-200';
            break;
        case 'warning':
            iconClass = 'fas fa-exclamation-triangle text-yellow-500';
            bgClass = 'bg-yellow-50 border-yellow-200';
            break;
    }
    
    toastIcon.innerHTML = `<i class="${iconClass}"></i>`;
    toast.className = `fixed top-4 right-4 ${bgClass} rounded-lg shadow-lg p-4 max-w-sm z-50 transition-all duration-300`;
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    
    toast.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideToast();
    }, 5000);
}

function hideToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('hidden');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to generate tier parlay
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        generateTierParlay();
    }
    
    // Ctrl/Cmd + Shift + Enter to generate custom parlay
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'Enter') {
        event.preventDefault();
        generateCustomParlay();
    }
    
    // Escape to clear results
    if (event.key === 'Escape') {
        clearResults();
    }
});

// Add CORS handling for development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('Development mode - CORS handling enabled');
}
