# Spring Ecommerce API

A REST API for an e-commerce platform built with Spring Boot. It handles user authentication, product catalog management, and order processing.

## Features

- User registration, login, logout, and token refresh using JWT
- Product CRUD operations and search
- Order creation and retrieval for authenticated users
- PostgreSQL persistence via Spring Data JPA
- Request validation and centralized exception handling

## Tech Stack

- Java with Spring Boot
- Spring Data JPA
- Spring Security with OAuth2 client support
- PostgreSQL
- Maven
- Lombok

## Project Structure

The application code lives under `api/`:

- `controller` - REST endpoints
- `service` - business logic
- `repository` - data access
- `model` - JPA entities
- `dto` - request and response objects
- `exceptions` - custom exceptions and global exception handling

## API Endpoints

### Auth
- `POST /api/auth/register` - register a new user
- `POST /api/auth/login` - log in and receive tokens
- `POST /api/auth/refresh` - refresh an access token
- `POST /api/auth/logout` - log out and invalidate a refresh token

### Products
- `GET /api/products` - list all products
- `GET /api/products/{productId}` - get a product by id
- `POST /api/products` - add a product
- `PUT /api/products/{productId}` - update a product
- `DELETE /api/products/{productId}` - delete a product
- `GET /api/products/search?search=` - search products

### Orders
- `POST /api/orders` - create an order
- `GET /api/orders` - get the authenticated user's orders

## Getting Started

### Prerequisites

- Java 17 or later
- Maven
- PostgreSQL

### Setup

1. Clone the repository
2. Create a `.env` file in `api/` with your database credentials
3. Run the application:

   ```
   cd api
   ./mvnw spring-boot:run
   ```

The API will start on `http://localhost:8080`.

## Running Tests

```
cd api
./mvnw test
```
