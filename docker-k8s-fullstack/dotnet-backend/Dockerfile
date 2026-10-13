# ======== Stage 1: build ========
# SDK image periyadhu (~800MB) — compile panna mattum use pannrom
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# csproj mattum mudhalla → restore layer cache aagum (package maaralana re-download illa)
COPY TaskApi.csproj .
RUN dotnet restore

COPY . .
RUN dotnet publish -c Release -o /app/publish --no-restore

# ======== Stage 2: runtime ========
# ASP.NET runtime mattum (~230MB). SDK, source code final image-la varadhu.
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

# .NET 8+ images-la `app` user already irukku (UID 1654), default port 8080
USER $APP_UID
EXPOSE 8080

# ENTRYPOINT fixed; `docker run image --init-db` nu kudutha adhu argument-a add aagum
ENTRYPOINT ["dotnet", "TaskApi.dll"]
