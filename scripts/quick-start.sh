#!/bin/bash

# Quick Start Script for Sentiment Analysis Project
# This script helps you set up and run the entire project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "=================================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=================================================="
    echo ""
}

print_success() {
    print_message "$GREEN" "✅ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠️  $1"
}

print_error() {
    print_message "$RED" "❌ $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=0
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        missing_tools=1
    else
        print_success "Docker is installed"
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        missing_tools=1
    else
        print_success "Docker Compose is installed"
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed"
        missing_tools=1
    else
        print_success "Node.js is installed ($(node --version))"
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed"
        missing_tools=1
    else
        print_success "npm is installed ($(npm --version))"
    fi
    
    if [ $missing_tools -eq 1 ]; then
        print_error "Please install missing prerequisites and try again"
        exit 1
    fi
}

# Check if .env files exist
check_env_files() {
    print_header "Checking Environment Files"
    
    local missing_env=0
    local env_files=(
        "airflow/.env"
        "backend/.env"
        "kafka/.env"
        "mlflow/.env"
    )
    
    for env_file in "${env_files[@]}"; do
        if [ ! -f "$env_file" ]; then
            print_warning "Missing: $env_file"
            missing_env=1
        else
            print_success "Found: $env_file"
        fi
    done
    
    if [ $missing_env -eq 1 ]; then
        print_warning "Some .env files are missing"
        echo ""
        echo "Please create the missing .env files using templates from ENV_TEMPLATES.md"
        echo "Example:"
        echo "  cd airflow && touch .env"
        echo "  # Then copy content from ENV_TEMPLATES.md"
        echo ""
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create Docker network
create_network() {
    print_header "Creating Docker Network"
    
    if docker network inspect net >/dev/null 2>&1; then
        print_success "Network 'net' already exists"
    else
        docker network create net
        print_success "Network 'net' created"
    fi
}

# Build Airflow image
build_airflow() {
    print_header "Building Airflow Image"
    
    cd airflow
    if docker build . --tag sentiman_airflow:0.1; then
        print_success "Airflow image built successfully"
    else
        print_error "Failed to build Airflow image"
        exit 1
    fi
    cd ..
}

# Start infrastructure services
start_infrastructure() {
    print_header "Starting Infrastructure Services (MongoDB, Kafka, MLflow)"
    
    docker-compose -f docker-compose.root.yaml up -d mongodb zookeeper kafka mlflow-postgres minio minio-setup mlflow
    
    print_message "$YELLOW" "Waiting for services to be healthy..."
    sleep 10
    
    print_success "Infrastructure services started"
}

# Initialize and start Airflow
start_airflow() {
    print_header "Initializing and Starting Airflow"
    
    cd airflow
    
    print_message "$YELLOW" "Initializing Airflow database..."
    docker-compose up airflow-init
    
    print_message "$YELLOW" "Starting Airflow services..."
    docker-compose up -d
    
    print_success "Airflow started"
    cd ..
}

# Start backend services
start_backend() {
    print_header "Starting Backend Services"
    
    docker-compose -f docker-compose.root.yaml up -d backend-consumer backend-api
    
    print_success "Backend services started"
}

# Install frontend dependencies
setup_frontend() {
    print_header "Setting Up Frontend"
    
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_message "$YELLOW" "Installing frontend dependencies..."
        npm install
        print_success "Frontend dependencies installed"
    else
        print_success "Frontend dependencies already installed"
    fi
    cd ..
}

# Display service status
show_status() {
    print_header "Service Status"
    
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep sentiman || true
    echo ""
}

# Display access information
show_access_info() {
    print_header "Access Information"
    
    echo ""
    print_message "$GREEN" "🌐 Frontend:       http://localhost:3000"
    print_message "$GREEN" "🔧 Backend API:    http://localhost:8000"
    print_message "$GREEN" "🔄 Airflow:        http://localhost:8080 (admin/airflow)"
    print_message "$GREEN" "📊 MLflow:         http://localhost:5001"
    print_message "$GREEN" "💾 MinIO Console:  http://localhost:9001"
    echo ""
    
    print_warning "To start the frontend, run:"
    echo "  cd frontend && npm run dev"
    echo ""
}

# Display next steps
show_next_steps() {
    print_header "Next Steps"
    
    echo "1. Configure your API keys in .env files (see ENV_TEMPLATES.md)"
    echo "2. Start the frontend:"
    echo "   cd frontend && npm run dev"
    echo ""
    echo "3. Access the services:"
    echo "   - Frontend:  http://localhost:3000"
    echo "   - Backend:   http://localhost:8000"
    echo "   - Airflow:   http://localhost:8080"
    echo "   - MLflow:    http://localhost:5001"
    echo ""
    echo "4. Enable Airflow DAGs in the Airflow UI"
    echo ""
    echo "To stop all services, run:"
    echo "   ./quick-start.sh stop"
    echo ""
}

# Stop all services
stop_services() {
    print_header "Stopping All Services"
    
    print_message "$YELLOW" "Stopping Airflow..."
    cd airflow && docker-compose down && cd ..
    
    print_message "$YELLOW" "Stopping other services..."
    docker-compose -f docker-compose.root.yaml down
    
    print_success "All services stopped"
}

# View logs
view_logs() {
    print_header "Viewing Logs"
    
    echo "Which service logs do you want to view?"
    echo "1) Backend Consumer"
    echo "2) Backend API"
    echo "3) Airflow Scheduler"
    echo "4) Airflow Webserver"
    echo "5) Kafka"
    echo "6) All services"
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1) docker logs -f sentiman_consumer ;;
        2) docker logs -f sentiman_api ;;
        3) docker logs -f sentiman-airflow-scheduler ;;
        4) docker logs -f sentiman-airflow-webserver ;;
        5) docker logs -f sentiman_kafka ;;
        6) docker-compose -f docker-compose.root.yaml logs -f ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Main menu
show_menu() {
    print_header "Sentiment Analysis - Quick Start Menu"
    
    echo "1) Full Setup - Start all services"
    echo "2) Stop all services"
    echo "3) View service status"
    echo "4) View logs"
    echo "5) Restart services"
    echo "6) Exit"
    echo ""
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1)
            check_prerequisites
            check_env_files
            create_network
            build_airflow
            start_infrastructure
            start_airflow
            start_backend
            setup_frontend
            show_status
            show_access_info
            show_next_steps
            ;;
        2)
            stop_services
            ;;
        3)
            show_status
            show_access_info
            ;;
        4)
            view_logs
            ;;
        5)
            stop_services
            sleep 2
            start_infrastructure
            start_airflow
            start_backend
            show_status
            ;;
        6)
            print_message "$GREEN" "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_menu
else
    case "$1" in
        start)
            check_prerequisites
            check_env_files
            create_network
            build_airflow
            start_infrastructure
            start_airflow
            start_backend
            setup_frontend
            show_status
            show_access_info
            show_next_steps
            ;;
        stop)
            stop_services
            ;;
        status)
            show_status
            show_access_info
            ;;
        logs)
            view_logs
            ;;
        restart)
            stop_services
            sleep 2
            start_infrastructure
            start_airflow
            start_backend
            show_status
            ;;
        help|--help|-h)
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  start     - Start all services"
            echo "  stop      - Stop all services"
            echo "  status    - Show service status"
            echo "  logs      - View service logs"
            echo "  restart   - Restart all services"
            echo "  help      - Show this help message"
            echo ""
            echo "If no command is provided, interactive menu will be shown."
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
fi

