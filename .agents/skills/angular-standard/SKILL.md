---
name: angular-standard
description: Apply modern Angular 22 conventions when creating, modifying, reviewing, or testing Angular applications, including components, services, routing, forms, state management, and CSS styling.
---

# Angular Standard Skill

## Scope

Use this skill for Angular application work. Follow the repository's `AGENTS.md`, existing architecture, and installed Angular version. Do not introduce a new dependency or rewrite existing patterns without a clear reason and approval.

## Architecture

- Organize application code by **feature**, not by technical type at the application root.
- Keep feature-specific components, services, models, routes, and utilities inside their feature directory.
- Put truly cross-feature primitives in `shared/`; put app-wide singleton infrastructure in `core/`.
- Prefer small, cohesive files and components with a single responsibility.
- Use descriptive, kebab-case file names and consistent class and symbol naming.

Example:

```text
src/app/
  core/
    auth/
    http/
  shared/
    ui/
    pipes/
  features/
    users/
      pages/
        user-list/
          user-list.ts
          user-list.html
          user-list.css
      components/
      data-access/
        user-api.service.ts
      models/
        user.model.ts
      users.routes.ts
  app.routes.ts
```

Follow the project's actual file naming convention if it differs.

## Components and Templates

- Prefer standalone components and explicit imports.
- Use `ChangeDetectionStrategy.OnPush` for new components unless there is a documented reason not to.
- Keep component templates in separate `.html` files and styles in separate `.css` files, matching this frontend's convention.
- Use `input()`, `input.required()`, `output()`, `model()`, and `computed()` when appropriate; avoid introducing legacy decorators in new code without a compatibility reason.
- Use Angular's built-in `@if`, `@for`, and `@switch` template control flow. Supply stable `track` expressions for `@for`.
- Keep business logic out of templates. Do not call expensive methods from templates.
- Prefer host bindings in component metadata over unnecessary DOM manipulation.
- Use semantic HTML, accessible labels, keyboard-accessible controls, and appropriate ARIA attributes.

## CSS and Design Variables

- Use `mcp-platform/frontend/src/variables.css` as the shared source for frontend design values. It is imported once by `mcp-platform/frontend/src/styles.css`, so component stylesheets can use its custom properties directly.
- When adding or changing colors, fonts, font weights, spacing, sizes, or radii, reuse an existing token with `var(--...)`. Add a clearly named token to `mcp-platform/frontend/src/variables.css` when a value is shared or represents an app-wide design choice.
- Keep component-specific measurements and CSS keywords in the component stylesheet. Do not duplicate an existing token's literal value in another CSS file.
- Keep responsive breakpoints literal in `@media` rules because CSS custom properties cannot be used in media conditions.

## State and Reactivity

- Use signals for synchronous local UI state and derived values.
- Use `computed()` for derived state rather than synchronizing redundant writable signals.
- Use `effect()` only for genuine side effects, not for ordinary state propagation.
- Use RxJS for asynchronous streams, HTTP composition, cancellation, and event streams when suitable.
- Prefer `async` pipe or `takeUntilDestroyed()` for subscriptions that require cleanup.
- Do not subscribe manually merely to copy observable values into component fields if a simpler reactive binding works.
- Use `toSignal()` and `toObservable()` when crossing reactive boundaries intentionally, with appropriate injection context and initial-value handling.

## Dependency Injection and Services

- Prefer `inject()` for dependency injection in new code.
- Use `providedIn: 'root'` only for genuinely app-wide services.
- Keep HTTP and persistence concerns in feature data-access services, not presentational components.
- Prefer typed public service APIs; avoid `any` and unsafe casts.
- Separate API DTOs from UI/domain models when their shapes or semantics differ.

## HTTP and Errors

- Use Angular `HttpClient` with typed responses.
- Centralize API base URLs in environment/configuration or an injection token; avoid hard-coded server hosts in components.
- Use interceptors for cross-cutting concerns such as authentication and standardized request handling.
- Handle loading, empty, success, and error states explicitly.
- Do not silently swallow errors. Show safe user-facing messages and preserve useful diagnostic context without exposing secrets.
- Never store credentials or tokens in source code.

## Routing

- Keep routes close to their features and lazy-load feature pages or route trees where useful.
- Prefer functional guards and resolvers where appropriate.
- Keep authorization enforced by the backend; frontend guards are for navigation and user experience, not security boundaries.
- Avoid putting unrelated business logic into route definitions.

## Forms

- Prefer typed reactive forms for nontrivial forms.
- Keep validation rules explicit and display accessible validation feedback.
- Use `ControlValueAccessor` for reusable custom form controls when appropriate.
- Do not mix template-driven and reactive approaches within the same form without a justified reason.

## TypeScript and Code Quality

- Respect strict TypeScript and Angular template checks.
- Prefer `readonly` for references that should not be reassigned.
- Use explicit types for public APIs and complex return values; allow inference for obvious locals.
- Avoid `any`, non-null assertions, and broad type assertions unless justified.
- Prefer pure functions and immutable updates for predictable state changes.
- Avoid unnecessary abstraction, premature generic frameworks, and excessive file splitting.
- Follow the project's formatter, ESLint rules, and naming conventions.
- Add TSDoc to exported utilities, complex public methods, and APIs where behavior, constraints, or side effects are not obvious. Do not add redundant comments to self-explanatory code.

## Performance

- Prefer OnPush, stable list tracking, lazy loading, and appropriately scoped state.
- Avoid expensive computations in templates and repeated unnecessary subscriptions.
- Use `@defer` for suitable noncritical UI, considering loading and accessibility behavior.
- Optimize only with evidence; avoid premature memoization or complexity.

## Testing

- Add or update tests for behavior changes, especially business logic, services, validation, and edge cases.
- Use the repository's configured test runner and Angular TestBed when appropriate.
- Test observable behavior rather than implementation details.
- Cover loading, error, empty, and successful outcomes for data-driven UI.
- Do not claim tests passed unless they were actually executed.

## Agent Workflow

1. Inspect nearby files, `package.json`, TypeScript config, and `AGENTS.md` before editing.
2. Reuse existing project conventions and installed dependencies.
3. Plan the smallest coherent change; place files in the relevant feature directory.
4. Implement accessible, typed, reactive code with separate template and styles for new components.
5. Add or update focused tests when relevant.
6. Run the available lint, type-check, test, or build commands if feasible.
7. Summarize changed files, key design choices, checks run, and any remaining risks.

## Avoid

- New NgModules for ordinary feature development unless integration requires them.
- Unnecessary global services or global state.
- Direct DOM access when Angular template bindings or supported APIs suffice.
- Nested subscriptions when RxJS composition is clearer.
- Using `effect()` to propagate state that should be `computed()`.
- Installing packages without asking when existing dependencies can solve the problem.
- Large refactors unrelated to the requested change.
