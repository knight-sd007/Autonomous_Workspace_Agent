# ==============================================================================
# Multi-Stage Production Dockerfile for Autonomous Workspace Agent (P07)
# Target: Linux amd64 / arm64 (OCI Ampere A1 & x86_64 Compatible)
# Public application endpoint: container :8080 -> host 127.0.0.1:8007
# The ASP.NET Core API also serves the built SvelteKit frontend.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build SvelteKit frontend
# ------------------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder

WORKDIR /src/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run check && npm run build


# ------------------------------------------------------------------------------
# Stage 2: Build ASP.NET Core backend
# ------------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:10.0-preview AS build

WORKDIR /src

# Copy project files first for dependency-restore layer caching.
COPY backend/P07.Api/P07.Api.csproj backend/P07.Api/
COPY backend/P07.Application/P07.Application.csproj backend/P07.Application/
COPY backend/P07.Domain/P07.Domain.csproj backend/P07.Domain/
COPY backend/P07.Infrastructure/P07.Infrastructure.csproj backend/P07.Infrastructure/

RUN dotnet restore backend/P07.Api/P07.Api.csproj

# Copy backend source.
COPY backend/ backend/

# Publish the SvelteKit static output through ASP.NET Core wwwroot.
COPY --from=frontend-builder /src/frontend/build/ backend/P07.Api/wwwroot/

WORKDIR /src/backend/P07.Api
RUN dotnet publish P07.Api.csproj -c Release -o /app/publish /p:UseAppHost=false


# ------------------------------------------------------------------------------
# Stage 3: Minimal non-root ASP.NET Core runtime
# ------------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/aspnet:10.0-preview AS runtime

WORKDIR /app

# Ensure non-root execution.
USER $APP_UID

COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3     CMD wget -qO- http://127.0.0.1:8080/health || exit 1

ENTRYPOINT ["dotnet", "P07.Api.dll"]
