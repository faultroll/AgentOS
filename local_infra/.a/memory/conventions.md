# .a Code Conventions

> Project-specific coding conventions. AI agents should follow these.

## General

- Follow existing code style in the project
- Use 4 spaces for indentation (no tabs)
- Keep lines under 120 characters
- Add docstrings to public functions/classes

## Git Commits

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Keep subject line under 72 characters
- Reference issue numbers when applicable

## File Naming

- Use kebab-case: `my-file-name.ts`
- Use PascalCase for components: `MyComponent.tsx`
- Use SCREAMING_SNAKE_CASE for constants: `MAX_RETRIES`

## TypeScript/JavaScript

- Use explicit types for function parameters and return values
- Prefer `const` over `let`, avoid `var`
- Use `async/await` over raw promises
- No `any` type without explanation

## Python

- Follow PEP 8
- Use type hints
- Docstrings for modules and public functions

## Testing

- Name test files: `*.test.ts` or `*_test.py`
- Use descriptive test names: `should_return_user_when_valid_id_provided`
- Keep tests independent (no shared state)

## Documentation

- Update README when changing features
- Document breaking changes
- Keep CHANGELOG up to date

## Security

- Never commit secrets (API keys, passwords)
- Use environment variables for sensitive config
- Validate all user input
