#!/bin/bash

# Pre-deployment checks for Lexi-BE
# Kiểm tra toàn bộ codebase trước khi deploy

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Deployment Checks - Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Counter for checks
PASSED=0
FAILED=0

check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ $2${NC}"
        ((FAILED++))
    fi
}

# 1. Check Python syntax
echo -e "${YELLOW}[1] Checking Python syntax...${NC}"
cd "$PROJECT_ROOT"

python_files=$(find src -name "*.py" -type f -not -path "*/venv/*")
syntax_errors=0

for file in $python_files; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}  Syntax error in: $file${NC}"
        ((syntax_errors++))
    fi
done

if [ $syntax_errors -eq 0 ]; then
    check_result 0 "Python syntax check"
else
    check_result 1 "Python syntax check ($syntax_errors errors)"
fi

# 2. Check imports
echo -e "\n${YELLOW}[2] Checking imports...${NC}"
import_errors=0

for file in $python_files; do
    if ! python3 -c "import ast; ast.parse(open('$file').read())" 2>/dev/null; then
        ((import_errors++))
    fi
done

check_result $import_errors "Import validation"

# 3. Check template.yaml
echo -e "\n${YELLOW}[3] Checking template.yaml...${NC}"
if command -v sam &> /dev/null; then
    if sam validate --template template.yaml > /dev/null 2>&1; then
        check_result 0 "SAM template validation"
    else
        check_result 1 "SAM template validation"
    fi
else
    echo -e "${YELLOW}  ⚠ SAM CLI not installed, skipping template validation${NC}"
fi

# 4. Check requirements.txt
echo -e "\n${YELLOW}[4] Checking requirements.txt...${NC}"
if [ -f "src/requirements.txt" ]; then
    check_result 0 "requirements.txt exists"
else
    check_result 1 "requirements.txt not found"
fi

# 5. Check for common issues
echo -e "\n${YELLOW}[5] Checking for common issues...${NC}"

# Check for print statements (should use logging)
print_count=$(grep -r "print(" src --include="*.py" | grep -v "logger\|#" | wc -l)
if [ $print_count -eq 0 ]; then
    check_result 0 "No print statements found (using logging)"
else
    echo -e "${YELLOW}  ⚠ Found $print_count print statements (should use logging)${NC}"
fi

# Check for hardcoded credentials
cred_count=$(grep -r "password\|secret\|api_key" src --include="*.py" | grep -v "PASSWORD\|SECRET\|API_KEY\|#" | wc -l)
if [ $cred_count -eq 0 ]; then
    check_result 0 "No hardcoded credentials found"
else
    echo -e "${YELLOW}  ⚠ Found potential hardcoded credentials${NC}"
fi

# 6. Check environment variables
echo -e "\n${YELLOW}[6] Checking environment variables...${NC}"
required_vars=("LEXI_TABLE_NAME" "LOG_LEVEL")
missing_vars=0

for var in "${required_vars[@]}"; do
    if grep -q "$var" template.yaml; then
        echo -e "${GREEN}  ✓ $var defined in template.yaml${NC}"
    else
        echo -e "${RED}  ✗ $var not found in template.yaml${NC}"
        ((missing_vars++))
    fi
done

check_result $missing_vars "Environment variables"

# 7. Check handlers exist
echo -e "\n${YELLOW}[7] Checking handler files...${NC}"
handlers=(
    "src/infrastructure/handlers/session_handler.py"
    "src/infrastructure/handlers/flashcard/create_flashcard_handler.py"
    "src/infrastructure/handlers/profile/get_profile_handler.py"
    "src/infrastructure/handlers/vocabulary/translate_vocabulary_handler.py"
    "src/infrastructure/handlers/admin/list_admin_users_handler.py"
    "src/infrastructure/handlers/onboarding/complete_onboarding_handler.py"
)

missing_handlers=0
for handler in "${handlers[@]}"; do
    if [ -f "$handler" ]; then
        echo -e "${GREEN}  ✓ $handler${NC}"
    else
        echo -e "${RED}  ✗ $handler not found${NC}"
        ((missing_handlers++))
    fi
done

check_result $missing_handlers "Handler files"

# 8. Check DTOs
echo -e "\n${YELLOW}[8] Checking DTO files...${NC}"
dtos=(
    "src/application/dtos/auth_dtos.py"
    "src/application/dtos/speaking_session_dtos.py"
    "src/application/dtos/flashcard_dtos.py"
    "src/application/dtos/vocabulary_dtos.py"
)

missing_dtos=0
for dto in "${dtos[@]}"; do
    if [ -f "$dto" ]; then
        echo -e "${GREEN}  ✓ $dto${NC}"
    else
        echo -e "${RED}  ✗ $dto not found${NC}"
        ((missing_dtos++))
    fi
done

check_result $missing_dtos "DTO files"

# 9. Check for TODO/FIXME comments
echo -e "\n${YELLOW}[9] Checking for TODO/FIXME comments...${NC}"
todo_count=$(grep -r "TODO\|FIXME" src --include="*.py" | wc -l)
if [ $todo_count -eq 0 ]; then
    check_result 0 "No TODO/FIXME comments"
else
    echo -e "${YELLOW}  ⚠ Found $todo_count TODO/FIXME comments${NC}"
    grep -r "TODO\|FIXME" src --include="*.py" | head -5
fi

# 10. Check config files
echo -e "\n${YELLOW}[10] Checking configuration files...${NC}"
config_files=(
    "src/infrastructure/configuration/config.py"
    "src/infrastructure/logging/config.py"
)

missing_configs=0
for config in "${config_files[@]}"; do
    if [ -f "$config" ]; then
        echo -e "${GREEN}  ✓ $config${NC}"
    else
        echo -e "${RED}  ✗ $config not found${NC}"
        ((missing_configs++))
    fi
done

check_result $missing_configs "Configuration files"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Deployment Check Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: sam build"
    echo "  2. Run: sam deploy --guided"
    echo "  3. Test with: python3 scripts/test_api.py <API_URL> <AUTH_TOKEN>"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
