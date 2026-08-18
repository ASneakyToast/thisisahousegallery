$ports = @(8000, 8001)
foreach ($p in $ports) {
  $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
  if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Output ("killed PID " + $conn.OwningProcess + " on port " + $p)
  } else {
    Write-Output ("port " + $p + " clear")
  }
}
Start-Sleep -Seconds 2