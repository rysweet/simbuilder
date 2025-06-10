# Testing Requirements

## Pre-Commit Requirements

- All code must always pass linting, formatting, unit tests, and integration tests before being
  committed
- Always use `uv run` to ensure correct virtual environment when running checks and tests
- Never skip tests under any circumstances
- Never disable checks or tests
- Never artificially cause checks or tests to exit successfully when they are not actually being
  evaluated

## Test Development Standards

- Write tests for each component
- Write unit tests for individual functions and methods
- When creating shared resources or code for unit tests ensure those resources can be safely
  accessed in parallel
- When unit test failures occur, we do not move on, instead we stop, think carefully about the code
  being tested, consider carefully the necessary setup conditions, and then carefully construct the
  test to ensure it is validating the functionality of the code. Then we either fix the code being
  tested or fix the test
- Write integration tests for module interactions
- Ensure public interfaces are well-tested
- Use dependency injection to make components testable
- Maintain test coverage during refactoring
- Integration tests should not use mocks for the components they are testing
- Do not mark tests as skipped or expected to fail
- Do not disable tests or cause tests to exit true when they would not otherwise succeed
- Always ensure that all tests and CI pass before moving on to the next milestone

## Test Execution Workflow

- Always run unit tests before integration tests
- If unit tests fail, fix the failure before continuing to integration tests
- When running integration tests, stop immediately upon first failure
- When a test fails, reason carefully about the failure, then fix either the test, the setup, or the
  code being tested
- Continue with remaining tests only after the failed test is passing
- Never proceed with development while any tests are failing

## Integration Test Requirements

- All integration tests must be self-contained
- Integration tests can have dependencies on code, but not on runtime state
- Integration tests must manage all their own setup and cleanup every time
- Integration tests must be runnable independently without any preconditions
- Never use mocks in integration tests for the components being tested

## Test Organization

- Organize tests in a parallel structure to the codebase
- Use descriptive names for test files and classes
- Group related functionality in dedicated test modules
- Use clear and consistent naming for test methods

## Test Quality Assurance

- Do not move on to the next milestone until the current milestone is complete with all tests for
  all milestones passing
- Do not move on to the next milestone while there are test failures anywhere in the project
- When there are test failures, think carefully about the intent of the code being tested, think
  carefully about the conditions required to test, setup the test conditions, and then think
  carefully about how to either fix the test or fix the code being tested
