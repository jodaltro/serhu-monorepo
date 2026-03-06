#!/bin/bash
# quick-logs.sh - Script para ativar logs e monitorá-los
# Usage: ./quick-logs.sh [debug|info|warning]

set -e

LEVEL="${1:-info}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 SerHu Logging Quick Start${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Validar nível
case "$LEVEL" in
  debug|info|warning)
    LOG_LEVEL="${LEVEL^^}"  # Converter para uppercase
    echo -e "${GREEN}✓ Log Level: ${LOG_LEVEL}${NC}"
    ;;
  *)
    echo -e "${RED}✗ Nível inválido: ${LEVEL}${NC}"
    echo "Opções: debug, info, warning"
    exit 1
    ;;
esac

echo ""
echo -e "${YELLOW}📋 Instruções:${NC}"
echo ""
echo "1. Abra 2 terminais lado a lado"
echo ""
echo "2. ${BLUE}Terminal 1${NC} - Execute a API:"
echo "   cd packages/api"
echo "   export LOG_LEVEL=${LOG_LEVEL}"
echo "   python -m uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000"
echo ""
echo "3. ${BLUE}Terminal 2${NC} - Monitore os logs:"
echo "   tail -f serhu.log"
echo ""
echo -e "${YELLOW}📝 Teste um endpoint (em outro terminal):${NC}"
echo ""
echo "   # Criar um novo Being"
echo "   curl -X POST http://localhost:8000/beings \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\":\"Luna\",\"language\":\"pt\"}'"
echo ""
echo "   # Chat com o Being"
echo "   curl -X POST http://localhost:8000/beings/<being_id>/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\":\"Hello!\"}'"
echo ""
echo -e "${YELLOW}🔍 Filtrar Logs:${NC}"
echo ""
echo "   # Apenas chat"
echo "   tail -f serhu.log | grep '🗨️'"
echo ""
echo "   # Apenas sleep"
echo "   tail -f serhu.log | grep '😴\\|⏰'"
echo ""
echo "   # Apenas erros"
echo "   tail -f serhu.log | grep 'ERROR\\|✗'"
echo ""
echo "   # Apenas sucessos"
echo "   tail -f serhu.log | grep '✓'"
echo ""
echo -e "${YELLOW}📚 Documentação:${NC}"
echo ""
echo "   - Guia completo: LOGGING.md"
echo "   - Resumo: RESUMO_LOGS.md"
echo "   - Exemplos: python exemplo_logging.py"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
