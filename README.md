# lexi-be

Backend serverless application for Lexi - English learning platform with AI-powered speaking practice.

## Architecture

This project uses AWS Serverless Application Model (SAM) with:
- **Lambda Functions**: Python 3.12 runtime
- **API Gateway**: REST API with Cognito Authorizer
- **WebSocket API**: Real-time speaking sessions
- **DynamoDB**: NoSQL database for user data, sessions, scenarios
- **Cognito**: User authentication and authorization
- **Bedrock**: AI conversation generation
- **Polly**: Text-to-speech synthesis
- **Transcribe**: Speech-to-text conversion

## Documentation

- **[Authentication Flow](./AUTHENTICATION_FLOW.md)** - Complete auth architecture and best practices
- **[Auth Cleanup Summary](./AUTH_CLEANUP_SUMMARY.md)** - Recent auth improvements
- **[Conversation Architecture](./CONVERSATION_ARCHITECTURE.md)** - Speaking session design
- **[Documentation Index](./DOCUMENTATION_INDEX.md)** - All project documentation

## Quick Start

### Prerequisites

- SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.12 installed](https://www.python.org/downloads/)
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
- AWS CLI configured with credentials

### Deploy

```bash
sam build
sam deploy --guided
```

### Test Authentication

```bash
# Get Cognito token
python scripts/get_cognito_token.py

# Test API with token
TOKEN="<your-token>"
curl -X GET https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
lexi-be/
├── src/
│   ├── application/          # Use cases and DTOs
│   ├── domain/              # Business logic and entities
│   ├── infrastructure/      # AWS services, repositories, handlers
│   └── interfaces/          # Controllers, view models, mappers
├── config/                  # SAM module configs (auth, database)
├── scripts/                 # Testing and utility scripts
├── template.yaml           # Main SAM template
└── README.md
```

## Authentication

All REST API endpoints (except `/scenarios`) are protected by **AWS Cognito User Pool Authorizer**.

**Flow:**
1. Frontend signs in to Cognito → gets JWT token
2. Frontend calls API with `Authorization: Bearer <token>`
3. API Gateway validates JWT (cached, fast, secure)
4. Lambda receives validated user claims

See [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md) for details.

## Development

### Local Testing

```bash
# Start local API
sam local start-api

# Invoke function locally
sam local invoke FunctionName -e events/event.json
```

### Run Tests

```bash
pytest tests/
```

## Deployment

### First Time

```bash
sam build
sam deploy --guided
```

### Subsequent Deploys

```bash
sam build && sam deploy
```

## Environment Variables

Key environment variables (set in template.yaml):
- `LEXI_TABLE_NAME`: DynamoDB table name
- `COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `COGNITO_APP_CLIENT_ID`: Cognito App Client ID
- `SPEAKING_AUDIO_BUCKET_NAME`: S3 bucket for audio files

## API Endpoints

### Public
- `GET /scenarios` - List available speaking scenarios

### Authenticated (Cognito)
- `GET /profile` - Get user profile
- `PATCH /profile` - Update user profile
- `POST /onboarding/complete` - Complete onboarding
- `POST /sessions` - Create speaking session
- `GET /sessions` - List user sessions
- `GET /sessions/{id}` - Get session details
- `POST /vocabulary/translate` - Translate vocabulary

### Admin Only
- `GET /admin/users` - List all users
- `PATCH /admin/users/{id}` - Update user
- `GET /admin/scenarios` - List all scenarios
- `POST /admin/scenarios` - Create scenario

## WebSocket API

- `wss://<api-id>.execute-api.us-east-1.amazonaws.com/Prod`
- Routes: `$connect`, `$disconnect`, `$default`
- Auth: JWT token in query parameter `?token=<jwt>`

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [AWS Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)

## License

This project is licensed under the MIT License.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Use the SAM CLI to build and test locally

Build your application locally with the `sam build` command.

```bash
lexi-be$ sam build
```

The SAM CLI installs dependencies defined in `src/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

If you need container parity for a specific debugging session, you can still use `sam build --use-container`, but the default path for this project is local build.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
lexi-be$ sam local invoke HelloWorldFunction --event events/event.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
lexi-be$ sam local start-api
lexi-be$ curl http://localhost:3000/
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. The `Events` property on each function's definition includes the route and method for each path.

```yaml
Events:
  HelloWorld:
    Type: Api
    Properties:
      Path: /hello
      Method: get
```

## Add a resource to your application

The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
lexi-be$ sam logs -n HelloWorldFunction --stack-name "lexi-be" --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
lexi-be$ pip install -r tests/requirements.txt --user
# unit test
lexi-be$ python -m pytest tests/unit -v
# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
lexi-be$ AWS_SAM_STACK_NAME="lexi-be" python -m pytest tests/integration -v
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name "lexi-be"
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
