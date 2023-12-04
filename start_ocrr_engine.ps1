# Terminate all running Python processes
Get-Process | Where-Object {$_.Name -like "python.exe"} | Stop-Process -Force

# Specify the path to your Python script
$pythonScriptPath = "C:\Program Files (x86)\OCRR\ocrr_engine.py"

# Run the Python script
Write-Host "Running OCRR Engine"
& python $pythonScriptPath

# Wait for the Python script to finish
$process = Start-Process -FilePath "python.exe" -ArgumentList $pythonScriptPath -Wait