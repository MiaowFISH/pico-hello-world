---
description: "Task list for Pico2W tracked arm car control system implementation"
---

# Tasks: Pico2W 履带机械臂小车控制系统

**Input**: Design documents from `/specs/001-pico-tracked-arm-car/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are NOT requested in this specification. Focus on implementation and manual integration testing.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses:
- **Backend**: `app/` (deployed to Pico root)
- **Frontend**: `frontend/src/` (builds to `static/`)
- **Libraries**: `lib/` (CircuitPython dependencies)
- **Tools**: `tools/` (deployment scripts)

---

## Phase 1: Setup (Shared Infrastructure) ✅

**Purpose**: Project initialization and basic structure

- [X] T001 Verify CircuitPython libraries in lib/ directory (adafruit_httpserver, adafruit_pca9685, adafruit_motor, adafruit_register)
- [X] T002 [P] Create app/config.json with WiFi credentials and hardware configuration
- [X] T003 [P] Initialize frontend project with package.json dependencies (React 19, Vite 5, react-use-websocket, zustand, TypeScript)

---

## Phase 2: Foundational (Blocking Prerequisites) ✅

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create app/config_loader.py - Load and validate config.json with schema validation
- [X] T005 [P] Create app/main.py - Entry point with asyncio event loop and WiFi connection
- [X] T006 [P] Create app/http_handler.py - HTTP routes for static files, /api/status, /api/config, /api/health
- [X] T007 Create app/websocket_handler.py - WebSocket endpoint /ws with single connection management and command dispatcher
- [X] T008 [P] Implement safety timeout mechanism in app/main.py (2-second auto-stop for motors)
- [X] T009 Create frontend/src/hooks/useDeviceWebSocket.ts - WebSocket connection hook with reconnection logic
- [X] T010 [P] Create frontend/src/hooks/useDeviceStore.ts - Zustand state store for device status and control state
- [X] T011 [P] Create frontend/src/components/ConnectionStatus.tsx - Display WiFi and WebSocket connection status
- [X] T012 [P] Create frontend/src/App.tsx - Main app component layout with mobile-first responsive design

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 履带控制与移动 (Priority: P1) 🎯 MVP ✅

**Goal**: User can control tracked vehicle movement (forward, backward, left, right, stop) through browser interface with press-and-hold buttons. This delivers a remotely controllable tracked vehicle.

**Independent Test**: Open browser to Pico IP, click direction buttons, verify vehicle moves in expected direction. Test safety timeout by holding button and disconnecting WiFi - vehicle should stop within 2 seconds.

### Implementation for User Story 1

- [X] T013 [P] [US1] Create app/motor_controller.py - TB6612FNG driver for track motors with differential steering logic
- [X] T014 [US1] Integrate motor_controller into app/websocket_handler.py - Handle "track" action messages with speed presets
- [X] T015 [US1] Add track control commands to app/websocket_handler.py - Implement forward/backward/left/right/stop commands
- [X] T016 [US1] Implement safety timeout for tracks in app/main.py - Auto-stop if no command for 2 seconds
- [X] T017 [P] [US1] Create frontend/src/hooks/useContinuousCommand.ts - Press-and-hold hook that sends commands every 100ms
- [X] T018 [P] [US1] Create frontend/src/components/TrackControls.tsx - D-pad style direction buttons (forward/back/left/right/stop)
- [X] T019 [P] [US1] Create frontend/src/components/SpeedSelector.tsx - Speed preset selector (slow/medium/fast)
- [X] T020 [US1] Integrate TrackControls and SpeedSelector into App.tsx with press-and-hold logic
- [X] T021 [US1] Add track state to useDeviceStore and connect to WebSocket messages
- [X] T022 [US1] Add track control logging to app/main.py for debugging

**Checkpoint**: At this point, User Story 1 should be fully functional - a complete remotely controllable tracked vehicle

---

## Phase 4: User Story 2 - 机械臂控制 (Priority: P2) ✅

**Goal**: User can control 3-joint mechanical arm (joint 1, joint 2, gripper) through angle sliders, with reset function. This adds object manipulation capability to the vehicle.

**Independent Test**: Access control interface, drag servo sliders to different angles, observe arm movement. Click reset button to verify arm returns to initial position. Test that angles are clamped to configured safe ranges.

### Implementation for User Story 2

- [X] T023 [P] [US2] Create app/servo_controller.py - PCA9685 driver for 3 servos with angle clamping to configured limits
- [X] T024 [US2] Integrate servo_controller into app/websocket_handler.py - Handle "servo", "servo_batch", "servo_reset" actions
- [X] T025 [US2] Add servo angle validation and clamping in app/websocket_handler.py with error responses
- [X] T026 [P] [US2] Create frontend/src/components/ServoSliders.tsx - Three angle sliders (joint1, joint2, gripper) with current angle display
- [X] T027 [US2] Add servo reset button to ServoSliders component that sends servo_reset command
- [X] T028 [US2] Add servo state to useDeviceStore and connect to WebSocket messages
- [X] T029 [US2] Integrate ServoSliders into App.tsx
- [X] T030 [US2] Update /api/config endpoint in app/http_handler.py to return servo configurations (min/max angles)
- [X] T031 [US2] Load servo constraints from config on frontend mount and apply to slider ranges

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - vehicle can move and manipulate objects

---

## Phase 5: User Story 3 - 底盘旋转控制 (Priority: P3) ✅

**Goal**: User can rotate the upper platform relative to the track base using CW/CCW buttons. This expands the working range of the mechanical arm without moving the whole vehicle.

**Independent Test**: Click rotation buttons, observe upper platform rotating relative to base. Verify press-and-hold behavior and auto-stop on release. Verify motor sleeps after 5 seconds of inactivity.

### Implementation for User Story 3

- [X] T032 [P] [US3] Create app/base_rotation_controller.py - DRV8837 driver with CW/CCW/stop control and sleep mode management
- [X] T033 [US3] Integrate base_rotation_controller into app/websocket_handler.py - Handle "base" action with direction and speed
- [X] T034 [US3] Implement idle sleep timer in app/base_rotation_controller.py - Sleep after 5 seconds without commands
- [X] T035 [US3] Add safety timeout for base rotation in app/main.py - Auto-stop if no command for 2 seconds
- [X] T036 [P] [US3] Create frontend/src/components/BaseRotation.tsx - CW/CCW buttons with press-and-hold support
- [X] T037 [US3] Add base rotation state to useDeviceStore and connect to WebSocket messages
- [X] T038 [US3] Integrate BaseRotation component into App.tsx
- [X] T039 [US3] Add base rotation status to /api/status endpoint in app/http_handler.py

**Checkpoint**: All primary user stories should now be independently functional - complete vehicle control system

---

## Phase 6: User Story 4 - 系统状态监控 (Priority: P4) ✅

**Goal**: User can view real-time system status including WiFi connection, component states, and current configuration on the control interface.

**Independent Test**: Access control interface, verify status panel displays WiFi signal, IP address, current servo angles, and motor states. Disconnect WiFi and verify error display.

### Implementation for User Story 4

- [X] T040 [P] [US4] Implement /api/status endpoint in app/http_handler.py - Return complete DeviceStatus with WiFi, servos, tracks, base_rotation
- [X] T041 [P] [US4] Add WiFi status collection in app/main.py (SSID, IP, RSSI, connected status)
- [X] T042 [P] [US4] Create frontend/src/components/StatusPanel.tsx - Display WiFi status, servo angles, motor states, errors
- [X] T043 [US4] Integrate StatusPanel into App.tsx with periodic status polling (every 2 seconds)
- [X] T044 [US4] Add error message handling in useDeviceStore for WebSocket error responses
- [X] T045 [US4] Display clamped angle warnings in StatusPanel when servo angles are limited by safety ranges

**Checkpoint**: Full system with status monitoring - users can troubleshoot and monitor all components

---

## Phase 7: User Story 5 - 配置管理 (Priority: P5) ✅

**Goal**: Administrator can modify system parameters through config.json (WiFi, servo limits, motor pins) without code changes. System loads configuration on startup.

**Independent Test**: Modify WiFi SSID in config.json, reboot Pico, verify connection to new network. Change servo min/max angles, reboot, verify angles are enforced in control interface.

### Implementation for User Story 5

- [X] T046 [P] [US5] Implement JSON schema validation in app/config_loader.py for all config sections
- [X] T047 [P] [US5] Add default configuration fallback in app/config_loader.py when config.json is missing or invalid
- [X] T048 [US5] Add configuration error logging in app/main.py with detailed error messages
- [X] T049 [US5] Update app/http_handler.py /api/config to return speed_presets and safety timeout configuration
- [X] T050 [US5] Document config.json schema in app/config.json with inline comments (as JSON doesn't support comments, create config.example.json)
- [X] T051 [US5] Verify all hardware controllers (servo, motor, base_rotation) read parameters from loaded config

**Checkpoint**: Configuration-driven system - hardware changes don't require code modifications

---

## Phase 8: Polish & Cross-Cutting Concerns ✅

**Purpose**: Improvements that affect multiple user stories

- [X] T052 [P] Add USB serial logging throughout app/ modules with log levels (INFO, WARNING, ERROR) - Implements FR-022: startup status, error info, key operations
- [X] T053 [P] Implement proper error handling for I2C communication failures in servo_controller.py
- [X] T054 [P] Add CORS headers to http_handler.py for development mode (optional, based on deployment needs)
- [X] T055 Frontend build configuration in frontend/vite.config.ts - Optimize bundle, configure proxy for development
- [X] T056 Add mobile touch optimizations to frontend controls - touch-action: none, vibration feedback
- [X] T057 [P] Create frontend/src/styles/main.css with mobile-first responsive design (min 320px width support)
- [X] T058 Performance testing - Verify WebSocket latency <50ms, UI response <100ms
- [X] T059 [P] Update README.md with deployment instructions and architecture diagram
- [X] T060 Validate quickstart.md by following all setup steps on fresh Pico device
- [X] T061 Add error recovery mechanisms - Handle PCA9685 initialization failures, motor driver errors
- [X] T062 Memory optimization - Verify system runs with <180KB heap usage after WiFi connection

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ Independent
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent, no integration with US1 needed ✅ Independent
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent, no integration with US1/US2 needed ✅ Independent
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Reads state from all stories but doesn't block them ✅ Independent
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Configuration affects all stories but can be validated independently ✅ Independent

### Within Each User Story

All user stories follow this pattern:
1. Backend controller implementation (models/hardware drivers)
2. WebSocket/HTTP integration (message handling)
3. Frontend component creation (UI controls)
4. State management integration (Zustand store)
5. Main app integration (wire components together)
6. Logging and validation

### Parallel Opportunities

**Phase 1 - Setup**: All 3 tasks can run in parallel
- T001: Library verification
- T002: Config file creation
- T003: Frontend project initialization

**Phase 2 - Foundational**: 7 tasks can run in parallel
- T004: config_loader.py
- T005: main.py skeleton
- T006: http_handler.py
- T009: useDeviceWebSocket.ts
- T010: useDeviceStore.ts
- T011: ConnectionStatus.tsx
- T012: App.tsx layout

**Phase 3 - User Story 1**: 4 tasks can run in parallel
- T013: motor_controller.py
- T017: useContinuousCommand.ts
- T018: TrackControls.tsx
- T019: SpeedSelector.tsx

**Phase 4 - User Story 2**: 2 tasks can run in parallel
- T023: servo_controller.py
- T026: ServoSliders.tsx

**Phase 5 - User Story 3**: 2 tasks can run in parallel
- T032: base_rotation_controller.py
- T036: BaseRotation.tsx

**Phase 6 - User Story 4**: 3 tasks can run in parallel
- T040: /api/status implementation
- T041: WiFi status collection
- T042: StatusPanel.tsx

**Phase 7 - User Story 5**: 3 tasks can run in parallel
- T046: Schema validation
- T047: Default config fallback
- T050: Config documentation

**Phase 8 - Polish**: 6 tasks can run in parallel
- T052: Serial logging
- T053: Error handling
- T054: CORS headers
- T057: CSS styling
- T059: Documentation
- T061: Error recovery

**User Stories in Parallel**: Once Phase 2 completes, all 5 user stories can be developed in parallel by different team members since they are independent.

---

## Parallel Example: User Story 1 (Tracked Movement)

```bash
# Launch parallel backend and frontend tasks together:
Task T013: "Create app/motor_controller.py - TB6612FNG driver"
Task T017: "Create frontend/src/hooks/useContinuousCommand.ts"
Task T018: "Create frontend/src/components/TrackControls.tsx"
Task T019: "Create frontend/src/components/SpeedSelector.tsx"

