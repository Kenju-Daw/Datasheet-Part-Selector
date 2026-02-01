function Test-MultiConnector {
    param (
        [int]$qty,
        [string]$size
    )

    $body = @{
        requirements = @(
            @{
                contact_type = "pin"
                quantity = $qty
                size = $size
            }
        )
        datasheet_id = "test-awg"
    } | ConvertTo-Json -Depth 5

    Write-Host "Testing $qty x Size $size..." -NoNewline
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/parts/search-inserts" -Method POST -Body $body -ContentType "application/json"
        
        if ($response.multi_connector) {
            Write-Host " [PASSED] Suggested: $($response.multi_connector.connector_1.code) + $($response.multi_connector.connector_2.code)" -ForegroundColor Green
        } else {
            Write-Host " [FAILED] No multi-connector suggestion." -ForegroundColor Red
            if ($response.suggestion) { Write-Host "   Suggestion: $($response.suggestion)" -ForegroundColor Yellow }
        }
    } catch {
        Write-Host " [ERROR] API Call Failed" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

Test-MultiConnector -qty 150 -size "22D" # Control (Should Pass)
Test-MultiConnector -qty 80 -size "20"   # Max single ~55
Test-MultiConnector -qty 40 -size "16"   # Max single ~29
Test-MultiConnector -qty 25 -size "12"   # Max single ~9?
