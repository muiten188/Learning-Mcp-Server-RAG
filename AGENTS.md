# Coding Agent Instructions

## General
- Follow existing project conventions.
- Prefer simple, maintainable solutions.
- Do not introduce dependencies unless requested.
- Do not modify unrelated code.
- For every task involving `mcp-platform/frontend`, read and follow
  `.agents/skills/angular-standard/SKILL.md` alongside this file.

## Java
- Always generate JavaDoc for new public and protected methods.
- Document parameters, return values, and exceptions.
- Follow Java naming conventions.
- Reuse existing utilities and services.
- Avoid unnecessary method extraction.

## TypeScript
- Always generate TSDoc for new exported functions,
  methods, classes, and interfaces.
- Document parameters and return values.
- Prefer strict typing; avoid `any`.
- Follow existing Angular conventions.

## Code Changes
- Preserve backward compatibility.
- Avoid unnecessary refactoring.
- Keep changes minimal and focused.

## Angular Architecture and Component Organization

### Package by Feature

- Always follow the Package by Feature architecture.
- Organize code by business feature rather than technical type.
- When creating a new component, place it inside the
  appropriate feature directory.
- Create a new feature directory if no suitable one exists.
- Keep feature-specific components, services, models,
  pipes, guards, and utilities inside their feature folder.
- Place reusable components and utilities in `shared/`
  only when they are genuinely shared across features.
- Avoid placing feature-specific code in global directories.
- Avoid circular dependencies between features.
- Prefer feature-level routing and lazy loading
  where appropriate.
- Follow existing project conventions when organizing files.

### Angular Component File Separation

- Always create separate files for new Angular components:
  - `.ts` for component logic.
  - `.html` for the component template.
- In `mcp-platform/frontend`, create a sibling `.css` file for every new Angular component and reference it with `styleUrl`.
- Style the component host with `:host` in its own stylesheet.
- Never use inline `template` for newly created components.
- Use `templateUrl` to reference the external HTML file.
- Never use inline `styles` for newly created components.
- Use `styleUrl` or `styleUrls` to reference the stylesheet.
- Do not embed large HTML templates inside TypeScript files.
- Keep TypeScript focused on component behavior and state.
- Keep HTML focused on presentation and template bindings.
- Keep component styling in its own CSS file. Do not style a child component from its parent stylesheet.
- Follow existing naming conventions for component files.

### Component Creation Example

When asked to create a `UserProfileComponent`,
generate the following structure:

```text
src/app/
├── core/
│   ├── auth/
│   ├── interceptors/
│   └── services/
├── shared/
│   ├── components/
│   ├── directives/
│   └── pipes/
└── features/
    └── users/
        ├── components/
        │   └── user-profile/
        │       ├── user-profile.ts
        │       ├── user-profile.html
        │       ├── user-profile.css
        │       └── user-profile.spec.ts
        ├── services/
        │   └── user.service.ts
        ├── models/
        │   └── user.model.ts
        └── users.routes.ts
```

### Component Implementation

Use standalone components unless the existing
project architecture requires otherwise.

Example TypeScript:

```typescript
import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  templateUrl: './user-profile.html',
  styleUrl: './user-profile.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserProfileComponent {
}
```

Example HTML:

```html
<section class="profile">
  <h2>User Profile</h2>
</section>
```

Example CSS:

```css
:host { display: block; }
.profile { display: flex; flex-direction: column; gap: 1rem; }
```

### Separation of Responsibilities

- Components handle presentation and user interaction.
- Services handle API communication and business logic.
- Models define data structures and contracts.
- Pipes handle reusable presentation transformations.
- Guards handle route access decisions.
- Utilities contain reusable pure helper functions.
- Avoid putting complex business logic in components.
- Avoid putting API requests directly inside components
  when a feature service is appropriate.
- Extract reusable logic into services or utilities
  when it improves maintainability.
- Do not create unnecessary abstractions or files.

### Angular Component Generation Rules

Whenever asked to create a new Angular component:

1. Identify the appropriate business feature.
2. Create the feature directory if necessary.
3. Create a dedicated component directory.
4. Generate a separate TypeScript component file.
5. Generate a separate HTML template file.
6. Create a sibling CSS file and style the component there.
7. Generate or update relevant tests.
8. Add JavaDoc/TSDoc to public methods where applicable.
9. Use Angular Signals when appropriate.
10. Use OnPush change detection.
11. Follow existing routing and dependency conventions.
12. Avoid modifying unrelated features.

### Existing Components

- Preserve existing component structures unless
  restructuring is explicitly requested.
- When substantially modifying a component that uses
  an inline template, prefer extracting it into
  a separate HTML file if the change is within scope.
- Do not automatically restructure unrelated components.
- Avoid creating empty files or unnecessary folders.
