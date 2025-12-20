#!/bin/bash
# Monitor both NLP and LLM consumers

echo "================================================================================"
echo "📊 CONSUMER MONITORING SCRIPT"
echo "================================================================================"
echo ""

# Check container status
echo "🔍 Container Status:"
docker ps --filter "name=consumer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Function to count processed articles
count_processed() {
    local container=$1
    local pattern=$2
    local count=$(docker logs $container 2>&1 | grep "$pattern" | wc -l | tr -d ' ')
    echo $count
}

echo "📈 Processing Statistics:"
echo "   NLP Consumer (extracted):  $(count_processed sentiman_nlp_consumer 'NLP features extracted') articles"
echo "   LLM Consumer (inferred):   $(count_processed sentiman_backend_consumerdock 'INFERED_POLICY') articles"
echo ""

echo "================================================================================"
echo "📝 RECENT NLP EXTRACTION LOGS (last 30 lines):"
echo "================================================================================"
docker logs sentiman_nlp_consumer --tail 30 2>&1 | grep -E "Processing article|NLP features extracted|Features:|⚠️" | tail -15
echo ""

echo "================================================================================"
echo "🧠 RECENT LLM GENERATION LOGS (last 30 lines):"
echo "================================================================================"
docker logs sentiman_backend_consumerdock --tail 30 2>&1 | grep -E "Processing|INFERED_POLICY|classification|⚠️" | tail -15
echo ""

echo "================================================================================"
echo "💡 TIP: For real-time monitoring, use:"
echo "   docker logs -f sentiman_nlp_consumer"
echo "   docker logs -f sentiman_backend_consumerdock"
echo "================================================================================"


