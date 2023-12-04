# Specify the path to the requirements.txt file
$requirementsFilePath = ".\requirements.txt"

# Install Python modules from requirements.txt
Write-Host "Installing Python modules from requirements.txt..."
& python -m pip install -r $requirementsFilePath

# Check for errors during installation
if ($LastExitCode -eq 0) {
    Write-Host "Python modules installed successfully."
} else {
    Write-Host "Error installing Python modules. Please check the requirements.txt file."
    Exit
}
