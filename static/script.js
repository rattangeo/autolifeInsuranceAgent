// Global state
let claims = [];
let policies = [];
let selectedClaim = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Page loaded, initializing...');
    await loadClaims();
    await loadPolicies();
    setupEventListeners();
    console.log('Initialization complete');
});

// Load claims from API
async function loadClaims() {
    try {
        console.log('Loading claims...');
        const response = await fetch('/api/claims');
        claims = await response.json();
        console.log('Loaded claims:', claims.length);
        renderClaimsList();
    } catch (error) {
        console.error('Error loading claims:', error);
        document.getElementById('claims-list').innerHTML = 
            '<p class="error-message">Error loading claims</p>';
    }
}

// Load policies from API
async function loadPolicies() {
    try {
        const response = await fetch('/api/policies');
        policies = await response.json();
    } catch (error) {
        console.error('Error loading policies:', error);
    }
}

// Render claims list
function renderClaimsList() {
    console.log('Rendering claims list...');
    const claimsList = document.getElementById('claims-list');
    claimsList.innerHTML = '';
    
    claims.forEach((claim, index) => {
        const claimItem = document.createElement('div');
        claimItem.className = 'claim-item';
        claimItem.dataset.claimId = claim.id;
        
        claimItem.innerHTML = `
            <div class="claim-title">${index + 1}. ${claim.title}</div>
            <div class="claim-desc">${claim.description}</div>
            <span class="claim-type ${claim.claim_type}">${claim.claim_type.toUpperCase()}</span>
        `;
        
        claimItem.addEventListener('click', (e) => {
            console.log('Claim clicked:', claim.id);
            selectClaim(claim, e.currentTarget);
        });
        claimsList.appendChild(claimItem);
    });
    console.log('Rendered', claims.length, 'claims');
}

// Select a claim
function selectClaim(claim, element) {
    console.log('Selecting claim:', claim.title);
    selectedClaim = claim;
    
    // Update UI selection
    document.querySelectorAll('.claim-item').forEach(item => {
        item.classList.remove('selected');
    });
    element.classList.add('selected');
    
    // Show claim details
    showClaimDetails(claim);
    console.log('Claim details displayed');
}

// Show claim details and policy
function showClaimDetails(claim) {
    const policy = policies.find(p => p.policy_number === claim.policy_number);
    
    // Show claim info
    const claimInfo = document.getElementById('claim-info');
    claimInfo.innerHTML = `
        <div class="info-row">
            <div class="info-label">Claim ID:</div>
            <div class="info-value">${claim.id}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Title:</div>
            <div class="info-value">${claim.title}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Type:</div>
            <div class="info-value">${claim.claim_type.toUpperCase()}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Amount:</div>
            <div class="info-value">$${claim.amount.toLocaleString()}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Policy Number:</div>
            <div class="info-value">${claim.policy_number}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Description:</div>
            <div class="info-value">${claim.description}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Claim Text:</div>
            <div class="info-value" style="font-style: italic; color: #666;">${claim.claim_text}</div>
        </div>
    `;
    
    // Show policy info
    const policyInfo = document.getElementById('policy-info');
    if (policy) {
        const totalCoverageLimit = policy.coverages ? policy.coverages.reduce((sum, c) => sum + c.coverage_limit, 0) : 0;
        const primaryDeductible = policy.coverages && policy.coverages.length > 0 ? policy.coverages[0].deductible : 0;
        
        let coveragesHtml = '';
        if (policy.coverages && policy.coverages.length > 0) {
            coveragesHtml = '<div style="margin-top: 10px;"><strong>Coverages:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
            policy.coverages.forEach(cov => {
                coveragesHtml += `<li style="font-size: 0.9rem; color: #666;">${cov.coverage_type.replace(/_/g, ' ').toUpperCase()}: $${cov.coverage_limit.toLocaleString()} (Deductible: $${cov.deductible.toLocaleString()})</li>`;
            });
            coveragesHtml += '</ul></div>';
        }
        
        policyInfo.innerHTML = `
            <div class="info-row">
                <div class="info-label">Policy Number:</div>
                <div class="info-value">${policy.policy_number}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Type:</div>
                <div class="info-value">${policy.policy_type.toUpperCase()}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Policyholder:</div>
                <div class="info-value">${policy.policyholder || 'N/A'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Status:</div>
                <div class="info-value">${policy.status.toUpperCase()}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Effective Date:</div>
                <div class="info-value">${policy.effective_date ? new Date(policy.effective_date).toLocaleDateString() : 'N/A'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Expiry Date:</div>
                <div class="info-value">${policy.expiry_date ? new Date(policy.expiry_date).toLocaleDateString() : 'N/A'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Annual Premium:</div>
                <div class="info-value">$${policy.annual_premium ? policy.annual_premium.toLocaleString() : 'N/A'}</div>
            </div>
            ${coveragesHtml}
        `;
    } else {
        policyInfo.innerHTML = '<p style="color: #dc3545;">Policy not found</p>';
    }
    
    // Show the details section
    hideAllSections();
    document.getElementById('claim-details').style.display = 'block';
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('process-btn').addEventListener('click', processClaim);
    document.getElementById('process-another-btn').addEventListener('click', () => {
        hideAllSections();
        if (selectedClaim) {
            showClaimDetails(selectedClaim);
        } else {
            document.getElementById('initial-state').style.display = 'block';
        }
    });
}

