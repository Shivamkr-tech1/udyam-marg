from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_sample():
    response = client.post('/api/analyze', json={
        'location': 'Maner, Patna, Bihar',
        'margin_capital': 100000,
        'business_category': 'Dairy'
    })
    assert response.status_code == 200
    data = response.json()
    assert data['financial']['project_cost'] == 1000000.0
    assert data['financial']['sanctionable_loan'] == 900000.0
    assert data['financial']['scheme']['name'] == 'Term Loan Scheme'
    assert 'swot' in data['advisory']
    assert data['geospatial']['competitor_mapping']['category'] == 'Dairy'
