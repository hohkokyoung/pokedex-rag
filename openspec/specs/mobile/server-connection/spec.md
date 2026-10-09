# mobile/server-connection Specification

## Purpose

Defines how the mobile app finds the pokérag backend on the home network, checks it,
and behaves when it can't reach it, without hosting, accounts or TLS.

## Requirements


### Requirement: Configurable server address
The app SHALL use a server address that defaults to a build-time value and that the user can change in settings. A changed address SHALL be saved on the device and used on the next launch.

#### Scenario: Simulator default
- **WHEN** the app is built for the iOS Simulator without an override
- **THEN** it uses `http://localhost:8001`

#### Scenario: Phone on Wi-Fi
- **WHEN** the user sets the address to `http://192.168.0.244:8001` and relaunches the app
- **THEN** the app loads the Pokédex from that address

### Requirement: The address is checked before it is saved
Saving an address SHALL first check the backend's health endpoint. An address that doesn't answer as a pokérag backend SHALL NOT be saved, and the user SHALL see why.

#### Scenario: Wrong address
- **WHEN** the user enters an address where nothing answers
- **THEN** the setting is not saved and the app says it couldn't reach a pokérag server there

#### Scenario: Right address
- **WHEN** the user enters an address whose `/health` answers `{"status": "ok"}`
- **THEN** the address is saved and the list reloads from it

### Requirement: Unreachable server state
When the backend can't be reached, the app SHALL show a clear "can't reach the server" state naming the address. It SHALL offer a retry and a way to change the address, and SHALL NOT show an empty list as if there were no Pokémon.

#### Scenario: Backend stopped
- **WHEN** the backend is down and the user opens the app
- **THEN** the app shows the can't-reach state with the current address, Retry and Change address

#### Scenario: Recovery
- **WHEN** the backend comes back and the user taps Retry
- **THEN** the list loads

### Requirement: Plain HTTP on the local network is allowed
The iOS build SHALL allow HTTP to local-network addresses and SHALL explain its local-network permission request. The Android build SHALL allow cleartext HTTP. No other transport rules SHALL be relaxed.

#### Scenario: iOS device on the LAN
- **WHEN** the app first contacts a LAN address on an iPhone
- **THEN** iOS shows the local-network permission with the app's reason, and after it is allowed requests succeed over HTTP

#### Scenario: Android emulator
- **WHEN** the app runs on the Android emulator against the host's backend
- **THEN** HTTP requests succeed
