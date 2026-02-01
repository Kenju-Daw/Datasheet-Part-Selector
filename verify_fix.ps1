$body = @{
    connector_type = "24"
    finish_code = "W"
    shell_class = "W"  # User selected "Olive Drab" (W) usually implies class W, but let's test the Shell Letter logic.
                       # Wait, shell_class usually maps to 'Series' stuff or material? 
                       # In D38999/24 W G 39 P N:
                       # 24 = Type
                       # W = Finish
                       # G = Shell Size (derived from 21)
                       # 39 = Insert
    
    # The API expects:
    # full_pn = f"D38999/{request.connector_type}{request.finish_code}{shell_letter}{insert_code_short}{request.contact_type}{request.key_position}"
    
    insert_code = "21-39"
    contact_type = "P"
    key_position = "N"
} | ConvertTo-Json

Write-Host "Testing Part Number Generation for Insert 21-39 (Shell 21 -> G)"
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/parts/generate-part-number" -Method POST -Body $body -ContentType "application/json"
    $pn = $response.full_part_number
    
    Write-Host "Generated Part Number: $pn"
    
    if ($pn -match "D38999/24WG39PN") {
        Write-Host "✅ PASSED: Correctly derived Shell Letter 'G'" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Expected '...WG39...', got '$pn'" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error calling API:"
    Write-Host $_
}
