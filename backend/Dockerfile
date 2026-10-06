# Stage 1: Build & Publish
FROM mcr.microsoft.com/dotnet/sdk:10.0-preview AS build
WORKDIR /src

# Copy project files for caching dependency restore layer
COPY ["P07.Api/P07.Api.csproj", "P07.Api/"]
COPY ["P07.Application/P07.Application.csproj", "P07.Application/"]
COPY ["P07.Domain/P07.Domain.csproj", "P07.Domain/"]
COPY ["P07.Infrastructure/P07.Infrastructure.csproj", "P07.Infrastructure/"]

RUN dotnet restore "P07.Api/P07.Api.csproj"

# Copy full source and publish
COPY . .
WORKDIR "/src/P07.Api"
RUN dotnet publish "P07.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Stage 2: Runtime Image
FROM mcr.microsoft.com/dotnet/aspnet:10.0-preview AS runtime
WORKDIR /app

# Ensure non-root execution
USER $APP_UID

COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "P07.Api.dll"]
