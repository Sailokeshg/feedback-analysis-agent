#!/usr/bin/env python3
"""
Verification script for documentation accuracy.
Checks that the quickstart and setup instructions are correct.
"""
import os
import sys
import subprocess
import json
from pathlib import Path


def check_prerequisites():
    """Check if all prerequisites are available."""
    print("🔍 Checking prerequisites...")

    checks = [
        ("Docker", "docker --version"),
        ("Docker Compose", "docker-compose --version"),
        ("Python", "python3 --version"),
        ("Node.js", "node --version"),
        ("npm", "npm --version"),
    ]

    for name, command in checks:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"   ✅ {name}: {version}")
            else:
                print(f"   ❌ {name}: Not found or not working")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"   ❌ {name}: Not found")
            return False

    return True


def check_project_structure():
    """Check that all required files and directories exist."""
    print("\n📁 Checking project structure...")

    required_paths = [
        "README.md",
        "CONTRIBUTING.md",
        "Makefile",
        "env.example",
        "client/package.json",
        "server/pyproject.toml",
        "worker/pyproject.toml",
        "scripts/bootstrap.sh",
        "scripts/dev-setup.sh",
        "infra/docker-compose.yml",
        "docs/architecture.md",
        "docs/api.md",
    ]

    missing = []
    for path in required_paths:
        if not Path(path).exists():
            missing.append(path)
            print(f"   ❌ Missing: {path}")
        else:
            print(f"   ✅ Found: {path}")

    if missing:
        print(f"\n❌ Missing {len(missing)} required files")
        return False

    print(f"\n✅ All {len(required_paths)} required files present")
    return True


def check_makefile_targets():
    """Check that documented Makefile targets exist."""
    print("\n🔧 Checking Makefile targets...")

    documented_targets = [
        "help", "bootstrap", "dev-setup", "dev", "build",
        "test", "test-server", "test-worker", "test-client",
        "demo-logging", "test-logging", "lint", "format",
        "docker-up", "docker-down", "clean"
    ]

    try:
        result = subprocess.run(["make", "help"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("   ❌ Makefile help target failed")
            return False

        help_output = result.stdout

        missing_targets = []
        for target in documented_targets:
            if f"make {target}" not in help_output and target not in help_output:
                missing_targets.append(target)

        if missing_targets:
            print(f"   ❌ Missing targets: {', '.join(missing_targets)}")
            return False

        print(f"   ✅ All {len(documented_targets)} Makefile targets documented")
        return True

    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("   ❌ Makefile not accessible")
        return False


def check_environment_variables():
    """Check that environment variables are properly documented."""
    print("\n🔐 Checking environment variables...")

    # Read env.example
    try:
        with open("env.example", "r") as f:
            env_content = f.read()
    except FileNotFoundError:
        print("   ❌ env.example not found")
        return False

    # Check for key environment variables
    required_vars = [
        "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
        "DATABASE_URL", "REDIS_URL", "EXTERNAL_CHROMA_URL",
        "API_HOST", "API_PORT", "API_DEBUG"
    ]

    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)

    if missing_vars:
        print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
        return False

    print(f"   ✅ All {len(required_vars)} key environment variables documented")
    return True


def check_package_dependencies():
    """Check that package.json and pyproject.toml have required dependencies."""
    print("\n📦 Checking dependencies...")

    # Check client/package.json
    try:
        with open("client/package.json", "r") as f:
            package_json = json.load(f)

        client_deps = package_json.get("dependencies", {})
        dev_deps = package_json.get("devDependencies", {})

        required_client_deps = ["react", "axios", "zustand", "@tanstack/react-query"]
        missing_client = [dep for dep in required_client_deps if dep not in client_deps]

        if missing_client:
            print(f"   ❌ Missing client dependencies: {', '.join(missing_client)}")
            return False

        print("   ✅ Client dependencies configured correctly")

    except (FileNotFoundError, json.JSONDecodeError):
        print("   ❌ client/package.json not readable")
        return False

    # Check server/pyproject.toml
    try:
        with open("server/pyproject.toml", "r") as f:
            toml_content = f.read()

        required_server_deps = ["fastapi", "sqlalchemy", "loguru", "prometheus-client"]
        missing_server = [dep for dep in required_server_deps if f'"{dep}==' not in toml_content]

        if missing_server:
            print(f"   ❌ Missing server dependencies: {', '.join(missing_server)}")
            return False

        print("   ✅ Server dependencies configured correctly")

    except FileNotFoundError:
        print("   ❌ server/pyproject.toml not readable")
        return False

    return True


def check_scripts_executable():
    """Check that shell scripts are executable."""
    print("\n📜 Checking script permissions...")

    scripts = [
        "scripts/bootstrap.sh",
        "scripts/dev-setup.sh",
    ]

    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"   ✅ {script} is executable")
            else:
                print(f"   ❌ {script} is not executable")
                return False
        else:
            print(f"   ❌ {script} not found")
            return False

    return True


def main():
    """Run all verification checks."""
    print("🔬 Verifying Documentation Accuracy")
    print("=" * 50)

    checks = [
        ("Prerequisites", check_prerequisites),
        ("Project Structure", check_project_structure),
        ("Makefile Targets", check_makefile_targets),
        ("Environment Variables", check_environment_variables),
        ("Dependencies", check_package_dependencies),
        ("Script Permissions", check_scripts_executable),
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"   ❌ {name} check failed")
        except Exception as e:
            print(f"   ❌ {name} check error: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Verification Results: {passed}/{total} checks passed")

    if passed == total:
        print("✅ All documentation checks passed!")
        print("\n🎉 The quickstart guide should work for newcomers.")
        return 0
    else:
        print("❌ Some documentation checks failed.")
        print("\n🔧 Please review and fix the documentation issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
