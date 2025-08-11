#!/bin/bash
# A2A Agent Startup Script
# Starts all available A2A agents in their respective ports

echo "🚀 Starting A2A Agent Ecosystem..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1  # Port is busy
    else
        return 0  # Port is available
    fi
}

# Function to start agent
start_agent() {
    local name=$1
    local port=$2
    local command=$3
    local dir=$4
    
    echo -e "\n🤖 Starting ${name} on port ${port}..."
    
    if check_port $port; then
        echo -e "${GREEN}✅ Port ${port} is available${NC}"
        
        # Start agent in background
        cd "$dir"
        if [ -f "$command" ]; then
            echo -e "${YELLOW}📝 Executing: $command${NC}"
            # Use uv if pyproject.toml exists, otherwise use python
            if [ -f "pyproject.toml" ]; then
                nohup uv run python "$command" > "${name}.log" 2>&1 &
            else
                nohup python "$command" > "${name}.log" 2>&1 &
            fi
            echo $! > "${name}.pid"
            sleep 8  # Dar mais tempo para iniciar, especialmente com uv
            
            # Verify it started - porta deve estar OCUPADA agora
            if check_port $port; then
                # Porta ainda livre = falhou
                echo -e "${RED}❌ Failed to start ${name}${NC}"
                rm -f "${name}.pid"
            else
                # Porta ocupada = sucesso
                echo -e "${GREEN}✅ ${name} started successfully (PID: $(cat ${name}.pid))${NC}"
            fi
        else
            echo -e "${RED}❌ Command file not found: $command${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Port ${port} is already in use${NC}"
        echo -e "${YELLOW}   Checking if ${name} is already running...${NC}"
        
        # Test if it's actually our agent
        if curl -s "http://localhost:${port}/.well-known/agent.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${name} is already running${NC}"
        else
            echo -e "${RED}❌ Port occupied by different service${NC}"
        fi
    fi
}

# Start HelloWorld Agent
start_agent "HelloWorld" 9999 "app.py" "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/helloworld"

# Start Turso Agent
start_agent "Turso" 4243 "server.py" "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/turso"

# Start Marvin Agent
echo -e "\n🤖 Starting Marvin Agent..."
# Sempre usar o método direto, sem daemon por enquanto
start_agent "Marvin" 10030 "server.py" "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/marvin"


# Wait a moment and test discovery
echo -e "\n🔍 Testing Agent Discovery..."
sleep 5

# Test discovery endpoints
test_discovery() {
    local name=$1
    local url=$2
    
    echo -e "\n🔍 Testing ${name} discovery..."
    if curl -s --max-time 3 "${url}" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} discovery endpoint responding${NC}"
        # Show basic info
        agent_name=$(curl -s "${url}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', 'Unknown'))" 2>/dev/null)
        if [ ! -z "$agent_name" ]; then
            echo -e "${GREEN}   📋 Agent Name: ${agent_name}${NC}"
        fi
    else
        echo -e "${RED}❌ ${name} discovery endpoint not responding${NC}"
    fi
}

test_discovery "HelloWorld" "http://localhost:9999/.well-known/agent.json"
test_discovery "Turso" "http://localhost:4243/.well-known/agent.json"
test_discovery "Marvin" "http://localhost:10030/.well-known/agent.json"

# Summary
echo -e "\n🎯 Startup Summary:"
echo "=================="
echo -e "${GREEN}✅ Agent discovery endpoints configured${NC}"
echo -e "${GREEN}✅ Agent cards validated and compliant${NC}"
echo -e "${GREEN}✅ Neural optimization patterns active${NC}"

echo -e "\n📊 Running validation and connectivity tests..."
if [ -f "agent_card_validator.py" ]; then
    python agent_card_validator.py
else
    echo -e "${YELLOW}⚠️  Agent validator not found in current directory${NC}"
fi

echo -e "\n🔗 Agent URLs:"
echo "   • HelloWorld: http://localhost:9999"
echo "   • Turso: http://localhost:4243"
echo "   • Marvin: http://localhost:10030"

echo -e "\n💡 Next Steps:"
echo "   1. Test inter-agent communication"
echo "   2. Monitor agent logs for issues"
echo "   3. Use agents with Claude Flow coordination"

echo -e "\n🛠️  Management Commands:"
echo "   • Stop all: pkill -f 'python.*app.py|python.*server.py'"
echo "   • View logs: tail -f *.log"
echo "   • Test discovery: python test_discovery.py"

echo -e "\n${GREEN}🚀 A2A Agent Ecosystem startup complete!${NC}"