# Then integration tasks in sequence:
Task T014: "Integrate motor_controller into websocket_handler"
Task T015: "Add track control commands"
Task T016: "Implement safety timeout"
Task T020: "Integrate TrackControls into App.tsx"
Task T021: "Add track state to store"
Task T022: "Add logging"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - Recommended ✅

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (8 tasks) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (10 tasks)
4. **STOP and VALIDATE**: Test tracked vehicle movement independently
5. Deploy/demo working vehicle ✅ **First deliverable: Remote-controlled tracked vehicle**

This gives you a fully functional remote-controlled vehicle in ~21 tasks.

### Incremental Delivery (Add features progressively)

1. Complete Setup + Foundational → Foundation ready (11 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo MVP! ✅ (21 total tasks)
3. Add User Story 2 → Test independently → Deploy/Demo with arm control ✅ (30 total tasks)
4. Add User Story 3 → Test independently → Deploy/Demo with rotation ✅ (38 total tasks)
5. Add User Story 4 → Test independently → Deploy/Demo with monitoring ✅ (44 total tasks)
6. Add User Story 5 → Test independently → Deploy/Demo with config management ✅ (50 total tasks)
7. Add Polish → Production-ready system ✅ (62 total tasks)

Each story adds value without breaking previous stories.

### Parallel Team Strategy (Maximum speed)

With 5 developers after completing Setup + Foundational (11 tasks):

1. **Team completes Phase 1 + Phase 2 together** (11 tasks) → Foundation ready
2. **Once Foundational is done, split into parallel tracks**:
   - Developer A: User Story 1 - Tracked movement (10 tasks)
   - Developer B: User Story 2 - Arm control (9 tasks)
   - Developer C: User Story 3 - Base rotation (8 tasks)
   - Developer D: User Story 4 - Status monitoring (6 tasks)
   - Developer E: User Story 5 - Configuration (6 tasks)
3. All stories complete independently → Integration testing
4. Team tackles Polish tasks together (11 tasks)

**Timeline**: With 5 developers, core features (US1-5) can be done in parallel after foundation.

---

## Task Summary

**Total Tasks**: 62

**By Phase**:
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 8 tasks ⚠️ BLOCKING
- Phase 3 (User Story 1 - P1): 10 tasks 🎯 MVP
- Phase 4 (User Story 2 - P2): 9 tasks
- Phase 5 (User Story 3 - P3): 8 tasks
- Phase 6 (User Story 4 - P4): 6 tasks
- Phase 7 (User Story 5 - P5): 6 tasks
- Phase 8 (Polish): 11 tasks

**By User Story**:
- User Story 1 (履带控制): 10 tasks
- User Story 2 (机械臂控制): 9 tasks
- User Story 3 (底盘旋转): 8 tasks
- User Story 4 (状态监控): 6 tasks
- User Story 5 (配置管理): 6 tasks
- Infrastructure (Setup + Foundational + Polish): 22 tasks

**Parallelizable Tasks**: 25 tasks marked with [P] can run in parallel with other tasks

**MVP Scope** (User Story 1 only): 21 tasks (Setup + Foundational + US1)
- Delivers: Remote-controlled tracked vehicle with safety timeout
- Estimated effort: 2-3 days for experienced developer
- Value: Complete working product, ready for field testing

**Independent Test Criteria**:
- ✅ US1: Control vehicle movement via browser, test safety timeout
- ✅ US2: Control arm angles via sliders, test reset function
- ✅ US3: Rotate base with buttons, test sleep mode
- ✅ US4: View real-time status on interface
- ✅ US5: Modify config file and verify changes take effect

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story is independently completable and testable** - this is critical for incremental delivery
- **No tests included**: Spec does not request automated tests, focus on implementation and manual testing per quickstart.md
- **Commit strategy**: Commit after each task or logical group for easy rollback
- **Validation points**: Stop at checkpoints to validate story independently before proceeding
- **File paths are absolute from repository root**: Adjust if your project structure differs
- **CircuitPython constraints**: ~180KB heap, single WebSocket connection, 2.4GHz WiFi only
- **Frontend mobile-first**: Minimum 320px width support, touch-optimized controls
