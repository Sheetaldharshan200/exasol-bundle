#!/usr/bin/env node
const { execSync } = require('child_process');
const os = require('os');

console.log("=== Bootstrapping Exasol Environment ===");

function checkCommand(cmd) {
    try {
        execSync(`${cmd} --version`, { stdio: 'ignore' });
        return true;
    } catch (e) {
        return false;
    }
}

function installPythonWindows() {
    console.log("[WARN] Python 3 is missing. Attempting to install via Windows Package Manager (winget)...");
    try {
        // Automatically accepts agreements to prevent the script from hanging
        execSync('winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements', { stdio: 'inherit' });
        console.log("[SUCCESS] Python 3 installed. NOTE: You may need to restart your terminal for Windows to recognize the 'python' command.");
    } catch (e) {
        console.error("\n[ERROR] Auto-installation failed. Please install Python from the Microsoft Store or python.org");
        process.exit(1);
    }
}

try {
    const isWindows = os.platform() === 'win32';

    if (!checkCommand('python3') && !checkCommand('python')) {
        if (isWindows) {
            installPythonWindows();
            // We exit here because Windows requires a terminal restart to reload PATH after a winget Python install
            console.log("\n[ACTION REQUIRED] Python has been installed, but your terminal's PATH has not been updated yet.");
            console.log("Please close this terminal, open a new one, and re-run the installation command:");
            console.log("  npm install -g exasol-bundle");
            process.exit(1);
        } else {
            console.error("\n[ERROR] Python 3 is required. Please install it to continue.");
            process.exit(1);
        }
    }

    const pyCmd = checkCommand('python3') ? 'python3' : 'python';
    let installCmd = '';

    if (checkCommand('uv')) {
        console.log("Detected 'uv'. Installing...");
        installCmd = 'uv tool install exasol-bundle';
    } else if (checkCommand('pipx')) {
        console.log("Detected 'pipx'. Installing...");
        installCmd = 'pipx install exasol-bundle';
    } else {
        console.log("Falling back to standard pip install...");
        installCmd = `${pyCmd} -m pip install --user exasol-bundle`;
    }

    execSync(installCmd, { stdio: 'inherit' });
    
    console.log("\nRunning Exasol initialization...");
    execSync('exa-bundle init', { stdio: 'inherit' });

} catch (error) {
    console.error(`\n[ERROR] Process failed: ${error.message}`);
    process.exit(1);
}