// Process claim
async function processClaim() {
    if (!selectedClaim) return;
    
    // Show processing state
    hideAllSections();
    document.getElementById('processing').style.display = 'block';
    
    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                claim_id: selectedClaim.id
            })
        });
        
        if (!response.ok) {
            throw new Error('Processing failed');
        }
        
        const result = await response.json();
        showResults(result);
        
    } catch (error) {
        console.error('Error processing claim:', error);
        hideAllSections();
        document.getElementById('results').style.display = 'block';
        document.getElementById('result-summary').innerHTML = 
            `<p class="error-message">Error processing claim: ${error.message}</p>`;
    }
}

// Show results
function showResults(result) {
    hideAllSections();
    document.getElementById('results').style.display = 'block';
    
    // Summary
    const summary = result.claim_summary;
    document.getElementById('result-summary').innerHTML = `
        <div class="info-row">
            <div class="info-label">Claim ID:</div>
            <div class="info-value">${summary.id}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Title:</div>
            <div class="info-value">${summary.title}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Policy:</div>
            <div class="info-value">${summary.policy_number}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Type:</div>
            <div class="info-value">${summary.claim_type.toUpperCase()}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Claimed Amount:</div>
            <div class="info-value">${summary.amount}</div>
        </div>
    `;
    
    // Decision
    const decision = result.decision;
    const statusClass = decision.status.toLowerCase();
    const fraudClass = (decision.fraud_risk || 'n/a').toLowerCase().replace('/', '-');
    
    document.getElementById('result-decision').innerHTML = `
        <div class="info-row">
            <div class="info-label">Status:</div>
            <div class="info-value">
                <span class="status-badge status-${statusClass}">${decision.status}</span>
            </div>
        </div>
        <div class="info-row">
            <div class="info-label">Approved Amount:</div>
            <div class="info-value" style="font-size: 1.2rem; font-weight: bold; color: #667eea;">
                ${decision.approved_amount}
            </div>
        </div>
        <div class="info-row">
            <div class="info-label">Confidence:</div>
            <div class="info-value">${decision.confidence}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Fraud Risk:</div>
            <div class="info-value">
                <span class="fraud-risk ${fraudClass}">${decision.fraud_risk}</span>
            </div>
        </div>
    `;
    
    // Reasoning
    document.getElementById('result-reasoning').textContent = result.reasoning;
    
    // Next Steps
    const nextStepsList = document.createElement('ul');
    nextStepsList.className = 'next-steps-list';
    result.next_steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        nextStepsList.appendChild(li);
    });
    document.getElementById('result-next-steps').innerHTML = '';
    document.getElementById('result-next-steps').appendChild(nextStepsList);
    
    // Processing Log
    const logBox = document.getElementById('result-log');
    logBox.innerHTML = '';
    result.processing_log.forEach(entry => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">[${entry.timestamp}]</span>
            <span>${entry.message}</span>
        `;
        logBox.appendChild(logEntry);
    });
}

// Hide all sections
function hideAllSections() {
    document.getElementById('claim-details').style.display = 'none';
    document.getElementById('processing').style.display = 'none';
    document.getElementById('results').style.display = 'none';
    document.getElementById('initial-state').style.display = 'none';
}
