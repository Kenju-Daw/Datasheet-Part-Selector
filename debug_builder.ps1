$id = "a2fa131e-b729-4258-8e24-295494e90795"
$body = @{
    datasheet_id = $id
    requirements = @(
        @{ size = "22D"; quantity = 10; contact_type = "pin" }
    )
} | ConvertTo-Json -Depth 5

Write-Host "Sending payload to Backend:"
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/parts/search-inserts" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✅ Success!"
    Write-Host ($response | ConvertTo-Json -Depth 2)
} catch {
    Write-Host "❌ Error:"
    Write-Host $_
}
