# UI/UX System Instructions & Technical Specification

## 1. Core Architectural Principles

- **Box Model**: Enforce `box-sizing: border-box` globally.
- **Layout Engine**: Use a Base-4/8px Grid. All spacing (`padding`, `margin`, `gap`, `height`, `width`) must be derived from the scale:
  - `[4, 8, 12, 16, 24, 32, 48, 64, 80]px`
- **No Arbitrary Values**: Hardcoded pixel values outside this scale are strictly forbidden.
- **Stacking Context**: Use a standardized Z-index scale:
  - `sticky`: 100
  - `dropdown`: 200
  - `overlay`: 300
  - `modal`: 400
  - `tooltip`: 500

## 2. Semantic Token System (The "Source of Truth")

All styling must reference semantic variables. Do not use raw hex codes.

### Colors

- **Action-Primary**: Main interaction color.
- **Text-Main**: Primary content (High contrast).
- **Text-Muted**: Secondary/Meta content (Min. WCAG AA contrast).
- **Status-[Success|Warning|Error]**: Feedback semantic roles.
- **Border-Subtle**: Default divider/stroke color.
- **Surface-Main**: Background layout color.

### Typography

- **Family**: Configurable global variable.
- **Scale**:
  - `xs`: 12px
  - `sm`: 14px
  - `base`: 16px
  - `lg`: 20px
  - `xl`: 24px

## 3. Table Component Specifications

- **Structure**: Semantic `<table>` with `<thead>` and `<tbody>`.
- **Spacing**:
  - Row height minimum: 48px
  - Horizontal cell padding: 16px
- **Style**:
  - `border-bottom` only (1px, `Border-Subtle`)
  - Strictly no zebra-striping
- **Alignment**:
  - **Strings/IDs**: `text-align: left`
  - **Numbers/Dates/Prices**: `text-align: right` + `font-variant-numeric: tabular-nums`
- **Responsiveness**:
  - Wrap tables in a container with `overflow-x: auto`
  - Implement a visual affordance (shadow or gradient) to indicate horizontal scroll availability
- **Interactivity**:
  - Headers must use `cursor: pointer`
  - Include a Lucide icon (16px) to indicate `aria-sort` state

## 4. Iconography & Assets (Lucide)

- **Source**: Use https://github.com/lucide-icons/lucide for logic or the provided SVG archive.
- **Sizing Rules**:
  - Default: 16px
  - Headers: 24px
  - Empty States/Illustrative: 32px or 48px
- **Alignment**: Use `inline-flex` with `items-center` for perfect optical alignment with text.
- **Stroke**: Maintain consistent `stroke-width` (default: 2px).

## 5. Edge Cases & States (The "Professional" Layer)

- **Empty States**:
  - Centered layout
  - Icon (32px, muted) + Title + Subtitle + Action (Primary Button)
- **Error States (404/500)**:
  - Full-page dedicated layout
  - Direct users back to safety with a clear "Home" action
- **Interactive States**: Every button/input must have explicit CSS definitions for:
  - `:hover`
  - `:active`
  - `:disabled` (cursor: `not-allowed`)
  - `:focus-visible` (Mandatory 2px offset ring)
- **Loading States**:
  - Implement skeleton screens or consistent loading indicators using the `Action-Primary` color

## 6. Responsive Strategy

- **Mobile-First**: Use Flexbox/Grid for fluid layouts.
- **Constraints**: No fixed widths. Use `max-width` for containers.
- **Touch Targets**: Ensure all interactive elements have a minimum target size of 40x40px for mobile usability, regardless of visual size.
