$body = @{
    requirements = @(
        @{
            contact_type = "pin"
            quantity = 150
            size = "22D"
        }
    )
    datasheet_id = "test-id"
} | ConvertTo-Json

Write-Host "Testing Multi-Connector Logic (150 pins > 128)"
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/parts/search-inserts" -Method POST -Body $body -ContentType "application/json"
    
    # We expect 'suggestion' or 'multi_connector' to be present
    if ($response.multi_connector) {
        Write-Host "✅ PASSED: Multi-connector suggestion received" -ForegroundColor Green
        Write-Host "Connector 1: $($response.multi_connector.connector_1.code) ($($response.multi_connector.connector_1.total_contacts))"
        Write-Host "Connector 2: $($response.multi_connector.connector_2.code) ($($response.multi_connector.connector_2.total_contacts))"
        Write-Host "Total Capacity: $($response.multi_connector.total_capacity)"
        Write-Host "Note: $($response.multi_connector.note)"
    } else {
        Write-Host "❌ FAILED: No multi-connector suggestion found" -ForegroundColor Red
        Write-Host "Matches found: $($response.matches.Count)"
    }
} catch {
    Write-Host "❌ Error calling API:"
    Write-Host $_
}
