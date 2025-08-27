## Service 1 (User Management Service) - Port 8000
- **Purpose**: Manages user data and provides CRUD operations
- **Features**:
  - Create, read, and delete users
  - Store user information (name, email, age)
  - Automatically sends user data to Service 2 for processing
  - Retrieves processed data from Service 2

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /users` - Create a new user
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get specific user
- `GET /users/{user_id}/processed` - Get user with processed data from Service 2
- `DELETE /users/{user_id}` - Delete user

## Interactive API Documentation

http://localhost:8000/docs