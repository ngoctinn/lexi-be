# Lexi Backend Documentation

## 📚 Documentation Index

### Quick Start
- **[QUICKSTART.md](./QUICKSTART.md)** - Deploy trong 5 phút

### Deployment
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Chi tiết deployment với AgentCore Memory

### Features
- **[TURN_ANALYSIS_FEATURE.md](./TURN_ANALYSIS_FEATURE.md)** - Turn-by-turn analysis architecture và usage
- **[AGENTCORE_MEMORY_SETUP.md](./AGENTCORE_MEMORY_SETUP.md)** - AgentCore Memory setup và configuration

### Implementation
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Tóm tắt implementation turn analysis feature

## 🚀 Getting Started

1. Read [QUICKSTART.md](./QUICKSTART.md) for fast deployment
2. Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed steps
3. Review [TURN_ANALYSIS_FEATURE.md](./TURN_ANALYSIS_FEATURE.md) to understand the feature

## 📖 Main Documentation

- **[API_DOCUMENTATION.md](../API_DOCUMENTATION.md)** - Complete API reference (in root)
- **[README.md](../README.md)** - Project overview (in root)

## 🎯 Feature Overview

### Turn-by-Turn Analysis
- **What**: On-demand formative assessment for learner conversations
- **How**: WebSocket action `ANALYZE_TURN`
- **Output**: Bilingual markdown (Vietnamese + English)
- **Sections**: Strengths ✅, Mistakes ⚠️, Improvements 💡, Assessment 🎯

### AgentCore Memory
- **What**: Long-term memory for AI to remember learner patterns
- **Retention**: 365 days
- **Strategies**: Semantic (mistake patterns) + Summarization (session summaries)
- **Cost**: ~$0.40/month for 1000 users

## 🏗️ Architecture

```
User → WebSocket → analyze_turn() → ConversationAnalyzer (LLM)
                                           ↓
                                    LearnerMemoryClient
                                           ↓
                                  AgentCore Memory (365 days)
                                           ↓
                              ConversationOrchestrator (retrieves context)
                                           ↓
                                  Personalized AI Response
```

## 📝 Files Structure

```
docs/
├── README.md                      # This file
├── QUICKSTART.md                  # 5-minute deployment
├── DEPLOYMENT_GUIDE.md            # Detailed deployment
├── TURN_ANALYSIS_FEATURE.md       # Feature documentation
├── AGENTCORE_MEMORY_SETUP.md      # Memory setup guide
└── IMPLEMENTATION_SUMMARY.md      # Implementation details
```

## 🔗 Related Files

### Core Implementation
- `src/domain/services/conversation_analyzer.py` - LLM-based analysis
- `src/infrastructure/services/memory_client.py` - Memory operations
- `src/infrastructure/handlers/websocket_handler.py` - WebSocket handler

### Configuration
- `template.yaml` - CloudFormation template with Memory resource
- `scripts/create_agentcore_memory.py` - Manual memory creation script

## 💡 Tips

- Start with QUICKSTART.md for fastest path to deployment
- Memory is optional - system works without it
- Use DEPLOYMENT_GUIDE.md for troubleshooting
- Check IMPLEMENTATION_SUMMARY.md for technical details

## 🆘 Support

For issues:
1. Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) troubleshooting section
2. Review CloudWatch logs
3. Check AWS Bedrock AgentCore documentation
