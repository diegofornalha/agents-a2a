#!/bin/bash
# A2A Agent Shutdown Script
# Stops all running A2A agents gracefully

echo "🛑 Stopping A2A Agent Ecosystem..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to stop agent using PID file
stop_agent_pid() {
    local name=$1
    local pid_file=$2
    
    echo -e "\n🤖 Stopping ${name}..."
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}📝 Killing process ${PID}...${NC}"
            kill $PID
            sleep 2
            
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Process still running, forcing...${NC}"
                kill -9 $PID
            fi
            
            rm -f "$pid_file"
            echo -e "${GREEN}✅ ${name} stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  PID file exists but process not running${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for ${name}${NC}"
    fi
}

# Function to stop agent by port
stop_agent_port() {
    local name=$1
    local port=$2
    
    echo -e "\n🤖 Stopping ${name} on port ${port}..."
    
    # Find process using the port
    PID=$(lsof -ti:$port -sTCP:LISTEN)
    
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}📝 Found process ${PID} on port ${port}${NC}"
        kill $PID
        sleep 2
        
        # Force kill if still running
        if lsof -ti:$port -sTCP:LISTEN > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Process still running, forcing...${NC}"
            kill -9 $PID
        fi
        
        echo -e "${GREEN}✅ ${name} stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  No process found on port ${port}${NC}"
    fi
}

# Stop HelloWorld Agent
echo -e "\n📍 Checking HelloWorld Agent..."
if [ -f "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/helloworld/HelloWorld.pid" ]; then
    stop_agent_pid "HelloWorld" "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/helloworld/HelloWorld.pid"
else
    stop_agent_port "HelloWorld" 9999
fi

# Stop Turso Agent
echo -e "\n📍 Checking Turso Agent..."
if [ -f "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/turso/Turso.pid" ]; then
    stop_agent_pid "Turso" "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/turso/Turso.pid"
else
    stop_agent_port "Turso" 4243
fi

# Stop Marvin Agent
echo -e "\n📍 Checking Marvin Agent..."
cd "/Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/marvin"
if [ -f "marvin_control.sh" ]; then
    echo -e "${YELLOW}📝 Using Marvin daemon control script${NC}"
    ./marvin_control.sh stop
else
    if [ -f "Marvin.pid" ]; then
        stop_agent_pid "Marvin" "Marvin.pid"
    else
        stop_agent_port "Marvin" 10030
    fi
fi

# Stop any other Python processes that might be agents
echo -e "\n🔍 Looking for other agent processes..."

# Kill any remaining app.py or server.py processes
APP_PIDS=$(pgrep -f "python.*app.py")
if [ ! -z "$APP_PIDS" ]; then
    echo -e "${YELLOW}📝 Found app.py processes: ${APP_PIDS}${NC}"
    kill $APP_PIDS
    echo -e "${GREEN}✅ Stopped app.py processes${NC}"
fi

SERVER_PIDS=$(pgrep -f "python.*server.py")
if [ ! -z "$SERVER_PIDS" ]; then
    echo -e "${YELLOW}📝 Found server.py processes: ${SERVER_PIDS}${NC}"
    kill $SERVER_PIDS
    echo -e "${GREEN}✅ Stopped server.py processes${NC}"
fi

# Clean up log files (optional)
echo -e "\n🧹 Cleanup options:"
read -p "Do you want to clean up log files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📝 Removing log files...${NC}"
    rm -f /Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/helloworld/*.log
    rm -f /Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/turso/*.log
    rm -f /Users/agents/Desktop/claude-20x/agents-a2a/.conductor/hangzhou/marvin/*.log
    rm -f *.log
    echo -e "${GREEN}✅ Log files cleaned${NC}"
fi

# Verify all agents are stopped
echo -e "\n🔍 Verifying shutdown..."
sleep 2

RUNNING=false

# Check ports
if lsof -ti:9999 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${RED}❌ Port 9999 still in use${NC}"
    RUNNING=true
else
    echo -e "${GREEN}✅ Port 9999 is free${NC}"
fi

if lsof -ti:4243 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${RED}❌ Port 4243 still in use${NC}"
    RUNNING=true
else
    echo -e "${GREEN}✅ Port 4243 is free${NC}"
fi

if lsof -ti:10030 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${RED}❌ Port 10030 still in use${NC}"
    RUNNING=true
else
    echo -e "${GREEN}✅ Port 10030 is free${NC}"
fi

# Summary
echo -e "\n🎯 Shutdown Summary:"
echo "==================="

if [ "$RUNNING" = false ]; then
    echo -e "${GREEN}✅ All agents successfully stopped${NC}"
    echo -e "${GREEN}✅ All ports are free${NC}"
    echo -e "${GREEN}✅ System ready for restart${NC}"
else
    echo -e "${YELLOW}⚠️  Some processes may still be running${NC}"
    echo -e "${YELLOW}   Use 'lsof -i:PORT' to check specific ports${NC}"
    echo -e "${YELLOW}   Use 'ps aux | grep python' to find remaining processes${NC}"
fi

echo -e "\n💡 Management Commands:"
echo "   • Start all: ./start_all_agents.sh"
echo "   • Check ports: lsof -i:9999,4243,10030"
echo "   • Force kill all: pkill -9 -f 'python.*app.py|python.*server.py'"
echo "   • View processes: ps aux | grep python"

echo -e "\n${GREEN}🛑 A2A Agent Ecosystem shutdown complete!${NC}"